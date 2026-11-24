---
title: "Fixing QuickBooks Web Connect OL-222 & <INTU.BID> Errors on CAMT.053 and MT940 Bank Statements"
tags: ["quickbooks", "iso20022", "fintech", "accounting"]
---

# Fixing QuickBooks Web Connect `OL-222` & `<INTU.BID>` Errors When Converting European `CAMT.053` and `MT940` Statements

If you import a European bank statement into QuickBooks Desktop or QuickBooks Online via Web Connect and hit **Error `OL-222`** (*"QuickBooks is unable to verify the Financial Institution Information for this download"*), the problem is rarely your bank account. It is almost always a structural mismatch between European ISO 20022 / SWIFT banking formats and Intuit's 1990s-era OFX 1.02 SGML specification.

With European banks deprecating legacy flat-text **SWIFT MT940** feeds in favor of deeply nested **ISO 20022 `camt.053.001.02` / `camt.053.001.08` XML**, naive XML-to-CSV scripts and generic OFX generators fail in four predictable ways:

1. **Missing or unwhitelisted `<INTU.BID>`** in `<SIGNONMSGSRSV1><SONRS>`.
2. **Collapsed `<NtryDtls><TxDtls>` SEPA batches**, turning 14 individual supplier payouts into one opaque lump sum.
3. **Inverted debit/credit signs** from `<CdtDbtInd>` (`CRDT`/`DBIT`) or MT940 `RC`/`RD` reversal codes.
4. **Non-deterministic `<FITID>` IDs or floating-point rounding drift** against `OPBD` / `CLBD` balances.

This guide breaks down the exact root causes, shows the working XML/OFX/Python structures, and includes a zero-upload workflow if you need to convert statements immediately without sending corporate IBANs to a third-party server.

---

## 1. Why QuickBooks Throws `OL-222` on Generic `.ofx` / `.qbo` Files

QuickBooks `.qbo` (Web Connect) is **not** standard XML—it is **OFX 102 SGML** wrapped with Intuit-proprietary tags and strict header formatting. When QuickBooks parses a `.qbo` file, it checks `<INTU.BID>` against Intuit's internal `fidir.txt` financial institution directory. If `<INTU.BID>` is missing, contains a non-US/unsupported bank code, or doesn't match a whitelisted institution ID, QuickBooks aborts immediately with **`OL-222`**.

### Common `OL-222` Triggers Checklist

| Symptom / Error | Root Cause in `.qbo` File | Required Fix |
|---|---|---|
| `OL-222` on import open | Missing `<INTU.BID>` or unsupported EU bank ID | Set `<INTU.BID>` to a whitelisted ID (e.g. `3000`, `2430`, `10898`, `1001`, `6526`) inside `<SONRS>` |
| `OL-222` after header read | Unclosed/XML-style `<?xml ...?>` prolog or CRLF header corruption | Start with `OFXHEADER:100`, `DATA:OFXSGML`, `VERSION:102`, blank line, then `<OFX>` |
| `OL-222` mid-stream | Unescaped `&`, `<`, or `>` inside `<NAME>` or `<MEMO>` | Sanitize `&` -> `and`, `<` -> `(`, `>` -> `)`, and truncate `<NAME>` to 32 chars, `<MEMO>` to 255 chars |
| Silent duplicate skips | Colliding or non-unique `<FITID>` values | Generate deterministic SHA-256 `<FITID>` per `(statement_id, account, date, cents, ref, occurrence)` |
| Wrong bank register | `<BANKID>` mismatch or unsupported `<ACCTTYPE>` | Match `<BANKID>` (`<= 9` chars) and restrict `<ACCTTYPE>` to `CHECKING`, `SAVINGS`, `CREDITLINE`, or `MONEYMRKT` |

### Valid QuickBooks Web Connect `.qbo` Header & Sign-On Block

```text
OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:UTF-8
CHARSET:CSUTF8
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS>
        <CODE>0</CODE>
        <SEVERITY>INFO</SEVERITY>
      </STATUS>
      <DTSERVER>20261112120000</DTSERVER>
      <LANGUAGE>ENG</LANGUAGE>
      <INTU.BID>3000</INTU.BID>
      <INTU.USERID>BankFeedBridge</INTU.USERID>
    </SONRS>
  </SIGNONMSGSRSV1>
```

> **Note:** `<INTU.BID>3000</INTU.BID>` maps to Universal Checking / Wells Fargo in Intuit's directory and is accepted across QuickBooks Desktop (US/CA/UK) and Web Connect imports regardless of whether the underlying `<CURDEF>` is `EUR`, `GBP`, `CHF`, or `USD` and `<ACCTID>` holds an EU IBAN (`<= 22` chars). When targeting Xero `.ofx` instead of QuickBooks `.qbo`, omit `<INTU.BID>` and `<INTU.USERID>` completely.

---

## 2. Flattening Nested ISO 20022 `CAMT.053` `<NtryDtls><TxDtls>` Batches

In ISO 20022 `camt.053.001.02` through `camt.053.001.08`, a single SEPA batch settlement appears as one `<Ntry>` containing the batch total (`654.50`), with individual invoices nested inside `<NtryDtls><TxDtls>`:

```xml
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
  <BkToCstmrStmt>
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
        <Amt Ccy="EUR">654.50</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <BookgDt><Dt>2026-11-12</Dt></BookgDt>
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
```

### Three Parser Pitfalls That Corrupt CAMT.053 Exports

1. **Hardcoded XML namespaces**: Banks send `camt.053.001.02`, `.04`, `.06`, or `.08`. Strip namespaces by matching local tag names (`tag.split("}", 1)[-1]`) instead of hardcoding `urn:iso:std:iso:20022:tech:xsd:camt.053.001.08`.
2. **Reading `<Ntry>/<Amt>` instead of `<TxDtls>/<AmtDtls>/<TxAmt>/<Amt>`**: If `<TxDtls>` nodes exist under `<Ntry>`, iterate every `<TxDtls>` and fall back to `<Ntry>/<Amt>` only when `<TxDtls>` is absent or carries no `<Amt>`.
3. **Counterparty role inversion (`Dbtr` vs `Cdtr`)**: When `CdtDbtInd == "DBIT"` (money leaving your account), the payee is `<Cdtr><Nm>` (Creditor). When `CdtDbtInd == "CRDT"` (money entering your account), the payee is `<Dbtr><Nm>` (Debtor).

---

## 3. Parsing Legacy SWIFT MT940 (`:61:` Reversals & `:86:` Subfields)

Even during the ISO 20022 transition, many Dutch, German, and Swiss banks still emit `.sta` / `.mt940` files. Two edge cases trip up regex parsers:

- **Reversal indicators (`RC` / `RD`) in `:61:`**:
  - `C` = Credit (`+`), `D` = Debit (`-`)
  - `RC` = Reversal of Credit (negative `-` flow!)
  - `RD` = Reversal of Debit (positive `+` flow!)
- **Two competing `:86:` formats**:
  - **German ZKA `?20`–`?33` tags**: `?20`–`?29` hold remittance text (`SVWZ+`, `EREF+`), `?31` holds counterparty IBAN, and `?32`+`?33` hold the counterparty name.
  - **Structured SEPA `/TAG/` pairs**: `/NAME/Nordic Partner AB/REMI/Invoice INV-2026-88/IBAN/SE4550000000058398257466`.

```text
:20:MT940-2026-11
:25:NL91ABNA0417164300
:60F:C261101EUR5000,00
:61:2611051105D310,25NTRFNONREF//TXMT002
:86:166?00SEPA-LASTSCHRIFT?20EREF+E2E-CLOUD-99?21SVWZ+Managed Hosting Q4?31DE12500105170648489890?32Hetzner Online GmbH
:61:2611081108RD45,00NCHGNONREF//TXMT003
:86:/NAME/Wire Fee Reversal/REMI/Fee correction Q4
:62F:C261108EUR4734,75
-
```

---

## 4. Integer-Cent `OPBD` / `CLBD` Reconciliation & Deterministic `<FITID>`

Never reconcile bank balances using IEEE-754 floats. Parse every `Amt` string with `Decimal` rounded `ROUND_HALF_UP` to integer cents, and apply the sign from `CdtDbtInd` (`DBIT`, `D`, `RC` -> negative; `CRDT`, `C`, `RD` -> positive):

```python
import hashlib
from decimal import Decimal, ROUND_HALF_UP

def to_cents(raw: str, cdt_dbt: str = "CRDT") -> int:
    dec = Decimal(str(raw).strip().replace(",", "."))
    cents = int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -abs(cents) if cdt_dbt.strip().upper() in {"DBIT", "D", "RC"} else abs(cents)

def make_fitid(stmt_id: str, account: str, tx_date: str, amount_cents: int, ref: str, occ: int) -> str:
    payload = f"{stmt_id}|{account}|{tx_date}|{amount_cents}|{ref}|{occ}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:16]
    return f"{tx_date.replace('-', '')[:8]}-{digest}"[:32]
```

Before emitting `.qbo`, `.ofx`, Xero CSV, or DATEV bank CSV, assert exact ledger integrity:

```python
variance_cents = open_cents + sum(tx["amount_cents"] for tx in stmt_txs) - close_cents
assert variance_cents == 0, f"Unreconciled statement variance: {variance_cents} cents"
```

If `variance_cents != 0`, you immediately know a `<TxDtls>` node was skipped, a `<CdtDbtInd>` sign was inverted, or the bank split a statement across multiple `<Stmt>` blocks—before corrupting your QuickBooks or Xero ledger.

---

## 5. Converting Offline Without Uploading Corporate IBANs

Cloud converters charge $180–$599/yr and require uploading sensitive corporate IBANs, payroll amounts, and counterparty details to third-party servers.

If you want to inspect the exact `OL-222` / `<INTU.BID>` fix or run an audited conversion right in your browser (with Chrome DevTools Network tab showing **0 outbound requests**) or via a zero-dependency Python CLI:

- **Step-by-step QuickBooks `OL-222` & `CAMT.053` Diagnostic Guide**: [QuickBooks Error OL-222 & CAMT.053 Fix Guide](https://domstijn.github.io/friction-killer-suite/guides/quickbooks-error-ol-222-camt053-fix/?ref=src.devto-ol222)
- **BankFeedBridge Browser Converter & Offline Python CLI**: [CAMT.053 & MT940 to QBO / Xero / DATEV Converter](https://domstijn.github.io/friction-killer-suite/products/camt053-mt940-qbo-xero-converter/?ref=src.devto-ol222)

Both the in-browser `DOMParser` converter and the Python `.whl` CLI flatten nested `<TxDtls>` batches, verify `OPBD`/`CLBD` integer-cent math (`variance == 0`), inject whitelisted `<INTU.BID>` tags + SHA-256 `<FITID>` IDs, and export QuickBooks `.qbo`, Xero `.ofx`/CSV, and semicolon-delimited DATEV bank CSVs strictly on your machine.
