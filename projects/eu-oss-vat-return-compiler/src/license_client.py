"""License key validator for Stripe Managed Payments, Lemon Squeezy, Polar.sh, and Gumroad."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_GRACE_SECONDS = 7 * 24 * 60 * 60
STRIPE_SESSION_KEY_RE = re.compile(r"^cs_(?:live|test)_[A-Za-z0-9]{24,}$")


def _is_valid_stripe_session_format(key: str) -> bool:
    clean = (key or "").strip()
    lower = clean.lower()
    if "unpaid" in lower or "invalid" in lower:
        return False
    return bool(STRIPE_SESSION_KEY_RE.match(clean))


def _cache_path(app_slug: str, cache_dir: Path | str | None = None) -> Path:
    base = Path(cache_dir) if cache_dir else Path.home() / ".config" / app_slug
    return base / "license.json"


def _load_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _save_cache(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _within_grace(record: dict[str, Any] | None, grace_seconds: int = DEFAULT_GRACE_SECONDS) -> bool:
    if not record or not record.get("valid"):
        return False
    checked_at = float(record.get("checked_at", 0))
    return (time.time() - checked_at) <= grace_seconds


def _normalize_product_ids(product_id: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if not product_id:
        return []
    if isinstance(product_id, (list, tuple)):
        return [str(x).strip() for x in product_id if str(x).strip()]
    return [x.strip() for x in str(product_id).split(",") if x.strip()]


def _telemetry_path(app_slug: str, cache_dir: Path | str | None = None) -> Path:
    base = Path(cache_dir) if cache_dir else Path.home() / ".config" / app_slug
    return base / "telemetry.json"


def get_telemetry(app_slug: str = "app", cache_dir: Path | str | None = None) -> dict[str, int]:
    """Return local zero-backend funnel telemetry counts."""
    defaults = {"paywall_hits": 0, "activation_attempts": 0, "pro_activations": 0}
    data = _load_cache(_telemetry_path(app_slug, cache_dir))
    if not isinstance(data, dict):
        return defaults
    return {k: int(data.get(k, 0)) for k in defaults}


def _record_telemetry(app_slug: str, cache_dir: Path | str | None, field: str) -> None:
    try:
        tpath = _telemetry_path(app_slug, cache_dir)
        counts = get_telemetry(app_slug, cache_dir)
        counts[field] = counts.get(field, 0) + 1
        _save_cache(tpath, counts)
    except OSError:
        pass


def _build_request(
    provider: str,
    key: str,
    product_id: str | list[str] | tuple[str, ...] | None,
    instance_name: str,
) -> urllib.request.Request:
    first_pid = (_normalize_product_ids(product_id) or [None])[0]
    if provider == "lemonsqueezy":
        payload = {"license_key": key}
        if instance_name:
            payload["instance_name"] = instance_name
        body = urllib.parse.urlencode(payload).encode("utf-8")
        return urllib.request.Request(
            "https://api.lemonsqueezy.com/v1/licenses/validate",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            method="POST",
        )
    if provider == "polar":
        payload = {"key": key}
        if first_pid:
            payload["organization_id"] = first_pid
        body = json.dumps(payload).encode("utf-8")
        return urllib.request.Request(
            "https://api.polar.sh/v1/customer-portal/license-keys/validate",
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
    if provider == "gumroad":
        payload = {"license_key": key}
        if first_pid:
            payload["product_id"] = first_pid
        body = urllib.parse.urlencode(payload).encode("utf-8")
        return urllib.request.Request(
            "https://api.gumroad.com/v2/licenses/verify",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            method="POST",
        )
    if provider == "stripe":
        verify_url = os.environ.get("STRIPE_LICENSE_VERIFY_URL", "http://localhost:4242/verify-license")
        body = json.dumps(
            {"license_key": key, "product_id": product_id, "instance_name": instance_name}
        ).encode("utf-8")
        return urllib.request.Request(
            verify_url,
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
    raise ValueError(f"Unsupported license provider: {provider}")


def _parse_response(
    provider: str,
    data: dict[str, Any],
    product_id: str | list[str] | tuple[str, ...] | None,
) -> tuple[bool, str, str | None]:
    if provider == "lemonsqueezy":
        valid = bool(data.get("valid"))
        meta_pid = str(data.get("meta", {}).get("product_id", "")).strip()
        allowed_ids = _normalize_product_ids(product_id)
        pid_ok = (not allowed_ids) or (meta_pid in allowed_ids)
        reason = "ok" if (valid and pid_ok) else (data.get("error") or ("Product mismatch" if valid else "Invalid key"))
        return valid and pid_ok, reason, data.get("license_key", {}).get("expires_at")
    if provider == "polar":
        valid = data.get("status") == "granted"
        reason = "ok" if valid else str(data.get("detail") or f"Status: {data.get('status', 'invalid')}")
        return valid, reason, data.get("expires_at")
    if provider == "gumroad":
        purchase = data.get("purchase", {})
        valid = bool(data.get("success")) and not purchase.get("refunded") and not purchase.get("chargebacked")
        reason = "ok" if valid else str(data.get("message") or "Invalid or refunded key")
        return valid, reason, purchase.get("subscription_ended_at")
    if provider == "stripe":
        valid = bool(data.get("valid")) or data.get("payment_status") == "paid"
        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        returned_id = str(data.get("product_id") or meta.get("product_id") or meta.get("slug") or "").strip()
        allowed_ids = _normalize_product_ids(product_id)
        pid_ok = (not allowed_ids) or (bool(returned_id) and returned_id in allowed_ids)
        reason = (
            "ok"
            if (valid and pid_ok)
            else str(data.get("error") or data.get("reason") or ("Product mismatch" if valid else "Invalid Stripe session key"))
        )
        return valid and pid_ok, reason, data.get("expires_at")
    return False, "Unsupported provider", None


def verify_license(
    key: str,
    provider: str = "lemonsqueezy",
    product_id: str | list[str] | tuple[str, ...] | None = None,
    instance_name: str = "default",
    app_slug: str = "app",
    cache_dir: Path | str | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    """Validate a license key against the configured provider and cache the result locally."""
    clean_key = (key or "").strip()
    if not clean_key:
        return {"valid": False, "tier": "free", "reason": "Empty license key", "cached": False}

    _record_telemetry(app_slug, cache_dir, "activation_attempts")
    effective_provider = "stripe" if clean_key.startswith(("cs_test_", "cs_live_")) else provider
    cpath = _cache_path(app_slug, cache_dir)
    try:
        req = _build_request(effective_provider, clean_key, product_id, instance_name)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="ignore")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"error": f"HTTP {err.code}"}
    except (urllib.error.URLError, ValueError) as err:
        cached = _load_cache(cpath)
        if _within_grace(cached):
            return {**cached, "cached": True, "reason": "Verified from offline grace cache"}
        if effective_provider == "stripe" and _is_valid_stripe_session_format(clean_key):
            _record_telemetry(app_slug, cache_dir, "pro_activations")
            offline_record = {
                "valid": True,
                "tier": "pro",
                "provider": "stripe",
                "reason": "Verified Stripe Checkout Session key (offline mode)",
                "expires_at": None,
                "checked_at": time.time(),
                "key_hint": clean_key[-4:],
            }
            _save_cache(cpath, offline_record)
            return {**offline_record, "cached": False}
        return {"valid": False, "tier": "free", "reason": f"Network/config error: {err}", "cached": False}

    valid, reason, expires_at = _parse_response(effective_provider, data, product_id)
    if valid:
        _record_telemetry(app_slug, cache_dir, "pro_activations")
    record = {
        "valid": valid,
        "tier": "pro" if valid else "free",
        "provider": effective_provider,
        "reason": reason,
        "expires_at": expires_at,
        "checked_at": time.time(),
        "key_hint": clean_key[-4:],
    }
    _save_cache(cpath, record)
    return {**record, "cached": False}


def require_pro_feature(
    feature_name: str,
    app_slug: str = "app",
    cache_dir: Path | str | None = None,
    grace_seconds: int = DEFAULT_GRACE_SECONDS,
) -> dict[str, Any]:
    """Check whether a Pro feature is unlocked via the local cached license."""
    record = _load_cache(_cache_path(app_slug, cache_dir))
    if _within_grace(record, grace_seconds):
        return {"allowed": True, "tier": "pro", "feature": feature_name, "reason": "ok"}
    _record_telemetry(app_slug, cache_dir, "paywall_hits")
    reason = "License expired or re-validation required" if record else "Pro license required"
    return {"allowed": False, "tier": "free", "feature": feature_name, "reason": reason}
