#!/usr/bin/env python3
"""OssVatBridge CLI: Compile Stripe Tax, Shopify & Lemon Squeezy CSVs into EU VAT OSS returns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addon import (  # noqa: E402
    FREE_ROW_LIMIT,
    SAMPLE_MULTI_PLATFORM_CSV,
    compile_oss_return,
    parse_transactions_csv,
    render_bzst_bop_csv,
    render_eu27_audit_csv,
    render_ros_xml,
)
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402

APP_SLUG = "eu-oss-vat-return-compiler"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_Vg2IUi88B9bJHq,prod_VeW6IYwGyYJkPv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OssVatBridge: Multi-platform Stripe Tax / Shopify / Lemon Squeezy -> EU VAT OSS compiler."
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Input CSV file path (repeatable to merge Stripe, Shopify, and Lemon Squeezy exports)",
    )
    parser.add_argument("--home-country", default="DE", help="Member State of Identification (default: DE)")
    parser.add_argument("--quarter", default="2026-Q4", help="OSS filing quarter (default: 2026-Q4)")
    parser.add_argument("--seller-vat", default="DE123456789", help="Seller VAT ID for ROS XML header")
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory to write Pro portal files (bzst-oss-return.csv, ros-oss-return.xml, eu27-oss-audit.csv)",
    )
    parser.add_argument("--activate", help="Activate Pro license key (Stripe cs_live_...)")
    parser.add_argument("--pro", action="store_true", help="Check cached Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation counts")
    parser.add_argument("--sample", action="store_true", help="Print built-in 20-row multi-platform sample CSV")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.sample:
        print(SAMPLE_MULTI_PLATFORM_CSV.strip())
        return 0

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
        gate = require_pro_feature("oss_portal_exports", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(gate, indent=2))
        return 0

    if args.input:
        all_rows: list[dict[str, Any]] = []
        for path_str in args.input:
            raw_text = Path(path_str).read_text(encoding="utf-8")
            all_rows.extend(parse_transactions_csv(raw_text))

        gate_feature = "oss_portal_exports" if args.out_dir else "unlimited_rows"
        gate = require_pro_feature(gate_feature, app_slug=APP_SLUG, cache_dir=args.cache_dir)
        pro_unlocked = bool(gate.get("allowed"))

        if args.out_dir and not pro_unlocked:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blocked_by_tier": True,
                        "free_row_limit": FREE_ROW_LIMIT,
                        "error": gate.get("reason") or "Pro license required for --out-dir OSS exports.",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

        report = compile_oss_return(
            all_rows,
            home_country=args.home_country,
            quarter=args.quarter,
            pro_unlocked=pro_unlocked,
        )

        if args.out_dir:
            out_path = Path(args.out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            (out_path / "bzst-oss-return.csv").write_text(render_bzst_bop_csv(report) + "\n", encoding="utf-8")
            (out_path / "ros-oss-return.xml").write_text(
                render_ros_xml(report, seller_vat_id=args.seller_vat) + "\n",
                encoding="utf-8",
            )
            (out_path / "eu27-oss-audit.csv").write_text(render_eu27_audit_csv(report) + "\n", encoding="utf-8")
            report["exported_files"] = [
                str(out_path / "bzst-oss-return.csv"),
                str(out_path / "ros-oss-return.xml"),
                str(out_path / "eu27-oss-audit.csv"),
            ]

        print(json.dumps(report, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
