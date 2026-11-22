#!/usr/bin/env python3
"""EInvoiceLocal CLI: Validate XRechnung/ZUGFeRD/Peppol XMLs & export DATEV EXTF, Xero, QBO CSVs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addon import (  # noqa: E402
    FREE_INVOICE_LIMIT,
    SAMPLE_CII_ZUGFERD_XML,
    SAMPLE_UBL_PEPPOL_XML,
    compile_einvoice_batch,
    render_datev_extf_csv,
    render_qbo_bills_csv,
    render_xero_bills_csv,
)
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402

APP_SLUG = "e-invoice-xml-batch-converter"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_Vg3C753ZbsDlQk,prod_VeW6IYwGyYJkPv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="EInvoiceLocal: XRechnung / ZUGFeRD / Peppol UBL & CII XML Validator + DATEV/Xero/QBO Converter."
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Path to an .xml invoice or directory of *.xml invoices (repeatable)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Directory to write Pro CSV exports (datev-extf-buchungsstapel.csv, xero-bills.csv, qbo-bills.csv)",
    )
    parser.add_argument("--activate", help="Activate Pro license key (Stripe cs_live_...)")
    parser.add_argument("--pro", action="store_true", help="Check cached Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation counts")
    parser.add_argument("--sample-ubl", action="store_true", help="Print sample EN 16931 UBL 2.1 XRechnung XML")
    parser.add_argument("--sample-cii", action="store_true", help="Print sample EN 16931 UN/CEFACT CII ZUGFeRD XML")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    return parser


def _collect_xml_docs(inputs: list[str]) -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    for raw_path in inputs:
        p = Path(raw_path)
        if p.is_dir():
            for xml_file in sorted(p.glob("*.xml")):
                docs.append((xml_file.name, xml_file.read_text(encoding="utf-8")))
        elif p.is_file():
            docs.append((p.name, p.read_text(encoding="utf-8")))
    return docs


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.sample_ubl:
        print(SAMPLE_UBL_PEPPOL_XML.strip())
        return 0

    if args.sample_cii:
        print(SAMPLE_CII_ZUGFERD_XML.strip())
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
        gate = require_pro_feature("einvoice_batch_exports", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(gate, indent=2))
        return 0

    if args.input:
        docs = _collect_xml_docs(args.input)
        gate_feature = "einvoice_batch_exports" if args.out_dir else "unlimited_xml_batches"
        gate = require_pro_feature(gate_feature, app_slug=APP_SLUG, cache_dir=args.cache_dir)
        pro_unlocked = bool(gate.get("allowed"))

        if args.out_dir and not pro_unlocked:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "blocked_by_tier": True,
                        "free_invoice_limit": FREE_INVOICE_LIMIT,
                        "error": gate.get("reason") or "Pro license required for --out-dir batch exports.",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

        batch = compile_einvoice_batch(docs, pro_unlocked=pro_unlocked)
        if not batch.get("ok"):
            print(json.dumps(batch, indent=2), file=sys.stderr)
            return 1

        if args.out_dir:
            out_path = Path(args.out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            (out_path / "datev-extf-buchungsstapel.csv").write_text(
                render_datev_extf_csv(batch) + "\n", encoding="utf-8"
            )
            (out_path / "xero-bills.csv").write_text(render_xero_bills_csv(batch) + "\n", encoding="utf-8")
            (out_path / "qbo-bills.csv").write_text(render_qbo_bills_csv(batch) + "\n", encoding="utf-8")
            batch["exported_files"] = [
                str(out_path / "datev-extf-buchungsstapel.csv"),
                str(out_path / "xero-bills.csv"),
                str(out_path / "qbo-bills.csv"),
            ]

        print(json.dumps(batch, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
