import json
import sys
import tempfile
import unittest
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from addon import (  # noqa: E402
    FREE_ROW_LIMIT,
    SAMPLE_MULTI_PLATFORM_CSV,
    compile_oss_return,
    parse_transactions_csv,
    render_bzst_bop_csv,
    render_eu27_audit_csv,
    render_ros_xml,
)
from cli import APP_SLUG, main as cli_main  # noqa: E402
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402


STRIPE_CSV = """tax_country,currency,taxable_amount,tax_amount,tax_rate,transaction_type,customer_vat_id
FR,EUR,100.00,20.00,0.20,charge,
FR,EUR,25.00,5.00,20%,refund,
GR,USD,100.00,24.00,0.24,charge,
DE,EUR,120.00,22.80,19.0,charge,
NL,EUR,300.00,0.00,0.0,charge,NL123456789B01
"""

SHOPIFY_CSV = """shipping_country,presentment_currency,net_sales,taxes,tax_rate,kind,supply_type
NL,EUR,50.00,10.50,21.0,order,GOODS
ES,GBP,100.00,21.00,21.0,order,GOODS
US,USD,200.00,0.00,0.0,order,GOODS
GB,GBP,75.00,0.00,0.0,order,GOODS
"""

LEMON_CSV = """billing_country,currency,subtotal,tax,vat_rate,status,product_type
AT,EUR,40.00,4.00,10.0,order,SERVICES
BE,EUR,60.00,12.60,21.0,order,SERVICES
"""


class TestOssVatCompiler(unittest.TestCase):
    def test_multi_platform_parse_fx_exclusions_and_refund_netting(self):
        rows = (
            parse_transactions_csv(STRIPE_CSV)
            + parse_transactions_csv(SHOPIFY_CSV)
            + parse_transactions_csv(LEMON_CSV)
        )
        report = compile_oss_return(rows, home_country="DE", quarter="2026-Q4", pro_unlocked=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["excluded"]["DOMESTIC_HOME_STATE"], 1)  # DE
        self.assertEqual(report["excluded"]["NON_EU"], 2)  # US + GB
        self.assertEqual(report["excluded"]["B2B_REVERSE_CHARGE"], 1)  # NL123456789B01

        by_key = {(b["mscon"], b["rate_type"]): b for b in report["buckets"]}
        # FR: 100 - 25 = 75.00 EUR, VAT 20 - 5 = 15.00 EUR
        self.assertIn(("FR", "STANDARD"), by_key)
        self.assertEqual(by_key[("FR", "STANDARD")]["net_taxable_eur"], "75.00")
        self.assertEqual(by_key[("FR", "STANDARD")]["net_vat_eur"], "15.00")

        # Greece GR -> EL with USD FX 0.92: 92.00 EUR taxable, 22.08 EUR VAT
        self.assertIn(("EL", "STANDARD"), by_key)
        self.assertEqual(by_key[("EL", "STANDARD")]["net_taxable_eur"], "92.00")
        self.assertEqual(by_key[("EL", "STANDARD")]["net_vat_eur"], "22.08")

        # ES with GBP FX 1.19: 119.00 EUR taxable, 24.99 EUR VAT
        self.assertIn(("ES", "STANDARD"), by_key)
        self.assertEqual(by_key[("ES", "STANDARD")]["net_taxable_eur"], "119.00")
        self.assertEqual(by_key[("ES", "STANDARD")]["net_vat_eur"], "24.99")

        # AT reduced 10% rate
        self.assertIn(("AT", "REDUCED"), by_key)
        self.assertEqual(by_key[("AT", "REDUCED")]["net_taxable_eur"], "40.00")
        self.assertEqual(by_key[("AT", "REDUCED")]["net_vat_eur"], "4.00")

        # Exact Decimal total across FR(15) + EL(22.08) + ES(24.99) + NL(10.50) + AT(4.00) + BE(12.60)
        self.assertEqual(report["summary"]["total_vat_due_eur"], "89.17")

    def test_vat_anomaly_warning(self):
        bad_csv = "country,currency,subtotal,tax_amount,tax_rate\nFR,EUR,100.00,15.00,20.0\n"
        report = compile_oss_return(parse_transactions_csv(bad_csv), pro_unlocked=True)
        self.assertTrue(any("differs from" in w for w in report["warnings"]))

    def test_portal_exports_bzst_ros_xml_and_audit_csv(self):
        rows = parse_transactions_csv(SAMPLE_MULTI_PLATFORM_CSV)
        report = compile_oss_return(rows, home_country="DE", quarter="2026-Q4", pro_unlocked=True)

        bzst = render_bzst_bop_csv(report)
        lines = bzst.splitlines()
        self.assertTrue(lines[0].startswith("Satzart;Land des Verbrauchs;"))
        self.assertTrue(any(ln.startswith("BOP_OSS_V1;EL;STANDARD;24,00;") for ln in lines))
        self.assertFalse(any(";GR;" in ln for ln in lines))

        ros_xml = render_ros_xml(report, seller_vat_id="DE998877665")
        root = ET.fromstring(ros_xml)
        self.assertEqual(root.tag, "OSSReturn")
        self.assertEqual(root.findtext("SellerVATID"), "DE998877665")
        self.assertGreater(len(root.findall("./Supplies/Supply")), 5)

        audit_csv = render_eu27_audit_csv(report)
        self.assertIn("Member State,Supply Type,Rate Type,VAT Rate %,Tx Count", audit_csv)

    def test_free_tier_limit_and_unlicensed_block_then_pro_unlock(self):
        rows = parse_transactions_csv(SAMPLE_MULTI_PLATFORM_CSV)
        self.assertEqual(len(rows), 20)

        free_report = compile_oss_return(rows, pro_unlocked=False)
        self.assertTrue(free_report["truncated_free_tier"])
        self.assertEqual(free_report["processed_rows"], FREE_ROW_LIMIT)
        self.assertEqual(free_report["truncated_rows"], 5)

        with self.assertRaises(PermissionError):
            render_bzst_bop_csv(free_report)
        with self.assertRaises(PermissionError):
            render_ros_xml(free_report)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cache_dir = tmp_path / "cache"
            out_dir = tmp_path / "out"
            in_stripe = tmp_path / "stripe.csv"
            in_shopify = tmp_path / "shopify.csv"
            in_stripe.write_text(STRIPE_CSV, encoding="utf-8")
            in_shopify.write_text(SHOPIFY_CSV, encoding="utf-8")

            # Unlicensed CLI export must block
            blocked_rc = cli_main(
                ["--input", str(in_stripe), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)]
            )
            self.assertNotEqual(blocked_rc, 0)
            self.assertFalse((out_dir / "bzst-oss-return.csv").exists())

            # Activate mocked valid Stripe Checkout Session key
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
                if payload.get("license_key") == "cs_live_ValidOssVatProKey1234567890":
                    return FakeResp({"valid": True, "product_id": "prod_VeW6IYwGyYJkPv"})
                return FakeResp({"valid": False, "error": "Invalid session"})

            urllib.request.urlopen = fake_urlopen
            try:
                lic = verify_license(
                    "cs_live_ValidOssVatProKey1234567890",
                    provider="stripe",
                    product_id=["prod_VeW6IYwGyYJkPv"],
                    app_slug=APP_SLUG,
                    cache_dir=cache_dir,
                )
                self.assertTrue(lic["valid"])
                self.assertEqual(lic["tier"], "pro")
            finally:
                urllib.request.urlopen = orig_urlopen

            gate = require_pro_feature("oss_portal_exports", app_slug=APP_SLUG, cache_dir=cache_dir)
            self.assertTrue(gate["allowed"])
            tel = get_telemetry(app_slug=APP_SLUG, cache_dir=cache_dir)
            self.assertGreaterEqual(tel["paywall_hits"], 1)
            self.assertEqual(tel["pro_activations"], 1)

            # Unlocked CLI multi-CSV merge + export succeeds
            ok_rc = cli_main(
                [
                    "--input",
                    str(in_stripe),
                    "--input",
                    str(in_shopify),
                    "--out-dir",
                    str(out_dir),
                    "--cache-dir",
                    str(cache_dir),
                ]
            )
            self.assertEqual(ok_rc, 0)
            self.assertTrue((out_dir / "bzst-oss-return.csv").is_file())
            self.assertTrue((out_dir / "ros-oss-return.xml").is_file())
            self.assertTrue((out_dir / "eu27-oss-audit.csv").is_file())


if __name__ == "__main__":
    unittest.main()
