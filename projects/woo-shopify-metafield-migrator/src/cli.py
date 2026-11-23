#!/usr/bin/env python3
"""ShopMetaShift CLI: Compile WooCommerce CSVs into Shopify Admin, Matrixify & 301 Redirect CSVs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addon import (  # noqa: E402
    APP_SLUG,
    DEFAULT_PRODUCT_ID,
    FREE_PRODUCT_LIMIT,
    PROVIDER,
    SAMPLE_WOO_CSV,
    compile_woo_to_shopify,
    render_matrixify_csv,
    render_redirects_csv,
    render_shopify_admin_csv,
)
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "ShopMetaShift: Zero-Dependency WooCommerce-to-Shopify Variant Metafield, "
            ">3-Option Overflow & 301 Redirect CSV Compiler."
        )
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Path to a WooCommerce product export .csv file (repeatable)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory to write Pro exports (shopify-admin-products.csv, matrixify-products.csv, shopify-301-redirects.csv, migration-audit.json)",
    )
    parser.add_argument(
        "--weight-unit",
        choices=["kg", "g", "lb", "oz"],
        default="kg",
        help="Source WooCommerce weight unit (default: kg)",
    )
    parser.add_argument(
        "--overflow-mode",
        choices=["metafield", "compound"],
        default="metafield",
        help="How to handle WooCommerce attributes beyond Shopify's 3-option cap (default: metafield)",
    )
    parser.add_argument(
        "--no-category-redirects",
        action="store_true",
        help="Skip /product-category/... -> /collections/... 301 redirects",
    )
    parser.add_argument("--activate", help="Activate Pro license key (Stripe cs_live_...)")
    parser.add_argument("--pro", action="store_true", help="Check cached Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation counts")
    parser.add_argument("--sample-csv", action="store_true", help="Print realistic sample WooCommerce CSV")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    return parser


def _merge_csv_inputs(paths: list[str]) -> str:
    blocks: list[str] = []
    header: str | None = None
    for raw in paths:
        p = Path(raw)
        if not p.is_file():
            continue
        lines = [ln for ln in p.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
        if not lines:
            continue
        if header is None:
            header = lines[0]
            blocks.extend(lines)
        else:
            blocks.extend(lines[1:] if lines[0] == header else lines)
    return "\n".join(blocks)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.sample_csv:
        print(SAMPLE_WOO_CSV.strip())
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
        gate = require_pro_feature("shopmetashift_pro_exports", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(gate, indent=2))
        return 0

    if args.input:
        csv_text = _merge_csv_inputs(args.input)
        gate_feature = "shopmetashift_pro_exports" if args.out_dir else "shopmetashift_unlimited"
        gate = require_pro_feature(gate_feature, app_slug=APP_SLUG, cache_dir=args.cache_dir)
        pro_unlocked = bool(gate.get("allowed"))

        if args.out_dir and not pro_unlocked:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blocked_by_tier": True,
                        "free_product_limit": FREE_PRODUCT_LIMIT,
                        "error": gate.get("reason") or "Pro license required for --out-dir CSV bundle exports.",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

        result = compile_woo_to_shopify(
            csv_text,
            weight_unit=args.weight_unit,
            overflow_mode=args.overflow_mode,
            include_category_redirects=not args.no_category_redirects,
            pro_unlocked=pro_unlocked,
        )
        if not result.get("ok"):
            print(json.dumps(result, indent=2), file=sys.stderr)
            return 1

        if args.out_dir:
            out_path = Path(args.out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            (out_path / "shopify-admin-products.csv").write_text(
                render_shopify_admin_csv(result) + "\n", encoding="utf-8"
            )
            (out_path / "matrixify-products.csv").write_text(
                render_matrixify_csv(result, pro_unlocked=True) + "\n", encoding="utf-8"
            )
            (out_path / "shopify-301-redirects.csv").write_text(
                render_redirects_csv(result, pro_unlocked=True) + "\n", encoding="utf-8"
            )
            audit = {
                "summary": result["summary"],
                "metafield_schema": result["metafield_schema"],
                "warnings": result["warnings"],
            }
            (out_path / "migration-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
            result["exported_files"] = [
                str(out_path / "shopify-admin-products.csv"),
                str(out_path / "matrixify-products.csv"),
                str(out_path / "shopify-301-redirects.csv"),
                str(out_path / "migration-audit.json"),
            ]

        print(json.dumps(result, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
