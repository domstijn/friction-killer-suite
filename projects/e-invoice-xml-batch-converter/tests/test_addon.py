import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from addon import (  # noqa: E402
    FREE_INVOICE_LIMIT,
    SAMPLE_CII_MIXED_XML,
    SAMPLE_CII_ZUGFERD_XML,
    SAMPLE_PEPPOL_BIS3_XML,
    SAMPLE_UBL_PEPPOL_XML,
    compile_einvoice_batch,
    parse_einvoice_xml,
    render_datev_extf_csv,
    render_qbo_bills_csv,
    render_xero_bills_csv,
)
from cli import APP_SLUG, main as cli_main  # noqa: E402
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402


class TestEInvoiceLocal(unittest.TestCase):
    def test_ubl_and_cii_parsing_validation_and_datev_bu_keys(self):
        ubl = parse_einvoice_xml(SAMPLE_UBL_PEPPOL_XML, filename="xr-1001.xml")
        self.assertEqual(ubl["syntax"], "UBL_2.1")
        self.assertEqual(ubl["invoice_id"], "XR-2026-1001")
        self.assertEqual(ubl["issue_date"], "2026-11-18")
        self.assertEqual(ubl["tax_exclusive_total"], "200.00")
        self.assertEqual(ubl["tax_total"], "38.00")
        self.assertEqual(ubl["payable_gross_total"], "238.00")
        self.assertEqual(ubl["datev_bu_key"], "9")
        self.assertEqual(ubl["datev_account"], "3400")
        self.assertTrue(ubl["en16931_valid"])

        cii = parse_einvoice_xml(SAMPLE_CII_ZUGFERD_XML, filename="zf-2002.xml")
        self.assertEqual(cii["syntax"], "CII_EN16931")
        self.assertEqual(cii["invoice_id"], "ZF-2026-2002")
        self.assertEqual(cii["issue_date"], "2026-11-19")
        self.assertEqual(cii["due_date"], "2026-12-05")
        self.assertEqual(cii["datev_bu_key"], "8")
        self.assertEqual(cii["datev_account"], "3300")
        self.assertTrue(cii["en16931_valid"])

        peppol_ae = parse_einvoice_xml(SAMPLE_PEPPOL_BIS3_XML, filename="pep-3003.xml")
        self.assertEqual(peppol_ae["invoice_id"], "PEP-2026-3003")
        self.assertEqual(peppol_ae["datev_bu_key"], "94")
        self.assertEqual(peppol_ae["datev_account"], "3123")
        self.assertTrue(peppol_ae["en16931_valid"])

        mixed = parse_einvoice_xml(SAMPLE_CII_MIXED_XML, filename="zf-4004.xml")
        self.assertEqual(mixed["invoice_id"], "ZF-2026-4004")
        self.assertEqual(mixed["datev_bu_key"], "8+9")
        self.assertEqual(mixed["datev_account"], "3300,3400")
        self.assertEqual(mixed["payable_gross_total"], "333.00")
        self.assertTrue(mixed["en16931_valid"])

        k_xml = SAMPLE_UBL_PEPPOL_XML.replace(
            "<cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory>",
            "<cac:ClassifiedTaxCategory><cbc:ID>K</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory>",
        ).replace(
            "<cbc:TaxAmount currencyID=\"EUR\">38.00</cbc:TaxAmount>",
            "<cbc:TaxAmount currencyID=\"EUR\">0.00</cbc:TaxAmount>",
        ).replace(
            "<cbc:PayableAmount currencyID=\"EUR\">238.00</cbc:PayableAmount>",
            "<cbc:PayableAmount currencyID=\"EUR\">200.00</cbc:PayableAmount>",
        )
        k_parsed = parse_einvoice_xml(k_xml, filename="eu-acq.xml")
        self.assertEqual(k_parsed["datev_bu_key"], "91")
        self.assertEqual(k_parsed["datev_account"], "3425")
        self.assertTrue(k_parsed["en16931_valid"])

    def test_credit_note_va_priority_multi_tax_total_and_bad_xml(self):
        # 1. CII TypeCode=381 Credit Note + multiple SpecifiedTaxRegistration (FC before VA)
        cn_cii = (
            SAMPLE_CII_ZUGFERD_XML
            .replace("<ram:TypeCode>380</ram:TypeCode>", "<ram:TypeCode>381</ram:TypeCode>")
            .replace("<ram:ID>ZF-2026-2002</ram:ID>", "<ram:ID>GS-2026-9001</ram:ID>")
            .replace(
                "<ram:Name>Fachverlag Berlin KG</ram:Name>",
                "<ram:Name>Fachverlag; Berlin KG</ram:Name>",
            )
            .replace(
                '<ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE812345678</ram:ID></ram:SpecifiedTaxRegistration>',
                '<ram:SpecifiedTaxRegistration><ram:ID schemeID="FC">12/345/67890</ram:ID></ram:SpecifiedTaxRegistration>'
                '<ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE812345678</ram:ID></ram:SpecifiedTaxRegistration>',
            )
        )
        cn_parsed = parse_einvoice_xml(cn_cii, filename="credit.xml")
        self.assertTrue(cn_parsed["en16931_valid"])
        self.assertTrue(cn_parsed["is_credit_note"])
        self.assertEqual(cn_parsed["seller_vat_id"], "DE812345678")

        batch = compile_einvoice_batch([("credit.xml", cn_cii)], pro_unlocked=True)
        datev = render_datev_extf_csv(batch)
        # Soll/Haben must be H for credit note and semicolon in supplier name properly CSV-quoted
        self.assertIn('107,00;H;EUR;3300;70000;8;1911;GS-2026-9001;"Fachverlag; Berlin KG (CII_EN16931)"', datev)

        # 2. UBL multi-TaxTotal selects matching DocumentCurrencyCode & CreditNote root works
        ubl_multi_tax = (
            SAMPLE_UBL_PEPPOL_XML
            .replace("<Invoice ", "<CreditNote ")
            .replace("</Invoice>", "</CreditNote>")
            .replace("<cbc:InvoiceLine>", "<cbc:CreditNoteLine>")
            .replace("</cbc:InvoiceLine>", "</cbc:CreditNoteLine>")
            .replace("<cac:InvoiceLine>", "<cac:CreditNoteLine>")
            .replace("</cac:InvoiceLine>", "</cac:CreditNoteLine>")
            .replace("<cbc:InvoicedQuantity", "<cbc:CreditedQuantity")
            .replace("</cbc:InvoicedQuantity>", "</cbc:CreditedQuantity>")
            .replace(
                '<cac:TaxTotal><cbc:TaxAmount currencyID="EUR">38.00</cbc:TaxAmount></cac:TaxTotal>',
                '<cac:TaxTotal><cbc:TaxAmount currencyID="USD">41.80</cbc:TaxAmount></cac:TaxTotal>'
                '<cac:TaxTotal><cbc:TaxAmount currencyID="EUR">38.00</cbc:TaxAmount></cac:TaxTotal>',
            )
        )
        ubl_cn = parse_einvoice_xml(ubl_multi_tax, filename="ubl-cn.xml")
        self.assertTrue(ubl_cn["is_credit_note"])
        self.assertEqual(ubl_cn["tax_total"], "38.00")
        self.assertTrue(ubl_cn["en16931_valid"])

        # 3. Malformed XML fails gracefully without raising
        bad = parse_einvoice_xml("<Invoice><unclosed></Invoice>", filename="corrupt.xml")
        self.assertFalse(bad["en16931_valid"])
        self.assertEqual(bad["syntax"], "UNKNOWN")
        self.assertTrue(bad["validation_errors"])

        # 4. Signed Invoice + CreditNote summary, Xero/QBO negative CreditNote & CSV injection safety
        xss_cn = (
            SAMPLE_UBL_PEPPOL_XML
            .replace("<Invoice ", "<CreditNote ")
            .replace("</Invoice>", "</CreditNote>")
            .replace("<cac:InvoiceLine>", "<cac:CreditNoteLine>")
            .replace("</cac:InvoiceLine>", "</cac:CreditNoteLine>")
            .replace("<cbc:InvoicedQuantity", "<cbc:CreditedQuantity")
            .replace("</cbc:InvoicedQuantity>", "</cbc:CreditedQuantity>")
            .replace("XR-2026-1001", "CN-2026-1")
            .replace("Nordic Cloud Infrastructure GmbH", "=cmd|' /C calc'!A0")
        )
        mixed_batch = compile_einvoice_batch(
            [("inv.xml", SAMPLE_UBL_PEPPOL_XML), ("cn.xml", xss_cn)], pro_unlocked=True
        )
        self.assertEqual(mixed_batch["summary"]["total_gross"], "0.00")
        self.assertEqual(mixed_batch["summary"]["total_net"], "0.00")
        self.assertEqual(mixed_batch["summary"]["total_vat"], "0.00")
        d_csv = render_datev_extf_csv(mixed_batch)
        x_csv = render_xero_bills_csv(mixed_batch)
        q_csv = render_qbo_bills_csv(mixed_batch)
        self.assertIn("'=cmd|", d_csv)
        self.assertIn("'=cmd|", x_csv)
        import csv as _csv, io as _io
        from decimal import Decimal as _Dec
        self.assertEqual(
            sum(_Dec(r["*Quantity"]) * _Dec(r["*UnitAmount"]) + _Dec(r["TaxAmount"]) for r in _csv.DictReader(_io.StringIO(x_csv))),
            _Dec("0.00"),
        )
        self.assertEqual(
            sum(_Dec(r["LineAmount"]) + _Dec(r["TaxAmount"]) for r in _csv.DictReader(_io.StringIO(q_csv))),
            _Dec("0.00"),
        )

        # 5. BaseQuantity & header AllowanceCharge & UNKNOWN skip across all CSVs
        hdr_ac_xml = (
            SAMPLE_UBL_PEPPOL_XML
            .replace("<cbc:PriceAmount>75.00</cbc:PriceAmount>", "<cbc:PriceAmount>7500.00</cbc:PriceAmount><cbc:BaseQuantity>100</cbc:BaseQuantity>")
            .replace("<cbc:TaxAmount currencyID=\"EUR\">38.00</cbc:TaxAmount>", "<cbc:TaxAmount currencyID=\"EUR\">39.90</cbc:TaxAmount>")
            .replace("<cbc:TaxExclusiveAmount currencyID=\"EUR\">200.00</cbc:TaxExclusiveAmount>", "<cbc:TaxExclusiveAmount currencyID=\"EUR\">210.00</cbc:TaxExclusiveAmount>")
            .replace("<cbc:PayableAmount currencyID=\"EUR\">238.00</cbc:PayableAmount>", "<cbc:PayableAmount currencyID=\"EUR\">249.90</cbc:PayableAmount>")
            .replace(
                "<cac:TaxTotal>",
                "<cac:AllowanceCharge><cbc:ChargeIndicator>true</cbc:ChargeIndicator><cbc:AllowanceChargeReason>Shipping</cbc:AllowanceChargeReason><cbc:Amount currencyID=\"EUR\">10.00</cbc:Amount><cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:TaxCategory></cac:AllowanceCharge><cac:TaxTotal>",
            )
        )
        ac_parsed = parse_einvoice_xml(hdr_ac_xml, filename="ac.xml")
        self.assertTrue(ac_parsed["en16931_valid"], ac_parsed["validation_errors"])
        self.assertEqual(ac_parsed["lines"][0]["unit_price"], "75.00")
        unk_batch = compile_einvoice_batch([("bad.xml", "<broken"), ("ac.xml", hdr_ac_xml)], pro_unlocked=True)
        self.assertEqual(len(list(_csv.DictReader(_io.StringIO(render_xero_bills_csv(unk_batch))))), 3)
        self.assertEqual(len(list(_csv.DictReader(_io.StringIO(render_qbo_bills_csv(unk_batch))))), 3)

    def test_en16931_math_error_detection(self):
        broken_ubl = SAMPLE_UBL_PEPPOL_XML.replace("<cbc:PayableAmount currencyID=\"EUR\">238.00</cbc:PayableAmount>", "<cbc:PayableAmount currencyID=\"EUR\">999.00</cbc:PayableAmount>")
        parsed = parse_einvoice_xml(broken_ubl, filename="bad.xml")
        self.assertFalse(parsed["en16931_valid"])
        self.assertTrue(any("BR-CO-15" in e for e in parsed["validation_errors"]))

    def test_batch_exports_datev_xero_qbo(self):
        import csv as _csv
        import io as _io
        from decimal import Decimal as _Dec

        docs = [
            ("a.xml", SAMPLE_UBL_PEPPOL_XML),
            ("b.xml", SAMPLE_CII_ZUGFERD_XML),
            ("c.xml", SAMPLE_PEPPOL_BIS3_XML),
            ("d.xml", SAMPLE_CII_MIXED_XML),
        ]
        batch = compile_einvoice_batch(docs, pro_unlocked=True)
        self.assertEqual(batch["summary"]["valid_count"], 4)
        self.assertEqual(batch["summary"]["total_net"], "840.00")
        self.assertEqual(batch["summary"]["total_vat"], "78.00")
        self.assertEqual(batch["summary"]["total_gross"], "918.00")

        datev = render_datev_extf_csv(batch)
        self.assertTrue(datev.startswith("Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Konto;Gegenkonto;BU-Schlüssel;"))
        self.assertIn("238,00;S;EUR;3400;70000;9;1811;XR-2026-1001;", datev)
        self.assertIn("107,00;S;EUR;3300;70000;8;1911;ZF-2026-2002;", datev)
        self.assertIn("240,00;S;EUR;3123;70000;94;2011;PEP-2026-3003;", datev)
        self.assertIn("214,00;S;EUR;3300;70000;8;2111;ZF-2026-4004;", datev)
        self.assertIn("119,00;S;EUR;3400;70000;9;2111;ZF-2026-4004;", datev)
        d_rows = list(_csv.DictReader(_io.StringIO(datev), delimiter=";"))
        datev_gross = sum(_Dec(r["Umsatz (ohne Soll/Haben-Kz)"].replace(",", ".")) for r in d_rows)
        self.assertEqual(datev_gross, _Dec("918.00"))

        xero = render_xero_bills_csv(batch)
        self.assertTrue(xero.startswith("*ContactName,*InvoiceNumber,*InvoiceDate,*DueDate,"))
        self.assertIn("Nordic Cloud Infrastructure GmbH,XR-2026-1001", xero)
        x_rows = list(_csv.DictReader(_io.StringIO(xero)))
        self.assertNotIn("400", {r["*AccountCode"] for r in x_rows})
        xero_gross = sum(_Dec(r["*Quantity"]) * _Dec(r["*UnitAmount"]) + _Dec(r["TaxAmount"]) for r in x_rows)
        self.assertEqual(xero_gross, _Dec("918.00"))

        qbo = render_qbo_bills_csv(batch)
        self.assertTrue(qbo.startswith("BillNo,Supplier,BillDate,DueDate,"))
        self.assertIn("ZF-2026-2002,Fachverlag Berlin KG", qbo)
        self.assertIn("Business Accommodation (2 Nights)", qbo)
        q_rows = list(_csv.DictReader(_io.StringIO(qbo)))
        qbo_gross = sum(_Dec(r["LineAmount"]) + _Dec(r["TaxAmount"]) for r in q_rows)
        self.assertEqual(qbo_gross, _Dec("918.00"))

    def test_free_limit_and_pro_directory_unlock(self):
        docs = [
            ("1.xml", SAMPLE_UBL_PEPPOL_XML),
            ("2.xml", SAMPLE_CII_ZUGFERD_XML),
            ("3.xml", SAMPLE_UBL_PEPPOL_XML),
            ("4.xml", SAMPLE_CII_ZUGFERD_XML),
        ]
        free_batch = compile_einvoice_batch(docs, pro_unlocked=False)
        self.assertTrue(free_batch["truncated_free_tier"])
        self.assertEqual(free_batch["processed_files"], FREE_INVOICE_LIMIT)
        self.assertEqual(free_batch["truncated_count"], 1)

        for exporter in (render_datev_extf_csv, render_xero_bills_csv, render_qbo_bills_csv):
            with self.assertRaises(PermissionError):
                exporter(free_batch)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            xml_dir = tmp_path / "xmls"
            out_dir = tmp_path / "out"
            cache_dir = tmp_path / "cache"
            xml_dir.mkdir()
            for fname, body in docs:
                (xml_dir / fname).write_text(body, encoding="utf-8")

            blocked_rc = cli_main(
                ["--input", str(xml_dir), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)]
            )
            self.assertNotEqual(blocked_rc, 0)
            self.assertFalse((out_dir / "datev-extf-buchungsstapel.csv").exists())

            orig_urlopen = urllib.request.urlopen

            class FakeResp:
                def __init__(self, body: dict):
                    self._buf = json.dumps(body).encode("utf-8")

                def read(self):
                    return self._buf

                def __enter__(self):
                    return self

                def __exit__(self, *_):
                    return False

            def fake_urlopen(req, timeout=10):
                payload = json.loads(req.data.decode("utf-8"))
                if payload.get("license_key") == "cs_live_ValidEInvoiceProKey123456":
                    return FakeResp({"valid": True, "product_id": "prod_VeW6IYwGyYJkPv"})
                return FakeResp({"valid": False, "error": "Invalid key"})

            urllib.request.urlopen = fake_urlopen
            try:
                lic = verify_license(
                    "cs_live_ValidEInvoiceProKey123456",
                    provider="stripe",
                    product_id=["prod_VeW6IYwGyYJkPv"],
                    app_slug=APP_SLUG,
                    cache_dir=cache_dir,
                )
                self.assertTrue(lic["valid"])
            finally:
                urllib.request.urlopen = orig_urlopen

            gate = require_pro_feature("einvoice_batch_exports", app_slug=APP_SLUG, cache_dir=cache_dir)
            self.assertTrue(gate["allowed"])
            tel = get_telemetry(app_slug=APP_SLUG, cache_dir=cache_dir)
            self.assertGreaterEqual(tel["paywall_hits"], 1)
            self.assertEqual(tel["pro_activations"], 1)

            ok_rc = cli_main(
                ["--input", str(xml_dir), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)]
            )
            self.assertEqual(ok_rc, 0)
            self.assertTrue((out_dir / "datev-extf-buchungsstapel.csv").is_file())
            self.assertTrue((out_dir / "xero-bills.csv").is_file())
            self.assertTrue((out_dir / "qbo-bills.csv").is_file())


if __name__ == "__main__":
    unittest.main()
