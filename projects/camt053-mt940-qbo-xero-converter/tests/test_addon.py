"""Deterministic unit & CLI tests for BankFeedBridge (camt053-mt940-qbo-xero-converter)."""

from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from addon import (  # noqa: E402
    FREE_TX_LIMIT,
    SAMPLE_CAMT053_XML,
    SAMPLE_MT940,
    compile_bank_statements,
    parse_camt053_xml,
    parse_mt940_text,
    render_datev_bank_csv,
    render_qbo_web_connect,
    render_xero_csv,
    render_xero_ofx,
    unlock_pro,
)
from cli import main as cli_main  # noqa: E402


class TestBankFeedBridge(unittest.TestCase):
    def test_camt053_nested_txdtls_and_balance_reconciliation(self) -> None:
        parsed = parse_camt053_xml(SAMPLE_CAMT053_XML, source_name="sample-camt.xml")
        self.assertTrue(parsed["ok"])
        self.assertEqual(len(parsed["statements"]), 1)
        st = parsed["statements"][0]
        self.assertEqual(st["account"], "DE89370400440532013000")
        self.assertEqual(st["opening_balance_cents"], 1000000)
        self.assertEqual(st["closing_balance_cents"], 1184550)
        self.assertEqual(st["variance_cents"], 0)
        self.assertTrue(st["reconciled"])

        txs = parsed["transactions"]
        # 1 incoming credit + 2 flattened nested batch debits = 3 transactions
        self.assertEqual(len(txs), 3)
        self.assertEqual(txs[0]["amount_cents"], 250000)
        self.assertEqual(txs[0]["payee"], "Acme GmbH")
        self.assertEqual(txs[0]["reference"], "E2E-INV-2026-01")

        self.assertEqual(txs[1]["amount_cents"], -42000)
        self.assertEqual(txs[1]["payee"], "CloudHost BV")
        self.assertEqual(txs[2]["amount_cents"], -23450)
        self.assertEqual(txs[2]["payee"], "Stripe Processing Fee")

    def test_mt940_subfields_reversals_and_deterministic_fitid(self) -> None:
        parsed_a = parse_mt940_text(SAMPLE_MT940, source_name="bank.sta")
        parsed_b = parse_mt940_text(SAMPLE_MT940, source_name="bank.sta")
        self.assertTrue(parsed_a["ok"])
        st = parsed_a["statements"][0]
        self.assertEqual(st["account"], "NL91ABNA0417164300")
        self.assertEqual(st["opening_balance_cents"], 500000)
        self.assertEqual(st["closing_balance_cents"], 598475)
        self.assertEqual(st["variance_cents"], 0)
        self.assertTrue(st["reconciled"])

        txs = parsed_a["transactions"]
        self.assertEqual(len(txs), 3)
        self.assertEqual(txs[0]["amount_cents"], 125000)
        self.assertEqual(txs[0]["payee"], "Nordic Partner AB")
        # German ?20..?33 structured :86:
        self.assertEqual(txs[1]["amount_cents"], -31025)
        self.assertEqual(txs[1]["payee"], "Hetzner Online GmbH")
        self.assertEqual(txs[1]["counterparty_iban"], "DE12500105170648489890")
        self.assertIn("Managed Hosting Q4", txs[1]["memo"])
        # RD = Reversal of Debit (+)
        self.assertEqual(txs[2]["amount_cents"], 4500)
        self.assertEqual(txs[2]["type"], "CREDIT")

        # Deterministic FITIDs across repeated runs and distinct across entries
        self.assertEqual([t["fitid"] for t in parsed_a["transactions"]], [t["fitid"] for t in parsed_b["transactions"]])
        self.assertEqual(len({t["fitid"] for t in txs}), 3)
        for t in txs:
            self.assertLessEqual(len(t["fitid"]), 32)

    def test_qbo_ofx_xero_and_datev_exports(self) -> None:
        res = compile_bank_statements(
            [("c.xml", SAMPLE_CAMT053_XML), ("m.sta", SAMPLE_MT940)],
            intu_bid="2430",
            account_type="CHECKING",
            pro_unlocked=True,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["summary"]["statements_count"], 2)
        self.assertEqual(res["summary"]["processed_transactions"], 6)
        self.assertTrue(res["summary"]["all_reconciled"])

        qbo = render_qbo_web_connect(res, intu_bid="2430", pro_unlocked=True)
        self.assertIn("OFXHEADER:100", qbo)
        self.assertIn("<INTU.BID>2430</INTU.BID>", qbo)
        self.assertIn("<LEDGERBAL>", qbo)
        self.assertIn("<FITID>", qbo)
        self.assertIn("<DTPOSTED>20261110120000</DTPOSTED>", qbo)

        ofx = render_xero_ofx(res, pro_unlocked=True)
        self.assertIn("<OFX>", ofx)
        self.assertNotIn("<INTU.BID>", ofx)

        xero_csv = render_xero_csv(res)
        rows = list(csv.DictReader(io.StringIO(xero_csv)))
        self.assertEqual(len(rows), 6)
        self.assertIn("*Date", rows[0])
        self.assertIn("*Amount", rows[0])
        self.assertEqual(rows[0]["*Amount"], "2500.00")

        datev_csv = render_datev_bank_csv(res, bank_account="1200", pro_unlocked=True)
        drows = list(csv.DictReader(io.StringIO(datev_csv), delimiter=";"))
        self.assertEqual(len(drows), 6)
        self.assertEqual(drows[0]["Umsatz"], "2500,00")
        self.assertEqual(drows[0]["Soll/Haben"], "S")
        self.assertEqual(drows[1]["Soll/Haben"], "H")

    def test_free_tx_limit_pro_gate_and_cli_out_dir_unlock(self) -> None:
        # Build MT940 statement with 14 transactions (> FREE_TX_LIMIT = 10)
        lines = [":20:BULK-MT940", ":25:DE001234567890", ":28C:1/1", ":60F:C261101EUR1000,00"]
        for i in range(1, 15):
            lines.append(f":61:2611{i:02d}11{i:02d}C10,00NTRFNONREF//B{i:02d}")
            lines.append(f":86:/NAME/Customer {i}/REMI/Order {i}")
        lines.extend([":62F:C261114EUR1140,00", "-"])
        bulk_mt940 = "\n".join(lines)

        free_res = compile_bank_statements([("bulk.sta", bulk_mt940)], pro_unlocked=False)
        self.assertTrue(free_res["truncated_by_free_tier"])
        self.assertEqual(free_res["summary"]["total_transactions"], 14)
        self.assertEqual(free_res["summary"]["processed_transactions"], FREE_TX_LIMIT)
        self.assertEqual(len(free_res["transactions"]), FREE_TX_LIMIT)

        # Free Xero CSV preview succeeds (10 rows), Pro exporters raise PermissionError
        self.assertEqual(len(list(csv.DictReader(io.StringIO(render_xero_csv(free_res))))), FREE_TX_LIMIT)
        with self.assertRaises(PermissionError):
            render_qbo_web_connect(free_res, pro_unlocked=False)
        with self.assertRaises(PermissionError):
            render_xero_ofx(free_res, pro_unlocked=False)
        with self.assertRaises(PermissionError):
            render_datev_bank_csv(free_res, pro_unlocked=False)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            cache_dir = tmp_dir / "lic_cache"
            in_file = tmp_dir / "bulk.sta"
            out_dir = tmp_dir / "exports"
            in_file.write_text(bulk_mt940, encoding="utf-8")

            # Unlicensed CLI --out-dir must exit 2 without writing files
            rc_locked = cli_main(["--input", str(in_file), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)])
            self.assertEqual(rc_locked, 2)
            self.assertFalse(out_dir.exists())

            lic = unlock_pro("cs_live_TestBankFeedBridgeKey1234567890", cache_dir=str(cache_dir))
            self.assertTrue(lic["valid"])

            rc_ok = cli_main(
                ["--input", str(in_file), "--out-dir", str(out_dir), "--intu-bid", "2430", "--cache-dir", str(cache_dir)]
            )
            self.assertEqual(rc_ok, 0)
            for fname in (
                "quickbooks-webconnect.qbo",
                "xero-bank.ofx",
                "xero-bank-statement.csv",
                "datev-bank-buchungsstapel.csv",
                "reconciliation-audit.json",
            ):
                self.assertTrue((out_dir / fname).is_file(), f"Missing {fname}")

            audit = json.loads((out_dir / "reconciliation-audit.json").read_text(encoding="utf-8"))
            self.assertEqual(audit["summary"]["processed_transactions"], 14)
            self.assertTrue(audit["summary"]["all_reconciled"])
            self.assertIn("<INTU.BID>2430</INTU.BID>", (out_dir / "quickbooks-webconnect.qbo").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
