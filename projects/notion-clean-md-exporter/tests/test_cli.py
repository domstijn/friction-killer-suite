import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from exporter import clean_markdown_content, export_workspace, strip_notion_uuid
from license_client import _parse_response, get_telemetry, require_pro_feature, verify_license


def test_strip_notion_uuid_and_links():
    assert (
        strip_notion_uuid("Product Spec a1b2c3d4e5f60123456789abcdef0123.md")
        == "product-spec.md"
    )
    assert (
        strip_notion_uuid(
            "Engineering%20Docs%200123456789abcdef0123456789abcdef/API%20Guide%20a1b2c3d4e5f60123456789abcdef0123.md"
        )
        == "engineering-docs/api-guide.md"
    )
    assert strip_notion_uuid("Diagram 0123456789abcdef0123456789abcdef.png") == "diagram.png"

    raw = (
        "# API Guide\n\n"
        "Status: Ready\n"
        "Tags: docs, api\n\n"
        "See [Overview](Overview%200123456789abcdef0123456789abcdef.md) and "
        "[External](https://example.com/a%200123456789abcdef0123456789abcdef.md).\n"
    )
    free_out = clean_markdown_content(raw, convert_frontmatter=False)
    assert "(overview.md)" in free_out
    assert "(https://example.com/a%200123456789abcdef0123456789abcdef.md)" in free_out
    assert "---\n" not in free_out

    pro_out = clean_markdown_content(raw, convert_frontmatter=True)
    assert pro_out.startswith("---\ntitle: \"API Guide\"\nstatus: \"Ready\"\ntags: [\"docs\", \"api\"]\n---\n")
    assert "(overview.md)" in pro_out


def test_free_cap_and_pro_unlock_export():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        in_dir = tmp_path / "notion_export"
        out_free = tmp_path / "out_free"
        out_pro = tmp_path / "out_pro"
        cache_dir = tmp_path / "cache"
        in_dir.mkdir(parents=True)

        # Create 11 Markdown files + 1 image asset
        sub = in_dir / "Guides a1b2c3d4e5f60123456789abcdef0123"
        sub.mkdir()
        for i in range(11):
            target = sub if i == 0 else in_dir
            (target / f"Page {i} 0123456789abcdef0123456789abcdef.md").write_text(
                f"# Page {i}\n\nStatus: Draft\n\nContent for page {i}.\n",
                encoding="utf-8",
            )
        (sub / "Arch Diagram 0123456789abcdef0123456789abcdef.png").write_bytes(b"PNG")

        # 1. Free tier blocks > 10 files
        free_res = export_workspace(in_dir, out_free, is_pro=False)
        assert free_res["ok"] is False
        assert free_res["blocked_by_tier"] is True

        # 2. Uncached license check returns allowed=False
        assert require_pro_feature("unlimited_yaml_export", app_slug="notion-clean-md-exporter", cache_dir=cache_dir)["allowed"] is False

        # 3. Cached Pro license unlocks all 11 files + YAML frontmatter + assets
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "license.json").write_text(
            json.dumps({"valid": True, "tier": "pro", "checked_at": time.time()}),
            encoding="utf-8",
        )
        gate = require_pro_feature("unlimited_yaml_export", app_slug="notion-clean-md-exporter", cache_dir=cache_dir)
        assert gate["allowed"] is True

        pro_res = export_workspace(in_dir, out_pro, is_pro=gate["allowed"])
        assert pro_res["ok"] is True
        assert pro_res["processed"] == 11
        cleaned_page0 = (out_pro / "guides" / "page-0.md").read_text(encoding="utf-8")
        assert cleaned_page0.startswith("---\ntitle: \"Page 0\"\nstatus: \"Draft\"\n---")
        assert (out_pro / "guides" / "arch-diagram.png").exists()

        # 4. Bundle product_id list validation + telemetry checks
        ok_bundle, reason_bundle, _ = _parse_response(
            "lemonsqueezy",
            {"valid": True, "meta": {"product_id": "BUNDLE-999"}, "license_key": {}},
            ["SINGLE-1", "BUNDLE-999"],
        )
        assert ok_bundle is True and reason_bundle == "ok"
        bad_bundle, reason_bad, _ = _parse_response(
            "lemonsqueezy",
            {"valid": True, "meta": {"product_id": "OTHER-0"}, "license_key": {}},
            ["SINGLE-1", "BUNDLE-999"],
        )
        assert bad_bundle is False and reason_bad == "Product mismatch"

        class _MockResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(
                    {"valid": True, "meta": {"product_id": "BUNDLE-999"}, "license_key": {}}
                ).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=_MockResp()):
            lic = verify_license(
                "BUNDLE-CLI-KEY",
                provider="lemonsqueezy",
                product_id=["SINGLE-1", "BUNDLE-999"],
                app_slug="notion-clean-md-exporter",
                cache_dir=cache_dir,
            )
            assert lic["valid"] is True
            assert lic["tier"] == "pro"

        tel = get_telemetry(app_slug="notion-clean-md-exporter", cache_dir=cache_dir)
        assert tel["paywall_hits"] >= 1
        assert tel["activation_attempts"] >= 1
        assert tel["pro_activations"] >= 1


if __name__ == "__main__":
    test_strip_notion_uuid_and_links()
    test_free_cap_and_pro_unlock_export()
    print("OK: NotionGitExport test_cli.py passed")
