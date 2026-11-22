import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from addon import (  # noqa: E402
    FREE_ROW_LIMIT,
    SAMPLE_AMAZON_V2_TSV,
    compile_settlement_journals,
    parse_amazon_settlement,
    render_datev_extf_csv,
    render_qbo_journal_csv,
    render_xero_journal_csv,
)
from cli import APP_SLUG, main as cli_main  # noqa: E402
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402


class TestAmzSettlementBridge(unittest.TestCase):
    def test_tsv_parse_ignores_summary_row_double_count_and_balances_to_zero(self):
        rows = parse_amazon_settlement(SAMPLE_AMAZON_V2_TSV)
        # 17 itemized rows in 2184990101 + 3 itemized rows in 2184990102 = 20 itemized rows (2 summary rows excluded)
        self.assertEqual(len(rows), 20)

        report = compile_settlement_journals(rows, pro_unlocked=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"]["settlement_count"], 2)
        self.assertEqual(report["summary"]["drift"], "0.00")
        self.assertEqual(report["warnings"], [])

        s1 = report["settlements"][0]
        self.assertEqual(s1["settlement_id"], "2184990101")
        self.assertEqual(s1["drift"], "0.00")
        # 120 + 200 + 10 = 330.00 Principal & Shipping
        self.assertEqual(s1["gross_sales"], "330.00")
        # (-18 -5.40 -30 -6.50 +4.20 -14) FBA/Referral + (-24) Ads = -93.70
        self.assertEqual(s1["fees_and_ads"], "-93.70")
        # +95 previous release - 40 current holdback = +55.00
        self.assertEqual(s1["reserve_change"], "55.00")
        # Header total-amount reconciliation = 264.10
        self.assertEqual(s1["net_deposit"], "264.10")

        s2 = report["settlements"][1]
        self.assertEqual(s2["settlement_id"], "2184990102")
        self.assertEqual(s2["net_deposit"], "106.50")
        self.assertEqual(s2["drift"], "0.00")

    def test_total_amount_mismatch_warning(self):
        bad_tsv = (
            "settlement-id\tdeposit-date\ttotal-amount\tcurrency\ttransaction-type\tamount-type\tamount-description\tamount\n"
            "999\t2026-11-16\t500.00\tEUR\t\t\t\t\n"
            "999\t2026-11-16\t\tEUR\tOrder\tItemPrice\tPrincipal\t100.00\n"
        )
        report = compile_settlement_journals(parse_amazon_settlement(bad_tsv), pro_unlocked=True)
        self.assertTrue(any("differs from header total-amount" in w for w in report["warnings"]))

    def test_xero_qbo_datev_exports(self):
        rows = parse_amazon_settlement(SAMPLE_AMAZON_V2_TSV)
        report = compile_settlement_journals(rows, pro_unlocked=True)

        xero = render_xero_journal_csv(report)
        self.assertTrue(xero.startswith("*Narration,*Date,*Description,*AccountCode,*TaxRate,*Amount"))
        self.assertIn("Amazon Settlement 2184990101", xero)
        self.assertIn("Amazon Settlement 2184990102", xero)

        qbo = render_qbo_journal_csv(report)
        self.assertTrue(qbo.startswith("JournalNo,JournalDate,AccountName,Debits,Credits,Description,Currency"))
        self.assertIn("AMZ-2184990101", qbo)
        self.assertIn("Marketplace Facilitator Tax Withheld", qbo)

        datev = render_datev_extf_csv(report)
        self.assertTrue(datev.startswith("Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;"))
        self.assertIn("264,10;S;EUR;1360;", datev)

    def test_free_tier_cap_and_pro_gate_lifecycle(self):
        rows = parse_amazon_settlement(SAMPLE_AMAZON_V2_TSV)
        free_rep = compile_settlement_journals(rows, pro_unlocked=False)
        self.assertTrue(free_rep["truncated_free_tier"])
        self.assertEqual(free_rep["processed_rows"], FREE_ROW_LIMIT)
        self.assertEqual(free_rep["summary"]["settlement_count"], 1)
        self.assertEqual(free_rep["summary"]["drift"], "0.00")

        with self.assertRaises(PermissionError):
            render_xero_journal_csv(free_rep)
        with self.assertRaises(PermissionError):
            render_qbo_journal_csv(free_rep)
        with self.assertRaises(PermissionError):
            render_datev_extf_csv(free_rep)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cache_dir = tmp_path / "cache"
            out_dir = tmp_path / "out"
            in_tsv = tmp_path / "settlement.tsv"
            in_tsv.write_text(SAMPLE_AMAZON_V2_TSV, encoding="utf-8")

            blocked_rc = cli_main(
                ["--input", str(in_tsv), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)]
            )
            self.assertNotEqual(blocked_rc, 0)
            self.assertFalse((out_dir / "xero-amazon-journals.csv").exists())

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
                if payload.get("license_key") == "cs_live_ValidAmzSettleProKey123456":
                    return FakeResp({"valid": True, "product_id": "prod_VeW6IYwGyYJkPv"})
                return FakeResp({"valid": False, "error": "Invalid key"})

            urllib.request.urlopen = fake_urlopen
            try:
                lic = verify_license(
                    "cs_live_ValidAmzSettleProKey123456",
                    provider="stripe",
                    product_id=["prod_VeW6IYwGyYJkPv"],
                    app_slug=APP_SLUG,
                    cache_dir=cache_dir,
                )
                self.assertTrue(lic["valid"])
                self.assertEqual(lic["tier"], "pro")
            finally:
                urllib.request.urlopen = orig_urlopen

            gate = require_pro_feature("amazon_journal_exports", app_slug=APP_SLUG, cache_dir=cache_dir)
            self.assertTrue(gate["allowed"])
            tel = get_telemetry(app_slug=APP_SLUG, cache_dir=cache_dir)
            self.assertGreaterEqual(tel["paywall_hits"], 1)
            self.assertEqual(tel["pro_activations"], 1)

            ok_rc = cli_main(
                ["--input", str(in_tsv), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)]
            )
            self.assertEqual(ok_rc, 0)
            self.assertTrue((out_dir / "xero-amazon-journals.csv").is_file())
            self.assertTrue((out_dir / "qbo-amazon-journals.csv").is_file())
            self.assertTrue((out_dir / "datev-amazon-extf.csv").is_file())


if __name__ == "__main__":
    unittest.main()
