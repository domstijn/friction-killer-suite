import io
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from addon import FREE_BATCH_CAP, parse_payout_csv, reconcile_payout_batches  # noqa: E402
from cli import APP_SLUG, main as cli_main  # noqa: E402
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402

SAMPLE_MULTI_BATCH_CSV = "\n".join(
    [
        "payout_id,payout_date,type,gross,fee,fx_fee,tax,net,currency,description",
        "po_nov_01,2026-11-05,charge,121.00,3.80,1.20,21.00,116.00,EUR,SaaS Pro Seat A",
        "po_nov_01,2026-11-05,charge,242.00,7.25,0.00,42.00,234.75,EUR,SaaS Pro Seat B",
        "po_nov_01,2026-11-05,refund,-60.50,0.00,0.00,-10.50,-60.50,EUR,Partial Refund (50% Seat A)",
        "po_nov_01,2026-11-05,dispute,-40.00,15.00,0.00,0.00,-55.00,EUR,Chargeback #102",
        "po_nov_02,2026-11-12,charge,363.00,10.50,2.50,63.00,350.00,EUR,Annual Plan",
    ]
)


def test_parse_and_free_tier_cap():
    records = parse_payout_csv(SAMPLE_MULTI_BATCH_CSV)
    assert len(records) == 5

    # Free tier processes 1 batch, verifies zero drift & debit == credit, and truncates batch #2
    free_res = reconcile_payout_batches(SAMPLE_MULTI_BATCH_CSV, is_pro=False, export_format="xero")
    assert free_res["ok"] is True
    assert free_res["is_pro"] is False
    assert free_res["total_batches"] == 2
    assert free_res["processed_batches"] == FREE_BATCH_CAP
    assert free_res["truncated_batches"] == 1
    assert free_res["balanced"] is True
    assert free_res["total_debits"] == free_res["total_credits"] == 352.5
    assert free_res["batches"][0]["tax_collected"] == 52.5
    assert free_res["batches"][0]["refunds_gross"] == 50.0
    assert free_res["batches"][0]["drift"] == 0.0
    assert free_res["batches"][0]["expected_net"] == 235.25
    assert "*Narration,*Date,Description,*AccountCode,*TaxType,*Amount" in free_res["xero_csv"]
    assert "NONE" in free_res["xero_csv"]
    assert "OUTPUT2" not in free_res["xero_csv"]
    assert "EXEMPTEXPENSES" not in free_res["xero_csv"]
    assert free_res["qbo_csv"] is None
    assert free_res["datev_csv"] is None

    # Free tier blocks QuickBooks and DATEV formats
    for blocked_fmt in ("qbo", "datev", "all"):
        blk = reconcile_payout_batches(SAMPLE_MULTI_BATCH_CSV, is_pro=False, export_format=blocked_fmt)
        assert blk["ok"] is False
        assert blk["blocked_by_tier"] is True


def test_stripe_license_activation_and_pro_exports():
    with tempfile.TemporaryDirectory() as cache_dir:
        gate_before = require_pro_feature("qbo_datev_export", app_slug=APP_SLUG, cache_dir=cache_dir)
        assert gate_before["allowed"] is False

        # Mock Stripe Managed Payments /verify-license endpoint
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
            if payload.get("license_key") == "cs_live_ValidPayoutBridgeKey123":
                return FakeResp({"valid": True, "product_id": "prod_VeW6IYwGyYJkPv"})
            return FakeResp({"valid": False, "error": "Invalid session"})

        urllib.request.urlopen = fake_urlopen
        try:
            lic = verify_license(
                "cs_live_ValidPayoutBridgeKey123",
                provider="stripe",
                product_id=["prod_PAYOUT", "prod_VeW6IYwGyYJkPv"],
                app_slug=APP_SLUG,
                cache_dir=cache_dir,
            )
            assert lic["valid"] is True
            assert lic["tier"] == "pro"
        finally:
            urllib.request.urlopen = orig_urlopen

        gate_after = require_pro_feature("qbo_datev_export", app_slug=APP_SLUG, cache_dir=cache_dir)
        assert gate_after["allowed"] is True

        tel = get_telemetry(app_slug=APP_SLUG, cache_dir=cache_dir)
        assert tel["paywall_hits"] >= 1
        assert tel["pro_activations"] == 1

        # CLI execution with Pro cache active
        csv_path = Path(cache_dir) / "sample.csv"
        csv_path.write_text(SAMPLE_MULTI_BATCH_CSV, encoding="utf-8")
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            rc = cli_main(["--csv", str(csv_path), "--format", "all", "--cache-dir", cache_dir])
        finally:
            sys.stdout = old_stdout
        assert rc == 0
        pro_res = json.loads(buf.getvalue())
        assert pro_res["ok"] is True
        assert pro_res["processed_batches"] == 2
        assert pro_res["truncated_batches"] == 0
        assert pro_res["balanced"] is True
        assert pro_res["total_debits"] == pro_res["total_credits"] == 715.5
        assert "JournalNo,JournalDate,AccountName,Debits,Credits,Memo" in pro_res["qbo_csv"]
        assert "Umsatz;Soll/Haben-Kennzeichen;Konto;Gegenkonto" in pro_res["datev_csv"]


if __name__ == "__main__":
    test_parse_and_free_tier_cap()
    test_stripe_license_activation_and_pro_exports()
    print("OK: StripePayoutBridge test_addon.py passed")
