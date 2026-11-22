"""AmzSettlementBridge core Amazon Seller Flat-File V2 parser and double-entry clearing journal compiler."""

from __future__ import annotations

import csv
import io
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

FREE_ROW_LIMIT = 15

BUCKET_DEFS: list[tuple[str, str, str, str]] = [
    ("sales_principal", "Amazon Sales (Principal & Shipping)", "200", "8400"),
    ("refunds", "Amazon Customer Refunds", "205", "8700"),
    ("promotions", "Amazon Promotional Rebates", "207", "8730"),
    ("sales_tax", "Amazon Sales Tax / VAT Collected", "220", "1776"),
    ("marketplace_facilitator_tax", "Marketplace Facilitator Tax Withheld", "221", "1779"),
    ("amazon_fba_selling_fees", "Amazon FBA, Referral & Storage Fees", "404", "4970"),
    ("amazon_advertising_ppc", "Amazon Sponsored Ads (PPC)", "406", "4600"),
    ("reserve_carry_forward", "Amazon Account-Level Reserve Hold/Release", "125", "1365"),
]

BANK_CLEARING_ACCOUNT = ("net_bank_deposit", "Amazon Net Bank Deposit Clearing", "120", "1360")

SAMPLE_AMAZON_V2_TSV = "\n".join(
    [
        "settlement-id\tsettlement-start-date\tsettlement-end-date\tdeposit-date\ttotal-amount\tcurrency\ttransaction-type\torder-id\tmarketplace-name\tposted-date\tamount-type\tamount-description\tamount",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t264.10\tEUR\t\t\t\t\t\t\t",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-001\tAmazon.de\t2026-11-02\tItemPrice\tPrincipal\t120.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-001\tAmazon.de\t2026-11-02\tItemPrice\tTax\t22.80",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-001\tAmazon.de\t2026-11-02\tItemFees\tCommission\t-18.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-001\tAmazon.de\t2026-11-02\tItemFees\tFBAPerUnitFulfillmentFee\t-5.40",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-002\tAmazon.de\t2026-11-04\tItemPrice\tPrincipal\t200.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-002\tAmazon.de\t2026-11-04\tItemPrice\tShipping\t10.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-002\tAmazon.de\t2026-11-04\tItemWithheldTax\tMarketplaceFacilitatorTax-Principal\t-38.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-002\tAmazon.de\t2026-11-04\tItemPrice\tTax\t38.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-002\tAmazon.de\t2026-11-04\tPromotion\tPromoRebate\t-10.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-002\tAmazon.de\t2026-11-04\tItemFees\tCommission\t-30.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tOrder\t302-1001-002\tAmazon.de\t2026-11-04\tItemFees\tFBAPerUnitFulfillmentFee\t-6.50",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tRefund\t302-1001-003\tAmazon.de\t2026-11-06\tItemPrice\tPrincipal\t-40.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tRefund\t302-1001-003\tAmazon.de\t2026-11-06\tItemFees\tRefundCommission\t4.20",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tServiceFee\t\tAmazon.de\t2026-11-10\tFBA Inventory Storage Fee\tStorage Fee\t-14.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tServiceFee\t\tAmazon.de\t2026-11-11\tCost of Advertising\tTransactionTotalAmount\t-24.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tother-transaction\t\tAmazon.de\t2026-11-01\tPrevious Reserve Amount Balance\tPrevious Reserve Amount Balance\t95.00",
        "2184990101\t2026-11-01\t2026-11-15\t2026-11-16\t\tEUR\tother-transaction\t\tAmazon.de\t2026-11-15\tCurrent Reserve Amount\tCurrent Reserve Amount\t-40.00",
        "2184990102\t2026-11-16\t2026-11-30\t2026-12-01\t106.50\tEUR\t\t\t\t\t\t\t",
        "2184990102\t2026-11-16\t2026-11-30\t2026-12-01\t\tEUR\tOrder\t302-2001-001\tAmazon.fr\t2026-11-18\tItemPrice\tPrincipal\t150.00",
        "2184990102\t2026-11-16\t2026-11-30\t2026-12-01\t\tEUR\tOrder\t302-2001-001\tAmazon.fr\t2026-11-18\tItemFees\tCommission\t-22.50",
        "2184990102\t2026-11-16\t2026-11-30\t2026-12-01\t\tEUR\tServiceFee\t\tAmazon.fr\t2026-11-20\tCost of Advertising\tTransactionTotalAmount\t-21.00",
    ]
)


def _to_cents(raw: Any) -> int:
    text = str(raw if raw is not None else "").strip()
    if not text:
        return 0
    cleaned = re.sub(r"[€$£\s]", "", text)
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        dec = Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return int(dec * 100)
    except InvalidOperation:
        return 0


def _fmt_cents(cents: int) -> str:
    return f"{Decimal(cents) / Decimal(100):.2f}"


def _pick(lowered: dict[str, str], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        if key in lowered and lowered[key] != "":
            return lowered[key]
    return default


def _detect_delimiter(text: str) -> str:
    first_line = next((ln for ln in text.splitlines() if ln.strip()), "")
    if "\t" in first_line and first_line.count("\t") >= max(first_line.count(","), first_line.count(";")):
        return "\t"
    if ";" in first_line and first_line.count(";") > first_line.count(","):
        return ";"
    return ","


def parse_amazon_settlement(text: str) -> list[dict[str, Any]]:
    """Parse Amazon Flat-File V2 (.txt/.tsv/.csv) separating header summary totals from line items."""
    cleaned = str(text or "").strip()
    if not cleaned:
        return []

    delimiter = _detect_delimiter(cleaned)
    reader = csv.DictReader(io.StringIO(cleaned), delimiter=delimiter)
    expected_totals: dict[str, int] = {}
    items: list[dict[str, Any]] = []

    for idx, raw_row in enumerate(reader, start=1):
        if not any(str(v or "").strip() for v in raw_row.values()):
            continue
        lowered = {
            str(k).strip().lower(): str(v).strip()
            for k, v in raw_row.items()
            if k is not None
        }
        sid = _pick(lowered, ("settlement-id", "settlement_id"), "settlement-1")
        total_raw = _pick(lowered, ("total-amount", "total_amount"), "")
        if total_raw != "" and sid not in expected_totals:
            expected_totals[sid] = _to_cents(total_raw)

        amt_raw = _pick(lowered, ("amount", "transaction-amount"), "")
        tx_type = _pick(lowered, ("transaction-type", "transaction_type", "type"), "")
        amt_type = _pick(lowered, ("amount-type", "amount_type"), "")
        amt_desc = _pick(lowered, ("amount-description", "amount_description", "description"), "")

        # Amazon Flat-File V2 includes a top summary row with total-amount set and empty amount/description.
        if amt_raw == "" and not tx_type and not amt_type and not amt_desc:
            continue

        dep_date = _pick(lowered, ("deposit-date", "deposit_date", "settlement-end-date", "posted-date"), "2026-11-16")[:10]
        currency = (_pick(lowered, ("currency",), "EUR") or "EUR").upper()
        items.append(
            {
                "row_num": idx,
                "settlement_id": sid,
                "settlement_start_date": _pick(lowered, ("settlement-start-date", "settlement_start_date"), dep_date)[:10],
                "settlement_end_date": _pick(lowered, ("settlement-end-date", "settlement_end_date"), dep_date)[:10],
                "deposit_date": dep_date,
                "currency": currency,
                "expected_total_cents": expected_totals.get(sid),
                "transaction_type": tx_type,
                "order_id": _pick(lowered, ("order-id", "order_id"), ""),
                "marketplace_name": _pick(lowered, ("marketplace-name", "marketplace_name"), ""),
                "posted_date": _pick(lowered, ("posted-date", "posted_date"), dep_date)[:10],
                "amount_type": amt_type,
                "amount_description": amt_desc,
                "amount_cents": _to_cents(amt_raw),
            }
        )
    return items


def classify_line_bucket(row: dict[str, Any]) -> str:
    """Map an Amazon Flat-File V2 row onto one of 8 accounting clearing buckets."""
    tx_type = str(row.get("transaction_type") or "").lower()
    amt_type = str(row.get("amount_type") or "").lower()
    amt_desc = str(row.get("amount_description") or "").lower()
    combined = f"{tx_type} {amt_type} {amt_desc}"

    if "advertising" in combined or "ppc" in combined or "sponsored" in combined:
        return "amazon_advertising_ppc"
    if "reserve" in combined:
        return "reserve_carry_forward"
    if "marketplacefacilitator" in combined or "facilitator" in combined or "itemwithheldtax" in combined:
        return "marketplace_facilitator_tax"
    if "promotion" in amt_type or "promo" in amt_desc or "rebate" in amt_desc:
        return "promotions"
    if (
        "fee" in amt_type
        or "fee" in amt_desc
        or "commission" in amt_desc
        or "fba" in combined
        or "storage" in combined
        or "referral" in amt_desc
        or "servicefee" in tx_type
        or "closing" in amt_desc
        or "disposal" in amt_desc
        or "removal" in amt_desc
    ):
        return "amazon_fba_selling_fees"
    if "refund" in tx_type or "chargeback" in tx_type or "reversal" in tx_type:
        if "tax" in amt_desc or "vat" in amt_desc:
            return "sales_tax"
        return "refunds"
    if "tax" in amt_desc or "vat" in amt_desc:
        return "sales_tax"
    return "sales_principal"


def compile_settlement_journals(rows: list[dict[str, Any]], *, pro_unlocked: bool = False) -> dict[str, Any]:
    """Compile itemized settlement rows into exact integer-cent double-entry journals."""
    total_input_rows = len(rows)
    if not rows:
        return {
            "ok": False,
            "error": "No itemized Amazon settlement rows found.",
            "pro_unlocked": pro_unlocked,
            "truncated_free_tier": False,
            "total_input_rows": 0,
            "processed_rows": 0,
            "truncated_rows": 0,
            "summary": {},
            "settlements": [],
            "warnings": [],
        }

    first_sid = rows[0]["settlement_id"]
    if pro_unlocked:
        selected = rows
        truncated_free_tier = False
    else:
        first_sid_rows = [r for r in rows if r["settlement_id"] == first_sid]
        selected = first_sid_rows[:FREE_ROW_LIMIT]
        truncated_free_tier = len(selected) < total_input_rows

    truncated_rows = max(0, total_input_rows - len(selected))

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in selected:
        grouped.setdefault(row["settlement_id"], []).append(row)

    warnings: list[str] = []
    settlements: list[dict[str, Any]] = []

    tot_gross = 0
    tot_fees_ads = 0
    tot_fac_tax = 0
    tot_reserve = 0
    tot_deposit = 0
    tot_debits = 0
    tot_credits = 0

    for sid, s_rows in grouped.items():
        first = s_rows[0]
        deposit_date = first.get("deposit_date") or "2026-11-16"
        currency = first.get("currency") or "EUR"
        expected_total = first.get("expected_total_cents")

        bucket_cents = {b[0]: 0 for b in BUCKET_DEFS}
        for row in s_rows:
            bucket = classify_line_bucket(row)
            bucket_cents[bucket] += int(row.get("amount_cents") or 0)

        net_deposit_cents = sum(bucket_cents.values())
        if expected_total is not None and not truncated_free_tier and expected_total != net_deposit_cents:
            warnings.append(
                f"Settlement {sid}: itemized sum {_fmt_cents(net_deposit_cents)} {currency} differs from header "
                f"total-amount {_fmt_cents(expected_total)} {currency}."
            )

        journal_lines: list[dict[str, Any]] = []
        s_debits = 0
        s_credits = 0

        for key, label, xero_code, skr03_code in BUCKET_DEFS:
            amt = bucket_cents[key]
            if amt == 0:
                continue
            debit = -amt if amt < 0 else 0
            credit = amt if amt > 0 else 0
            s_debits += debit
            s_credits += credit
            journal_lines.append(
                {
                    "bucket": key,
                    "description": f"{label} ({sid})",
                    "xero_account": xero_code,
                    "qbo_account": label,
                    "datev_account": skr03_code,
                    "debit": _fmt_cents(debit),
                    "credit": _fmt_cents(credit),
                    "net_cents": amt,
                }
            )

        if net_deposit_cents != 0:
            _, bank_label, bank_xero, bank_skr03 = BANK_CLEARING_ACCOUNT
            bank_debit = net_deposit_cents if net_deposit_cents > 0 else 0
            bank_credit = -net_deposit_cents if net_deposit_cents < 0 else 0
            s_debits += bank_debit
            s_credits += bank_credit
            journal_lines.append(
                {
                    "bucket": "net_bank_deposit",
                    "description": f"{bank_label} ({sid})",
                    "xero_account": bank_xero,
                    "qbo_account": bank_label,
                    "datev_account": bank_skr03,
                    "debit": _fmt_cents(bank_debit),
                    "credit": _fmt_cents(bank_credit),
                    "net_cents": net_deposit_cents,
                }
            )

        drift_cents = s_debits - s_credits
        tot_gross += bucket_cents["sales_principal"]
        tot_fees_ads += bucket_cents["amazon_fba_selling_fees"] + bucket_cents["amazon_advertising_ppc"]
        tot_fac_tax += bucket_cents["marketplace_facilitator_tax"]
        tot_reserve += bucket_cents["reserve_carry_forward"]
        tot_deposit += net_deposit_cents
        tot_debits += s_debits
        tot_credits += s_credits

        settlements.append(
            {
                "settlement_id": sid,
                "deposit_date": deposit_date,
                "currency": currency,
                "line_count": len(s_rows),
                "gross_sales": _fmt_cents(bucket_cents["sales_principal"]),
                "fees_and_ads": _fmt_cents(
                    bucket_cents["amazon_fba_selling_fees"] + bucket_cents["amazon_advertising_ppc"]
                ),
                "reserve_change": _fmt_cents(bucket_cents["reserve_carry_forward"]),
                "net_deposit": _fmt_cents(net_deposit_cents),
                "total_debits": _fmt_cents(s_debits),
                "total_credits": _fmt_cents(s_credits),
                "drift": _fmt_cents(drift_cents),
                "journal_lines": journal_lines,
            }
        )

    return {
        "ok": True,
        "pro_unlocked": pro_unlocked,
        "truncated_free_tier": truncated_free_tier,
        "total_input_rows": total_input_rows,
        "processed_rows": len(selected),
        "truncated_rows": truncated_rows,
        "summary": {
            "settlement_count": len(settlements),
            "gross_sales": _fmt_cents(tot_gross),
            "total_fees_and_ads": _fmt_cents(tot_fees_ads),
            "facilitator_tax_withheld": _fmt_cents(tot_fac_tax),
            "net_reserve_change": _fmt_cents(tot_reserve),
            "total_net_deposit": _fmt_cents(tot_deposit),
            "total_debits": _fmt_cents(tot_debits),
            "total_credits": _fmt_cents(tot_credits),
            "drift": _fmt_cents(tot_debits - tot_credits),
        },
        "settlements": settlements,
        "warnings": warnings,
    }


def _require_pro_report(report: dict[str, Any]) -> None:
    if not report.get("pro_unlocked"):
        raise PermissionError("Pro license required to export Amazon settlement clearing journals.")


def render_xero_journal_csv(report: dict[str, Any]) -> str:
    """Render Pro-gated Xero Manual Journal import CSV."""
    _require_pro_report(report)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["*Narration", "*Date", "*Description", "*AccountCode", "*TaxRate", "*Amount"])
    for st in report.get("settlements", []):
        for ln in st.get("journal_lines", []):
            debit = Decimal(ln["debit"])
            credit = Decimal(ln["credit"])
            signed_xero = debit - credit
            tax_rate = "Tax on Sales" if ln["bucket"] == "sales_principal" else "BAS Excluded"
            writer.writerow(
                [
                    f"Amazon Settlement {st['settlement_id']}",
                    st["deposit_date"],
                    ln["description"],
                    ln["xero_account"],
                    tax_rate,
                    f"{signed_xero:.2f}",
                ]
            )
    return buf.getvalue().rstrip("\n")


def render_qbo_journal_csv(report: dict[str, Any]) -> str:
    """Render Pro-gated QuickBooks Online Journal Entry import CSV."""
    _require_pro_report(report)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["JournalNo", "JournalDate", "AccountName", "Debits", "Credits", "Description", "Currency"])
    for st in report.get("settlements", []):
        for ln in st.get("journal_lines", []):
            writer.writerow(
                [
                    f"AMZ-{st['settlement_id']}",
                    st["deposit_date"],
                    ln["qbo_account"],
                    ln["debit"] if Decimal(ln["debit"]) > 0 else "",
                    ln["credit"] if Decimal(ln["credit"]) > 0 else "",
                    ln["description"],
                    st["currency"],
                ]
            )
    return buf.getvalue().rstrip("\n")


def render_datev_extf_csv(report: dict[str, Any]) -> str:
    """Render Pro-gated DATEV EXTF Buchungsstapel CSV (semicolon delimiter, comma decimals)."""
    _require_pro_report(report)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\n")
    writer.writerow(
        [
            "Umsatz (ohne Soll/Haben-Kz)",
            "Soll/Haben-Kennzeichen",
            "WKZ Umsatz",
            "Konto",
            "Gegenkonto",
            "Belegdatum",
            "Belegfeld 1",
            "Buchungstext",
        ]
    )
    for st in report.get("settlements", []):
        parts = st["deposit_date"].split("-")
        ddmm = f"{parts[2]}{parts[1]}" if len(parts) == 3 else "1611"
        for ln in st.get("journal_lines", []):
            debit = Decimal(ln["debit"])
            credit = Decimal(ln["credit"])
            sh_flag = "S" if debit > 0 else "H"
            amt = debit if debit > 0 else credit
            writer.writerow(
                [
                    f"{amt:.2f}".replace(".", ","),
                    sh_flag,
                    st["currency"],
                    ln["datev_account"],
                    "1369",
                    ddmm,
                    st["settlement_id"],
                    ln["description"],
                ]
            )
    return buf.getvalue().rstrip("\n")
