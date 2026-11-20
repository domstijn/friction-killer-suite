#!/usr/bin/env python3
"""ClaudeProfileSwitch CLI: multi-account & MCP profile switching + 5-hour JSONL quota guard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from license_client import get_telemetry, require_pro_feature, verify_license
from profile_manager import (
    audit_quota_burn,
    auto_switch_for_repo,
    list_profiles,
    save_profile,
    switch_profile,
)

APP_SLUG = "claude-profile-switcher"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_VfKeANX0phOIoi,prod_VeW6IYwGyYJkPv"

DEFAULT_CLAUDE_CONFIG = Path.home() / ".claude.json"
DEFAULT_MCP_CONFIG = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
DEFAULT_STORE_DIR = Path.home() / ".config" / APP_SLUG
DEFAULT_SESSIONS_DIR = Path.home() / ".claude" / "projects"


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cache-dir", default=argparse.SUPPRESS, help="Optional custom license cache directory")
    parser.add_argument("--store-dir", default=argparse.SUPPRESS, help="Profile storage directory")
    parser.add_argument("--claude-config", default=argparse.SUPPRESS, help="Path to ~/.claude.json")
    parser.add_argument("--mcp-config", default=argparse.SUPPRESS, help="Path to claude_desktop_config.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ClaudeProfileSwitch: Multi-Account, MCP Profile & Quota Guard for Claude Code."
    )
    parser.add_argument("--activate", help="Activate a Stripe Pro license key")
    parser.add_argument("--pro", action="store_true", help="Check current Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation telemetry counts")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")
    parser.add_argument("--store-dir", default=str(DEFAULT_STORE_DIR), help="Profile storage directory")
    parser.add_argument("--claude-config", default=str(DEFAULT_CLAUDE_CONFIG), help="Path to ~/.claude.json")
    parser.add_argument("--mcp-config", default=str(DEFAULT_MCP_CONFIG), help="Path to claude_desktop_config.json")

    sub = parser.add_subparsers(dest="command")

    p_save = sub.add_parser("save", help="Snapshot current Claude & MCP configs into a named profile")
    p_save.add_argument("--name", required=True, help="Profile name (e.g. work, personal, client-acme)")
    _add_common_flags(p_save)

    p_switch = sub.add_parser("switch", help="Switch active Claude & MCP configs to a saved profile")
    p_switch.add_argument("--name", required=True, help="Saved profile name")
    _add_common_flags(p_switch)

    p_list = sub.add_parser("list", help="List saved profiles and active profile")
    _add_common_flags(p_list)

    p_auto = sub.add_parser(
        "auto-switch",
        help="Switch to repo .claude-profile & inject ${ENV_VAR} MCP secrets (Pro)",
    )
    p_auto.add_argument("--repo-dir", default=".", help="Directory containing .claude-profile")
    _add_common_flags(p_auto)

    p_quota = sub.add_parser("quota", help="Audit 5-hour Claude Code JSONL token burn")
    p_quota.add_argument("--sessions-dir", default=str(DEFAULT_SESSIONS_DIR), help="Directory with JSONL logs")
    p_quota.add_argument("--window-hours", type=float, default=5.0, help="Rolling window length in hours")
    p_quota.add_argument("--budget", type=int, default=500000, help="Token budget for the window")
    p_quota.add_argument("--now-epoch", type=float, default=None, help="Optional reference UNIX epoch seconds")
    p_quota.add_argument("--csv", action="store_true", help="Print CSV report instead of JSON (Pro)")
    _add_common_flags(p_quota)

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
        status = require_pro_feature("unlimited_profiles_and_quota", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(status, indent=2))
        return 0

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "list":
        res = list_profiles(args.store_dir)
        print(json.dumps(res, indent=2))
        return 0

    if args.command == "switch":
        res = switch_profile(args.name, args.claude_config, args.mcp_config, args.store_dir)
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 2

    pro_status = require_pro_feature("unlimited_profiles_and_quota", app_slug=APP_SLUG, cache_dir=args.cache_dir)
    is_pro = bool(pro_status.get("allowed"))

    if args.command == "save":
        res = save_profile(
            args.name,
            args.claude_config,
            args.mcp_config,
            args.store_dir,
            is_pro=is_pro,
        )
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 2

    if args.command == "auto-switch":
        res = auto_switch_for_repo(
            args.repo_dir,
            args.claude_config,
            args.mcp_config,
            args.store_dir,
            is_pro=is_pro,
        )
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 2

    if args.command == "quota":
        res = audit_quota_burn(
            args.sessions_dir,
            window_hours=args.window_hours,
            window_token_budget=args.budget,
            now_epoch=args.now_epoch,
            is_pro=is_pro,
        )
        if args.csv:
            if not is_pro:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "blocked_by_tier": True,
                            "reason": "CSV quota burn export requires an active Pro license key.",
                        },
                        indent=2,
                    )
                )
                return 2
            print(res.get("csv_report", ""), end="")
            return 0 if res.get("ok") else 2
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
