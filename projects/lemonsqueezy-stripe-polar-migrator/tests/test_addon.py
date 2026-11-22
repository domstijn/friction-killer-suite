import io
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from addon import FREE_ROW_CAP, build_migration_pack, iso_to_unix, parse_lemonsqueezy_csv  # noqa: E402
from cli import APP_SLUG, main as cli_main  # noqa: E402
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402


def _make_sample_csv() -> str:
    rows = ["email,name,status,payment_method,mrr,currency,variant_name,renews_at,license_key,activation_limit"]
    for i in range(1, 21):
        is_pp = i % 4 == 0  # 5 PayPal subscribers (i=4,8,12,16,20)
        method = "paypal" if is_pp else "visa"
        mrr = "29.00" if is_pp else "19.00"
        renews = f"2026-12-{(i % 20) + 1:02d}T12:00:00Z"
        key = f"LEMON-{i:04d}-ABCD-{i + 10:04d}"
        rows.append(f"user{i}@acme.io,User {i},active,{method},{mrr},USD,Pro Monthly,{renews},{key},3")
    return "\n".join(rows)


def test_audit_unix_trial_end_and_free_cap():
    sample_csv = _make_sample_csv()
    records = parse_lemonsqueezy_csv(sample_csv)
    assert len(records) == 20
    assert iso_to_unix("2026-12-01T12:00:00Z") > 1790000000

    # Free tier audits all 20 rows (15 card * 19 = 285.0, 5 paypal * 29 = 145.0), exports 15
    free_res = build_migration_pack(sample_csv, is_pro=False)
    assert free_res["ok"] is True
    assert free_res["is_pro"] is False
    assert free_res["total_rows"] == 20
    assert free_res["processed_rows"] == FREE_ROW_CAP
    assert free_res["truncated_rows"] == 5
    assert free_res["card_mrr"] == 285.0
    assert free_res["paypal_mrr_at_risk"] == 145.0
    assert free_res["paypal_count"] == 5
    assert free_res["license_keys_found"] == 20
    assert "paypal_manual_reauth" in free_res["stripe_polar_csv"]
    assert "stripe_card_transfer" in free_res["stripe_polar_csv"]
    assert free_res["paypal_cohort_csv"] is None
    assert free_res["license_bundle_json"] is None

    # Pro flags blocked when Free
    for kwargs in ({"include_paypal_cohort": True}, {"include_license_bundle": True}):
        blk = build_migration_pack(sample_csv, is_pro=False, **kwargs)
        assert blk["ok"] is False
        assert blk["blocked_by_tier"] is True


def test_stripe_license_and_pro_migration_pack():
    sample_csv = _make_sample_csv()
    with tempfile.TemporaryDirectory() as cache_dir:
        gate_before = require_pro_feature("paypal_and_legacy_keys", app_slug=APP_SLUG, cache_dir=cache_dir)
        assert gate_before["allowed"] is False

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
            if payload.get("license_key") == "cs_live_ValidLemonExitKey123456":
                return FakeResp({"valid": True, "product_id": "prod_VeW6IYwGyYJkPv"})
            return FakeResp({"valid": False, "error": "Invalid session"})

        urllib.request.urlopen = fake_urlopen
        try:
            lic = verify_license(
                "cs_live_ValidLemonExitKey123456",
                provider="stripe",
                product_id=["prod_LEMON", "prod_VeW6IYwGyYJkPv"],
                app_slug=APP_SLUG,
                cache_dir=cache_dir,
            )
            assert lic["valid"] is True
            assert lic["tier"] == "pro"
        finally:
            urllib.request.urlopen = orig_urlopen

        tel = get_telemetry(app_slug=APP_SLUG, cache_dir=cache_dir)
        assert tel["paywall_hits"] >= 1
        assert tel["pro_activations"] == 1

        csv_path = Path(cache_dir) / "ls_store.csv"
        csv_path.write_text(sample_csv, encoding="utf-8")
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            rc = cli_main(
                ["--csv", str(csv_path), "--paypal-cohort", "--license-bundle", "--cache-dir", cache_dir]
            )
        finally:
            sys.stdout = old_stdout
        assert rc == 0

        pro_res = json.loads(buf.getvalue())
        assert pro_res["ok"] is True
        assert pro_res["processed_rows"] == 20
        assert pro_res["truncated_rows"] == 0
        assert "user4@acme.io" in pro_res["paypal_cohort_csv"]
        assert "user1@acme.io" not in pro_res["paypal_cohort_csv"]
        bundle = json.loads(pro_res["license_bundle_json"])
        assert bundle["total_keys"] == 20
        assert bundle["keys"]["LEMON-0020-ABCD-0030"]["valid"] is True


if __name__ == "__main__":
    test_audit_unix_trial_end_and_free_cap()
    test_stripe_license_and_pro_migration_pack()
    print("OK: LemonExitBridge test_addon.py passed")
