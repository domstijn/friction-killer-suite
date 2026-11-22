#!/usr/bin/env python3
"""AmzSettlementBridge CLI: Compile Amazon Flat-File V2 (.txt/.tsv) settlements into Xero, QBO & DATEV journals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addon import (  # noqa: E402
    FREE_ROW_LIMIT,
    SAMPLE_AMAZON_V2_TSV,
    compile_settlement_journals,
    parse_amazon_settlement,
    render_datev_extf_csv,
    render_qbo_journal_csv,
    render_xero_journal_csv,
)
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402

APP_SLUG = "amazon-settlement-xero-qbo-splitter"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_Vg2d5RyhHCcgKb,prod_VeW6IYwGyYJkPv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AmzSettlementBridge: Amazon Flat-File V2 (.txt/.tsv) to Xero, QuickBooks & DATEV clearing journals."
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Path to Amazon Flat-File V2 .txt/.tsv/.csv settlement export (repeatable for multi-settlement batching)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory to write Pro journal CSVs (xero-amazon-journals.csv, qbo-amazon-journals.csv, datev-amazon-extf.csv)",
    )
    parser.add_argument("--activate", help="Activate Pro license key (Stripe cs_live_...)")
    parser.add_argument("--pro", action="store_true", help="Check cached Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation counts")
    parser.add_argument("--sample", action="store_true", help="Print sample 2-settlement Flat-File V2 TSV")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.sample:
        print(SAMPLE_AMAZON_V2_TSV)
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
        gate = require_pro_feature("amazon_journal_exports", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(gate, indent=2))
        return 0

    if args.input:
        all_rows: list[dict[str, Any]] = []
        for path_str in args.input:
            raw_text = Path(path_str).read_text(encoding="utf-8")
            all_rows.extend(parse_amazon_settlement(raw_text))

        gate_feature = "amazon_journal_exports" if args.out_dir else "unlimited_settlements"
        gate = require_pro_feature(gate_feature, app_slug=APP_SLUG, cache_dir=args.cache_dir)
        pro_unlocked = bool(gate.get("allowed"))

        if args.out_dir and not pro_unlocked:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blocked_by_tier": True,
                        "free_row_limit": FREE_ROW_LIMIT,
                        "error": gate.get("reason") or "Pro license required for --out-dir journal exports.",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

        report = compile_settlement_journals(all_rows, pro_unlocked=pro_unlocked)
        if not report.get("ok"):
            print(json.dumps(report, indent=2), file=sys.stderr)
            return 1

        if args.out_dir:
            out_path = Path(args.out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            (out_path / "xero-amazon-journals.csv").write_text(render_xero_journal_csv(report) + "\n", encoding="utf-8")
            (out_path / "qbo-amazon-journals.csv").write_text(render_qbo_journal_csv(report) + "\n", encoding="utf-8")
            (out_path / "datev-amazon-extf.csv").write_text(render_datev_extf_csv(report) + "\n", encoding="utf-8")
            report["exported_files"] = [
                str(out_path / "xero-amazon-journals.csv"),
                str(out_path / "qbo-amazon-journals.csv"),
                str(out_path / "datev-amazon-extf.csv"),
            ]

        print(json.dumps(report, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
