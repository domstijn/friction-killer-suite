#!/usr/bin/env python3
"""Low-token pain-signal harvester querying HN Algolia, GitHub Issues, and Stack Overflow APIs."""

from __future__ import annotations

import argparse
import gzip
import html
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

USER_AGENT = "FrictionKillerBot/1.1 (+https://github.com/local/friction-factory)"
MAX_SNIPPET = 250


def clean_text(raw: str, max_len: int = MAX_SNIPPET) -> str:
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def fetch_json(url: str, timeout: int = 10) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding", "").lower() == "gzip" or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8", errors="replace"))


TARGET_ALIASES = {
    "vscode": {"vs code", "visual studio code", "microsoft/vscode"},
    "notion": {"notion.so", "notionhq"},
    "linear": {"linear.app"},
    "shopify": {"myshopify", "shopify plus"},
    "airtable": {"airtable.com"},
    "hubspot": {"hubspot.com"},
    "figma": {"figma.com"},
}


def target_matches(target: str, *fields: str) -> bool:
    needle = target.strip().lower()
    aliases = {needle}
    aliases.update(TARGET_ALIASES.get(needle, set()))
    haystack = " ".join(f or "" for f in fields).lower()
    return any(alias in haystack for alias in aliases)


def mine_hn(target: str, limit: int) -> tuple[list[dict[str, Any]], str | None]:
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for suffix in ("workaround", "plugin"):
        params = urllib.parse.urlencode(
            {"query": f"{target} {suffix}", "tags": "story", "hitsPerPage": max(limit, 10)}
        )
        url = f"https://hn.algolia.com/api/v1/search?{params}"
        try:
            data = fetch_json(url)
        except Exception as exc:
            errors.append(f"HN({suffix}): {exc}")
            continue
        for hit in data.get("hits", []):
            title = clean_text(hit.get("title") or hit.get("story_title") or "", 140)
            if not title or not target_matches(target, title):
                continue
            item_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            snippet = clean_text(hit.get("story_text") or hit.get("comment_text") or "")
            points = int(hit.get("points") or 0)
            comments = int(hit.get("num_comments") or 0)
            items.append(
                {
                    "source": "HN",
                    "title": title,
                    "url": item_url,
                    "engagement": points + comments * 2,
                    "meta": f"{points} pts / {comments} comments",
                    "snippet": snippet,
                }
            )
    err = "; ".join(errors) if errors and not items else None
    return items, err


def mine_github(target: str, limit: int) -> tuple[list[dict[str, Any]], str | None]:
    query = f'"{target}" in:title (workaround OR plugin OR extension OR export OR sync OR config) is:issue is:open'
    params = urllib.parse.urlencode(
        {"q": query, "sort": "reactions-+1", "order": "desc", "per_page": max(limit * 2, 12)}
    )
    url = f"https://api.github.com/search/issues?{params}"
    try:
        data = fetch_json(url)
    except Exception as exc:
        return [], f"GitHub error: {exc}"

    items: list[dict[str, Any]] = []
    for issue in data.get("items", []):
        title = clean_text(issue.get("title") or "", 140)
        html_url = issue.get("html_url") or ""
        if not title or not target_matches(target, title, html_url):
            continue
        comments = int(issue.get("comments") or 0)
        reactions = int((issue.get("reactions") or {}).get("total_count") or 0)
        items.append(
            {
                "source": "GitHub",
                "title": title,
                "url": html_url,
                "engagement": reactions * 3 + comments,
                "meta": f"{reactions} reactions / {comments} comments",
                "snippet": clean_text(issue.get("body") or ""),
            }
        )
    return items, None


def _query_stackexchange(
    target: str,
    limit: int,
    site: str,
    source_label: str,
) -> tuple[list[dict[str, Any]], str | None]:
    params = urllib.parse.urlencode(
        {
            "order": "desc",
            "sort": "votes",
            "title": target,
            "site": site,
            "pagesize": max(limit * 2, 15),
        }
    )
    url = f"https://api.stackexchange.com/2.3/search/advanced?{params}"
    try:
        data = fetch_json(url)
    except Exception as exc:
        return [], f"{source_label} error: {exc}"

    items: list[dict[str, Any]] = []
    for q in data.get("items", []):
        title = clean_text(q.get("title") or "", 140)
        tags = " ".join(q.get("tags") or [])
        if not title or not target_matches(target, title, tags):
            continue
        score = int(q.get("score") or 0)
        answers = int(q.get("answer_count") or 0)
        views = int(q.get("view_count") or 0)
        items.append(
            {
                "source": source_label,
                "title": title,
                "url": q.get("link") or "",
                "engagement": score * 2 + answers * 3,
                "meta": f"{score} votes / {answers} answers / {views} views",
                "snippet": f"Tags: {tags}" if tags else "",
            }
        )
    return items, None


def mine_stackexchange(target: str, limit: int) -> tuple[list[dict[str, Any]], str | None]:
    return _query_stackexchange(target, limit, site="stackoverflow", source_label="StackOverflow")


def mine_b2b_webapps(target: str, limit: int) -> tuple[list[dict[str, Any]], str | None]:
    return _query_stackexchange(target, limit, site="webapps", source_label="B2B-WebApps")


SOURCE_MINERS = {
    "hn": mine_hn,
    "github": mine_github,
    "stackoverflow": mine_stackexchange,
    "b2b": mine_b2b_webapps,
}


def deduplicate_and_rank(
    items: list[dict[str, Any]], limit: int, balance_sources: bool = True
) -> list[dict[str, Any]]:
    seen_keys: set[str] = set()
    unique: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    per_source_cap = max(1, math.ceil(limit / 2)) if balance_sources else limit

    for item in sorted(items, key=lambda x: x.get("engagement", 0), reverse=True):
        src = item.get("source", "unknown")
        if source_counts.get(src, 0) >= per_source_cap:
            continue
        norm_title = re.sub(r"[^a-z0-9]+", "", item["title"].lower())[:60]
        url_key = item["url"].split("?")[0].rstrip("/").lower()
        if norm_title in seen_keys or (url_key and url_key in seen_keys):
            continue
        seen_keys.add(norm_title)
        if url_key:
            seen_keys.add(url_key)
        source_counts[src] = source_counts.get(src, 0) + 1
        unique.append(item)
        if len(unique) >= limit:
            break
    return unique


def format_markdown(target: str, items: list[dict[str, Any]], warnings: list[str]) -> str:
    lines = [f"### Pain Signals Digest: `{target}` ({len(items)} items)"]
    if warnings:
        lines.append(f"> Warnings: {'; '.join(warnings)}")
    if not items:
        lines.append("No signals matched (or all sources failed/rate-limited).")
        return "\n".join(lines)
    for idx, item in enumerate(items, 1):
        snippet_part = f" — {item['snippet']}" if item.get("snippet") else ""
        lines.append(
            f"{idx}. **[{item['source']}]** {item['title']} ({item['meta']}) — {item['url']}{snippet_part}"
        )
    return "\n".join(lines)


def mine_for_target(target: str, source: str, limit: int) -> dict[str, Any]:
    sources = list(SOURCE_MINERS.keys()) if source == "all" else [source]
    all_items: list[dict[str, Any]] = []
    warnings: list[str] = []

    for src in sources:
        items, err = SOURCE_MINERS[src](target, limit)
        all_items.extend(items)
        if err:
            warnings.append(err)

    ranked = deduplicate_and_rank(all_items, max(1, limit), balance_sources=(source == "all"))
    return {"target": target, "warnings": warnings, "items": ranked}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mine compact software pain signals from HN, GitHub, and Stack Overflow."
    )
    parser.add_argument("--target", help="Single target software or niche (e.g., notion)")
    parser.add_argument("--targets", help="Comma-separated targets (e.g., notion,linear,vscode)")
    parser.add_argument(
        "--source", choices=["all", "hn", "github", "stackoverflow", "b2b"], default="all", help="Signal source"
    )
    parser.add_argument("--limit", type=int, default=8, help="Maximum results per target")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format")
    args = parser.parse_args()

    targets: list[str] = []
    if args.targets:
        targets.extend(t.strip() for t in args.targets.split(",") if t.strip())
    if args.target and args.target.strip() not in targets:
        targets.append(args.target.strip())

    if not targets:
        parser.error("Provide --target or --targets")

    results = [mine_for_target(t, args.source, args.limit) for t in targets]

    if args.format == "json":
        payload: Any = results[0] if len(results) == 1 and not args.targets else {"targets": results}
        print(json.dumps(payload, indent=2))
    else:
        print("\n\n".join(format_markdown(r["target"], r["items"], r["warnings"]) for r in results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
