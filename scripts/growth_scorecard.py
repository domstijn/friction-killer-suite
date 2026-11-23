#!/usr/bin/env python3
"""Pull live Cloudflare funnel events, GitHub traffic, VS Code & PyPI metrics and evaluate Day 14 Gate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ANALYTICS_CFG = REPO_ROOT / "pipeline" / "analytics_config.json"
DEFAULT_HISTORY_PATH = REPO_ROOT / "pipeline" / "growth_history.jsonl"
DEFAULT_SCORECARD_PATH = REPO_ROOT / "pipeline" / "GROWTH_SCORECARD.md"
GITHUB_REPO = "domstijn/friction-killer-suite"
VSCE_ITEM = "friction-killer.vscode-workspace-profile-config"

ACTIVE_PYPI_NAMES = [
    "eu-oss-vat-return-compiler",
    "amazon-settlement-xero-qbo-splitter",
    "e-invoice-xml-batch-converter",
    "lemonsqueezy-stripe-polar-migrator",
    "stripe-payout-xero-qbo-splitter",
    "notion-clean-md-exporter",
    "claude-profile-switch",
    "woo-shopify-metafield-migrator",
    "camt053-mt940-qbo-xero-converter",
]


def _http_json(url: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None, timeout: int = 10) -> tuple[int, Any]:
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"User-Agent": "FrictionKiller-Scorecard/1.0", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": f"HTTP {exc.code}"}
    except (OSError, json.JSONDecodeError) as exc:
        return 0, {"error": str(exc)}


def _gh_api_json(endpoint: str) -> Any:
    try:
        proc = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return {"error": (proc.stderr or proc.stdout).strip()}
        return json.loads(proc.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}


def fetch_worker_stats(worker_url: str, days: int) -> dict[str, Any]:
    if not worker_url:
        return {"ok": False, "error": "worker_url not configured"}
    status, data = _http_json(f"{worker_url.rstrip('/')}/stats?days={days}")
    if status == 200 and isinstance(data, dict):
        return data
    return {"ok": False, "status": status, "error": data.get("error", "Unknown error")}


def fetch_github_metrics() -> dict[str, Any]:
    repo = _gh_api_json(f"repos/{GITHUB_REPO}")
    views = _gh_api_json(f"repos/{GITHUB_REPO}/traffic/views")
    clones = _gh_api_json(f"repos/{GITHUB_REPO}/traffic/clones")
    referrers = _gh_api_json(f"repos/{GITHUB_REPO}/traffic/popular/referrers")
    releases = _gh_api_json(f"repos/{GITHUB_REPO}/releases")

    release_rows: list[dict[str, Any]] = []
    if isinstance(releases, list):
        for rel in releases:
            assets = rel.get("assets") or []
            release_rows.append(
                {
                    "tag": rel.get("tag_name"),
                    "created_at": rel.get("created_at"),
                    "asset_count": len(assets),
                    "total_downloads": sum(int(a.get("download_count", 0)) for a in assets),
                }
            )

    return {
        "stars": repo.get("stargazers_count", 0) if isinstance(repo, dict) else 0,
        "forks": repo.get("forks_count", 0) if isinstance(repo, dict) else 0,
        "open_issues": repo.get("open_issues_count", 0) if isinstance(repo, dict) else 0,
        "views_14d": views.get("count", 0) if isinstance(views, dict) else 0,
        "views_uniques_14d": views.get("uniques", 0) if isinstance(views, dict) else 0,
        "clones_14d": clones.get("count", 0) if isinstance(clones, dict) else 0,
        "clones_uniques_14d": clones.get("uniques", 0) if isinstance(clones, dict) else 0,
        "referrers": referrers if isinstance(referrers, list) else [],
        "releases": release_rows,
    }


def fetch_vsce_stats() -> dict[str, Any]:
    payload = json.dumps(
        {
            "filters": [{"criteria": [{"filterType": 7, "value": VSCE_ITEM}]}],
            "flags": 914,
        }
    ).encode("utf-8")
    status, data = _http_json(
        "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery",
        method="POST",
        body=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json;api-version=3.0-preview.1",
        },
    )
    if status != 200 or not isinstance(data, dict):
        return {"ok": False, "error": f"HTTP {status}"}
    try:
        ext = data["results"][0]["extensions"][0]
        stats = {s["statisticName"]: s["value"] for s in ext.get("statistics", [])}
        return {"ok": True, "downloadCount": stats.get("downloadCount", 0), "install": stats.get("install", 0)}
    except (KeyError, IndexError, TypeError):
        return {"ok": False, "error": "Unexpected VSCE response"}


def fetch_pypi_stats() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pkg in ACTIVE_PYPI_NAMES:
        st_json, _ = _http_json(f"https://pypi.org/pypi/{pkg}/json", timeout=8)
        live = st_json == 200
        dl_7d: int | None = None
        dl_30d: int | None = None
        if live:
            st_recent, recent_data = _http_json(f"https://pypistats.org/api/packages/{pkg}/recent", timeout=8)
            if st_recent == 200 and isinstance(recent_data, dict):
                d = recent_data.get("data") or {}
                dl_7d = d.get("last_week")
                dl_30d = d.get("last_month")
        rows.append({"package": pkg, "live": live, "last_week": dl_7d, "last_month": dl_30d})
    return rows


def evaluate_decision_gate(
    human_visitors: int,
    tool_runs: int,
    checkout_clicks: int,
    paid_orders: int,
) -> tuple[str, str]:
    act_rate = (tool_runs / human_visitors * 100.0) if human_visitors > 0 else 0.0
    chk_rate = (checkout_clicks / human_visitors * 100.0) if human_visitors > 0 else 0.0
    if paid_orders >= 3 or (human_visitors >= 50 and act_rate >= 20.0 and chk_rate >= 3.0):
        return (
            "UP THE ANTE",
            "Strong commercial pull validated (>=3 paid orders OR >=20% tool activation + >=3% checkout rate on >=50 visitors). Isolate winners onto dedicated domain and scale.",
        )
    if human_visitors >= 200 and act_rate >= 15.0 and paid_orders == 0:
        return (
            "CONTINUE & FIX CONVERSION",
            ">=200 qualified visitors with >=15% tool runs but 0 paid sales: pain is real, fix domain trust / Free tier caps / pricing without building new tools.",
        )
    if human_visitors >= 300 and act_rate < 5.0 and paid_orders == 0:
        return (
            "ABANDON ACTIVE WORK",
            ">=300 qualified visitors with <5% activation and 0 sales: leave static assets online passively at €0/mo and pivot strategy.",
        )
    return (
        "COLLECTING DATA (NEED >= 200 QUALIFIED VISITORS)",
        f"Current human funnel sample is too small ({human_visitors} page_view(s)) for a Day 14 verdict; continue targeted outreach and daily tracking.",
    )


def render_scorecard_md(snapshot: dict[str, Any]) -> str:
    funnel = snapshot["cloudflare_funnel"]
    ev = funnel.get("totals_by_event", {}) if funnel.get("ok") else {}
    by_slug = funnel.get("totals_by_slug", {}) if funnel.get("ok") else {}
    by_ref = funnel.get("totals_by_referrer", {}) if funnel.get("ok") else {}

    human_pv = int(ev.get("page_view", 0))
    uploads = int(ev.get("file_upload", 0))
    runs = int(ev.get("tool_run", 0))
    paywalls = int(ev.get("paywall_hit", 0))
    chk_clicks = int(ev.get("checkout_click", 0))
    fb_clicks = int(ev.get("feedback_click", 0))
    act_pct = f"{((uploads + runs) / human_pv * 100):.1f}%" if human_pv > 0 else "0.0%"
    chk_pct = f"{(chk_clicks / human_pv * 100):.1f}%" if human_pv > 0 else "0.0%"

    stripe = snapshot["stripe"]
    gh = snapshot["github"]
    vsce = snapshot["vsce"]
    pypi_rows = snapshot["pypi"]

    slug_rows = "\n".join(
        f"| `{slug}` | {m.get('page_view', 0)} | {m.get('file_upload', 0)} | {m.get('tool_run', 0)} | {m.get('paywall_hit', 0)} | {m.get('checkout_click', 0)} | {m.get('feedback_click', 0)} |"
        for slug, m in sorted(by_slug.items(), key=lambda kv: kv[1].get("page_view", 0), reverse=True)
    ) or "| *(no human events recorded yet — newly deployed)* | 0 | 0 | 0 | 0 | 0 | 0 |"

    ref_rows = "\n".join(
        f"| `{ref}` | {cnt} |" for ref, cnt in sorted(by_ref.items(), key=lambda kv: kv[1], reverse=True)
    ) or "| *(none yet)* | 0 |"

    rel_rows = "\n".join(
        f"| `{r['tag']}` | {r['created_at']} | {r['asset_count']} | {r['total_downloads']} |"
        for r in gh.get("releases", [])
    ) or "| *(none)* | - | 0 | 0 |"

    pypi_md = "\n".join(
        f"| `{p['package']}` | {'LIVE (HTTP 200)' if p['live'] else 'PENDING (429 cooldown)'} | {p['last_week'] if p['last_week'] is not None else 'n/a'} | {p['last_month'] if p['last_month'] is not None else 'n/a'} |"
        for p in pypi_rows
    )

    return f"""# Friction-Killer Suite — Growth & Validation Scorecard

- **Updated (UTC):** `{snapshot['timestamp']}`
- **Window:** Last `{snapshot['window_days']}` days
- **Objective Decision Gate:** **{snapshot['decision']}**
  - *{snapshot['decision_reason']}*

---

## 1. Verified Human Funnel (Cloudflare EU D1 Worker — Bots Filtered Out)

| Metric | Count | Rate vs. Page Views |
| :--- | :---: | :---: |
| **Human `page_view`** | **{human_pv}** | 100% |
| **Real `file_upload`** | **{uploads}** | {f"{uploads / human_pv * 100:.1f}%" if human_pv > 0 else "0.0%"} |
| **Interactive `tool_run`** | **{runs}** | {f"{runs / human_pv * 100:.1f}%" if human_pv > 0 else "0.0%"} |
| **Total Activations (`file_upload` + `tool_run`)** | **{uploads + runs}** | **{act_pct}** |
| **Pro `paywall_hit`** | **{paywalls}** | {f"{paywalls / human_pv * 100:.1f}%" if human_pv > 0 else "0.0%"} |
| **Stripe `checkout_click`** | **{chk_clicks}** | **{chk_pct}** |
| **User `feedback_click`** | **{fb_clicks}** | - |

### By Product / Page
| Slug | `page_view` | `file_upload` | `tool_run` | `paywall_hit` | `checkout_click` | `feedback_click` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
{slug_rows}

### Referrers
| Referrer Host | Events |
| :--- | :---: |
{ref_rows}

---

## 2. Live Stripe Revenue (`acct_1UdCWDH2AcdDmQyR`)

| Metric | Value | Notes |
| :--- | :---: | :--- |
| **Net Revenue Balance** | **€{stripe['revenue_eur']:.2f}** | Verified live Stripe balance |
| **Paid Orders** | **{stripe['paid_orders']}** | Completed live PaymentIntents / paid sessions |
| **Total Checkout Sessions Created** | {stripe['checkout_sessions']} | Includes unpaid/expired & crawler link previews |
| **Currently Open Unpaid Sessions** | {stripe['unpaid_open_sessions']} | Exclude from revenue metrics |

---

## 3. Channel Baselines (Noise-Flagged — Never Confuse Scraper Clones with Sales)

- **GitHub (`{GITHUB_REPO}`):** `{gh['stars']}` stars · `{gh['forks']}` forks · `{gh['views_14d']}` repo views (`{gh['views_uniques_14d']}` uniques, 14d) · `{gh['clones_14d']}` clones (`{gh['clones_uniques_14d']}` uniques — *mostly automated GitHub cloners/mirror bots*)
- **VS Code Marketplace (`{VSCE_ITEM}`):** `{vsce.get('downloadCount', 'n/a')}` `downloadCount` *(includes automated scanner pulls)*

### Releases
| Tag | Created (UTC) | Assets | Total Downloads (incl. bots) |
| :--- | :--- | :---: | :---: |
{rel_rows}

### PyPI Packages (`4` Live / `5` Pending Rate-Limit Cooldown)
| Package | Registry Status | Downloads (7d) | Downloads (30d) |
| :--- | :--- | :---: | :---: |
{pypi_md}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Growth & Validation Scorecard.")
    parser.add_argument("--days", type=int, default=14, help="Lookback window in days (default: 14)")
    parser.add_argument("--save", action="store_true", help="Write pipeline/GROWTH_SCORECARD.md and append growth_history.jsonl")
    parser.add_argument("--stripe-revenue-eur", type=float, default=0.0, help="Verified live Stripe EUR revenue")
    parser.add_argument("--stripe-paid-orders", type=int, default=0, help="Verified live Stripe paid order count")
    parser.add_argument("--stripe-checkout-sessions", type=int, default=0, help="Total Stripe Checkout sessions")
    parser.add_argument("--stripe-unpaid-open", type=int, default=0, help="Open unpaid Stripe Checkout sessions")
    args = parser.parse_args()

    cfg = {}
    if DEFAULT_ANALYTICS_CFG.is_file():
        cfg = json.loads(DEFAULT_ANALYTICS_CFG.read_text(encoding="utf-8"))

    worker_stats = fetch_worker_stats(str(cfg.get("worker_url", "")), args.days)
    gh_metrics = fetch_github_metrics()
    vsce_metrics = fetch_vsce_stats()
    pypi_metrics = fetch_pypi_stats()

    ev = worker_stats.get("totals_by_event", {}) if worker_stats.get("ok") else {}
    human_pv = int(ev.get("page_view", 0))
    tool_runs = int(ev.get("tool_run", 0)) + int(ev.get("file_upload", 0))
    checkout_clicks = int(ev.get("checkout_click", 0))

    decision, decision_reason = evaluate_decision_gate(
        human_pv, tool_runs, checkout_clicks, args.stripe_paid_orders
    )

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_days": args.days,
        "decision": decision,
        "decision_reason": decision_reason,
        "stripe": {
            "revenue_eur": float(args.stripe_revenue_eur),
            "paid_orders": int(args.stripe_paid_orders),
            "checkout_sessions": int(args.stripe_checkout_sessions),
            "unpaid_open_sessions": int(args.stripe_unpaid_open),
        },
        "cloudflare_funnel": worker_stats,
        "github": gh_metrics,
        "vsce": vsce_metrics,
        "pypi": pypi_metrics,
    }

    md = render_scorecard_md(snapshot)
    if args.save:
        DEFAULT_SCORECARD_PATH.write_text(md, encoding="utf-8")
        with DEFAULT_HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        print(f"Saved Growth Scorecard -> {DEFAULT_SCORECARD_PATH} (Decision: {decision})")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
