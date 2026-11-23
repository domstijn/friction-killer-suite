#!/usr/bin/env python3
"""BankFeedBridge CLI: Convert ISO 20022 CAMT.053 XML & MT940 -> QBO, OFX, Xero CSV & DATEV."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addon import (  # noqa: E402
    APP_SLUG,
    DEFAULT_PRODUCT_ID,
    FREE_TX_LIMIT,
    PROVIDER,
    SAMPLE_CAMT053_XML,
    SAMPLE_MT940,
    compile_bank_statements,
    render_datev_bank_csv,
    render_qbo_web_connect,
    render_xero_csv,
    render_xero_ofx,
)
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402

SUPPORTED_EXTS = {".xml", ".sta", ".mt940", ".940", ".txt"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "BankFeedBridge: Zero-Dependency ISO 20022 CAMT.053 XML & MT940 to "
            "QuickBooks (.QBO), Xero (.OFX/CSV) & DATEV Converter."
        )
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Path to a CAMT.053 .xml / MT940 .sta/.mt940/.txt file or folder (repeatable)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory to write Pro exports (.qbo, .ofx, Xero CSV, DATEV CSV, reconciliation JSON)",
    )
    parser.add_argument("--intu-bid", default="3000", help="QuickBooks Intuit Bank ID (<INTU.BID>, default: 3000)")
    parser.add_argument(
        "--account-type",
        choices=["CHECKING", "SAVINGS", "CREDITLINE"],
        default="CHECKING",
        help="OFX/QBO bank account type (default: CHECKING)",
    )
    parser.add_argument("--datev-account", default="1200", help="DATEV SKR03/04 bank account number (default: 1200)")
    parser.add_argument("--activate", help="Activate Pro license key (Stripe cs_live_...)")
    parser.add_argument("--pro", action="store_true", help="Check cached Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation counts")
    parser.add_argument("--sample-camt053", action="store_true", help="Print sample ISO 20022 CAMT.053 XML")
    parser.add_argument("--sample-mt940", action="store_true", help="Print sample SWIFT MT940 statement")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    return parser


def _collect_inputs(paths: list[str]) -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in sorted(p.iterdir()):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                    docs.append((f.name, f.read_text(encoding="utf-8-sig", errors="replace")))
        elif p.is_file():
            docs.append((p.name, p.read_text(encoding="utf-8-sig", errors="replace")))
    return docs


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.sample_camt053:
        print(SAMPLE_CAMT053_XML.strip())
        return 0

    if args.sample_mt940:
        print(SAMPLE_MT940.strip())
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
        gate = require_pro_feature("bankfeed_pro_exports", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(gate, indent=2))
        return 0

    if args.input:
        docs = _collect_inputs(args.input)
        gate_feature = "bankfeed_pro_exports" if args.out_dir else "bankfeed_unlimited"
        gate = require_pro_feature(gate_feature, app_slug=APP_SLUG, cache_dir=args.cache_dir)
        pro_unlocked = bool(gate.get("allowed"))

        if args.out_dir and not pro_unlocked:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blocked_by_tier": True,
                        "free_tx_limit": FREE_TX_LIMIT,
                        "error": gate.get("reason") or "Pro license required for --out-dir statement exports.",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

        result = compile_bank_statements(
            docs,
            intu_bid=args.intu_bid,
            account_type=args.account_type,
            datev_bank_account=args.datev_account,
            pro_unlocked=pro_unlocked,
        )
        if not result.get("ok"):
            print(json.dumps(result, indent=2), file=sys.stderr)
            return 1

        if args.out_dir:
            out_path = Path(args.out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            (out_path / "quickbooks-webconnect.qbo").write_text(
                render_qbo_web_connect(
                    result,
                    intu_bid=args.intu_bid,
                    account_type=args.account_type,
                    pro_unlocked=True,
                )
                + "\n",
                encoding="utf-8",
            )
            (out_path / "xero-bank.ofx").write_text(
                render_xero_ofx(result, account_type=args.account_type, pro_unlocked=True) + "\n",
                encoding="utf-8",
            )
            (out_path / "xero-bank-statement.csv").write_text(
                render_xero_csv(result) + "\n", encoding="utf-8"
            )
            (out_path / "datev-bank-buchungsstapel.csv").write_text(
                render_datev_bank_csv(result, bank_account=args.datev_account, pro_unlocked=True) + "\n",
                encoding="utf-8",
            )
            audit = {
                "summary": result["summary"],
                "statements": result["statements"],
                "warnings": result["warnings"],
            }
            (out_path / "reconciliation-audit.json").write_text(
                json.dumps(audit, indent=2) + "\n", encoding="utf-8"
            )
            result["exported_files"] = [
                str(out_path / "quickbooks-webconnect.qbo"),
                str(out_path / "xero-bank.ofx"),
                str(out_path / "xero-bank-statement.csv"),
                str(out_path / "datev-bank-buchungsstapel.csv"),
                str(out_path / "reconciliation-audit.json"),
            ]

        print(json.dumps(result, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
