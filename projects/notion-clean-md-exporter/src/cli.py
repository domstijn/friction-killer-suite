#!/usr/bin/env python3
"""NotionGitExport CLI: clean Notion Markdown exports for Git, Obsidian, and Astro."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exporter import export_workspace
from license_client import get_telemetry, require_pro_feature, verify_license

APP_SLUG = "notion-clean-md-exporter"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_VeW69bJBCk3Nbr,prod_VeW6IYwGyYJkPv"


def main() -> int:
    parser = argparse.ArgumentParser(description="NotionGitExport: Clean Notion Markdown exports.")
    parser.add_argument("--input", help="Path to unzipped Notion export directory")
    parser.add_argument("--output", help="Destination directory for cleaned Markdown")
    parser.add_argument("--activate", help="Activate a Stripe Pro license key")
    parser.add_argument("--pro", action="store_true", help="Check current Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation telemetry counts")
    parser.add_argument("--cache-dir", help="Optional custom license cache directory")
    args = parser.parse_args()

    if args.telemetry:
        print(json.dumps(get_telemetry(app_slug=APP_SLUG, cache_dir=args.cache_dir), indent=2))
        return 0

    if args.activate:
        res = verify_license(
            args.activate,
            provider=PROVIDER,
            product_id=DEFAULT_PRODUCT_ID,
            app_slug=APP_SLUG,
            cache_dir=args.cache_dir,
        )
        print(json.dumps(res, indent=2))
        return 0 if res.get("valid") else 1

    if args.pro:
        status = require_pro_feature("unlimited_yaml_export", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(status, indent=2))
        return 0

    if not args.input or not args.output:
        parser.print_help()
        return 0

    pro_status = require_pro_feature("unlimited_yaml_export", app_slug=APP_SLUG, cache_dir=args.cache_dir)
    result = export_workspace(args.input, args.output, is_pro=bool(pro_status.get("allowed")))
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
