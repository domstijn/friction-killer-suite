#!/usr/bin/env python3
"""LemonExitBridge CLI & local Lemon Squeezy shutdown CSV migration engine."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from license_client import get_telemetry, require_pro_feature, verify_license  # noqa: E402

APP_SLUG = "lemonsqueezy-stripe-polar-migrator"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_VfygILC9yvd9U8,prod_VeW6IYwGyYJkPv"
FREE_ROW_CAP = 15
SHUTDOWN_DATE = "2027-03-31"


def _pick(row: dict[str, str], keys: tuple[str, ...], default: str = "") -> str:
    lowered = {str(k).strip().lower(): str(v).strip() for k, v in row.items() if k is not None}
    for key in keys:
        if key in lowered and lowered[key] != "":
            return lowered[key]
    return default


def _to_cents(raw: Any) -> int:
    text = str(raw if raw is not None else "").strip().replace(",", "")
    if not text:
        return 0
    return int(round(float(text) * 100))


def _from_cents(cents: int) -> float:
    return round(cents / 100.0, 2)


def iso_to_unix(date_str: str) -> int:
    """Convert ISO-8601 date or timestamp into UTC UNIX seconds."""
    text = str(date_str or "").strip()
    if not text:
        return 0
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def parse_lemonsqueezy_csv(csv_text: str) -> list[dict[str, Any]]:
    """Parse Lemon Squeezy Orders / Subscriptions / License Keys CSV export."""
    cleaned = str(csv_text or "").strip()
    if not cleaned:
        return []

    reader = csv.DictReader(io.StringIO(cleaned))
    records: list[dict[str, Any]] = []
    for raw_row in reader:
        if not any(str(v or "").strip() for v in raw_row.values()):
            continue
        email = _pick(raw_row, ("email", "customer_email", "user_email"))
        name = _pick(raw_row, ("name", "customer_name", "user_name"), email or "Customer")
        status = _pick(raw_row, ("status", "subscription_status"), "active").lower()
        pm_raw = _pick(raw_row, ("payment_method", "gateway", "card_brand"), "card").lower()
        is_paypal = "paypal" in pm_raw
        mrr_cents = max(0, _to_cents(_pick(raw_row, ("mrr", "subtotal", "amount", "price"), "0")))
        currency = _pick(raw_row, ("currency",), "USD").upper()
        variant_name = _pick(raw_row, ("variant_name", "product_name", "plan_name", "product"), "Pro Plan")
        renews_at = _pick(raw_row, ("renews_at", "ends_at", "trial_ends_at", "next_billing_at"), "")
        license_key = _pick(raw_row, ("license_key", "key"), "")
        try:
            activation_limit = int(_pick(raw_row, ("activation_limit", "instances_limit"), "3") or "3")
        except ValueError:
            activation_limit = 3

        records.append(
            {
                "customer_email": email,
                "customer_name": name,
                "status": status,
                "payment_method": "paypal" if is_paypal else (pm_raw or "card"),
                "is_paypal": is_paypal,
                "mrr_cents": mrr_cents,
                "currency": currency,
                "product_variant": variant_name,
                "renews_at": renews_at,
                "trial_end_unix": iso_to_unix(renews_at),
                "license_key": license_key,
                "activation_limit": activation_limit,
            }
        )
    return records


def build_migration_pack(
    csv_text: str,
    *,
    is_pro: bool = False,
    include_paypal_cohort: bool = False,
    include_license_bundle: bool = False,
) -> dict[str, Any]:
    """Audit Card vs. PayPal MRR and export Stripe/Polar CSVs and Legacy Key JSON."""
    if not is_pro and (include_paypal_cohort or include_license_bundle):
        return {
            "ok": False,
            "blocked_by_tier": True,
            "reason": (
                "PayPal prorated trial_end cohorts and Legacy License Key JSON/Worker bundles "
                "require a Pro license key."
            ),
        }

    records = parse_lemonsqueezy_csv(csv_text)
    if not records:
        return {"ok": False, "error": "CSV must contain headers and at least one customer/order row."}

    active_statuses = {"active", "on_trial", "past_due", "paused"}
    active_subscriptions = 0
    card_mrr_cents = 0
    paypal_mrr_cents = 0
    paypal_count = 0
    license_keys_found = 0

    for rec in records:
        if rec["license_key"]:
            license_keys_found += 1
        if rec["status"] in active_statuses:
            active_subscriptions += 1
            if rec["is_paypal"]:
                paypal_count += 1
                paypal_mrr_cents += rec["mrr_cents"]
            else:
                card_mrr_cents += rec["mrr_cents"]

    selected = records if is_pro else records[:FREE_ROW_CAP]
    truncated_rows = max(0, len(records) - len(selected))

    main_buf = io.StringIO()
    main_writer = csv.writer(main_buf, lineterminator="\n")
    main_writer.writerow(
        [
            "customer_email",
            "customer_name",
            "product_variant",
            "status",
            "payment_method",
            "mrr",
            "currency",
            "renews_at",
            "trial_end_unix",
            "migration_track",
        ]
    )
    for rec in selected:
        track = "paypal_manual_reauth" if rec["is_paypal"] else "stripe_card_transfer"
        main_writer.writerow(
            [
                rec["customer_email"],
                rec["customer_name"],
                rec["product_variant"],
                rec["status"],
                rec["payment_method"],
                f"{_from_cents(rec['mrr_cents']):.2f}",
                rec["currency"],
                rec["renews_at"],
                rec["trial_end_unix"],
                track,
            ]
        )

    paypal_cohort_csv = None
    if is_pro and include_paypal_cohort:
        pp_buf = io.StringIO()
        pp_writer = csv.writer(pp_buf, lineterminator="\n")
        pp_writer.writerow(
            [
                "customer_email",
                "customer_name",
                "product_variant",
                "mrr",
                "renews_at",
                "trial_end_unix",
                "action_required",
            ]
        )
        for rec in selected:
            if rec["is_paypal"] and rec["status"] in active_statuses:
                pp_writer.writerow(
                    [
                        rec["customer_email"],
                        rec["customer_name"],
                        rec["product_variant"],
                        f"{_from_cents(rec['mrr_cents']):.2f}",
                        rec["renews_at"],
                        rec["trial_end_unix"],
                        f"Email PayPal re-auth link before {SHUTDOWN_DATE}",
                    ]
                )
        paypal_cohort_csv = pp_buf.getvalue().rstrip("\n")

    license_bundle_json = None
    if is_pro and include_license_bundle:
        keys_map: dict[str, Any] = {}
        for rec in selected:
            key = rec["license_key"]
            if not key:
                continue
            keys_map[key] = {
                "valid": rec["status"] in {"active", "on_trial", "paid", "unused"},
                "customer_email": rec["customer_email"],
                "product_variant": rec["product_variant"],
                "activation_limit": rec["activation_limit"],
                "expires_at": rec["renews_at"] or None,
            }
        license_bundle_json = json.dumps(
            {
                "schema": "lemon.legacy_keys.v1",
                "shutdown_deadline": SHUTDOWN_DATE,
                "total_keys": len(keys_map),
                "keys": keys_map,
            },
            indent=2,
        )

    return {
        "ok": True,
        "is_pro": is_pro,
        "shutdown_deadline": SHUTDOWN_DATE,
        "total_rows": len(records),
        "processed_rows": len(selected),
        "truncated_rows": truncated_rows,
        "active_subscriptions": active_subscriptions,
        "card_mrr": _from_cents(card_mrr_cents),
        "paypal_mrr_at_risk": _from_cents(paypal_mrr_cents),
        "total_mrr": _from_cents(card_mrr_cents + paypal_mrr_cents),
        "paypal_count": paypal_count,
        "license_keys_found": license_keys_found,
        "stripe_polar_csv": main_buf.getvalue().rstrip("\n"),
        "paypal_cohort_csv": paypal_cohort_csv,
        "license_bundle_json": license_bundle_json,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LemonExitBridge: Audit Lemon Squeezy CSVs, split PayPal cohorts & bridge license keys before shutdown."
    )
    parser.add_argument("--activate", help="Activate Stripe Pro license key (cs_live_...)")
    parser.add_argument("--pro", action="store_true", help="Check current Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation telemetry counts")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    parser.add_argument("--csv", help="Path to exported Lemon Squeezy Customers/Subscriptions CSV")
    parser.add_argument("--paypal-cohort", action="store_true", help="Export PayPal prorated re-auth CSV (Pro)")
    parser.add_argument("--license-bundle", action="store_true", help="Export Legacy License Key JSON bundle (Pro)")
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
        res = require_pro_feature("paypal_and_legacy_keys", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(res, indent=2))
        return 0

    if args.csv:
        csv_text = Path(args.csv).read_text(encoding="utf-8")
        gate_name = "paypal_and_legacy_keys" if (args.paypal_cohort or args.license_bundle) else "unlimited_rows"
        gate = require_pro_feature(gate_name, app_slug=APP_SLUG, cache_dir=args.cache_dir)
        out = build_migration_pack(
            csv_text,
            is_pro=bool(gate.get("allowed")),
            include_paypal_cohort=bool(args.paypal_cohort),
            include_license_bundle=bool(args.license_bundle),
        )
        if not out.get("ok"):
            print(json.dumps(out, indent=2), file=sys.stderr)
            return 1
        print(json.dumps(out, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
