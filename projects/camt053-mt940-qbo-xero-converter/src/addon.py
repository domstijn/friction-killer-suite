"""BankFeedBridge core compiler: pure stdlib CAMT.053 XML & SWIFT MT940 -> QBO/OFX/Xero/DATEV."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

try:
    from .license_client import require_pro_feature, verify_license
except ImportError:
    from license_client import require_pro_feature, verify_license

APP_SLUG = "camt053-mt940-qbo-xero-converter"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_VgPF3c0DrjRVFW,prod_VeW6IYwGyYJkPv"
FREE_TX_LIMIT = 10

INTU_BID_PRESETS = {
    "3000": "Universal Checking / Wells Fargo (3000)",
    "2430": "Chase Bank (2430)",
    "10898": "Chase Business (10898)",
    "1001": "Bank of America (1001)",
    "6526": "Citibank (6526)",
}

SAMPLE_CAMT053_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
  <BkToCstmrStmt>
    <GrpHdr>
      <MsgId>CAMT053-SAMPLE-2026-11</MsgId>
      <CreDtTm>2026-11-12T18:00:00Z</CreDtTm>
    </GrpHdr>
    <Stmt>
      <Id>STMT-2026-11-01</Id>
      <Acct>
        <Id><IBAN>DE89370400440532013000</IBAN></Id>
        <Ccy>EUR</Ccy>
      </Acct>
      <Bal>
        <Tp><CdOrPrtry><Cd>OPBD</Cd></CdOrPrtry></Tp>
        <Amt Ccy="EUR">10000.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Dt><Dt>2026-11-01</Dt></Dt>
      </Bal>
      <Bal>
        <Tp><CdOrPrtry><Cd>CLBD</Cd></CdOrPrtry></Tp>
        <Amt Ccy="EUR">11845.50</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Dt><Dt>2026-11-12</Dt></Dt>
      </Bal>
      <Ntry>
        <Amt Ccy="EUR">2500.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <BookgDt><Dt>2026-11-10</Dt></BookgDt>
        <ValDt><Dt>2026-11-10</Dt></ValDt>
        <AcctSvcrRef>REF-2026-001</AcctSvcrRef>
        <NtryDtls>
          <TxDtls>
            <Refs><EndToEndId>E2E-INV-2026-01</EndToEndId></Refs>
            <RltdPties>
              <Dbtr><Nm>Acme GmbH</Nm></Dbtr>
              <DbtrAcct><Id><IBAN>DE44500105175407324931</IBAN></Id></DbtrAcct>
            </RltdPties>
            <RmtInf><Ustrd>Invoice 2026-01 SaaS Subscription</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">654.50</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <BookgDt><Dt>2026-11-12</Dt></BookgDt>
        <ValDt><Dt>2026-11-12</Dt></ValDt>
        <AcctSvcrRef>BATCH-2026-002</AcctSvcrRef>
        <NtryDtls>
          <TxDtls>
            <Refs><EndToEndId>E2E-HOST-001</EndToEndId></Refs>
            <AmtDtls><TxAmt><Amt Ccy="EUR">420.00</Amt></TxAmt></AmtDtls>
            <RltdPties>
              <Cdtr><Nm>CloudHost BV</Nm></Cdtr>
              <CdtrAcct><Id><IBAN>NL20INGB0001234567</IBAN></Id></CdtrAcct>
            </RltdPties>
            <RmtInf><Ustrd>Server Cluster November 2026</Ustrd></RmtInf>
          </TxDtls>
          <TxDtls>
            <Refs><EndToEndId>E2E-FEE-002</EndToEndId></Refs>
            <AmtDtls><TxAmt><Amt Ccy="EUR">234.50</Amt></TxAmt></AmtDtls>
            <RltdPties>
              <Cdtr><Nm>Stripe Processing Fee</Nm></Cdtr>
              <CdtrAcct><Id><IBAN>IE29AIBK93115212345678</IBAN></Id></CdtrAcct>
            </RltdPties>
            <RmtInf><Ustrd>SEPA Settlement Fee Batch 42</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
"""

SAMPLE_MT940 = """:20:MT940-2026-11
:25:NL91ABNA0417164300
:28C:00142/001
:60F:C261101EUR5000,00
:61:2611031103C1250,00NTRFNONREF//TXMT001
:86:/NAME/Nordic Partner AB/REMI/Invoice INV-2026-88/IBAN/SE4550000000058398257466
:61:2611051105D310,25NTRFNONREF//TXMT002
:86:166?00SEPA-LASTSCHRIFT?20EREF+E2E-CLOUD-99?21SVWZ+Managed Hosting Q4?31DE12500105170648489890?32Hetzner Online GmbH
:61:2611081108RD45,00NCHGNONREF//TXMT003
:86:/NAME/Wire Fee Reversal/REMI/Fee correction Q4
:62F:C261108EUR5984,75
-
"""

MT940_TAG_RE = re.compile(r"^:(\d{2}[A-Z]?):(.*)$")
MT940_BAL_RE = re.compile(r"^([CD])(\d{6})([A-Z]{3})([\d,\.]+)$")
MT940_TX_RE = re.compile(r"^(\d{6})(\d{4})?(RC|RD|C|D)(?:[A-Z](?=\d))?([\d,\.]+)([A-Z0-9]{4})([^/\r\n]*)(?://([^\r\n]+))?(.*)$")


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1].split(":", 1)[-1]


def _child_text(elem: ET.Element, path: list[str]) -> str:
    cur: list[ET.Element] = [elem]
    for step in path:
        nxt: list[ET.Element] = []
        for node in cur:
            for ch in node:
                if _local(ch.tag) == step:
                    nxt.append(ch)
        cur = nxt
        if not cur:
            return ""
    for node in cur:
        txt = (node.text or "").strip()
        if txt:
            return txt
    return ""


def _all_texts(elem: ET.Element, target_local: str) -> list[str]:
    out: list[str] = []
    for node in elem.iter():
        if _local(node.tag) == target_local and (node.text or "").strip():
            out.append(node.text.strip())
    return out


def _to_cents(raw: str, cdt_dbt: str = "CRDT") -> int:
    s = str(raw or "").strip().replace(",", ".")
    if not s:
        return 0
    try:
        dec = Decimal(s)
    except InvalidOperation:
        return 0
    cents = int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    ind = str(cdt_dbt or "").strip().upper()
    if ind in {"DBIT", "D", "RC"}:
        return -abs(cents)
    return abs(cents)


def _format_decimal_cents(cents: int, *, comma: bool = False) -> str:
    sign = "-" if cents < 0 else ""
    abs_val = abs(cents)
    s = f"{sign}{abs_val // 100}.{abs_val % 100:02d}"
    return s.replace(".", ",") if comma else s


def _make_fitid(stmt_id: str, account: str, tx_date: str, amount_cents: int, ref: str, occ: int) -> str:
    payload = f"{stmt_id}|{account}|{tx_date}|{amount_cents}|{ref}|{occ}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:16]
    compact_date = tx_date.replace("-", "")[:8] or "19700101"
    return f"{compact_date}-{digest}"[:32]


def _yymmdd_to_iso(raw: str) -> str:
    digits = re.sub(r"\D", "", str(raw or ""))
    if len(digits) < 6:
        return "1970-01-01"
    yy = int(digits[:2])
    mm = int(digits[2:4])
    dd = int(digits[4:6])
    year = 2000 + yy if yy < 80 else 1900 + yy
    return f"{year:04d}-{mm:02d}-{dd:02d}"


def _clean_ofx_text(text: str, limit: int) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    s = s.replace("&", "and").replace("<", "(").replace(">", ")")
    return s[:limit]


def parse_camt053_xml(xml_text: str, source_name: str = "statement.xml") -> dict[str, Any]:
    """Parse ISO 20022 CAMT.053 XML statements and flatten nested NtryDtls/TxDtls batches."""
    clean_xml = (xml_text or "").lstrip("\ufeff").strip()
    if not clean_xml:
        return {"ok": False, "errors": [f"{source_name}: Empty XML input."], "statements": [], "transactions": []}

    try:
        root = ET.fromstring(clean_xml)
    except ET.ParseError as exc:
        return {"ok": False, "errors": [f"{source_name}: Malformed XML ({exc})."], "statements": [], "transactions": []}

    stmts = [el for el in root.iter() if _local(el.tag) == "Stmt"]
    if not stmts:
        return {
            "ok": False,
            "errors": [f"{source_name}: No <Stmt> element found in CAMT.053 document."],
            "statements": [],
            "transactions": [],
        }

    statements: list[dict[str, Any]] = []
    all_txs: list[dict[str, Any]] = []

    for idx, stmt in enumerate(stmts, start=1):
        stmt_id = _child_text(stmt, ["Id"]) or f"{source_name}-STMT-{idx}"
        account = (
            _child_text(stmt, ["Acct", "Id", "IBAN"])
            or _child_text(stmt, ["Acct", "Id", "Othr", "Id"])
            or f"ACCT-{idx}"
        )
        currency = _child_text(stmt, ["Acct", "Ccy"]) or "EUR"

        open_bal: dict[str, Any] | None = None
        close_bal: dict[str, Any] | None = None
        for ch in stmt:
            if _local(ch.tag) != "Bal":
                continue
            code = _child_text(ch, ["Tp", "CdOrPrtry", "Cd"]).upper()
            amt_el = next((c for c in ch if _local(c.tag) == "Amt"), None)
            if amt_el is None:
                continue
            currency = amt_el.attrib.get("Ccy", currency) or currency
            ind = _child_text(ch, ["CdtDbtInd"]) or "CRDT"
            dt_str = (_child_text(ch, ["Dt", "Dt"]) or _child_text(ch, ["Dt", "DtTm"]) or "")[:10]
            bal_obj = {"code": code, "cents": _to_cents(amt_el.text or "", ind), "date": dt_str}
            if code in {"OPBD", "PRCD", "ITBD"}:
                if open_bal is None or code == "OPBD":
                    open_bal = bal_obj
            elif code in {"CLBD", "CLAV"}:
                if close_bal is None or code == "CLBD":
                    close_bal = bal_obj

        stmt_txs: list[dict[str, Any]] = []
        occ_counter: dict[tuple[str, str, int, str], int] = {}

        for ntry in stmt:
            if _local(ntry.tag) != "Ntry":
                continue
            ntry_amt_el = next((c for c in ntry if _local(c.tag) == "Amt"), None)
            ntry_amt_txt = (ntry_amt_el.text or "").strip() if ntry_amt_el is not None else "0"
            ntry_ccy = ntry_amt_el.attrib.get("Ccy", currency) if ntry_amt_el is not None else currency
            ntry_ind = _child_text(ntry, ["CdtDbtInd"]) or "CRDT"
            tx_date = (
                _child_text(ntry, ["BookgDt", "Dt"])
                or _child_text(ntry, ["BookgDt", "DtTm"])
                or _child_text(ntry, ["ValDt", "Dt"])
                or _child_text(ntry, ["ValDt", "DtTm"])
                or (close_bal or {}).get("date")
                or "1970-01-01"
            )[:10]
            ntry_ref = _child_text(ntry, ["AcctSvcrRef"])
            ntry_info = _child_text(ntry, ["AddtlNtryInf"])

            tx_dtls = [el for el in ntry.iter() if _local(el.tag) == "TxDtls"]
            if tx_dtls:
                for tx in tx_dtls:
                    tx_amt_el = next(
                        (el for el in tx.iter() if _local(el.tag) == "Amt" and (el.text or "").strip()),
                        None,
                    )
                    amt_txt = (tx_amt_el.text or "").strip() if tx_amt_el is not None else ntry_amt_txt
                    tx_ccy = tx_amt_el.attrib.get("Ccy", ntry_ccy) if tx_amt_el is not None else ntry_ccy
                    tx_ind = _child_text(tx, ["CdtDbtInd"]) or ntry_ind
                    amt_cents = _to_cents(amt_txt, tx_ind)
                    if amt_cents < 0:
                        payee = (
                            _child_text(tx, ["RltdPties", "Cdtr", "Nm"])
                            or _child_text(tx, ["RltdPties", "UltmtCdtr", "Nm"])
                            or _child_text(tx, ["RltdPties", "Dbtr", "Nm"])
                            or "Bank Debit"
                        )
                        cp_iban = (
                            _child_text(tx, ["RltdPties", "CdtrAcct", "Id", "IBAN"])
                            or _child_text(tx, ["RltdPties", "DbtrAcct", "Id", "IBAN"])
                        )
                    else:
                        payee = (
                            _child_text(tx, ["RltdPties", "Dbtr", "Nm"])
                            or _child_text(tx, ["RltdPties", "UltmtDbtr", "Nm"])
                            or _child_text(tx, ["RltdPties", "Cdtr", "Nm"])
                            or "Bank Credit"
                        )
                        cp_iban = (
                            _child_text(tx, ["RltdPties", "DbtrAcct", "Id", "IBAN"])
                            or _child_text(tx, ["RltdPties", "CdtrAcct", "Id", "IBAN"])
                        )
                    ref = (
                        _child_text(tx, ["Refs", "EndToEndId"])
                        or _child_text(tx, ["Refs", "TxId"])
                        or ntry_ref
                        or "NONREF"
                    )
                    ustrd_list = _all_texts(tx, "Ustrd")
                    memo = " | ".join(ustrd_list) or _child_text(tx, ["AddtlTxInf"]) or ntry_info or payee
                    sig = (account, tx_date, amt_cents, ref)
                    occ = occ_counter.get(sig, 0)
                    occ_counter[sig] = occ + 1
                    stmt_txs.append(
                        {
                            "source": source_name,
                            "format": "camt053",
                            "statement_id": stmt_id,
                            "account": account,
                            "currency": tx_ccy or currency,
                            "date": tx_date,
                            "amount_cents": amt_cents,
                            "type": "CREDIT" if amt_cents >= 0 else "DEBIT",
                            "payee": payee,
                            "counterparty_iban": cp_iban,
                            "memo": memo,
                            "reference": ref,
                            "fitid": _make_fitid(stmt_id, account, tx_date, amt_cents, ref, occ),
                        }
                    )
            else:
                amt_cents = _to_cents(ntry_amt_txt, ntry_ind)
                ref = ntry_ref or "NONREF"
                memo = ntry_info or ("Bank Credit" if amt_cents >= 0 else "Bank Debit")
                sig = (account, tx_date, amt_cents, ref)
                occ = occ_counter.get(sig, 0)
                occ_counter[sig] = occ + 1
                stmt_txs.append(
                    {
                        "source": source_name,
                        "format": "camt053",
                        "statement_id": stmt_id,
                        "account": account,
                        "currency": ntry_ccy or currency,
                        "date": tx_date,
                        "amount_cents": amt_cents,
                        "type": "CREDIT" if amt_cents >= 0 else "DEBIT",
                        "payee": memo[:32],
                        "counterparty_iban": "",
                        "memo": memo,
                        "reference": ref,
                        "fitid": _make_fitid(stmt_id, account, tx_date, amt_cents, ref, occ),
                    }
                )

        tx_net = sum(t["amount_cents"] for t in stmt_txs)
        open_cents = open_bal["cents"] if open_bal else 0
        close_cents = close_bal["cents"] if close_bal else (open_cents + tx_net)
        has_both_bals = open_bal is not None and close_bal is not None
        variance = (open_cents + tx_net - close_cents) if has_both_bals else 0

        statements.append(
            {
                "source": source_name,
                "format": "camt053",
                "statement_id": stmt_id,
                "account": account,
                "currency": currency,
                "opening_balance_cents": open_cents,
                "closing_balance_cents": close_cents,
                "closing_date": (close_bal or {}).get("date") or (stmt_txs[-1]["date"] if stmt_txs else "1970-01-01"),
                "tx_net_cents": tx_net,
                "tx_count": len(stmt_txs),
                "variance_cents": variance,
                "reconciled": variance == 0,
            }
        )
        all_txs.extend(stmt_txs)

    return {"ok": True, "errors": [], "statements": statements, "transactions": all_txs}


def _parse_mt940_86(raw_86: str) -> tuple[str, str, str]:
    """Extract (payee, counterparty_iban, memo) from SEPA /NAME/... or German ?20..?33 subfields."""
    txt = re.sub(r"\s+", " ", (raw_86 or "")).strip()
    if not txt:
        return "Bank Transfer", "", ""

    if re.search(r"\?\d{2}", txt):
        tags: dict[str, str] = {}
        parts = re.split(r"\?(\d{2})", txt)
        for i in range(1, len(parts) - 1, 2):
            code = parts[i]
            val = parts[i + 1].strip()
            tags[code] = (tags.get(code, "") + " " + val).strip() if code in tags else val
        payee = f"{tags.get('32', '')} {tags.get('33', '')}".strip() or tags.get("20", "") or "Bank Transfer"
        cp_iban = tags.get("31", "").strip()
        memo_parts = [tags[k] for k in sorted(tags.keys()) if "20" <= k <= "29" and tags[k]]
        memo = " | ".join(memo_parts) or txt
        return payee, cp_iban, memo

    if "/NAME/" in txt or "/REMI/" in txt or "/IBAN/" in txt:
        fields: dict[str, str] = {}
        matches = list(re.finditer(r"/([A-Z]{2,8})/", txt))
        for idx, m in enumerate(matches):
            start = m.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(txt)
            fields[m.group(1)] = txt[start:end].strip()
        payee = fields.get("NAME") or fields.get("CNTP") or "Bank Transfer"
        cp_iban = fields.get("IBAN") or ""
        memo = fields.get("REMI") or fields.get("EREF") or txt
        return payee, cp_iban, memo

    return txt[:32], "", txt


def parse_mt940_text(mt940_text: str, source_name: str = "statement.sta") -> dict[str, Any]:
    """Parse SWIFT MT940 statements supporting :60F:/:62F:, :61: (C/D/RC/RD), and :86: subfields."""
    clean = (mt940_text or "").lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not clean:
        return {"ok": False, "errors": [f"{source_name}: Empty MT940 input."], "statements": [], "transactions": []}

    raw_fields: list[tuple[str, str]] = []
    for raw_line in clean.splitlines():
        line = raw_line.rstrip()
        if not line or line == "-" or line == "$":
            if line == "-":
                raw_fields.append(("__END__", ""))
            continue
        m = MT940_TAG_RE.match(line)
        if m:
            raw_fields.append((m.group(1).upper(), m.group(2).strip()))
        elif raw_fields and raw_fields[-1][0] != "__END__":
            prev_tag, prev_val = raw_fields[-1]
            sep = "" if prev_tag == "86" and line.startswith("?") else " "
            raw_fields[-1] = (prev_tag, f"{prev_val}{sep}{line.strip()}".strip())

    blocks: list[list[tuple[str, str]]] = []
    cur_block: list[tuple[str, str]] = []
    for tag, val in raw_fields:
        if tag == "__END__":
            if cur_block:
                blocks.append(cur_block)
                cur_block = []
        else:
            if tag == "20" and any(t == "61" or t == "62F" for t, _ in cur_block):
                blocks.append(cur_block)
                cur_block = []
            cur_block.append((tag, val))
    if cur_block:
        blocks.append(cur_block)

    if not blocks:
        return {"ok": False, "errors": [f"{source_name}: No MT940 tags found."], "statements": [], "transactions": []}

    statements: list[dict[str, Any]] = []
    all_txs: list[dict[str, Any]] = []

    for idx, block in enumerate(blocks, start=1):
        stmt_id = f"{source_name}-MT-{idx}"
        account = f"MT940-ACCT-{idx}"
        currency = "EUR"
        open_cents: int | None = None
        close_cents: int | None = None
        close_date = "1970-01-01"
        stmt_txs: list[dict[str, Any]] = []
        occ_counter: dict[tuple[str, str, int, str], int] = {}

        for tag, val in block:
            if tag == "20" and val:
                stmt_id = val
            elif tag == "25" and val:
                account = val.split()[0]
            elif tag in {"60F", "60M"}:
                bm = MT940_BAL_RE.match(val.replace(" ", ""))
                if bm:
                    ind, dt6, ccy, amt = bm.groups()
                    currency = ccy
                    if open_cents is None or tag == "60F":
                        open_cents = _to_cents(amt, ind)
            elif tag in {"62F", "62M"}:
                bm = MT940_BAL_RE.match(val.replace(" ", ""))
                if bm:
                    ind, dt6, ccy, amt = bm.groups()
                    currency = ccy
                    close_cents = _to_cents(amt, ind)
                    close_date = _yymmdd_to_iso(dt6)
            elif tag == "61":
                tm = MT940_TX_RE.match(val.strip())
                if not tm:
                    continue
                val6, _ent4, ind, amt, _code4, cust_ref, bank_ref, tail = tm.groups()
                tx_date = _yymmdd_to_iso(val6)
                amt_cents = _to_cents(amt, ind)
                ref = (bank_ref or cust_ref or tail or "NONREF").strip()
                sig = (account, tx_date, amt_cents, ref)
                occ = occ_counter.get(sig, 0)
                occ_counter[sig] = occ + 1
                stmt_txs.append(
                    {
                        "source": source_name,
                        "format": "mt940",
                        "statement_id": stmt_id,
                        "account": account,
                        "currency": currency,
                        "date": tx_date,
                        "amount_cents": amt_cents,
                        "type": "CREDIT" if amt_cents >= 0 else "DEBIT",
                        "payee": ref[:32] or "Bank Transfer",
                        "counterparty_iban": "",
                        "memo": ref,
                        "reference": ref,
                        "fitid": _make_fitid(stmt_id, account, tx_date, amt_cents, ref, occ),
                    }
                )
            elif tag == "86" and stmt_txs:
                payee, cp_iban, memo = _parse_mt940_86(val)
                stmt_txs[-1]["payee"] = payee
                stmt_txs[-1]["counterparty_iban"] = cp_iban
                stmt_txs[-1]["memo"] = memo

        if not stmt_txs and open_cents is None and close_cents is None:
            continue

        tx_net = sum(t["amount_cents"] for t in stmt_txs)
        eff_open = open_cents if open_cents is not None else 0
        eff_close = close_cents if close_cents is not None else (eff_open + tx_net)
        variance = (eff_open + tx_net - eff_close) if (open_cents is not None and close_cents is not None) else 0
        statements.append(
            {
                "source": source_name,
                "format": "mt940",
                "statement_id": stmt_id,
                "account": account,
                "currency": currency,
                "opening_balance_cents": eff_open,
                "closing_balance_cents": eff_close,
                "closing_date": close_date if close_cents is not None else (stmt_txs[-1]["date"] if stmt_txs else "1970-01-01"),
                "tx_net_cents": tx_net,
                "tx_count": len(stmt_txs),
                "variance_cents": variance,
                "reconciled": variance == 0,
            }
        )
        all_txs.extend(stmt_txs)

    if not statements:
        return {"ok": False, "errors": [f"{source_name}: Failed to extract MT940 statements."], "statements": [], "transactions": []}

    return {"ok": True, "errors": [], "statements": statements, "transactions": all_txs}


def compile_bank_statements(
    docs: list[tuple[str, str]],
    *,
    intu_bid: str = "3000",
    account_type: str = "CHECKING",
    datev_bank_account: str = "1200",
    pro_unlocked: bool = False,
) -> dict[str, Any]:
    """Parse one or more CAMT.053 XML / MT940 statements, reconcile balances, and enforce Free/Pro limits."""
    if not docs:
        return {"ok": False, "errors": ["No statement files provided."], "warnings": []}

    statements: list[dict[str, Any]] = []
    all_txs: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []

    for name, raw_text in docs:
        txt = (raw_text or "").lstrip("\ufeff").strip()
        if not txt:
            warnings.append(f"{name}: Empty file skipped.")
            continue
        if "<Document" in txt or "<BkToCstmrStmt" in txt or "<Stmt" in txt or txt.startswith("<"):
            parsed = parse_camt053_xml(txt, source_name=name)
        elif ":20:" in txt or ":60F:" in txt or ":61:" in txt:
            parsed = parse_mt940_text(txt, source_name=name)
        else:
            errors.append(f"{name}: Unrecognized bank statement format (expected CAMT.053 XML or SWIFT MT940).")
            continue

        if not parsed["ok"]:
            errors.extend(parsed["errors"])
            continue
        statements.extend(parsed["statements"])
        all_txs.extend(parsed["transactions"])

    if not statements and errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    for st in statements:
        if not st["reconciled"]:
            warnings.append(
                f"Statement '{st['statement_id']}' ({st['account']}) has balance variance of {_format_decimal_cents(st['variance_cents'])} {st['currency']}."
            )

    total_tx = len(all_txs)
    truncated = (not pro_unlocked) and total_tx > FREE_TX_LIMIT
    active_txs = all_txs if pro_unlocked else all_txs[:FREE_TX_LIMIT]
    if truncated:
        warnings.append(
            f"Free tier preview capped at {FREE_TX_LIMIT} of {total_tx} transactions (matching ProperSoft trial cap). Activate Pro for unlimited statements."
        )

    net_cents = sum(t["amount_cents"] for t in active_txs)
    total_variance = sum(abs(s["variance_cents"]) for s in statements)
    summary = {
        "statements_count": len(statements),
        "total_transactions": total_tx,
        "processed_transactions": len(active_txs),
        "reconciled_statements": sum(1 for s in statements if s["reconciled"]),
        "net_flow_cents": net_cents,
        "net_flow_formatted": _format_decimal_cents(net_cents),
        "total_abs_variance_cents": total_variance,
        "all_reconciled": total_variance == 0,
        "intu_bid": str(intu_bid),
        "account_type": account_type,
        "datev_bank_account": datev_bank_account,
    }

    return {
        "ok": len(errors) == 0 or len(statements) > 0,
        "truncated_by_free_tier": truncated,
        "free_tx_limit": FREE_TX_LIMIT,
        "summary": summary,
        "statements": statements,
        "transactions": active_txs,
        "warnings": warnings,
        "errors": errors,
    }


def render_xero_csv(result: dict[str, Any]) -> str:
    """Render Xero bank statement CSV (*Date,*Amount,Payee,Description,Reference,Cheque Number)."""
    buf = io.StringIO()
    headers = ["*Date", "*Amount", "Payee", "Description", "Reference", "Cheque Number"]
    writer = csv.DictWriter(buf, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for tx in result.get("transactions", []):
        writer.writerow(
            {
                "*Date": tx["date"],
                "*Amount": _format_decimal_cents(tx["amount_cents"]),
                "Payee": tx["payee"],
                "Description": tx["memo"],
                "Reference": tx["reference"],
                "Cheque Number": "",
            }
        )
    return buf.getvalue().rstrip("\n")


def _render_ofx_or_qbo(
    result: dict[str, Any],
    *,
    include_intuit: bool,
    intu_bid: str,
    account_type: str,
) -> str:
    txs = result.get("transactions", [])
    stmts = result.get("statements", [])
    by_acct: dict[str, list[dict[str, Any]]] = {}
    for tx in txs:
        by_acct.setdefault(tx["account"], []).append(tx)
    stmt_by_acct = {s["account"]: s for s in stmts}

    asof = (stmts[-1]["closing_date"].replace("-", "") + "120000") if stmts else "20261123120000"
    bid = str(intu_bid or "3000").strip()
    atype = str(account_type or "CHECKING").strip().upper()
    if atype not in {"CHECKING", "SAVINGS", "CREDITLINE", "MONEYMRKT"}:
        atype = "CHECKING"

    lines = [
        "OFXHEADER:100",
        "DATA:OFXSGML",
        "VERSION:102",
        "SECURITY:NONE",
        "ENCODING:UTF-8",
        "CHARSET:CSUTF8",
        "COMPRESSION:NONE",
        "OLDFILEUID:NONE",
        "NEWFILEUID:NONE",
        "",
        "<OFX>",
        "  <SIGNONMSGSRSV1>",
        "    <SONRS>",
        "      <STATUS>",
        "        <CODE>0</CODE>",
        "        <SEVERITY>INFO</SEVERITY>",
        "      </STATUS>",
        f"      <DTSERVER>{asof}</DTSERVER>",
        "      <LANGUAGE>ENG</LANGUAGE>",
    ]
    if include_intuit:
        lines.extend(
            [
                f"      <INTU.BID>{bid}</INTU.BID>",
                "      <INTU.USERID>BankFeedBridge</INTU.USERID>",
            ]
        )
    lines.extend(["    </SONRS>", "  </SIGNONMSGSRSV1>", "  <BANKMSGSRSV1>"])

    for idx, (acct, acct_txs) in enumerate(by_acct.items(), start=1):
        st = stmt_by_acct.get(acct, {})
        ccy = st.get("currency") or (acct_txs[0].get("currency") if acct_txs else "EUR")
        close_str = _format_decimal_cents(int(st.get("closing_balance_cents", 0)))
        close_dt = str(st.get("closing_date") or "2026-11-23").replace("-", "") + "120000"
        dates = sorted(t["date"] for t in acct_txs) if acct_txs else ["2026-11-23"]
        dt_start = dates[0].replace("-", "") + "000000"
        dt_end = dates[-1].replace("-", "") + "235959"
        bank_id = bid if include_intuit else (acct[:8] or "BANK0001")

        lines.extend(
            [
                "    <STMTTRNRS>",
                f"      <TRNUID>{idx}</TRNUID>",
                "      <STATUS>",
                "        <CODE>0</CODE>",
                "        <SEVERITY>INFO</SEVERITY>",
                "      </STATUS>",
                "      <STMTRS>",
                f"        <CURDEF>{ccy}</CURDEF>",
                "        <BANKACCTFROM>",
                f"          <BANKID>{_clean_ofx_text(bank_id, 9)}</BANKID>",
                f"          <ACCTID>{_clean_ofx_text(acct, 22)}</ACCTID>",
                f"          <ACCTTYPE>{atype}</ACCTTYPE>",
                "        </BANKACCTFROM>",
                "        <BANKTRANLIST>",
                f"          <DTSTART>{dt_start}</DTSTART>",
                f"          <DTEND>{dt_end}</DTEND>",
            ]
        )
        for t in acct_txs:
            dt_post = t["date"].replace("-", "") + "120000"
            amt_str = _format_decimal_cents(t["amount_cents"])
            name = _clean_ofx_text(t["payee"], 32)
            memo = _clean_ofx_text(t["memo"], 255)
            lines.extend(
                [
                    "          <STMTTRN>",
                    f"            <TRNTYPE>{t['type']}</TRNTYPE>",
                    f"            <DTPOSTED>{dt_post}</DTPOSTED>",
                    f"            <TRNAMT>{amt_str}</TRNAMT>",
                    f"            <FITID>{t['fitid']}</FITID>",
                    f"            <NAME>{name}</NAME>",
                    f"            <MEMO>{memo}</MEMO>",
                    "          </STMTTRN>",
                ]
            )
        lines.extend(
            [
                "        </BANKTRANLIST>",
                "        <LEDGERBAL>",
                f"          <BALAMT>{close_str}</BALAMT>",
                f"          <DTASOF>{close_dt}</DTASOF>",
                "        </LEDGERBAL>",
                "      </STMTRS>",
                "    </STMTTRNRS>",
            ]
        )

    lines.extend(["  </BANKMSGSRSV1>", "</OFX>"])
    return "\n".join(lines)


def render_qbo_web_connect(
    result: dict[str, Any],
    *,
    intu_bid: str = "3000",
    account_type: str = "CHECKING",
    pro_unlocked: bool = False,
) -> str:
    """Render Pro-gated Intuit QuickBooks Web Connect (.qbo) OFX 102 SGML with <INTU.BID>."""
    if not pro_unlocked:
        raise PermissionError("Pro license required for QuickBooks Web Connect (.qbo) export.")
    return _render_ofx_or_qbo(result, include_intuit=True, intu_bid=intu_bid, account_type=account_type)


def render_xero_ofx(
    result: dict[str, Any],
    *,
    account_type: str = "CHECKING",
    pro_unlocked: bool = False,
) -> str:
    """Render Pro-gated standard Xero .ofx statement without Intuit-proprietary tags."""
    if not pro_unlocked:
        raise PermissionError("Pro license required for Xero .ofx export.")
    return _render_ofx_or_qbo(result, include_intuit=False, intu_bid="", account_type=account_type)


def render_datev_bank_csv(
    result: dict[str, Any],
    *,
    bank_account: str = "1200",
    pro_unlocked: bool = False,
) -> str:
    """Render Pro-gated semicolon-delimited DATEV bank Buchungsstapel CSV with comma decimals & S/H."""
    if not pro_unlocked:
        raise PermissionError("Pro license required for DATEV bank CSV export.")
    buf = io.StringIO()
    headers = [
        "Umsatz",
        "Soll/Haben",
        "WKZ",
        "Konto",
        "Gegenkonto",
        "Belegdatum",
        "Belegfeld 1",
        "Buchungstext",
    ]
    writer = csv.DictWriter(buf, fieldnames=headers, delimiter=";", lineterminator="\n")
    writer.writeheader()
    for tx in result.get("transactions", []):
        amt_cents = int(tx["amount_cents"])
        sh = "S" if amt_cents >= 0 else "H"
        contra = "1360"
        date_parts = tx["date"].split("-")
        belegdatum = f"{date_parts[2]}{date_parts[1]}" if len(date_parts) == 3 else "0101"
        text = re.sub(r"[\r\n;]+", " ", f"{tx['payee']} - {tx['memo']}").strip()[:60]
        writer.writerow(
            {
                "Umsatz": _format_decimal_cents(abs(amt_cents), comma=True),
                "Soll/Haben": sh,
                "WKZ": tx["currency"],
                "Konto": bank_account,
                "Gegenkonto": contra,
                "Belegdatum": belegdatum,
                "Belegfeld 1": str(tx["reference"])[:36],
                "Buchungstext": text,
            }
        )
    return buf.getvalue().rstrip("\n")


def unlock_pro(license_key: str, *, cache_dir: str | None = None) -> dict[str, Any]:
    """Validate and cache a Stripe Managed Payments / Bundle Pro license key."""
    return verify_license(
        license_key,
        provider=PROVIDER,
        product_id=DEFAULT_PRODUCT_ID,
        app_slug=APP_SLUG,
        cache_dir=cache_dir,
    )


def check_pro_gate(*, cache_dir: str | None = None) -> dict[str, Any]:
    """Check cached Pro license state."""
    return require_pro_feature("bankfeed_pro_exports", app_slug=APP_SLUG, cache_dir=cache_dir)
