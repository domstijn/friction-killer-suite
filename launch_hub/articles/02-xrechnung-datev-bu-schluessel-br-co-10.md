---
title: "XRechnung 3.0 & ZUGFeRD XML to DATEV EXTF: EN 16931 Math Checks (BR-CO-10/15) & BU-Schl\u00fcssel Mapping Without Cloud Uploads"
tags: ["xrechnung", "zugferd", "datev", "en16931"]
---

# XRechnung 3.0 & ZUGFeRD XML to DATEV EXTF: EN 16931 Math Checks (`BR-CO-10` / `BR-CO-15`) and `BU-Schlüssel` Mapping Without Cloud Uploads

Under Germany's mandatory B2B e-invoicing rollout (*E-Rechnungspflicht*, 2025–2027), bookkeepers and *Steuerberater* no longer receive uniform PDFs. Half of your suppliers send **XRechnung 3.0** (`OASIS UBL 2.1`), while the other half send **ZUGFeRD 2.x** (`UN/CEFACT CrossIndustryInvoice / CII`).

Opening those `.xml` attachments in Chrome or Excel dumps raw tags without checking whether the line items actually add up to the header totals—and uploading supplier XMLs (containing IBANs, *USt-IdNr.*, and unit pricing) to random "free online XML viewers" creates immediate **GDPR and GoBD** compliance headaches.

This technical reference covers:
1. Exact **UBL 2.1 vs. UN/CEFACT CII** tag differences in EN 16931.
2. Implementing deterministic **`BR-CO-10` and `BR-CO-15`** math validation.
3. Mapping **`BT-151` (VAT Category)** + **`BT-118` (VAT Rate)** to **DATEV `EXTF_Buchungsstapel` `BU-Schlüssel`** (`9`, `8`, `94`, `40`, `0`).

---

## 1. Two Syntaxes, One Semantic Model: `UBL 2.1` vs. `UN/CEFACT CII`

A common bug in custom Python or Node.js parsers is writing XPaths for UBL `<Invoice>` and silently failing on ZUGFeRD `<rsm:CrossIndustryInvoice>`. Even dates are encoded differently: UBL uses ISO `YYYY-MM-DD`, while CII typically uses UN/EDIFACT `format="102"` (`YYYYMMDD`, e.g., `20261119`).

### EN 16931 Tag Crosswalk (`UBL 2.1` vs. `UN/CEFACT CII`)

| Business Term (EN 16931) | Description | OASIS UBL 2.1 (`<Invoice>`) | UN/CEFACT CII (`<CrossIndustryInvoice>`) |
|---|---|---|---|
| **BT-1** | Invoice Number | `cbc:ID` | `ExchangedDocument/ram:ID` |
| **BT-2** | Issue Date | `cbc:IssueDate` (`YYYY-MM-DD`) | `ExchangedDocument/ram:IssueDateTime/udt:DateTimeString[@format='102']` |
| **BT-10** | Buyer Reference (*Leitweg-ID*) | `cbc:BuyerReference` | `ApplicableHeaderTradeAgreement/ram:BuyerReference` |
| **BT-109** | Tax-Exclusive Net Total | `LegalMonetaryTotal/cbc:TaxExclusiveAmount` | `SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount` |
| **BT-110** | Total VAT Amount | `TaxTotal/cbc:TaxAmount` | `SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount` |
| **BT-115** | Payable Gross Total | `LegalMonetaryTotal/cbc:PayableAmount` | `SpecifiedTradeSettlementHeaderMonetarySummation/ram:DuePayableAmount` |
| **BT-131** | Line Net Amount | `InvoiceLine/cbc:LineExtensionAmount` | `IncludedSupplyChainTradeLineItem/.../ram:LineTotalAmount` |
| **BT-151** | Line VAT Category Code | `InvoiceLine/Item/ClassifiedTaxCategory/cbc:ID` | `SpecifiedLineTradeSettlement/ApplicableTradeTax/ram:CategoryCode` |
| **BT-118 / BT-152** | VAT Rate (%) | `InvoiceLine/Item/ClassifiedTaxCategory/cbc:Percent` | `SpecifiedLineTradeSettlement/ApplicableTradeTax/ram:RateApplicablePercent` |

### Minimal Valid UBL 2.1 vs. CII Snippets

**XRechnung 3.0 (UBL 2.1):**
```xml
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>
  <cbc:ID>XR-2026-1001</cbc:ID>
  <cbc:IssueDate>2026-11-18</cbc:IssueDate>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>991-12345-67</cbc:BuyerReference>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">38.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:TaxExclusiveAmount currencyID="EUR">200.00</cbc:TaxExclusiveAmount>
    <cbc:PayableAmount currencyID="EUR">238.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:LineExtensionAmount currencyID="EUR">200.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>Dedicated PostgreSQL Nodes</cbc:Name>
      <cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory>
    </cac:Item>
  </cac:InvoiceLine>
</Invoice>
```

**ZUGFeRD CII (`CrossIndustryInvoice`):**
```xml
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
                          xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
                          xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocument>
    <ram:ID>ZF-2026-2002</ram:ID>
    <ram:IssueDateTime><udt:DateTimeString format="102">20261119</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>7.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">7.00</ram:TaxTotalAmount>
        <ram:DuePayableAmount>107.00</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
```

---

## 2. Enforcing EN 16931 Math Rules (`BR-CO-10` & `BR-CO-15`)

Before posting an invoice to DATEV or Xero, validate the arithmetic invariants in fixed-point `Decimal` (never binary floats):

- **`BR-CO-10`**: Sum of invoice line net amounts (`BT-131`) must equal `TaxExclusiveAmount` (`BT-109` / `TaxBasisTotalAmount`).
- **`BR-CO-15`**: `TaxExclusiveAmount` (`BT-109`) + `TaxTotalAmount` (`BT-110`) must equal `PayableAmount` (`BT-115` / `DuePayableAmount`).
- **`BR-CO-13`**: Required header fields (`invoice_id`, `issue_date`, `seller_name`, `buyer_name`, `currency`) must be non-empty.

```python
from decimal import Decimal

def validate_en16931_math(lines: list[dict], tax_exclusive: Decimal, tax_total: Decimal, payable_gross: Decimal) -> list[str]:
    errors: list[str] = []
    if lines:
        sum_lines = sum((Decimal(ln["line_net"]) for ln in lines), Decimal("0.00"))
        if abs(sum_lines - tax_exclusive) > Decimal("0.01"):
            errors.append(
                f"BR-CO-10: Sum of line net amounts ({sum_lines:.2f}) != TaxExclusiveAmount ({tax_exclusive:.2f})."
            )
    if abs((tax_exclusive + tax_total) - payable_gross) > Decimal("0.01"):
        errors.append(
            f"BR-CO-15: TaxExclusiveAmount + TaxTotal ({tax_exclusive + tax_total:.2f}) != PayableAmount ({payable_gross:.2f})."
        )
    return errors
```

Catching a `BR-CO-10` or `BR-CO-15` mismatch during XML ingestion prevents silent VAT discrepancies during your monthly *Umsatzsteuer-Voranmeldung*.

---

## 3. Mapping `BT-151` & `BT-118` to DATEV EXTF `BU-Schlüssel`

DATEV `EXTF_Buchungsstapel` imports require German comma-decimal amounts (`238,00`), semicolon delimiters (`;`), `DDMM` `Belegdatum` (`1811`), `Soll/Haben-Kennzeichen` (`S`/`H`), and the exact **`BU-Schlüssel`** tax code derived from `BT-151` (Category Code) and `BT-118` (VAT Rate):

| EN 16931 `BT-151` (Code) | `BT-118` Rate | Tax Scenario (Germany / EU) | DATEV `BU-Schlüssel` | Typical SKR03 Expense Acct |
|---|---|---|---|---|
| `S` (Standard rate) | `19.00%` | Standard domestic *Vorsteuer* 19% | **`9`** | `3400` (*Wareneingang 19%*) |
| `S` (Standard rate) | `7.00%` | Reduced *Vorsteuer* 7% (books, print, food) | **`8`** | `3300` (*Wareneingang 7%*) |
| `AE` (Reverse charge) | `0.00%` | § 13b UStG Reverse Charge (SaaS / EU services) | **`94`** | `3123` (*Leistungen § 13b*) |
| `Z` / `K` / `G` (Zero / Intra-EU) | `0.00%` | *Innergemeinschaftlicher Erwerb* / Zero-rated / Export | **`40`** / **`0`** | `3425` / `3200` |
| `E` (Exempt) | `0.00%` | VAT-exempt (*Steuerfrei* / § 19 UStG) | **`0`** | `3200` (*Wareneingang steuerfrei*) |

> **Implementation Tip:** Use `40` (*Steueraufhebung* / explicit 0% override) when posting to an automatic-tax account (*Automatikkonto*) that would otherwise default to 19%, and `0` when posting directly to a non-automatic 0% account such as `3200`.

### Resulting DATEV `EXTF_Buchungsstapel` CSV Output

```csv
Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Konto;Gegenkonto;BU-Schlüssel;Belegdatum;Belegfeld 1;Buchungstext
238,00;S;EUR;3400;70000;9;1811;XR-2026-1001;Nordic Cloud Infrastructure GmbH (UBL_2.1)
107,00;S;EUR;3300;70000;8;1911;ZF-2026-2002;Fachverlag Berlin KG (CII_EN16931)
```

---

## 4. Zero-Upload Batch Validation & A4 PDF Rendering in Chrome

Because incoming B2B e-invoices contain vendor IBANs, tax IDs, and commercial pricing, parsing should happen client-side via `DOMParser` or via an offline Python CLI—never on a third-party cloud server.

To validate mixed `XRechnung` (`UBL 2.1`), `ZUGFeRD` (`CII`), and `Peppol BIS 3.0` batches locally in Chrome (check DevTools Network tab: **0 requests**), inspect `BR-CO-10` / `BR-CO-15` status, print clean A4 PDFs, and export `DATEV EXTF`, `Xero Bills`, or `QuickBooks Bills` CSVs:

- **Offline XRechnung & ZUGFeRD Converter (DE)**: [EInvoiceLocal — XRechnung & ZUGFeRD Konverter (0 Cloud-Uploads)](https://domstijn.github.io/friction-killer-suite/de/xrechnung-zugferd-konverter/?ref=src.devto-xrechnung)
