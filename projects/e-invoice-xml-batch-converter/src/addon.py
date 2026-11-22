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
    if not text:
        return Decimal(default)
    try:
        return Decimal(text).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return Decimal(default)


def _norm_date(raw: str) -> str:
    clean = str(raw or "").strip()
    if re.fullmatch(r"\d{8}", clean):
        return f"{clean[:4]}-{clean[4:6]}-{clean[6:8]}"
    return clean[:10] if len(clean) >= 10 else clean


def _map_datev_bu_and_account(lines: list[dict[str, Any]], tax_exclusive: Decimal, tax_total: Decimal) -> tuple[str, str]:
    rates = {_dec(ln.get("vat_rate", 0)) for ln in lines} if lines else set()
    cats = {str(ln.get("vat_category") or "").upper() for ln in lines} if lines else set()
    if not rates and tax_exclusive > Decimal("0.00") and tax_total > Decimal("0.00"):
        inferred = ((tax_total / tax_exclusive) * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
        rates.add(inferred)

    if "AE" in cats:
        return "94", "3123"
    if any(r == Decimal("19.00") for r in rates):
        return "9", "3400"
    if any(r == Decimal("7.00") for r in rates):
        return "8", "3300"
    if all(r == Decimal("0.00") for r in rates) or bool(cats & {"E", "Z", "K", "G"}):
        return "0", "3200"
    return "0", "3425"


def parse_einvoice_xml(xml_text: str, filename: str = "invoice.xml") -> dict[str, Any]:
    """Parse UBL 2.1 or UN/CEFACT CII e-invoice XML, validate EN 16931 math rules, and assign DATEV BU."""
    root = ET.fromstring(str(xml_text or "").strip())
    root_name = _local(root.tag)

    lines: list[dict[str, Any]] = []
    if root_name in {"Invoice", "CreditNote"}:
        syntax = "UBL_2.1"
        invoice_id = _text(root, "ID")
        issue_date = _norm_date(_text(root, "IssueDate"))
        due_date = _norm_date(_text(root, "DueDate") or _text(root, "PaymentMeans", "PaymentDueDate")) or issue_date
        currency = (_text(root, "DocumentCurrencyCode") or "EUR").upper()
        buyer_ref = _text(root, "BuyerReference")

        sup_party = _path(root, "AccountingSupplierParty", "Party")
        seller_name = _text(sup_party, "PartyLegalEntity", "RegistrationName") or _text(sup_party, "PartyName", "Name")
        seller_vat = _text(sup_party, "PartyTaxScheme", "CompanyID")
        seller_iban = _text(root, "PaymentMeans", "PayeeFinancialAccount", "ID")

        cust_party = _path(root, "AccountingCustomerParty", "Party")
        buyer_name = _text(cust_party, "PartyLegalEntity", "RegistrationName") or _text(cust_party, "PartyName", "Name")
        buyer_vat = _text(cust_party, "PartyTaxScheme", "CompanyID")

        tax_total = _dec(_text(root, "TaxTotal", "TaxAmount"))
        lmt = _child(root, "LegalMonetaryTotal")
        tax_exclusive = _dec(_text(lmt, "TaxExclusiveAmount"))
        payable_gross = _dec(_text(lmt, "PayableAmount") or _text(lmt, "TaxInclusiveAmount"))

        line_tag = "CreditNoteLine" if root_name == "CreditNote" else "InvoiceLine"
        qty_tag = "CreditedQuantity" if root_name == "CreditNote" else "InvoicedQuantity"
        for item_el in _children(root, line_tag):
            name = _text(item_el, "Item", "Name") or _text(item_el, "Item", "Description") or "Line Item"
            qty = _dec(_text(item_el, qty_tag) or "1", "1.00")
            unit_price = _dec(_text(item_el, "Price", "PriceAmount"))
            line_net = _dec(_text(item_el, "LineExtensionAmount"))
            tax_cat = _path(item_el, "Item", "ClassifiedTaxCategory")
            vat_rate = _dec(_text(tax_cat, "Percent"))
            vat_cat = (_text(tax_cat, "ID") or "S").upper()
            lines.append(
                {
                    "name": name,
                    "qty": f"{qty:.2f}",
                    "unit_price": f"{unit_price:.2f}",
                    "line_net": f"{line_net:.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "vat_category": vat_cat,
                }
            )
    elif root_name == "CrossIndustryInvoice":
        syntax = "CII_EN16931"
        exch = _child(root, "ExchangedDocument")
        invoice_id = _text(exch, "ID")
        issue_date = _norm_date(_text(exch, "IssueDateTime", "DateTimeString"))

        tx = _child(root, "SupplyChainTradeTransaction")
        hdr_agr = _child(tx, "ApplicableHeaderTradeAgreement")
        buyer_ref = _text(hdr_agr, "BuyerReference")

        seller_p = _child(hdr_agr, "SellerTradeParty")
        seller_name = _text(seller_p, "Name")
        seller_vat = _text(seller_p, "SpecifiedTaxRegistration", "ID")

        buyer_p = _child(hdr_agr, "BuyerTradeParty")
        buyer_name = _text(buyer_p, "Name")
        buyer_vat = _text(buyer_p, "SpecifiedTaxRegistration", "ID")

        hdr_set = _child(tx, "ApplicableHeaderTradeSettlement")
        currency = (_text(hdr_set, "InvoiceCurrencyCode") or "EUR").upper()
        seller_iban = _text(hdr_set, "SpecifiedTradeSettlementPaymentMeans", "PayeePartyCreditorFinancialAccount", "IBANID")
        due_date = _norm_date(_text(hdr_set, "SpecifiedTradePaymentTerms", "DueDateDateTime", "DateTimeString")) or issue_date

        summ = _child(hdr_set, "SpecifiedTradeSettlementHeaderMonetarySummation")
        tax_exclusive = _dec(_text(summ, "TaxBasisTotalAmount"))
        tax_total = _dec(_text(summ, "TaxTotalAmount"))
        payable_gross = _dec(_text(summ, "DuePayableAmount") or _text(summ, "GrandTotalAmount"))

        for li in _children(tx, "IncludedSupplyChainTradeLineItem"):
            name = _text(li, "SpecifiedTradeProduct", "Name") or "Line Item"
            qty = _dec(_text(li, "SpecifiedLineTradeDelivery", "BilledQuantity") or "1", "1.00")
            unit_price = _dec(
                _text(li, "SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "ChargeAmount")
            )
            li_set = _child(li, "SpecifiedLineTradeSettlement")
            line_net = _dec(_text(li_set, "SpecifiedTradeSettlementLineMonetarySummation", "LineTotalAmount"))
            t_el = _child(li_set, "ApplicableTradeTax")
            vat_rate = _dec(_text(t_el, "RateApplicablePercent"))
            vat_cat = (_text(t_el, "CategoryCode") or "S").upper()
            lines.append(
                {
                    "name": name,
                    "qty": f"{qty:.2f}",
                    "unit_price": f"{unit_price:.2f}",
                    "line_net": f"{line_net:.2f}",
                    "vat_rate": f"{vat_rate:.2f}",
                    "vat_category": vat_cat,
                }
            )
    else:
        raise ValueError(f"Unsupported e-invoice root element: <{root_name}> (expected UBL Invoice or CII CrossIndustryInvoice)")

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
        if abs(sum_lines - tax_exclusive) > Decimal("0.01"):
            validation_errors.append(
                f"BR-CO-10: Sum of line net amounts ({sum_lines:.2f}) differs from TaxExclusiveAmount ({tax_exclusive:.2f})."
            )

    if abs((tax_exclusive + tax_total) - payable_gross) > Decimal("0.01"):
        validation_errors.append(
            f"BR-CO-15: TaxExclusiveAmount + TaxTotal ({tax_exclusive + tax_total:.2f}) differs from PayableAmount ({payable_gross:.2f})."
        )

    bu_key, skr03_acct = _map_datev_bu_and_account(lines, tax_exclusive, tax_total)
    return {
        "filename": filename,
        "syntax": syntax,
        "invoice_id": invoice_id,
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
        tot_net += Decimal(inv["tax_exclusive_total"])
        tot_vat += Decimal(inv["tax_total"])
        tot_gross += Decimal(inv["payable_gross_total"])

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
        parts = str(inv.get("issue_date") or "").split("-")
        ddmm = f"{parts[2]}{parts[1]}" if len(parts) == 3 else "1811"
        writer.writerow(
            [
                _de_num(inv["payable_gross_total"]),
                "S",
                inv["currency"],
                inv["datev_account"],
                "70000",
                inv["datev_bu_key"],
                ddmm,
                inv["invoice_id"],
                f"{inv['seller_name']} ({inv['syntax']})",
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
            "Currency",
        ]
    )
    for inv in batch.get("invoices", []):
        for ln in inv.get("lines") or [
            {
                "name": inv["invoice_id"],
                "qty": "1.00",
                "unit_price": inv["tax_exclusive_total"],
                "vat_rate": "0.00",
            }
        ]:
            rate = Decimal(str(ln.get("vat_rate") or "0"))
            tax_type = f"Tax on Purchases ({rate:.0f}%)" if rate > 0 else "Tax Exempt"
            writer.writerow(
                [
                    inv["seller_name"],
                    inv["invoice_id"],
                    inv["issue_date"],
                    inv["due_date"],
                    ln["name"],
                    ln["qty"],
                    ln["unit_price"],
                    "400",
                    tax_type,
                    inv["currency"],
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
            "LineAmount",
            "TaxAmount",
            "Currency",
        ]
    )
    for inv in batch.get("invoices", []):
        writer.writerow(
            [
                inv["invoice_id"],
                inv["seller_name"],
                inv["issue_date"],
                inv["due_date"],
                "Accounts Payable Expenses",
                f"{inv['syntax']} Invoice {inv['invoice_id']}",
                inv["tax_exclusive_total"],
                inv["tax_total"],
                inv["currency"],
            ]
        )
    return buf.getvalue().rstrip("\n")
