#!/usr/bin/env python3
"""Low-token pain-signal harvester querying HN Algolia, GitHub Issues, and Stack Exchange APIs."""

from __future__ import annotations

import argparse
import gzip
import html
import json
import math
import os
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

USER_AGENT = "FrictionKillerBot/2.0 (+https://github.com/domstijn/friction-killer-suite)"
MAX_SNIPPET = 250
WORKAROUND_HINTS = (
    "workaround",
    "solved",
    "built-in",
    "native",
    "docker compose config",
    "claude_config_dir",
    "plugin",
    "extension",
    "i built",
    "use this instead",
)
_GH_TOKEN_CACHE: str | None = None
_GH_TOKEN_CHECKED = False


def _get_github_token() -> str | None:
    global _GH_TOKEN_CACHE, _GH_TOKEN_CHECKED
    if _GH_TOKEN_CHECKED:
        return _GH_TOKEN_CACHE
    _GH_TOKEN_CHECKED = True
    env_tok = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if env_tok:
        _GH_TOKEN_CACHE = env_tok
        return _GH_TOKEN_CACHE
    try:
        proc = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            _GH_TOKEN_CACHE = proc.stdout.strip()
    except Exception:
        _GH_TOKEN_CACHE = None
    return _GH_TOKEN_CACHE


def clean_text(raw: str, max_len: int = MAX_SNIPPET) -> str:
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def fetch_json(url: str, timeout: int = 10) -> dict[str, Any] | list[Any]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }
    if url.startswith("https://api.github.com"):
        headers["Accept"] = "application/vnd.github+json"
        tok = _get_github_token()
        if tok:
            headers["Authorization"] = f"Bearer {tok}"

    req = urllib.request.Request(url, headers=headers)
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
    "claude": {"claude-code", "claude.ai", "anthropic"},
    "codex": {"openai/codex", "codex-cli"},
}


def target_matches(target: str, *fields: str) -> bool:
    needle = target.strip().lower()
    aliases = {needle}
    aliases.update(TARGET_ALIASES.get(needle, set()))
    haystack = " ".join(f or "" for f in fields).lower()
    return any(alias in haystack for alias in aliases)


def _recency_multiplier(year: int | None) -> float:
    if not year:
        return 1.0
    if year >= 2026:
        return 1.25
    if year == 2025:
        return 1.1
    if year == 2024:
        return 1.0
    return 0.65


def mine_hn(target: str, limit: int, since_year: int = 2024) -> tuple[list[dict[str, Any]], str | None]:
    since_epoch = int(datetime(since_year, 1, 1, tzinfo=timezone.utc).timestamp())
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for suffix in ("workaround", "plugin"):
        params = urllib.parse.urlencode(
            {
                "query": f"{target} {suffix}",
                "tags": "story",
                "numericFilters": f"created_at_i>={since_epoch}",
                "hitsPerPage": max(limit, 10),
            }
        )
        url = f"https://hn.algolia.com/api/v1/search?{params}"
        try:
            data = fetch_json(url)
        except Exception as exc:
            errors.append(f"HN({suffix}): {exc}")
            continue
        if not isinstance(data, dict):
            continue
        for hit in data.get("hits", []):
            title = clean_text(hit.get("title") or hit.get("story_title") or "", 140)
            if not title or not target_matches(target, title):
                continue
            ts = int(hit.get("created_at_i") or 0)
            if ts < since_epoch:
                continue
            dt_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            item_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            snippet = clean_text(hit.get("story_text") or hit.get("comment_text") or "")
            points = int(hit.get("points") or 0)
            comments = int(hit.get("num_comments") or 0)
            mult = _recency_multiplier(int(dt_str[:4]))
            items.append(
                {
                    "source": "HN",
                    "title": title,
                    "url": item_url,
                    "engagement": (points + comments * 2) * mult,
                    "meta": f"{points} pts / {comments} comments / {dt_str}",
                    "snippet": snippet,
                }
            )
    err = "; ".join(errors) if errors and not items else None
    return items, err


def mine_github(target: str, limit: int, since_year: int = 2024) -> tuple[list[dict[str, Any]], str | None]:
    query = (
        f'"{target}" in:title (workaround OR plugin OR extension OR export OR sync) '
        f"is:issue is:open created:>={since_year}-01-01"
    )
    params = urllib.parse.urlencode(
        {"q": query, "sort": "reactions-+1", "order": "desc", "per_page": max(limit * 2, 12)}
    )
    url = f"https://api.github.com/search/issues?{params}"
    try:
        data = fetch_json(url)
    except Exception as exc:
        return [], f"GitHub error: {exc}"

    if not isinstance(data, dict):
        return [], None
    items: list[dict[str, Any]] = []
    for issue in data.get("items", []):
        title = clean_text(issue.get("title") or "", 140)
        html_url = issue.get("html_url") or ""
        if not title or not target_matches(target, title, html_url):
            continue
        comments = int(issue.get("comments") or 0)
        reactions = int((issue.get("reactions") or {}).get("total_count") or 0)
        created = str(issue.get("created_at") or "")[:10]
        year = int(created[:4]) if created[:4].isdigit() else None
        mult = _recency_multiplier(year)
        items.append(
            {
                "source": "GitHub",
                "title": title,
                "url": html_url,
                "comments_url": issue.get("comments_url") or "",
                "engagement": (reactions * 3 + comments) * mult,
                "meta": f"{reactions} reactions / {comments} comments / {created or 'unknown'}",
                "snippet": clean_text(issue.get("body") or ""),
            }
        )
    return items, None


def _query_stackexchange(
    target: str,
    limit: int,
    site: str,
    source_label: str,
    since_year: int = 2024,
) -> tuple[list[dict[str, Any]], str | None]:
    since_epoch = int(datetime(since_year, 1, 1, tzinfo=timezone.utc).timestamp())
    params = urllib.parse.urlencode(
        {
            "order": "desc",
            "sort": "votes",
            "title": target,
            "site": site,
            "fromdate": since_epoch,
            "pagesize": max(limit * 2, 15),
        }
    )
    url = f"https://api.stackexchange.com/2.3/search/advanced?{params}"
    try:
        data = fetch_json(url)
    except Exception as exc:
        return [], f"{source_label} error: {exc}"

    if not isinstance(data, dict):
        return [], None
    items: list[dict[str, Any]] = []
    for q in data.get("items", []):
        title = clean_text(q.get("title") or "", 140)
        tags = " ".join(q.get("tags") or [])
        if not title or not target_matches(target, title, tags):
            continue
        score = int(q.get("score") or 0)
        answers = int(q.get("answer_count") or 0)
        views = int(q.get("view_count") or 0)
        cdate = int(q.get("creation_date") or 0)
        dt_str = datetime.fromtimestamp(cdate, tz=timezone.utc).strftime("%Y-%m-%d") if cdate else "unknown"
        items.append(
            {
                "source": source_label,
                "title": title,
                "url": q.get("link") or "",
                "engagement": score * 2 + answers * 3,
                "meta": f"{score} votes / {answers} answers / {views} views / {dt_str}",
                "snippet": f"Tags: {tags}" if tags else "",
            }
        )
    return items, None


def mine_stackexchange(target: str, limit: int, since_year: int = 2024) -> tuple[list[dict[str, Any]], str | None]:
    return _query_stackexchange(target, limit, site="stackoverflow", source_label="StackOverflow", since_year=since_year)


def mine_b2b_webapps(target: str, limit: int, since_year: int = 2024) -> tuple[list[dict[str, Any]], str | None]:
    return _query_stackexchange(target, limit, site="webapps", source_label="B2B-WebApps", since_year=since_year)


SOURCE_MINERS = {
    "hn": mine_hn,
    "github": mine_github,
    "stackoverflow": mine_stackexchange,
    "b2b": mine_b2b_webapps,
}


def scan_existing_supply(target: str, items: list[dict[str, Any]]) -> list[str]:
    """Fetch top existing OSS repos for target and scan issue comments for existing workarounds."""
    top_repos: list[str] = []
    repo_q = urllib.parse.urlencode(
        {"q": f"{target} extension OR plugin OR sync", "sort": "stars", "order": "desc", "per_page": 3}
    )
    try:
        rdata = fetch_json(f"https://api.github.com/search/repositories?{repo_q}")
        if isinstance(rdata, dict):
            for repo in rdata.get("items", [])[:3]:
                top_repos.append(f"{repo.get('full_name')} ({repo.get('stargazers_count', 0)}*)")
    except Exception:
        pass

    for item in items:
        if item.get("source") != "GitHub":
            continue
        comments_url = item.pop("comments_url", "")
        if not comments_url:
            m = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)", item.get("url", ""))
            if m:
                comments_url = f"https://api.github.com/repos/{m.group(1)}/issues/{m.group(2)}/comments"
        if not comments_url:
            continue
        sep = "&" if "?" in comments_url else "?"
        try:
            comments = fetch_json(f"{comments_url}{sep}per_page=8")
        except Exception:
            continue
        if not isinstance(comments, list):
            continue

        matched_hints: list[str] = []
        linked_repos: list[str] = []
        for c in comments:
            body = str(c.get("body") or "")
            lower = body.lower()
            if any(h in lower for h in WORKAROUND_HINTS):
                matched_hints.append(clean_text(body, 110))
            for repo_link in re.findall(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", body):
                if repo_link not in linked_repos:
                    linked_repos.append(repo_link)

        supply: dict[str, Any] = {}
        if linked_repos:
            supply["linked_repos"] = linked_repos[:3]
        if matched_hints:
            supply["comment_signals"] = matched_hints[:2]
        if supply:
            item["existing_supply"] = supply

    return top_repos


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


def format_markdown(
    target: str,
    items: list[dict[str, Any]],
    warnings: list[str],
    existing_repos: list[str] | None = None,
) -> str:
    lines = [f"### Pain Signals Digest: `{target}` ({len(items)} items)"]
    if existing_repos:
        lines.append(f"> Existing OSS Supply (`{target}`): {', '.join(existing_repos)}")
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
        supply = item.get("existing_supply")
        if supply:
            parts: list[str] = []
            if supply.get("linked_repos"):
                parts.append("Repos: " + ", ".join(supply["linked_repos"]))
            if supply.get("comment_signals"):
                parts.append("Comments: " + " | ".join(supply["comment_signals"]))
            lines.append(f"   - *Existing Supply Check*: {'; '.join(parts)}")
    return "\n".join(lines)


def mine_for_target(
    target: str,
    source: str,
    limit: int,
    since_year: int = 2024,
    check_existing: bool = False,
) -> dict[str, Any]:
    sources = list(SOURCE_MINERS.keys()) if source == "all" else [source]
    all_items: list[dict[str, Any]] = []
    warnings: list[str] = []

    for src in sources:
        items, err = SOURCE_MINERS[src](target, limit, since_year=since_year)
        all_items.extend(items)
        if err:
            warnings.append(err)

    ranked = deduplicate_and_rank(all_items, max(1, limit), balance_sources=(source == "all"))
    existing_repos: list[str] = []
    if check_existing and ranked:
        existing_repos = scan_existing_supply(target, ranked)
    for it in ranked:
        it.pop("comments_url", None)
    return {"target": target, "warnings": warnings, "existing_repos": existing_repos, "items": ranked}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mine recent software pain signals from HN, GitHub, and Stack Exchange with supply checks."
    )
    parser.add_argument("--target", help="Single target software or niche (e.g., notion)")
    parser.add_argument("--targets", help="Comma-separated targets (e.g., notion,linear,vscode)")
    parser.add_argument(
        "--source", choices=["all", "hn", "github", "stackoverflow", "b2b"], default="all", help="Signal source"
    )
    parser.add_argument("--since-year", type=int, default=2024, help="Only mine items created on/after Jan 1 of year")
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Scan GitHub issue comments and top OSS repos for existing workarounds/competitors",
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

    results = [
        mine_for_target(
            t,
            args.source,
            args.limit,
            since_year=args.since_year,
            check_existing=args.check_existing,
        )
        for t in targets
    ]

    if args.format == "json":
        payload: Any = results[0] if len(results) == 1 and not args.targets else {"targets": results}
        print(json.dumps(payload, indent=2))
    else:
        print(
            "\n\n".join(
                format_markdown(r["target"], r["items"], r["warnings"], r.get("existing_repos"))
                for r in results
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
