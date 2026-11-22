#!/usr/bin/env python3
"""Submit all active GitHub Pages sitemap URLs to IndexNow (Bing, DuckDuckGo, Yandex, AI Search)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOCS_DIR = REPO_ROOT / "docs"
SITE_BASE_URL = "https://domstijn.github.io/friction-killer-suite"
SITE_HOST = "domstijn.github.io"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def find_key_file(docs_dir: Path) -> tuple[str, Path]:
    """Locate the docs/fk-indexnow-*.txt file and return (key, path)."""
    matches = sorted(docs_dir.glob("fk-indexnow-*.txt"))
    if not matches:
        raise FileNotFoundError(f"No fk-indexnow-*.txt key file found in {docs_dir}")
    key_path = matches[0]
    key = key_path.read_text(encoding="utf-8").strip()
    if key_path.name != f"{key}.txt":
        raise ValueError(f"Key file name {key_path.name} does not match content {key!r}")
    return key, key_path


def load_sitemap_urls(sitemap_path: Path) -> list[str]:
    """Extract all <loc> URLs from sitemap.xml preserving document order."""
    if not sitemap_path.is_file():
        raise FileNotFoundError(f"Sitemap not found: {sitemap_path}")
    root = ET.fromstring(sitemap_path.read_text(encoding="utf-8"))
    urls: list[str] = []
    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            urls.append(elem.text.strip())
    if not urls:
        raise ValueError(f"No <loc> URLs found in {sitemap_path}")
    return urls


def verify_live_key(key_url: str, expected_key: str) -> None:
    """Confirm the key file is live over HTTPS before pinging IndexNow."""
    req = urllib.request.Request(key_url, headers={"User-Agent": "FrictionKiller-IndexNow/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace").strip()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Key verification failed at {key_url}: HTTP {exc.code} {body}") from exc
    if status != 200 or body != expected_key:
        raise RuntimeError(
            f"Unexpected key response at {key_url}: HTTP {status}, body={body!r}"
        )


def submit_indexnow(payload: dict[str, object], endpoint: str = INDEXNOW_ENDPOINT) -> tuple[int, str]:
    """POST the IndexNow payload and return (http_status, response_body)."""
    raw = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "FrictionKiller-IndexNow/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit sitemap URLs to IndexNow.")
    parser.add_argument("--docs-dir", default=str(DEFAULT_DOCS_DIR), help="GitHub Pages docs/ directory")
    parser.add_argument("--endpoint", default=INDEXNOW_ENDPOINT, help="IndexNow endpoint URL")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    key, key_path = find_key_file(docs_dir)
    urls = load_sitemap_urls(docs_dir / "sitemap.xml")
    key_location = f"{SITE_BASE_URL}/{key_path.name}"

    verify_live_key(key_location, key)

    payload = {
        "host": SITE_HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    status, body = submit_indexnow(payload, endpoint=args.endpoint)
    print(f"IndexNow POST {args.endpoint} -> HTTP {status} ({len(urls)} URLs)")
    if body.strip():
        print(f"Response: {body.strip()}")
    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(main())
