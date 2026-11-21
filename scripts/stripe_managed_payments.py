#!/usr/bin/env python3
"""Stripe Managed Payments (2025-03-31.basil) provisioning, session creator, and license server."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG_PATH = REPO_ROOT / "pipeline" / "stripe_catalog.json"
DEFAULT_ORDERS_PATH = REPO_ROOT / "pipeline" / "stripe_orders.jsonl"
DEFAULT_DOCS_DIR = REPO_ROOT / "docs"
CONFIGURE_CHECKOUT_SCRIPT = REPO_ROOT / "scripts" / "configure_checkout.py"

STRIPE_API_BASE = "https://api.stripe.com/v1"
STRIPE_API_VERSION = "2025-03-31.basil"
DEFAULT_TAX_CODE = "txcd_10103000"
DEFAULT_SITE_URL = "https://domstijn.github.io/friction-killer-suite"

DEFAULT_CATALOG_ITEMS = [
    {
        "slug": "notion-linear-prd-sync",
        "name": "LinearBridge Pro",
        "description": "1-click Notion PRD to Linear Parent Epic & Sub-Issues Chrome extension (Pro License).",
        "unit_amount": 2900,
        "currency": "eur",
        "mode": "payment",
    },
    {
        "slug": "notion-clean-md-exporter",
        "name": "NotionGitExport Pro",
        "description": "Lossless Notion Markdown cleaner with YAML frontmatter and asset localization CLI (Pro License).",
        "unit_amount": 2400,
        "currency": "eur",
        "mode": "payment",
    },
    {
        "slug": "vscode-workspace-profile-config",
        "name": "ExtProfileLock Pro",
        "description": "Declarative VS Code workspace extension locks and .env interpolation (Pro License).",
        "unit_amount": 1900,
        "currency": "eur",
        "mode": "payment",
    },
    {
        "slug": "claude-profile-switcher",
        "name": "ClaudeProfileSwitch Pro",
        "description": "Multi-account & MCP profile switcher with .claude-profile env injection and 5-hour JSONL quota guard (Pro License).",
        "unit_amount": 2400,
        "currency": "eur",
        "mode": "payment",
    },
    {
        "slug": "docker-volume-compose-tool",
        "name": "DockerVolumeForge Pro",
        "description": "Atomic Docker volume rename/clone, Compose v3 extends flattener & multi-tag batch pusher (Pro License).",
        "unit_amount": 2400,
        "currency": "eur",
        "mode": "payment",
    },
    {
        "slug": "notion-guest-mcp-bridge",
        "name": "NotionGuestBridge Pro",
        "description": "1-click client Notion Guest page & database extractor to Claude/Cursor Markdown and .mcp-context.json packs with PII redaction (Pro License).",
        "unit_amount": 2900,
        "currency": "eur",
        "mode": "payment",
    },
    {
        "slug": "all-access-bundle",
        "name": "All-Access Friction-Killer Bundle",
        "description": "Pro licenses for LinearBridge, NotionGitExport, and ExtProfileLock.",
        "unit_amount": 4900,
        "currency": "eur",
        "mode": "payment",
    },
]


def load_dotenv(env_path: Path = REPO_ROOT / ".env") -> None:
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, val)


def stripe_request(
    method: str,
    path: str,
    api_key: str,
    form_data: dict[str, Any] | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    url = f"{STRIPE_API_BASE}{path}"
    encoded = urllib.parse.urlencode(form_data).encode("utf-8") if form_data is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Stripe-Version": STRIPE_API_VERSION,
        "Accept": "application/json",
    }
    if encoded is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=encoded, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Stripe API error ({err.code}) on {path}: {detail}") from err


def resolve_api_key(cli_key: str | None) -> str:
    key = (cli_key or os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        raise ValueError("Missing Stripe secret key. Pass --api-key or set STRIPE_SECRET_KEY.")
    return key


def load_catalog(catalog_path: Path) -> dict[str, Any]:
    if not catalog_path.is_file():
        return {"api_version": STRIPE_API_VERSION, "products": {}}
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def save_catalog(catalog_path: Path, catalog: dict[str, Any]) -> None:
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


def create_checkout_session_with_fallback(
    api_key: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    try:
        return stripe_request("POST", "/checkout/sessions", api_key, params)
    except RuntimeError as err:
        if "managed_payments" not in str(err).lower():
            raise
        fallback_params = {k: v for k, v in params.items() if not k.startswith("managed_payments")}
        session = stripe_request("POST", "/checkout/sessions", api_key, fallback_params)
        session["managed_payments_fallback"] = True
        return session


def cmd_provision(args: argparse.Namespace) -> int:
    catalog_path = Path(args.catalog_path)
    clean_site = args.site_url.rstrip("/")
    catalog: dict[str, Any] = {
        "api_version": STRIPE_API_VERSION,
        "tax_code": args.tax_code,
        "site_url": clean_site,
        "server_url": args.server_url.rstrip("/"),
        "dry_run": bool(args.dry_run),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "products": {},
    }

    if args.dry_run:
        for idx, item in enumerate(DEFAULT_CATALOG_ITEMS, 1):
            slug = item["slug"]
            catalog["products"][slug] = {
                **item,
                "product_id": f"prod_dryrun_{idx}_{slug.replace('-', '_')}",
                "price_id": f"price_dryrun_{idx}_{slug.replace('-', '_')}",
                "payment_link_id": f"plink_dryrun_{idx}",
                "payment_link_url": f"https://buy.stripe.com/test_dryrun_{idx}",
                "checkout_endpoint": f"{catalog['server_url']}/create-checkout-session?slug={slug}",
            }
        save_catalog(catalog_path, catalog)
        print(f"[DRY-RUN] Wrote {len(DEFAULT_CATALOG_ITEMS)} EUR Stripe products -> {catalog_path}")
        return 0

    api_key = resolve_api_key(args.api_key)
    existing_prods = stripe_request("GET", "/products?active=true&limit=100", api_key).get("data", [])
    existing_links = stripe_request("GET", "/payment_links?active=true&limit=100", api_key).get("data", [])

    for item in DEFAULT_CATALOG_ITEMS:
        slug = item["slug"]
        matched_prod = next(
            (
                p
                for p in existing_prods
                if (p.get("metadata") or {}).get("slug") == slug or p.get("name") == item["name"]
            ),
            None,
        )
        if matched_prod:
            prod = matched_prod
            default_price = prod.get("default_price")
            price_id = default_price.get("id") if isinstance(default_price, dict) else default_price
            if not price_id:
                created_price = stripe_request(
                    "POST",
                    "/prices",
                    api_key,
                    {
                        "product": prod["id"],
                        "unit_amount": item["unit_amount"],
                        "currency": item["currency"],
                        "tax_behavior": "inclusive",
                    },
                )
                price_id = created_price["id"]
        else:
            payload = {
                "name": item["name"],
                "description": item["description"],
                "tax_code": args.tax_code,
                "default_price_data[unit_amount]": item["unit_amount"],
                "default_price_data[currency]": item["currency"],
                "default_price_data[tax_behavior]": "inclusive",
                "metadata[slug]": slug,
            }
            prod = stripe_request("POST", "/products", api_key, payload)
            default_price = prod.get("default_price")
            price_id = default_price.get("id") if isinstance(default_price, dict) else default_price

        matched_link = next(
            (
                pl
                for pl in existing_links
                if (pl.get("metadata") or {}).get("slug") == slug and pl.get("active")
            ),
            None,
        )
        if matched_link:
            plink = matched_link
        else:
            plink_params = {
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": 1,
                "managed_payments[enabled]": "true",
                "after_completion[type]": "redirect",
                "after_completion[redirect][url]": (
                    f"{clean_site}/success.html?session_id={{CHECKOUT_SESSION_ID}}&slug={slug}"
                ),
                "metadata[slug]": slug,
            }
            try:
                plink = stripe_request("POST", "/payment_links", api_key, plink_params)
            except RuntimeError as err:
                if "managed_payments" not in str(err).lower():
                    raise
                plink_params.pop("managed_payments[enabled]", None)
                plink = stripe_request("POST", "/payment_links", api_key, plink_params)

        catalog["products"][slug] = {
            **item,
            "product_id": prod["id"],
            "price_id": price_id,
            "payment_link_id": plink["id"],
            "payment_link_url": plink["url"],
            "checkout_endpoint": f"{catalog['server_url']}/create-checkout-session?slug={slug}",
        }
        print(
            f"Provisioned {item['name']} -> product={prod['id']}, price={price_id}, link={plink['url']}"
        )

    save_catalog(catalog_path, catalog)
    print(f"Saved Stripe catalog -> {catalog_path}")

    if args.wire_checkout:
        bundle_entry = catalog["products"]["all-access-bundle"]
        bundle_pid = bundle_entry["product_id"]
        for slug in ("notion-linear-prd-sync", "notion-clean-md-exporter", "vscode-workspace-profile-config"):
            entry = catalog["products"][slug]
            subprocess.run(
                [
                    sys.executable,
                    str(CONFIGURE_CHECKOUT_SCRIPT),
                    "--slug",
                    slug,
                    "--checkout-url",
                    entry["payment_link_url"],
                    "--product-id",
                    entry["product_id"],
                    "--bundle-product-id",
                    bundle_pid,
                    "--skip-portfolio",
                ],
                check=True,
            )
        subprocess.run(
            [
                sys.executable,
                str(CONFIGURE_CHECKOUT_SCRIPT),
                "--bundle-url",
                bundle_entry["payment_link_url"],
            ],
            check=True,
        )

    return 0


def build_session_params(
    *,
    slug: str,
    price_id: str,
    mode: str,
    site_url: str,
) -> dict[str, Any]:
    clean_site = site_url.rstrip("/")
    return {
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": 1,
        "managed_payments[enabled]": "true",
        "mode": mode,
        "success_url": f"{clean_site}/success.html?session_id={{CHECKOUT_SESSION_ID}}&slug={slug}",
        "cancel_url": f"{clean_site}/cancel.html",
        "metadata[slug]": slug,
    }


def cmd_create_session(args: argparse.Namespace) -> int:
    catalog = load_catalog(Path(args.catalog_path))
    product_entry = catalog.get("products", {}).get(args.slug, {})
    price_id = args.price_id or product_entry.get("price_id")
    if not price_id:
        if args.dry_run:
            price_id = f"price_dryrun_{args.slug.replace('-', '_')}"
        else:
            raise ValueError(
                f"No price_id found for slug '{args.slug}'. Pass --price-id or run 'provision' first."
            )

    params = build_session_params(
        slug=args.slug,
        price_id=price_id,
        mode=args.mode,
        site_url=args.site_url,
    )
    if args.dry_run:
        out = {
            "dry_run": True,
            "api_version": STRIPE_API_VERSION,
            "endpoint": f"{STRIPE_API_BASE}/checkout/sessions",
            "params": params,
            "url": f"https://checkout.stripe.com/c/pay/cs_test_dryrun_{args.slug}",
        }
        print(json.dumps(out, indent=2))
        return 0

    api_key = resolve_api_key(args.api_key)
    session = create_checkout_session_with_fallback(api_key, params)
    print(
        json.dumps(
            {
                "id": session["id"],
                "url": session["url"],
                "managed_payments_fallback": bool(session.get("managed_payments_fallback", False)),
            },
            indent=2,
        )
    )
    return 0


def verify_stripe_signature(raw_body: bytes, sig_header: str, secret: str) -> bool:
    parts = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
    ts = parts.get("t", "")
    v1 = parts.get("v1", "")
    if not ts or not v1:
        return False
    signed_payload = f"{ts}.".encode("utf-8") + raw_body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


def verify_checkout_session_license(
    license_key: str,
    *,
    api_key: str | None,
    mock: bool,
) -> dict[str, Any]:
    clean_key = (license_key or "").strip()
    if not clean_key:
        return {"valid": False, "payment_status": "unpaid", "reason": "Empty license key"}

    if mock:
        is_bad = "unpaid" in clean_key.lower() or "invalid" in clean_key.lower()
        valid = clean_key.startswith(("cs_test_", "cs_live_")) and not is_bad
        return {
            "valid": valid,
            "payment_status": "paid" if valid else "unpaid",
            "product_id": "all-access-bundle",
            "metadata": {"slug": "all-access-bundle"},
            "expires_at": None,
            "reason": "ok" if valid else "Invalid or unpaid mock Checkout Session key",
        }

    key = resolve_api_key(api_key)
    encoded_id = urllib.parse.quote(clean_key, safe="")
    session = stripe_request("GET", f"/checkout/sessions/{encoded_id}?expand[]=line_items", key)
    payment_status = session.get("payment_status", "")
    paid = payment_status == "paid"
    metadata = session.get("metadata") or {}
    line_items = (session.get("line_items") or {}).get("data") or []
    product_id = None
    if line_items:
        price_obj = line_items[0].get("price") or {}
        product_id = price_obj.get("product")
    if not product_id:
        product_id = metadata.get("slug")
    return {
        "valid": paid,
        "payment_status": payment_status,
        "product_id": product_id,
        "metadata": metadata,
        "expires_at": None,
        "reason": "ok" if paid else f"Session payment_status is '{payment_status}'",
    }


def make_handler(
    *,
    catalog_path: Path,
    orders_path: Path,
    site_url: str,
    api_key: str | None,
    mock: bool,
):
    class ManagedPaymentsHandler(BaseHTTPRequestHandler):
        server_version = "StripeManagedPayments/1.0"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            sys.stderr.write(f"[stripe-server] {format % args}\n")

        def _send_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, status: int, html_text: str) -> None:
            body = html_text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length") or 0)
            return self.rfile.read(length) if length > 0 else b""

        def _parse_params(self, raw_body: bytes) -> dict[str, str]:
            parsed_url = urllib.parse.urlparse(self.path)
            params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed_url.query).items() if v}
            ctype = (self.headers.get("Content-Type") or "").lower()
            text = raw_body.decode("utf-8", errors="replace").strip()
            if text:
                if "application/json" in ctype or text.startswith("{"):
                    try:
                        loaded = json.loads(text)
                        if isinstance(loaded, dict):
                            params.update({str(k): str(v) for k, v in loaded.items() if v is not None})
                    except json.JSONDecodeError:
                        pass
                else:
                    form = urllib.parse.parse_qs(text)
                    params.update({k: v[0] for k, v in form.items() if v})
            return params

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            self._send_cors_headers()
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/create-checkout-session":
                self._handle_checkout(self._parse_params(b""))
                return
            if parsed.path in ("/success", "/success.html"):
                page = DEFAULT_DOCS_DIR / "success.html"
                html_text = page.read_text(encoding="utf-8") if page.is_file() else "<h1>Thanks for purchasing!</h1>"
                self._send_html(200, html_text)
                return
            if parsed.path in ("/cancel", "/cancel.html"):
                page = DEFAULT_DOCS_DIR / "cancel.html"
                html_text = page.read_text(encoding="utf-8") if page.is_file() else "<p>Checkout canceled.</p>"
                self._send_html(200, html_text)
                return
            if parsed.path == "/health":
                self._send_json(200, {"ok": True, "api_version": STRIPE_API_VERSION, "mock": mock})
                return
            self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            raw_body = self._read_body()
            if parsed.path == "/create-checkout-session":
                self._handle_checkout(self._parse_params(raw_body))
                return
            if parsed.path == "/verify-license":
                params = self._parse_params(raw_body)
                key = params.get("license_key") or params.get("key") or ""
                try:
                    res = verify_checkout_session_license(key, api_key=api_key, mock=mock)
                    self._send_json(200 if res["valid"] else 400, res)
                except Exception as exc:
                    self._send_json(400, {"valid": False, "error": str(exc)})
                return
            if parsed.path == "/webhook":
                self._handle_webhook(raw_body)
                return
            self._send_json(404, {"error": "Not found"})

        def _handle_checkout(self, params: dict[str, str]) -> None:
            slug = params.get("slug", "all-access-bundle")
            mode = params.get("mode", "payment")
            if mode not in ("payment", "subscription"):
                mode = "payment"
            catalog = load_catalog(catalog_path)
            prod_entry = catalog.get("products", {}).get(slug, {})
            price_id = params.get("price_id") or prod_entry.get("price_id")

            if mock:
                clean_slug = slug.replace("-", "_")
                session_url = f"https://checkout.stripe.com/c/pay/cs_test_mock_{clean_slug}"
            else:
                if not price_id:
                    self._send_json(
                        400,
                        {"error": f"No price_id configured for '{slug}'. Run provision first."},
                    )
                    return
                try:
                    key = resolve_api_key(api_key)
                    session = create_checkout_session_with_fallback(
                        key,
                        build_session_params(
                            slug=slug,
                            price_id=price_id,
                            mode=mode,
                            site_url=site_url,
                        ),
                    )
                    session_url = session["url"]
                except Exception as exc:
                    self._send_json(500, {"error": str(exc)})
                    return

            self.send_response(303)
            self._send_cors_headers()
            self.send_header("Location", session_url)
            self.end_headers()

        def _handle_webhook(self, raw_body: bytes) -> None:
            webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
            if webhook_secret:
                sig = self.headers.get("Stripe-Signature", "")
                if not verify_stripe_signature(raw_body, sig, webhook_secret):
                    self._send_json(400, {"error": "Invalid Stripe-Signature"})
                    return
            try:
                event = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(400, {"error": "Invalid JSON payload"})
                return

            etype = event.get("type", "")
            handled = {
                "checkout.session.completed",
                "checkout.session.async_payment_succeeded",
                "checkout.session.async_payment_failed",
            }
            if etype in handled:
                obj = (event.get("data") or {}).get("object") or {}
                record = {
                    "received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "event_type": etype,
                    "session_id": obj.get("id"),
                    "payment_status": obj.get("payment_status"),
                    "slug": (obj.get("metadata") or {}).get("slug"),
                }
                orders_path.parent.mkdir(parents=True, exist_ok=True)
                with orders_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record) + "\n")
            self._send_json(200, {"received": True, "event_type": etype})

    return ManagedPaymentsHandler


def cmd_serve(args: argparse.Namespace) -> int:
    handler_cls = make_handler(
        catalog_path=Path(args.catalog_path),
        orders_path=Path(args.orders_path),
        site_url=args.site_url,
        api_key=args.api_key,
        mock=bool(args.mock),
    )
    server = ThreadingHTTPServer((args.host, args.port), handler_cls)
    mode_label = "MOCK" if args.mock else "LIVE/TEST-STRIPE"
    print(f"Stripe Managed Payments server ({mode_label}) listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Provision & serve Stripe Managed Payments Checkout and License verification."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_prov = sub.add_parser("provision", help="Create Stripe Managed Payments Products & Prices")
    p_prov.add_argument("--api-key", help="Stripe secret key (or STRIPE_SECRET_KEY env)")
    p_prov.add_argument("--tax-code", default=DEFAULT_TAX_CODE, help="Managed Payments eligible tax code")
    p_prov.add_argument("--site-url", default=DEFAULT_SITE_URL, help="Hosted site base URL")
    p_prov.add_argument("--server-url", default="http://localhost:4242", help="Checkout server base URL")
    p_prov.add_argument("--catalog-path", default=str(DEFAULT_CATALOG_PATH), help="Catalog output JSON")
    p_prov.add_argument("--wire-checkout", action="store_true", help="Wire Payment Links into landing pages, zips, and docs/")
    p_prov.add_argument("--dry-run", action="store_true", help="Write dry-run catalog without calling Stripe")
    p_prov.set_defaults(func=cmd_provision)

    p_sess = sub.add_parser("create-session", help="Create a Managed Payments Checkout Session")
    p_sess.add_argument("--slug", default="all-access-bundle", help="Product slug")
    p_sess.add_argument("--price-id", help="Stripe price ID override")
    p_sess.add_argument("--mode", choices=["payment", "subscription"], default="payment", help="Checkout mode")
    p_sess.add_argument("--site-url", default=DEFAULT_SITE_URL, help="Hosted site base URL")
    p_sess.add_argument("--catalog-path", default=str(DEFAULT_CATALOG_PATH), help="Catalog JSON path")
    p_sess.add_argument("--api-key", help="Stripe secret key (or STRIPE_SECRET_KEY env)")
    p_sess.add_argument("--dry-run", action="store_true", help="Print session request payload without calling Stripe")
    p_sess.set_defaults(func=cmd_create_session)

    p_srv = sub.add_parser("serve", help="Run Checkout, License Verify, and Webhook HTTP server")
    p_srv.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"), help="Bind host")
    p_srv.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", 4242)),
        help="Bind port (default: $PORT or 4242)",
    )
    p_srv.add_argument("--site-url", default=DEFAULT_SITE_URL, help="Success/cancel redirect site URL")
    p_srv.add_argument("--catalog-path", default=str(DEFAULT_CATALOG_PATH), help="Catalog JSON path")
    p_srv.add_argument("--orders-path", default=str(DEFAULT_ORDERS_PATH), help="Fulfilled webhook orders log")
    p_srv.add_argument("--api-key", help="Stripe secret key (or STRIPE_SECRET_KEY env)")
    p_srv.add_argument("--mock", action="store_true", help="Serve deterministic mock checkout/verify responses")
    p_srv.set_defaults(func=cmd_serve)

    return parser


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
