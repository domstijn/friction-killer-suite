"""EInvoiceLocal core dual UBL 2.1 / UN/CEFACT CII XML parser, EN 16931 validator & DATEV/Xero/QBO exporter."""

from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

FREE_INVOICE_LIMIT = 3
CENT = Decimal("0.01")

SAMPLE_UBL_PEPPOL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>
  <cbc:ID>XR-2026-1001</cbc:ID>
  <cbc:IssueDate>2026-11-18</cbc:IssueDate>
  <cbc:DueDate>2026-12-18</cbc:DueDate>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>991-12345-67</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyTaxScheme><cbc:CompanyID>DE298765432</cbc:CompanyID></cac:PartyTaxScheme>
      <cac:PartyLegalEntity><cbc:RegistrationName>Nordic Cloud Infrastructure GmbH</cbc:RegistrationName></cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyTaxScheme><cbc:CompanyID>DE112233445</cbc:CompanyID></cac:PartyTaxScheme>
      <cac:PartyLegalEntity><cbc:RegistrationName>Mittelstand Ops GmbH</cbc:RegistrationName></cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:PaymentMeans>
    <cac:PayeeFinancialAccount><cbc:ID>DE89370400440532013000</cbc:ID></cac:PayeeFinancialAccount>
  </cac:PaymentMeans>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">38.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:TaxExclusiveAmount currencyID="EUR">200.00</cbc:TaxExclusiveAmount>
    <cbc:PayableAmount currencyID="EUR">238.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">2</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="EUR">150.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>Dedicated PostgreSQL Nodes</cbc:Name>
      <cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="EUR">75.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
  <cac:InvoiceLine>
    <cbc:ID>2</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">1</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="EUR">50.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>Daily Encrypted Snapshots</cbc:Name>
      <cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="EUR">50.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
</Invoice>
"""

SAMPLE_CII_ZUGFERD_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
                          xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
                          xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocument>
    <ram:ID>ZF-2026-2002</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime><udt:DateTimeString format="102">20261119</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:AssociatedDocumentLineDocument><ram:LineID>1</ram:LineID></ram:AssociatedDocumentLineDocument>
      <ram:SpecifiedTradeProduct><ram:Name>Technical Compliance Handbook (Print Edition)</ram:Name></ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeAgreement>
        <ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice>
      </ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="H87">1</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>7.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:BuyerReference>LEITWEG-04011000-12345-01</ram:BuyerReference>
      <ram:SellerTradeParty>
        <ram:Name>Fachverlag Berlin KG</ram:Name>
        <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE812345678</ram:ID></ram:SpecifiedTaxRegistration>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>Mittelstand Ops GmbH</ram:Name>
        <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE112233445</ram:ID></ram:SpecifiedTaxRegistration>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementPaymentMeans>
        <ram:PayeePartyCreditorFinancialAccount><ram:IBANID>DE44500105175407324931</ram:IBANID></ram:PayeePartyCreditorFinancialAccount>
      </ram:SpecifiedTradeSettlementPaymentMeans>
      <ram:SpecifiedTradePaymentTerms>
        <ram:DueDateDateTime><udt:DateTimeString format="102">20261205</udt:DateTimeString></ram:DueDateDateTime>
      </ram:SpecifiedTradePaymentTerms>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">7.00</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>107.00</ram:GrandTotalAmount>
        <ram:DuePayableAmount>107.00</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""


SAMPLE_PEPPOL_BIS3_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ID>PEP-2026-3003</cbc:ID>
  <cbc:IssueDate>2026-11-20</cbc:IssueDate>
  <cbc:DueDate>2026-12-20</cbc:DueDate>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-2026-BE-44</cbc:BuyerReference>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyTaxScheme><cbc:CompanyID>BE0897234567</cbc:CompanyID></cac:PartyTaxScheme>
      <cac:PartyLegalEntity><cbc:RegistrationName>Antwerp Logistics Systems BV</cbc:RegistrationName></cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyTaxScheme><cbc:CompanyID>DE112233445</cbc:CompanyID></cac:PartyTaxScheme>
      <cac:PartyLegalEntity><cbc:RegistrationName>Mittelstand Ops GmbH</cbc:RegistrationName></cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:PaymentMeans>
    <cac:PayeeFinancialAccount><cbc:ID>BE68539007547034</cbc:ID></cac:PayeeFinancialAccount>
  </cac:PaymentMeans>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">0.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:TaxExclusiveAmount currencyID="EUR">240.00</cbc:TaxExclusiveAmount>
    <cbc:PayableAmount currencyID="EUR">240.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">1</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="EUR">180.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>EU Peppol Access Point Gateway</cbc:Name>
      <cac:ClassifiedTaxCategory><cbc:ID>AE</cbc:ID><cbc:Percent>0.00</cbc:Percent></cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="EUR">180.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
  <cac:InvoiceLine>
    <cbc:ID>2</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">3</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="EUR">60.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>AS4 Message Routing Tier</cbc:Name>
      <cac:ClassifiedTaxCategory><cbc:ID>AE</cbc:ID><cbc:Percent>0.00</cbc:Percent></cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="EUR">20.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
</Invoice>
"""

SAMPLE_CII_MIXED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
                          xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
                          xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocument>
    <ram:ID>ZF-2026-4004</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime><udt:DateTimeString format="102">20261121</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:AssociatedDocumentLineDocument><ram:LineID>1</ram:LineID></ram:AssociatedDocumentLineDocument>
      <ram:SpecifiedTradeProduct><ram:Name>Business Accommodation (2 Nights)</ram:Name></ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeAgreement>
        <ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice>
      </ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="DAY">2</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>7.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>200.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:AssociatedDocumentLineDocument><ram:LineID>2</ram:LineID></ram:AssociatedDocumentLineDocument>
      <ram:SpecifiedTradeProduct><ram:Name>Conference Room &amp; Catering Package</ram:Name></ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeAgreement>
        <ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice>
      </ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="EA">1</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>19.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:BuyerReference>CONF-MUC-2026</ram:BuyerReference>
      <ram:SellerTradeParty>
        <ram:Name>Tagungshotel München GmbH</ram:Name>
        <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE276543219</ram:ID></ram:SpecifiedTaxRegistration>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>Mittelstand Ops GmbH</ram:Name>
        <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE112233445</ram:ID></ram:SpecifiedTaxRegistration>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementPaymentMeans>
        <ram:PayeePartyCreditorFinancialAccount><ram:IBANID>DE12700202700015984000</ram:IBANID></ram:PayeePartyCreditorFinancialAccount>
      </ram:SpecifiedTradeSettlementPaymentMeans>
      <ram:SpecifiedTradePaymentTerms>
        <ram:DueDateDateTime><udt:DateTimeString format="102">20261206</udt:DateTimeString></ram:DueDateDateTime>
      </ram:SpecifiedTradePaymentTerms>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:TaxBasisTotalAmount>300.00</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">33.00</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>333.00</ram:GrandTotalAmount>
        <ram:DuePayableAmount>333.00</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(node: ET.Element | None, name: str) -> list[ET.Element]:
    if node is None:
        return []
    return [c for c in node if _local(c.tag) == name]


def _child(node: ET.Element | None, name: str) -> ET.Element | None:
    if node is None:
        return None
    for c in node:
        if _local(c.tag) == name:
            return c
    return None


def _path(node: ET.Element | None, *parts: str) -> ET.Element | None:
    cur = node
    for part in parts:
        cur = _child(cur, part)
        if cur is None:
            return None
    return cur


def _text(node: ET.Element | None, *parts: str, default: str = "") -> str:
    target = _path(node, *parts) if parts else node
    if target is None or target.text is None:
        return default
    return target.text.strip()


def _dec(raw: Any, default: str = "0.00") -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text or not re.fullmatch(r"[+-]?\s*\d+(?:\.\d+)?", text):
        return Decimal(default)
    try:
        return Decimal(text.replace(" ", "")).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return Decimal(default)


def _fmt_rate(val: Decimal) -> str:
    norm = val.quantize(CENT, rounding=ROUND_HALF_UP).normalize()
    s = format(norm, "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


def _csv_safe_cell(val: Any) -> str:
    s = str(val if val is not None else "")
    if re.match(r"^[=+\-@\t\r]", s) and not re.fullmatch(r"-?\d+(?:[.,]\d+)?", s):
        return "'" + s
    return s


def _norm_date(raw: str) -> str:
    clean = str(raw or "").strip()
    if re.fullmatch(r"\d{8}", clean):
        return f"{clean[:4]}-{clean[4:6]}-{clean[6:8]}"
    return clean[:10] if len(clean) >= 10 else clean


def _map_line_tax(vat_cat: str, vat_rate: Decimal) -> tuple[str, str, str, str]:
    """Deterministically map EN 16931 tax category + rate to DATEV BU, SKR03, Xero TaxType, and QBO Account."""
    cat = (vat_cat or "S").strip().upper()
    rate = _dec(vat_rate)
    if cat == "AE":
        return "94", "3123", "Reverse Charge Expenses (0%)", "3123 EU Reverse Charge (§13b)"
    if cat == "K":
        if abs(rate - Decimal("7.00")) <= Decimal("0.05"):
            return "92", "3420", "EC Acquisitions (7%)", "3420 Intra-EU Acquisition (7%)"
        return "91", "3425", "EC Acquisitions (19%)", "3425 Intra-EU Acquisition (19%)"
    if abs(rate - Decimal("19.00")) <= Decimal("0.05"):
        return "9", "3400", "INPUT (19%)", "3400 Standard Purchases (19%)"
    if abs(rate - Decimal("7.00")) <= Decimal("0.05"):
        return "8", "3300", "INPUT (7%)", "3300 Reduced Purchases (7%)"
    if rate == Decimal("0.00") or cat in {"E", "Z", "O", "G"}:
        return "0", "3200", "EXEMPTINPUT (0%)", "3200 Tax-Exempt Purchases (0%)"
    return "0", "3425", f"INPUT ({_fmt_rate(rate)}%)", "3425 General Purchases"


def _map_datev_bu_and_account(lines: list[dict[str, Any]], tax_exclusive: Decimal, tax_total: Decimal) -> tuple[str, str]:
    if lines:
        seen_bu: list[str] = []
        seen_acct: list[str] = []
        for ln in lines:
            bu = str(ln.get("datev_bu_key") or "")
            acct = str(ln.get("datev_account") or "")
            if bu and bu not in seen_bu:
                seen_bu.append(bu)
            if acct and acct not in seen_acct:
                seen_acct.append(acct)
        if seen_bu and seen_acct:
            return "+".join(seen_bu), ",".join(seen_acct)

    if abs(tax_exclusive) > Decimal("0.00") and abs(tax_total) > Decimal("0.00"):
        inferred = ((abs(tax_total) / abs(tax_exclusive)) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        bu, acct, _, _ = _map_line_tax("S", inferred)
        return bu, acct
    return "0", "3200"


def _pick_ubl_vat_id(party: ET.Element | None) -> str:
    if party is None:
        return ""
    fallback = ""
    for pts in _children(party, "PartyTaxScheme"):
        cid = _text(pts, "CompanyID")
        if not cid:
            continue
        scheme = _text(pts, "TaxScheme", "ID").upper()
        if scheme == "VAT":
            return cid
        if not fallback:
            fallback = cid
    return fallback


def _pick_currency_amt(parent: ET.Element | None, tag_name: str, currency: str) -> Decimal:
    els = _children(parent, tag_name)
    if not els:
        return Decimal("0.00")
    cur_u = (currency or "EUR").upper()
    for el in els:
        cid = str(el.attrib.get("currencyID", "")).strip().upper()
        if not cid or cid == cur_u:
            return _dec(el.text)
    return _dec(els[0].text)


def _pick_cii_vat_id(party: ET.Element | None) -> str:
    if party is None:
        return ""
    fallback = ""
    for reg in _children(party, "SpecifiedTaxRegistration"):
        id_el = _child(reg, "ID")
        if id_el is None or id_el.text is None:
            continue
        txt = id_el.text.strip()
        if not txt:
            continue
        scheme = str(id_el.attrib.get("schemeID", "")).strip().upper()
        if scheme == "VA":
            return txt
        if not fallback:
            fallback = txt
    return fallback


def _pick_ubl_tax_total(root: ET.Element, currency: str) -> Decimal:
    tax_totals = _children(root, "TaxTotal")
    if not tax_totals:
        return Decimal("0.00")
    cur_u = (currency or "EUR").upper()
    for tt in tax_totals:
        amt_el = _child(tt, "TaxAmount")
        if amt_el is None:
            continue
        cid = str(amt_el.attrib.get("currencyID", "")).strip().upper()
        if not cid or cid == cur_u:
            return _dec(amt_el.text)
    return _dec(_text(tax_totals[0], "TaxAmount"))


def parse_einvoice_xml(xml_text: str, filename: str = "invoice.xml") -> dict[str, Any]:
    """Parse UBL 2.1 or UN/CEFACT CII e-invoice XML, validate EN 16931 math rules, and assign DATEV BU."""
    try:
        root = ET.fromstring(str(xml_text or "").strip())
    except ET.ParseError as exc:
        return {
            "filename": filename,
            "syntax": "UNKNOWN",
            "is_credit_note": False,
            "invoice_id": filename,
            "issue_date": "",
            "due_date": "",
            "currency": "EUR",
            "buyer_reference": "",
            "seller_name": "",
            "seller_vat_id": "",
            "seller_iban": "",
            "buyer_name": "",
            "buyer_vat_id": "",
            "lines": [],
            "tax_exclusive_total": "0.00",
            "tax_total": "0.00",
            "payable_gross_total": "0.00",
            "datev_bu_key": "0",
            "datev_account": "3200",
            "en16931_valid": False,
            "validation_errors": [f"Invalid XML syntax: {exc}"],
        }
    root_name = _local(root.tag)
    is_credit_note = False

    lines: list[dict[str, Any]] = []
    if root_name in {"Invoice", "CreditNote"}:
        syntax = "UBL_2.1"
        is_credit_note = root_name == "CreditNote"
        invoice_id = _text(root, "ID")
        issue_date = _norm_date(_text(root, "IssueDate"))
        due_date = _norm_date(_text(root, "DueDate") or _text(root, "PaymentMeans", "PaymentDueDate")) or issue_date
        currency = (_text(root, "DocumentCurrencyCode") or "EUR").upper()
        buyer_ref = _text(root, "BuyerReference")

        sup_party = _path(root, "AccountingSupplierParty", "Party")
        seller_name = _text(sup_party, "PartyLegalEntity", "RegistrationName") or _text(sup_party, "PartyName", "Name")
        seller_vat = _pick_ubl_vat_id(sup_party)
        seller_iban = _text(root, "PaymentMeans", "PayeeFinancialAccount", "ID")

        cust_party = _path(root, "AccountingCustomerParty", "Party")
        buyer_name = _text(cust_party, "PartyLegalEntity", "RegistrationName") or _text(cust_party, "PartyName", "Name")
        buyer_vat = _pick_ubl_vat_id(cust_party)

        tax_total = _pick_ubl_tax_total(root, currency)
        lmt = _child(root, "LegalMonetaryTotal")
        tax_exclusive = _dec(_text(lmt, "TaxExclusiveAmount"))
        payable_gross = _dec(_text(lmt, "PayableAmount") or _text(lmt, "TaxInclusiveAmount"))

        line_tag = "CreditNoteLine" if root_name == "CreditNote" else "InvoiceLine"
        qty_tag = "CreditedQuantity" if root_name == "CreditNote" else "InvoicedQuantity"
        for item_el in _children(root, line_tag):
            name = _text(item_el, "Item", "Name") or _text(item_el, "Item", "Description") or "Line Item"
            qty = _dec(_text(item_el, qty_tag) or "1", "1.00")
            raw_unit = _dec(_text(item_el, "Price", "PriceAmount"))
            base_qty = _dec(_text(item_el, "Price", "BaseQuantity") or "1", "1.00")
            unit_price = (raw_unit / base_qty).quantize(CENT, rounding=ROUND_HALF_UP) if base_qty > Decimal("0.00") and base_qty != Decimal("1.00") else raw_unit
            line_net = _dec(_text(item_el, "LineExtensionAmount"))
            if qty != Decimal("0.00") and abs((qty * unit_price).quantize(CENT, rounding=ROUND_HALF_UP) - line_net) > Decimal("0.02"):
                unit_price = (line_net / qty).quantize(CENT, rounding=ROUND_HALF_UP)
            tax_cat = _path(item_el, "Item", "ClassifiedTaxCategory")
            vat_rate = _dec(_text(tax_cat, "Percent"))
            vat_cat = (_text(tax_cat, "ID") or "S").upper()
            eff_rate = Decimal("0.00") if vat_cat in {"AE", "K"} else vat_rate
            line_tax = ((line_net * eff_rate) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
            bu_l, acct_l, xero_tax_l, qbo_acct_l = _map_line_tax(vat_cat, vat_rate)
            lines.append(
                {
                    "name": name,
                    "qty": f"{qty:.2f}",
                    "unit_price": f"{unit_price:.2f}",
                    "line_net": f"{line_net:.2f}",
                    "line_tax": f"{line_tax:.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "vat_category": vat_cat,
                    "datev_bu_key": bu_l,
                    "datev_account": acct_l,
                    "xero_tax_type": xero_tax_l,
                    "qbo_account": qbo_acct_l,
                }
            )
        for ac in _children(root, "AllowanceCharge"):
            is_charge = (_text(ac, "ChargeIndicator") or "false").lower() == "true"
            sign = Decimal("1") if is_charge else Decimal("-1")
            amt = (sign * _dec(_text(ac, "Amount"))).quantize(CENT, rounding=ROUND_HALF_UP)
            cat_el = _child(ac, "TaxCategory")
            vat_rate = _dec(_text(cat_el, "Percent"))
            vat_cat = (_text(cat_el, "ID") or "S").upper()
            eff_rate = Decimal("0.00") if vat_cat in {"AE", "K"} else vat_rate
            line_tax = ((amt * eff_rate) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
            bu_l, acct_l, xero_tax_l, qbo_acct_l = _map_line_tax(vat_cat, vat_rate)
            reason = _text(ac, "AllowanceChargeReason") or ("Header Charge" if is_charge else "Header Allowance")
            lines.append(
                {
                    "name": reason,
                    "qty": "1.00",
                    "unit_price": f"{amt:.2f}",
                    "line_net": f"{amt:.2f}",
                    "line_tax": f"{line_tax:.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "vat_category": vat_cat,
                    "datev_bu_key": bu_l,
                    "datev_account": acct_l,
                    "xero_tax_type": xero_tax_l,
                    "qbo_account": qbo_acct_l,
                }
            )
    elif root_name == "CrossIndustryInvoice":
        syntax = "CII_EN16931"
        exch = _child(root, "ExchangedDocument")
        invoice_id = _text(exch, "ID")
        type_code = _text(exch, "TypeCode") or "380"
        is_credit_note = type_code == "381"
        issue_date = _norm_date(_text(exch, "IssueDateTime", "DateTimeString"))

        tx = _child(root, "SupplyChainTradeTransaction")
        hdr_agr = _child(tx, "ApplicableHeaderTradeAgreement")
        buyer_ref = _text(hdr_agr, "BuyerReference")

        seller_p = _child(hdr_agr, "SellerTradeParty")
        seller_name = _text(seller_p, "Name")
        seller_vat = _pick_cii_vat_id(seller_p)

        buyer_p = _child(hdr_agr, "BuyerTradeParty")
        buyer_name = _text(buyer_p, "Name")
        buyer_vat = _pick_cii_vat_id(buyer_p)

        hdr_set = _child(tx, "ApplicableHeaderTradeSettlement")
        currency = (_text(hdr_set, "InvoiceCurrencyCode") or "EUR").upper()
        seller_iban = _text(hdr_set, "SpecifiedTradeSettlementPaymentMeans", "PayeePartyCreditorFinancialAccount", "IBANID")
        due_date = _norm_date(_text(hdr_set, "SpecifiedTradePaymentTerms", "DueDateDateTime", "DateTimeString")) or issue_date

        summ = _child(hdr_set, "SpecifiedTradeSettlementHeaderMonetarySummation")
        tax_exclusive = _pick_currency_amt(summ, "TaxBasisTotalAmount", currency)
        tax_total = _pick_currency_amt(summ, "TaxTotalAmount", currency)
        payable_gross = _dec(_text(summ, "DuePayableAmount") or _text(summ, "GrandTotalAmount"))

        for li in _children(tx, "IncludedSupplyChainTradeLineItem"):
            name = _text(li, "SpecifiedTradeProduct", "Name") or "Line Item"
            qty = _dec(_text(li, "SpecifiedLineTradeDelivery", "BilledQuantity") or "1", "1.00")
            raw_unit = _dec(_text(li, "SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "ChargeAmount"))
            basis_qty = _dec(_text(li, "SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "BasisQuantity") or "1", "1.00")
            unit_price = (raw_unit / basis_qty).quantize(CENT, rounding=ROUND_HALF_UP) if basis_qty > Decimal("0.00") and basis_qty != Decimal("1.00") else raw_unit
            li_set = _child(li, "SpecifiedLineTradeSettlement")
            line_net = _dec(_text(li_set, "SpecifiedTradeSettlementLineMonetarySummation", "LineTotalAmount"))
            if qty != Decimal("0.00") and abs((qty * unit_price).quantize(CENT, rounding=ROUND_HALF_UP) - line_net) > Decimal("0.02"):
                unit_price = (line_net / qty).quantize(CENT, rounding=ROUND_HALF_UP)
            t_el = _child(li_set, "ApplicableTradeTax")
            vat_rate = _dec(_text(t_el, "RateApplicablePercent"))
            vat_cat = (_text(t_el, "CategoryCode") or "S").upper()
            eff_rate = Decimal("0.00") if vat_cat in {"AE", "K"} else vat_rate
            line_tax = ((line_net * eff_rate) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
            bu_l, acct_l, xero_tax_l, qbo_acct_l = _map_line_tax(vat_cat, vat_rate)
            lines.append(
                {
                    "name": name,
                    "qty": f"{qty:.2f}",
                    "unit_price": f"{unit_price:.2f}",
                    "line_net": f"{line_net:.2f}",
                    "line_tax": f"{line_tax:.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "vat_category": vat_cat,
                    "datev_bu_key": bu_l,
                    "datev_account": acct_l,
                    "xero_tax_type": xero_tax_l,
                    "qbo_account": qbo_acct_l,
                }
            )
        for ac in _children(hdr_set, "SpecifiedTradeAllowanceCharge"):
            ind = (_text(ac, "ChargeIndicator", "Indicator") or _text(ac, "ChargeIndicator") or "false").lower()
            is_charge = ind == "true"
            sign = Decimal("1") if is_charge else Decimal("-1")
            amt = (sign * _dec(_text(ac, "ActualAmount"))).quantize(CENT, rounding=ROUND_HALF_UP)
            cat_el = _child(ac, "CategoryTradeTax")
            vat_rate = _dec(_text(cat_el, "RateApplicablePercent"))
            vat_cat = (_text(cat_el, "CategoryCode") or "S").upper()
            eff_rate = Decimal("0.00") if vat_cat in {"AE", "K"} else vat_rate
            line_tax = ((amt * eff_rate) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
            bu_l, acct_l, xero_tax_l, qbo_acct_l = _map_line_tax(vat_cat, vat_rate)
            reason = _text(ac, "Reason") or ("Header Charge" if is_charge else "Header Allowance")
            lines.append(
                {
                    "name": reason,
                    "qty": "1.00",
                    "unit_price": f"{amt:.2f}",
                    "line_net": f"{amt:.2f}",
                    "line_tax": f"{line_tax:.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "vat_category": vat_cat,
                    "datev_bu_key": bu_l,
                    "datev_account": acct_l,
                    "xero_tax_type": xero_tax_l,
                    "qbo_account": qbo_acct_l,
                }
            )
    else:
        return {
            "filename": filename,
            "syntax": "UNKNOWN",
            "is_credit_note": False,
            "invoice_id": filename,
            "issue_date": "",
            "due_date": "",
            "currency": "EUR",
            "buyer_reference": "",
            "seller_name": "",
            "seller_vat_id": "",
            "seller_iban": "",
            "buyer_name": "",
            "buyer_vat_id": "",
            "lines": [],
            "tax_exclusive_total": "0.00",
            "tax_total": "0.00",
            "payable_gross_total": "0.00",
            "datev_bu_key": "0",
            "datev_account": "3200",
            "en16931_valid": False,
            "validation_errors": [
                f"Unsupported e-invoice root element: <{root_name}> (expected UBL Invoice/CreditNote or CII CrossIndustryInvoice)"
            ],
        }

    validation_errors: list[str] = []
    for field_label, val in (
        ("invoice_id", invoice_id),
        ("issue_date", issue_date),
        ("seller_name", seller_name),
        ("buyer_name", buyer_name),
        ("currency", currency),
    ):
        if not val:
            validation_errors.append(f"BR-CO-13: Missing required field '{field_label}'.")

    if lines:
        sum_lines = sum((Decimal(ln["line_net"]) for ln in lines), Decimal("0.00"))
        if abs(sum_lines - tax_exclusive) > Decimal("0.02"):
            validation_errors.append(
                f"BR-CO-10: Sum of line net amounts ({sum_lines:.2f}) differs from TaxExclusiveAmount ({tax_exclusive:.2f})."
            )
        sum_line_vat = sum((Decimal(ln["line_tax"]) for ln in lines), Decimal("0.00"))
        diff_vat = tax_total - sum_line_vat
        if abs(diff_vat) > Decimal("0.05"):
            validation_errors.append(
                f"BR-CO-14: Sum of line VAT amounts ({sum_line_vat:.2f}) differs from TaxTotal ({tax_total:.2f})."
            )
        elif diff_vat != Decimal("0.00"):
            adj_target = next((ln for ln in reversed(lines) if Decimal(ln["line_tax"]) != Decimal("0.00")), lines[-1])
            adj_target["line_tax"] = f"{(Decimal(adj_target['line_tax']) + diff_vat):.2f}"

    if abs((tax_exclusive + tax_total) - payable_gross) > Decimal("0.02"):
        validation_errors.append(
            f"BR-CO-15: TaxExclusiveAmount + TaxTotal ({tax_exclusive + tax_total:.2f}) differs from PayableAmount ({payable_gross:.2f})."
        )

    bu_key, skr03_acct = _map_datev_bu_and_account(lines, tax_exclusive, tax_total)
    return {
        "filename": filename,
        "syntax": syntax,
        "is_credit_note": is_credit_note,
        "invoice_id": invoice_id or filename or "(missing ID)",
        "issue_date": issue_date,
        "due_date": due_date,
        "currency": currency,
        "buyer_reference": buyer_ref,
        "seller_name": seller_name,
        "seller_vat_id": seller_vat,
        "seller_iban": seller_iban,
        "buyer_name": buyer_name,
        "buyer_vat_id": buyer_vat,
        "lines": lines,
        "tax_exclusive_total": f"{tax_exclusive:.2f}",
        "tax_total": f"{tax_total:.2f}",
        "payable_gross_total": f"{payable_gross:.2f}",
        "datev_bu_key": bu_key,
        "datev_account": skr03_acct,
        "en16931_valid": len(validation_errors) == 0,
        "validation_errors": validation_errors,
    }


def compile_einvoice_batch(
    xml_docs: list[tuple[str, str]],
    *,
    pro_unlocked: bool = False,
) -> dict[str, Any]:
    """Compile a batch of (filename, xml_text) e-invoices with Free 3-XML cap and EN 16931 summary."""
    total_input_files = len(xml_docs)
    if not xml_docs:
        return {
            "ok": False,
            "error": "No XML e-invoice files provided.",
            "pro_unlocked": pro_unlocked,
            "truncated_free_tier": False,
            "total_input_files": 0,
            "processed_files": 0,
            "truncated_count": 0,
            "summary": {},
            "invoices": [],
        }

    truncated_free_tier = (not pro_unlocked) and (total_input_files > FREE_INVOICE_LIMIT)
    selected = xml_docs if pro_unlocked else xml_docs[:FREE_INVOICE_LIMIT]
    truncated_count = max(0, total_input_files - len(selected))

    invoices: list[dict[str, Any]] = []
    valid_count = 0
    invalid_count = 0
    tot_net = Decimal("0.00")
    tot_vat = Decimal("0.00")
    tot_gross = Decimal("0.00")

    for fname, raw_xml in selected:
        inv = parse_einvoice_xml(raw_xml, filename=fname)
        invoices.append(inv)
        if inv["en16931_valid"]:
            valid_count += 1
        else:
            invalid_count += 1
        sign = Decimal("-1") if inv.get("is_credit_note") else Decimal("1")
        tot_net += Decimal(inv["tax_exclusive_total"]) * sign
        tot_vat += Decimal(inv["tax_total"]) * sign
        tot_gross += Decimal(inv["payable_gross_total"]) * sign

    return {
        "ok": True,
        "pro_unlocked": pro_unlocked,
        "truncated_free_tier": truncated_free_tier,
        "total_input_files": total_input_files,
        "processed_files": len(selected),
        "truncated_count": truncated_count,
        "summary": {
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "total_net": f"{tot_net:.2f}",
            "total_vat": f"{tot_vat:.2f}",
            "total_gross": f"{tot_gross:.2f}",
        },
        "invoices": invoices,
    }


def _require_pro_batch(batch: dict[str, Any]) -> None:
    if not batch.get("pro_unlocked"):
        raise PermissionError("Pro license required to export DATEV EXTF, Xero Bills, or QuickBooks Bills CSVs.")


def _de_num(val: Any) -> str:
    return f"{Decimal(str(val)):.2f}".replace(".", ",")


def _fallback_header_line(inv: dict[str, Any]) -> dict[str, Any]:
    net_d = Decimal(str(inv.get("tax_exclusive_total") or "0.00"))
    vat_d = Decimal(str(inv.get("tax_total") or "0.00"))
    inf_rate = (
        ((abs(vat_d) / abs(net_d)) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        if abs(net_d) > Decimal("0.00") and abs(vat_d) > Decimal("0.00")
        else Decimal("0.00")
    )
    bu_f, acct_f, xtax_f, qacct_f = _map_line_tax("S", inf_rate)
    return {
        "name": f"{inv['syntax']} Invoice {inv['invoice_id']}",
        "qty": "1.00",
        "unit_price": f"{net_d:.2f}",
        "line_net": f"{net_d:.2f}",
        "line_tax": f"{vat_d:.2f}",
        "vat_rate": f"{inf_rate:.2f}",
        "datev_bu_key": inv.get("datev_bu_key") or bu_f,
        "datev_account": inv.get("datev_account") or acct_f,
        "xero_tax_type": xtax_f,
        "qbo_account": qacct_f,
    }


def _is_skipped_unknown(inv: dict[str, Any]) -> bool:
    return (
        inv.get("syntax") == "UNKNOWN"
        and not inv.get("lines")
        and Decimal(str(inv.get("payable_gross_total") or "0.00")) == Decimal("0.00")
    )


def render_datev_extf_csv(batch: dict[str, Any]) -> str:
    """Render Pro-gated DATEV EXTF Buchungsstapel CSV with BU-Schlüssel tax keys."""
    _require_pro_batch(batch)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\n")
    writer.writerow(
        [
            "Umsatz (ohne Soll/Haben-Kz)",
            "Soll/Haben-Kennzeichen",
            "WKZ Umsatz",
            "Konto",
            "Gegenkonto",
            "BU-Schlüssel",
            "Belegdatum",
            "Belegfeld 1",
            "Buchungstext",
        ]
    )
    for inv in batch.get("invoices", []):
        if _is_skipped_unknown(inv):
            continue
        parts = str(inv.get("issue_date") or "").split("-")
        ddmm = f"{parts[2]}{parts[1]}" if len(parts) == 3 and len(parts[1]) == 2 and len(parts[2]) == 2 else ""
        is_cn = bool(inv.get("is_credit_note"))
        lines = inv.get("lines") or [_fallback_header_line(inv)]

        buckets: dict[tuple[str, str, str], Decimal] = {}
        for ln in lines:
            bkey = (
                str(ln.get("datev_bu_key") or inv["datev_bu_key"]),
                str(ln.get("datev_account") or inv["datev_account"]),
                str(ln.get("vat_rate") or "0.00"),
            )
            gross_l = Decimal(str(ln["line_net"])) + Decimal(str(ln.get("line_tax") or "0.00"))
            buckets[bkey] = buckets.get(bkey, Decimal("0.00")) + gross_l

        multi = len(buckets) > 1
        for (bu_b, acct_b, _rate_b), gross_b in buckets.items():
            is_neg_bucket = gross_b < Decimal("0.00")
            sh_flag = "H" if (is_cn ^ is_neg_bucket) else "S"
            text = f"{inv['seller_name']} ({inv['syntax']} · BU {bu_b})" if multi else f"{inv['seller_name']} ({inv['syntax']})"
            writer.writerow(
                [
                    _csv_safe_cell(c)
                    for c in (
                        _de_num(abs(gross_b)),
                        sh_flag,
                        inv["currency"],
                        acct_b,
                        "70000",
                        bu_b,
                        ddmm,
                        inv["invoice_id"],
                        text,
                    )
                ]
            )
    return buf.getvalue().rstrip("\n")


def render_xero_bills_csv(batch: dict[str, Any]) -> str:
    """Render Pro-gated Xero Bills import CSV."""
    _require_pro_batch(batch)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "*ContactName",
            "*InvoiceNumber",
            "*InvoiceDate",
            "*DueDate",
            "*Description",
            "*Quantity",
            "*UnitAmount",
            "*AccountCode",
            "*TaxType",
            "TaxAmount",
            "Currency",
        ]
    )
    for inv in batch.get("invoices", []):
        if _is_skipped_unknown(inv):
            continue
        doc_sign = Decimal("-1") if inv.get("is_credit_note") else Decimal("1")
        for ln in inv.get("lines") or [_fallback_header_line(inv)]:
            unit_signed = (Decimal(str(ln["unit_price"])) * doc_sign).quantize(CENT, rounding=ROUND_HALF_UP)
            tax_signed = (Decimal(str(ln.get("line_tax") or "0.00")) * doc_sign).quantize(CENT, rounding=ROUND_HALF_UP)
            writer.writerow(
                [
                    _csv_safe_cell(c)
                    for c in (
                        inv["seller_name"],
                        inv["invoice_id"],
                        inv["issue_date"],
                        inv["due_date"],
                        ln["name"],
                        ln["qty"],
                        f"{unit_signed:.2f}",
                        str(ln.get("datev_account") or "3425"),
                        str(ln.get("xero_tax_type") or "INPUT (0%)"),
                        f"{tax_signed:.2f}",
                        inv["currency"],
                    )
                ]
            )
    return buf.getvalue().rstrip("\n")


def render_qbo_bills_csv(batch: dict[str, Any]) -> str:
    """Render Pro-gated QuickBooks Online Bills CSV."""
    _require_pro_batch(batch)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "BillNo",
            "Supplier",
            "BillDate",
            "DueDate",
            "Account",
            "LineDescription",
            "Quantity",
            "UnitPrice",
            "LineAmount",
            "TaxCode",
            "TaxAmount",
            "Currency",
        ]
    )
    for inv in batch.get("invoices", []):
        if _is_skipped_unknown(inv):
            continue
        doc_sign = Decimal("-1") if inv.get("is_credit_note") else Decimal("1")
        for ln in inv.get("lines") or [_fallback_header_line(inv)]:
            unit_signed = (Decimal(str(ln["unit_price"])) * doc_sign).quantize(CENT, rounding=ROUND_HALF_UP)
            net_signed = (Decimal(str(ln["line_net"])) * doc_sign).quantize(CENT, rounding=ROUND_HALF_UP)
            tax_signed = (Decimal(str(ln.get("line_tax") or "0.00")) * doc_sign).quantize(CENT, rounding=ROUND_HALF_UP)
            writer.writerow(
                [
                    _csv_safe_cell(c)
                    for c in (
                        inv["invoice_id"],
                        inv["seller_name"],
                        inv["issue_date"],
                        inv["due_date"],
                        ln.get("qbo_account") or "3425 General Purchases",
                        ln["name"],
                        ln["qty"],
                        f"{unit_signed:.2f}",
                        f"{net_signed:.2f}",
                        f"BU {ln.get('datev_bu_key') or inv.get('datev_bu_key', '0')}",
                        f"{tax_signed:.2f}",
                        inv["currency"],
                    )
                ]
            )
    return buf.getvalue().rstrip("\n")
