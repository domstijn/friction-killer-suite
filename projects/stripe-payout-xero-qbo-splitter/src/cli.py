#!/usr/bin/env python3
"""StripePayoutBridge CLI & double-entry payout CSV reconciliation engine."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402

APP_SLUG = "stripe-payout-xero-qbo-splitter"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_VfyImk6C1cdbcU,prod_VeW6IYwGyYJkPv"
FREE_BATCH_CAP = 1
FREE_TX_CAP = 25

ACCOUNT_MAP = {
    "clearing": ("120", "Bank / Stripe Clearing Settlement", "NONE"),
    "sales": ("200", "Sales Revenue (Net)", "NONE"),
    "refunds": ("205", "Refunds & Returns", "NONE"),
    "disputes": ("206", "Chargebacks & Disputes", "NONE"),
    "fees": ("404", "Stripe Processing Fees", "NONE"),
    "fx_fees": ("405", "FX Conversion Fees", "NONE"),
    "tax": ("820", "Sales Tax / VAT Payable", "NONE"),
}

DATEV_ACCOUNTS = {
    "clearing": "1200",
    "sales": "8400",
    "refunds": "8400",
    "disputes": "4970",
    "fees": "4970",
    "fx_fees": "6880",
    "tax": "1776",
    "transit": "1360",
}


def _to_cents(raw: Any) -> int:
    text = str(raw if raw is not None else "").strip().replace(",", "")
    if not text:
        return 0
    return int(round(float(text) * 100))


def _from_cents(cents: int) -> float:
    return round(cents / 100.0, 2)


def _pick(row: dict[str, str], keys: tuple[str, ...], default: str = "") -> str:
    lowered = {str(k).strip().lower(): str(v).strip() for k, v in row.items() if k is not None}
    for key in keys:
        if key in lowered and lowered[key] != "":
            return lowered[key]
    return default


def parse_payout_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse Stripe or PayPal itemized payout CSV rows into normalized records."""
    cleaned = str(csv_text or "").strip()
    if not cleaned:
        return []

    reader = csv.DictReader(io.StringIO(cleaned))
    records: list[dict[str, Any]] = []
    for idx, raw_row in enumerate(reader, 1):
        if not any(str(v or "").strip() for v in raw_row.values()):
            continue
        payout_id = _pick(
            raw_row,
            ("payout_id", "automatic_payout_id", "payout", "batch_id", "settlement_id"),
            "po_default_batch",
        )
        payout_date = _pick(
            raw_row,
            ("payout_date", "automatic_payout_effective_at", "date", "created"),
            "2026-11-01",
        )[:10]
        tx_type = _pick(
            raw_row,
            ("type", "reporting_category", "transaction_type"),
            "charge",
        ).lower()
        gross_cents = _to_cents(_pick(raw_row, ("gross", "amount", "gross_amount"), "0"))
        fee_raw_cents = _to_cents(_pick(raw_row, ("fee", "processing_fee", "fees"), "0"))
        fx_raw_cents = _to_cents(_pick(raw_row, ("fx_fee", "fx", "currency_conversion_fee"), "0"))
        tax_cents = abs(_to_cents(_pick(raw_row, ("tax", "vat", "tax_amount", "sales_tax"), "0")))
        net_raw = _pick(raw_row, ("net", "net_amount"), "")
        net_cents = _to_cents(net_raw) if net_raw != "" else (gross_cents - abs(fee_raw_cents) - abs(fx_raw_cents))
        currency = _pick(raw_row, ("currency",), "EUR").upper()
        tax_rate = _pick(raw_row, ("tax_rate", "vat_rate"), "21%")
        desc = _pick(raw_row, ("description", "memo"), f"Row {idx}")

        records.append(
            {
                "payout_id": payout_id,
                "payout_date": payout_date,
                "type": tx_type,
                "gross_cents": gross_cents,
                "fee_cents": abs(fee_raw_cents),
                "fx_fee_cents": abs(fx_raw_cents),
                "tax_cents": tax_cents,
                "net_cents": net_cents,
                "currency": currency,
                "tax_rate": tax_rate,
                "description": desc,
            }
        )
    return records


def _build_batch_journal(batch_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    payout_date = rows[0]["payout_date"]
    currency = rows[0]["currency"]

    gross_sales_cents = 0
    tax_collected_cents = 0
    refunds_net_cents = 0
    refunded_tax_cents = 0
    disputes_gross_cents = 0
    processing_fees_cents = 0
    fx_fees_cents = 0
    reported_net_cents = 0

    for row in rows:
        tx_type = row["type"]
        processing_fees_cents += row["fee_cents"]
        fx_fees_cents += row["fx_fee_cents"]
        reported_net_cents += row["net_cents"]

        if "refund" in tx_type or (tx_type in ("charge", "payment", "sale") and row["gross_cents"] < 0):
            abs_gross = abs(row["gross_cents"])
            ref_tax = min(max(0, row["tax_cents"]), abs_gross)
            refunded_tax_cents += ref_tax
            refunds_net_cents += abs_gross - ref_tax
            tax_collected_cents -= ref_tax
        elif "dispute" in tx_type or "chargeback" in tx_type:
            disputes_gross_cents += abs(row["gross_cents"])
        else:
            gross_sales_cents += max(0, row["gross_cents"])
            tax_collected_cents += min(max(0, row["tax_cents"]), max(0, row["gross_cents"]))

    net_sales_cents = gross_sales_cents - (tax_collected_cents + refunded_tax_cents)
    expected_net_cents = (
        gross_sales_cents
        - refunds_net_cents
        - refunded_tax_cents
        - disputes_gross_cents
        - processing_fees_cents
        - fx_fees_cents
    )
    drift_cents = expected_net_cents - reported_net_cents

    lines: list[dict[str, Any]] = []

    def add_line(key: str, side: str, cents: int, memo: str) -> None:
        if cents <= 0:
            return
        code, name, tax_type = ACCOUNT_MAP[key]
        lines.append(
            {
                "key": key,
                "account_code": code,
                "account_name": name,
                "tax_type": tax_type,
                "side": side,
                "cents": cents,
                "amount": _from_cents(cents),
                "signed_xero": _from_cents(cents if side == "debit" else -cents),
                "description": memo,
            }
        )

    add_line("sales", "credit", net_sales_cents, f"Stripe gross sales net of tax ({batch_id})")
    if tax_collected_cents >= 0:
        add_line("tax", "credit", tax_collected_cents, f"VAT/Sales tax collected ({batch_id})")
    else:
        add_line("tax", "debit", abs(tax_collected_cents), f"VAT/Sales tax refunded ({batch_id})")
    add_line("refunds", "debit", refunds_net_cents, f"Customer refunds net of tax ({batch_id})")
    add_line("disputes", "debit", disputes_gross_cents, f"Chargebacks & disputes ({batch_id})")
    add_line("fees", "debit", processing_fees_cents, f"Processing fees ({batch_id})")
    add_line("fx_fees", "debit", fx_fees_cents, f"Multi-currency FX fees ({batch_id})")
    if expected_net_cents >= 0:
        add_line("clearing", "debit", expected_net_cents, f"Net bank payout deposit ({batch_id})")
    else:
        add_line("clearing", "credit", abs(expected_net_cents), f"Negative payout debit ({batch_id})")

    total_debits_cents = sum(line["cents"] for line in lines if line["side"] == "debit")
    total_credits_cents = sum(line["cents"] for line in lines if line["side"] == "credit")
    assert total_debits_cents == total_credits_cents, (
        f"Unbalanced journal for {batch_id}: debits={total_debits_cents}, credits={total_credits_cents}"
    )

    return {
        "payout_id": batch_id,
        "payout_date": payout_date,
        "currency": currency,
        "transaction_count": len(rows),
        "gross_sales": _from_cents(gross_sales_cents),
        "tax_collected": _from_cents(tax_collected_cents),
        "net_sales": _from_cents(net_sales_cents),
        "refunds_gross": _from_cents(refunds_net_cents),
        "disputes_gross": _from_cents(disputes_gross_cents),
        "processing_fees": _from_cents(processing_fees_cents),
        "fx_fees": _from_cents(fx_fees_cents),
        "expected_net": _from_cents(expected_net_cents),
        "reported_net": _from_cents(reported_net_cents),
        "drift": _from_cents(drift_cents),
        "total_debits": _from_cents(total_debits_cents),
        "total_credits": _from_cents(total_credits_cents),
        "lines": lines,
    }


def _render_xero_csv(batches: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["*Narration", "*Date", "Description", "*AccountCode", "*TaxType", "*Amount"])
    for b in batches:
        narration = f"Stripe Payout Clearing {b['payout_id']}"
        for line in b["lines"]:
            writer.writerow(
                [
                    narration,
                    b["payout_date"],
                    line["description"],
                    line["account_code"],
                    line["tax_type"],
                    f"{line['signed_xero']:.2f}",
                ]
            )
    return buf.getvalue().rstrip("\n")


def _render_qbo_csv(batches: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["JournalNo", "JournalDate", "AccountName", "Debits", "Credits", "Memo"])
    for idx, b in enumerate(batches, 1):
        jno = f"SPB-{idx:03d}"
        for line in b["lines"]:
            writer.writerow(
                [
                    jno,
                    b["payout_date"],
                    line["account_name"],
                    f"{line['amount']:.2f}" if line["side"] == "debit" else "",
                    f"{line['amount']:.2f}" if line["side"] == "credit" else "",
                    line["description"],
                ]
            )
    return buf.getvalue().rstrip("\n")


def _render_datev_csv(batches: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\n")
    writer.writerow(
        [
            "Umsatz",
            "Soll/Haben-Kennzeichen",
            "Konto",
            "Gegenkonto",
            "BU-Schluessel",
            "Belegdatum",
            "Belegfeld 1",
            "Buchungstext",
        ]
    )
    for b in batches:
        parts = b["payout_date"].split("-")
        belegdatum = f"{parts[2]}{parts[1]}" if len(parts) == 3 else "0111"
        for line in b["lines"]:
            sh = "S" if line["side"] == "debit" else "H"
            konto = DATEV_ACCOUNTS.get(line["key"], "1360")
            gegenkonto = DATEV_ACCOUNTS["transit"]
            bu = "9" if line["key"] == "tax" else ""
            umsatz = f"{line['amount']:.2f}".replace(".", ",")
            writer.writerow(
                [
                    umsatz,
                    sh,
                    konto,
                    gegenkonto,
                    bu,
                    belegdatum,
                    b["payout_id"][:12],
                    line["description"],
                ]
            )
    return buf.getvalue().rstrip("\n")


def reconcile_payout_batches(
    csv_text: str,
    *,
    is_pro: bool = False,
    export_format: str = "xero",
) -> dict[str, Any]:
    """Reconcile itemized payout CSV into balanced double-entry journals."""
    fmt = (export_format or "xero").strip().lower()
    if fmt not in ("xero", "qbo", "datev", "all"):
        return {"ok": False, "error": f"Unsupported format '{export_format}'."}

    if not is_pro and fmt in ("qbo", "datev", "all"):
        return {
            "ok": False,
            "blocked_by_tier": True,
            "reason": "QuickBooks and DATEV Buchungsstapel exports require a Pro license key.",
        }

    records = parse_payout_csv(csv_text)
    if not records:
        return {"ok": False, "error": "CSV must contain headers and at least one payout transaction row."}

    grouped: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        grouped.setdefault(rec["payout_id"], []).append(rec)

    all_batch_ids = list(grouped.keys())
    selected_ids = all_batch_ids if is_pro else all_batch_ids[:FREE_BATCH_CAP]
    truncated_batches = max(0, len(all_batch_ids) - len(selected_ids))

    processed_batches: list[dict[str, Any]] = []
    truncated_transactions = 0
    for bid in selected_ids:
        b_rows = grouped[bid]
        if not is_pro and len(b_rows) > FREE_TX_CAP:
            truncated_transactions += len(b_rows) - FREE_TX_CAP
            b_rows = b_rows[:FREE_TX_CAP]
        processed_batches.append(_build_batch_journal(bid, b_rows))

    total_debits = round(sum(b["total_debits"] for b in processed_batches), 2)
    total_credits = round(sum(b["total_credits"] for b in processed_batches), 2)
    xero_csv = _render_xero_csv(processed_batches)
    qbo_csv = _render_qbo_csv(processed_batches) if is_pro else None
    datev_csv = _render_datev_csv(processed_batches) if is_pro else None

    return {
        "ok": True,
        "is_pro": is_pro,
        "format": fmt,
        "total_batches": len(all_batch_ids),
        "processed_batches": len(processed_batches),
        "truncated_batches": truncated_batches,
        "truncated_transactions": truncated_transactions,
        "total_debits": total_debits,
        "total_credits": total_credits,
        "balanced": total_debits == total_credits,
        "batches": processed_batches,
        "xero_csv": xero_csv,
        "qbo_csv": qbo_csv,
        "datev_csv": datev_csv,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="StripePayoutBridge: Reconcile Stripe/PayPal payout CSVs into balanced Xero, QuickBooks & DATEV journals."
    )
    parser.add_argument("--activate", help="Activate Stripe Pro license key (cs_live_...)")
    parser.add_argument("--pro", action="store_true", help="Check current Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation telemetry counts")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    parser.add_argument("--csv", help="Path to itemized Stripe/PayPal payout CSV")
    parser.add_argument(
        "--format",
        choices=["xero", "qbo", "datev", "all"],
        default="xero",
        help="Target accounting export format",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
        res = require_pro_feature("qbo_datev_export", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(res, indent=2))
        return 0

    if args.csv:
        csv_text = Path(args.csv).read_text(encoding="utf-8")
        if args.format in ("qbo", "datev", "all"):
            gate = require_pro_feature("qbo_datev_export", app_slug=APP_SLUG, cache_dir=args.cache_dir)
            is_pro = bool(gate.get("allowed"))
        else:
            gate = require_pro_feature("unlimited_batches", app_slug=APP_SLUG, cache_dir=args.cache_dir)
            is_pro = bool(gate.get("allowed"))
        out = reconcile_payout_batches(csv_text, is_pro=is_pro, export_format=args.format)
        if not out.get("ok"):
            print(json.dumps(out, indent=2), file=sys.stderr)
            return 1
        if args.format == "qbo":
            print(out["qbo_csv"])
        elif args.format == "datev":
            print(out["datev_csv"])
        elif args.format == "all":
            print(json.dumps(out, indent=2))
        else:
            print(out["xero_csv"])
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
