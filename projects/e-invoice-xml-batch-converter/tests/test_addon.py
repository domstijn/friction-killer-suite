import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from addon import (  # noqa: E402
    FREE_INVOICE_LIMIT,
    SAMPLE_CII_ZUGFERD_XML,
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

    def test_en16931_math_error_detection(self):
        broken_ubl = SAMPLE_UBL_PEPPOL_XML.replace("<cbc:PayableAmount currencyID=\"EUR\">238.00</cbc:PayableAmount>", "<cbc:PayableAmount currencyID=\"EUR\">999.00</cbc:PayableAmount>")
        parsed = parse_einvoice_xml(broken_ubl, filename="bad.xml")
        self.assertFalse(parsed["en16931_valid"])
        self.assertTrue(any("BR-CO-15" in e for e in parsed["validation_errors"]))

    def test_batch_exports_datev_xero_qbo(self):
        docs = [
            ("a.xml", SAMPLE_UBL_PEPPOL_XML),
            ("b.xml", SAMPLE_CII_ZUGFERD_XML),
        ]
        batch = compile_einvoice_batch(docs, pro_unlocked=True)
        self.assertEqual(batch["summary"]["valid_count"], 2)
        self.assertEqual(batch["summary"]["total_net"], "300.00")
        self.assertEqual(batch["summary"]["total_vat"], "45.00")
        self.assertEqual(batch["summary"]["total_gross"], "345.00")

        datev = render_datev_extf_csv(batch)
        self.assertTrue(datev.startswith("Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Konto;Gegenkonto;BU-Schlüssel;"))
        self.assertIn("238,00;S;EUR;3400;70000;9;1811;XR-2026-1001;", datev)
        self.assertIn("107,00;S;EUR;3300;70000;8;1911;ZF-2026-2002;", datev)

        xero = render_xero_bills_csv(batch)
        self.assertTrue(xero.startswith("*ContactName,*InvoiceNumber,*InvoiceDate,*DueDate,"))
        self.assertIn("Nordic Cloud Infrastructure GmbH,XR-2026-1001", xero)

        qbo = render_qbo_bills_csv(batch)
        self.assertTrue(qbo.startswith("BillNo,Supplier,BillDate,DueDate,"))
        self.assertIn("ZF-2026-2002,Fachverlag Berlin KG", qbo)

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
