#!/usr/bin/env python3
"""DockerVolumeForge CLI: Docker volume rename/clone, Compose v3 extends flattener & multi-tag batcher."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forge_engine import build_multi_tag_push, flatten_compose_extends, plan_volume_migration
from license_client import get_telemetry, require_pro_feature, verify_license

APP_SLUG = "docker-volume-compose-tool"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_VfWC3UQKBawhsd,prod_VeW6IYwGyYJkPv"


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cache-dir", default=argparse.SUPPRESS, help="Optional custom license cache directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DockerVolumeForge: Atomic Docker volume rename/clone & Compose v3 extends flattener."
    )
    parser.add_argument("--activate", help="Activate a Stripe Pro license key")
    parser.add_argument("--pro", action="store_true", help="Check current Pro license status")
    parser.add_argument("--telemetry", action="store_true", help="Print local paywall/activation telemetry counts")
    parser.add_argument("--cache-dir", default=None, help="Optional custom license cache directory")

    sub = parser.add_subparsers(dest="command")

    p_vol = sub.add_parser("rename-volume", help="Plan or execute container-safe Docker volume rename/clone")
    p_vol.add_argument("--old", required=True, help="Existing Docker volume name")
    p_vol.add_argument("--new", required=True, help="Destination Docker volume name")
    p_vol.add_argument("--mode", choices=["rename", "clone"], default="rename", help="Migration mode")
    p_vol.add_argument("--containers", default="", help="Comma-separated attached container names (Pro)")
    p_vol.add_argument("--execute", action="store_true", help="Execute Docker commands locally (Pro)")
    _add_common_flags(p_vol)

    p_cmp = sub.add_parser("flatten-compose", help="Resolve Compose extends into stack-deployable v3 YAML")
    p_cmp.add_argument("--input", required=True, help="Path to compose YAML/JSON file")
    p_cmp.add_argument("--base-files", nargs="*", default=[], help="Optional extra base compose file paths")
    p_cmp.add_argument("--output", help="Optional destination path to write flattened YAML")
    p_cmp.add_argument("--yaml", action="store_true", help="Print raw flattened YAML instead of JSON summary")
    _add_common_flags(p_cmp)

    p_push = sub.add_parser("push-tags", help="Generate or run multi-tag docker tag + push batch (Pro)")
    p_push.add_argument("--repo", required=True, help="Target image repository (e.g. ghcr.io/acme/api)")
    p_push.add_argument("--tags", required=True, help="Comma-separated destination tags (e.g. 1.2.0,1.2,latest)")
    p_push.add_argument("--source-tag", default="latest", help="Source local tag to re-tag from")
    p_push.add_argument("--execute", action="store_true", help="Execute docker tag & push commands")
    _add_common_flags(p_push)

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
        status = require_pro_feature("docker_volume_and_compose_pro", app_slug=APP_SLUG, cache_dir=args.cache_dir)
        print(json.dumps(status, indent=2))
        return 0

    if not args.command:
        parser.print_help()
        return 0

    pro_status = require_pro_feature("docker_volume_and_compose_pro", app_slug=APP_SLUG, cache_dir=args.cache_dir)
    is_pro = bool(pro_status.get("allowed"))

    if args.command == "rename-volume":
        containers = [c.strip() for c in args.containers.split(",") if c.strip()]
        res = plan_volume_migration(
            args.old,
            args.new,
            mode=args.mode,
            attached_containers=containers,
            execute=args.execute,
            is_pro=is_pro,
        )
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 2

    if args.command == "flatten-compose":
        input_path = Path(args.input)
        base_map: dict[str, str] = {}
        for bf in args.base_files:
            bp = Path(bf)
            raw = bp.read_text(encoding="utf-8")
            base_map[bf] = raw
            base_map[bp.name] = raw
        res = flatten_compose_extends(
            input_path.read_text(encoding="utf-8"),
            base_files=base_map,
            is_pro=is_pro,
        )
        if res.get("ok") and args.output:
            Path(args.output).write_text(res["flattened_yaml"], encoding="utf-8")
        if args.yaml and res.get("ok"):
            print(res["flattened_yaml"], end="")
        else:
            print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 2

    if args.command == "push-tags":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        res = build_multi_tag_push(
            args.repo,
            tags=tags,
            source_tag=args.source_tag,
            is_pro=is_pro,
            execute=args.execute,
        )
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 2

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
