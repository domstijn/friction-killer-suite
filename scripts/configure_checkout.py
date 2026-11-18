#!/usr/bin/env python3
"""Inject live checkout URLs and license product IDs, rebuild zips, and refresh launch_hub/ & docs/."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECTS_DIR = REPO_ROOT / "projects"
SHIP_CHECK_SCRIPT = REPO_ROOT / "scripts" / "ship_check.py"
BUILD_PORTFOLIO_SCRIPT = REPO_ROOT / "scripts" / "build_portfolio.py"


def update_landing_html(landing_path: Path, checkout_url: str) -> int:
    if not landing_path.is_file():
        raise FileNotFoundError(f"Landing page not found: {landing_path}")
    html = landing_path.read_text(encoding="utf-8")
    count = 0

    if "#CHECKOUT_URL_HERE" in html:
        count += html.count("#CHECKOUT_URL_HERE")
        html = html.replace("#CHECKOUT_URL_HERE", checkout_url)

    pattern = re.compile(
        r'(<a\s+[^>]*?href=")([^"]+)("[^>]*?class="[^"]*lemonsqueezy-button[^"]*")',
        re.IGNORECASE,
    )

    def _repl(match: re.Match[str]) -> str:
        nonlocal count
        if match.group(2) != checkout_url:
            count += 1
        return f"{match.group(1)}{checkout_url}{match.group(3)}"

    html = pattern.sub(_repl, html)
    landing_path.write_text(html, encoding="utf-8")
    return count


def update_src_product_id(src_dir: Path, checkout_url: str, product_id: str) -> list[str]:
    updated_files: list[str] = []
    if not src_dir.is_dir():
        return updated_files

    for path in sorted(src_dir.rglob("*")):
        if not path.is_file() or path.suffix not in (".js", ".py"):
            continue
        text = path.read_text(encoding="utf-8")
        new_text = text
        new_text = re.sub(
            r"DEFAULT_PRODUCT_ID\s*=\s*None\b",
            f'DEFAULT_PRODUCT_ID = "{product_id}"',
            new_text,
        )
        new_text = re.sub(
            r"DEFAULT_PRODUCT_ID\s*=\s*null\b",
            f'DEFAULT_PRODUCT_ID = "{product_id}"',
            new_text,
        )
        new_text = re.sub(
            r"productId\s*:\s*null\b",
            f'productId: "{product_id}"',
            new_text,
        )
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            updated_files.append(path.name)

    cfg_path = src_dir / "checkout_config.json"
    cfg_path.write_text(
        json.dumps({"checkout_url": checkout_url, "product_id": product_id}, indent=2) + "\n",
        encoding="utf-8",
    )
    updated_files.append("checkout_config.json")
    return updated_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure live checkout URL & product ID and refresh packages + GitHub Pages storefront."
    )
    parser.add_argument("--slug", help="Project slug under projects/")
    parser.add_argument("--checkout-url", help="Live Lemon Squeezy / Polar / Gumroad checkout URL for --slug")
    parser.add_argument("--product-id", help="Optional provider product ID for strict license validation")
    parser.add_argument(
        "--bundle-product-id",
        help="Optional All-Access Bundle product ID so bundle keys also unlock this product",
    )
    parser.add_argument("--bundle-url", help="Optional live checkout URL for the $49 All-Access Bundle")
    parser.add_argument("--projects-dir", default=str(DEFAULT_PROJECTS_DIR), help="Parent projects directory")
    parser.add_argument("--skip-portfolio", action="store_true", help="Skip regenerating launch_hub/ and docs/")
    args = parser.parse_args()

    if not args.slug and not args.bundle_url:
        parser.error("Provide --slug (with --checkout-url) and/or --bundle-url")

    projects_dir = Path(args.projects_dir)
    if args.slug:
        if not args.checkout_url:
            parser.error("--checkout-url is required when --slug is set")
        proj_dir = projects_dir / args.slug
        if not proj_dir.is_dir():
            print(f"Error: Project directory not found: {proj_dir}", file=sys.stderr)
            return 1

        replaced = update_landing_html(proj_dir / "launch" / "landing.html", args.checkout_url)
        print(f"Updated landing.html ({replaced} link(s) set to {args.checkout_url})")

        combined_product_id = None
        if args.product_id and args.bundle_product_id:
            combined_product_id = f"{args.product_id},{args.bundle_product_id}"
        elif args.product_id:
            combined_product_id = args.product_id
        elif args.bundle_product_id:
            combined_product_id = args.bundle_product_id

        if combined_product_id:
            touched = update_src_product_id(proj_dir / "src", args.checkout_url, combined_product_id)
            print(f"Updated src product config: {', '.join(touched)}")

        proc = subprocess.run(
            [
                sys.executable,
                str(SHIP_CHECK_SCRIPT),
                "--slug",
                args.slug,
                "--package",
                "--projects-dir",
                str(projects_dir),
            ],
            check=False,
        )
        if proc.returncode != 0:
            return proc.returncode

    if not args.skip_portfolio:
        cmd = [sys.executable, str(BUILD_PORTFOLIO_SCRIPT), "--projects-dir", str(projects_dir)]
        if args.bundle_url:
            cmd.extend(["--bundle-url", args.bundle_url])
        port_proc = subprocess.run(cmd, check=False)
        if port_proc.returncode != 0:
            return port_proc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
