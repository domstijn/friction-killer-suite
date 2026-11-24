#!/usr/bin/env python3
"""Live GitHub buyer-signal radar: finds fresh open, unlocked issues matching Friction-Killer workflows."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.parse

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTREACH_QUEUE_PATH = REPO_ROOT / "pipeline" / "OUTREACH_QUEUE.md"
SITE_BASE_URL = "https://domstijn.github.io/friction-killer-suite"

QUERIES: list[dict[str, str]] = [
    {"keyword": "XRechnung", "product": "EInvoiceLocal", "slug": "e-invoice-xml-batch-converter"},
    {"keyword": "ZUGFeRD", "product": "EInvoiceLocal", "slug": "e-invoice-xml-batch-converter"},
    {"keyword": "CAMT.053", "product": "BankFeedBridge", "slug": "camt053-mt940-qbo-xero-converter"},
    {"keyword": "MT940", "product": "BankFeedBridge", "slug": "camt053-mt940-qbo-xero-converter"},
    {"keyword": "BZSt OSS", "product": "OssVatBridge", "slug": "eu-oss-vat-return-compiler"},
    {"keyword": "Lemon Squeezy migrate", "product": "LemonExitBridge", "slug": "lemonsqueezy-stripe-polar-migrator"},
    {"keyword": "WooCommerce Shopify metafields", "product": "ShopMetaShift", "slug": "woo-shopify-metafield-migrator"},
    {"keyword": "ProperSoft", "product": "BankFeedBridge", "slug": "camt053-mt940-qbo-xero-converter"},
]


def load_existing_issue_urls(queue_path: Path) -> set[str]:
    """Return GitHub issue URLs already listed in OUTREACH_QUEUE.md for deduplication."""
    if not queue_path.is_file():
        return set()
    text = queue_path.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"https://github\.com/[^\s)]+/issues/\d+", text))


def search_issues(keyword: str, since_date: str, per_page: int = 8) -> list[dict[str, object]]:
    """Query GitHub Search API via gh CLI for open, unlocked issues updated since YYYY-MM-DD."""
    q = f"{keyword} is:issue is:open updated:>={since_date}"
    endpoint = f"search/issues?q={urllib.parse.quote(q)}&sort=updated&order=desc&per_page={per_page}"
    try:
        proc = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if proc.returncode != 0:
            return []
        payload = json.loads(proc.stdout)
        return list(payload.get("items") or [])
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []


NOISE_TITLE_RE = re.compile(
    r"dependency dashboard|submit your mcp|release train|lead tracker|radar\s+\w+|\[tracking\]|\(tracking\)|autonomous development mission",
    re.I,
)


def score_issue(item: dict[str, object], now_utc: datetime) -> float:
    """Rank issues by recency and genuine discussion traction while down-ranking noisy megathreads."""
    updated_raw = str(item.get("updated_at") or "")
    age_days = 30.0
    if updated_raw:
        try:
            dt = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
            age_days = max(0.0, (now_utc - dt).total_seconds() / 86400.0)
        except ValueError:
            pass
    comments = int(item.get("comments") or 0)
    recency_pts = max(0.0, 40.0 - age_days)
    if comments > 80:
        traction_pts = -15.0
    else:
        traction_pts = min(comments, 12) * 1.5
    return round(recency_pts + traction_pts, 1)


def gather_signals(days: int) -> list[dict[str, object]]:
    now_utc = datetime.now(timezone.utc)
    since_date = (now_utc - timedelta(days=days)).strftime("%Y-%m-%d")
    seen_urls = load_existing_issue_urls(OUTREACH_QUEUE_PATH)
    candidates: list[dict[str, object]] = []

    for qspec in QUERIES:
        items = search_issues(qspec["keyword"], since_date)
        for item in items:
            url = str(item.get("html_url") or "")
            title = str(item.get("title") or "").strip()
            if not url or "/pull/" in url or url in seen_urls:
                continue
            if item.get("locked") or item.get("state") != "open" or NOISE_TITLE_RE.search(title):
                continue
            repo_url = str(item.get("repository_url") or "")
            repo_name = "/".join(repo_url.rstrip("/").split("/")[-2:]) if "/" in repo_url else ""
            if repo_name.startswith("domstijn/"):
                continue
            seen_urls.add(url)
            candidates.append(
                {
                    "keyword": qspec["keyword"],
                    "product": qspec["product"],
                    "target_link": f"{SITE_BASE_URL}/products/{qspec['slug']}/?ref=src.gh-sniper",
                    "repo": repo_name,
                    "title": title,
                    "url": url,
                    "updated_at": str(item.get("updated_at") or "")[:10],
                    "comments": int(item.get("comments") or 0),
                    "score": score_issue(item, now_utc),
                }
            )
        time.sleep(0.4)

    candidates.sort(key=lambda r: float(r["score"]), reverse=True)
    return candidates


def render_markdown(candidates: list[dict[str, object]], days: int) -> str:
    now_str = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = "\n".join(
        f"| {c['score']} | `{c['product']}` | `{c['keyword']}` | {c['updated_at']} | {c['comments']} | [{c['repo']}: {str(c['title']).replace('|', ' ')}]({c['url']}) | {c['target_link']} |"
        for c in candidates
    ) or "| - | - | - | - | - | *(No unseen open issues in lookback window)* | - |"
    return f"""# Live Buyer Radar — Fresh GitHub Signals (`pipeline/FRESH_BUYER_SIGNALS.md`)

- **Scanned (UTC):** `{now_str}` (`days={days}`)
- **Filter:** `state == "open"`, `locked == false`, deduplicated against `pipeline/OUTREACH_QUEUE.md`, excluding `domstijn/*`
- **Signals Found:** `{len(candidates)}`

| Score | Target Tool | Query | Updated | Comments | Open Unlocked Issue | Tracked Tool Link |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
{rows}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Find fresh open unlocked GitHub buyer signals.")
    parser.add_argument("--days", type=int, default=21, help="Lookback window in days (default: 21)")
    parser.add_argument("--save", help="Optional Markdown file path to write results")
    args = parser.parse_args()

    candidates = gather_signals(args.days)
    md = render_markdown(candidates, args.days)
    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"Saved {len(candidates)} fresh buyer signal(s) -> {out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
