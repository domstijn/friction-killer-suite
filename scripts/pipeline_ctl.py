#!/usr/bin/env python3
"""CLI tool to inspect and deterministically update pipeline/state.json."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = REPO_ROOT / "pipeline" / "state.json"
VALID_STAGES = [
    "IDLE",
    "STAGE_1_DISCOVERY",
    "STAGE_2_SPEC",
    "STAGE_3_BUILD",
    "STAGE_4_LAUNCH",
    "COMPLETED",
]


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def upsert_idea(state: dict[str, Any], idea: dict[str, Any]) -> dict[str, Any]:
    opportunities: list[dict[str, Any]] = state.setdefault("opportunities", [])
    existing_idx = next((i for i, item in enumerate(opportunities) if item.get("id") == idea["id"]), None)
    idea["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if existing_idx is not None:
        opportunities[existing_idx] = idea
    else:
        opportunities.append(idea)
    opportunities.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    return state


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state(Path(args.state_file))
    gates = state.get("gates", {})
    opps = state.get("opportunities", [])
    projects = state.get("projects", {})
    print(f"Stage: {state.get('current_stage', 'UNKNOWN')} | Mode: {state.get('mode', 'lean_gatekeeper')}")
    print(f"Active Project: {state.get('active_project') or 'None'}")
    print(
        f"Gates: Gate1(Idea/Spec)={gates.get('gate_1_idea_and_spec_approved', False)}, "
        f"Gate2(Launch)={gates.get('gate_2_launch_approved', False)}"
    )
    print(f"Opportunities: {len(opps)} | Projects: {len(projects)}")
    if opps:
        top = opps[:3]
        print("Top Scored Ideas:")
        for idx, item in enumerate(top, 1):
            print(
                f"  {idx}. [{item.get('id')}] {item.get('title')} "
                f"({item.get('ecosystem')}) — Score: {item.get('score')} {item.get('verdict', '')}".rstrip()
            )
    return 0


def cmd_add_idea(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file)
    state = load_state(state_path)
    idea = {
        "id": args.id,
        "title": args.title,
        "ecosystem": args.ecosystem,
        "target_software": args.target_software,
        "pain": args.pain,
        "solution": args.solution,
        "score": round(float(args.score), 2),
        "verdict": args.verdict,
    }
    upsert_idea(state, idea)
    save_state(state_path, state)
    print(f"Saved idea '{args.id}' (score={idea['score']}) -> {state_path.name}")
    return 0


def cmd_select_idea(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file)
    state = load_state(state_path)
    slug = args.id
    matched = next((o for o in state.get("opportunities", []) if o.get("id") == slug), None)

    state["active_project"] = slug
    state["current_stage"] = "STAGE_2_SPEC"
    state.setdefault("gates", {})["gate_1_idea_and_spec_approved"] = True

    projects = state.setdefault("projects", {})
    proj = projects.get(slug, {})
    proj.update(
        {
            "id": slug,
            "title": matched.get("title", slug) if matched else proj.get("title", slug),
            "ecosystem": matched.get("ecosystem", "unknown") if matched else proj.get("ecosystem", "unknown"),
            "target_software": matched.get("target_software", "") if matched else proj.get("target_software", ""),
            "status": "STAGE_2_SPEC",
            "selected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
    projects[slug] = proj
    save_state(state_path, state)
    print(f"Selected '{slug}'. Stage -> STAGE_2_SPEC. Gate 1 approved.")
    return 0


def cmd_set_stage(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file)
    state = load_state(state_path)
    state["current_stage"] = args.stage
    active = state.get("active_project")
    if active and active in state.get("projects", {}):
        state["projects"][active]["status"] = args.stage
    if args.stage == "COMPLETED":
        state.setdefault("gates", {})["gate_2_launch_approved"] = True
    save_state(state_path, state)
    print(f"Stage updated -> {args.stage}" + (f" (project: {active})" if active else ""))
    return 0


def cmd_reset_gates(args: argparse.Namespace) -> int:
    state_path = Path(args.state_file)
    state = load_state(state_path)
    state["gates"] = {
        "gate_1_idea_and_spec_approved": False,
        "gate_2_launch_approved": False,
    }
    if args.full:
        state["active_project"] = None
        state["current_stage"] = "IDLE"
        state["opportunities"] = []
    save_state(state_path, state)
    print("Gates reset" + (" (full state reset to IDLE)" if args.full else "") + ".")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage pipeline/state.json deterministically.")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_PATH), help="Path to state.json")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Show compact pipeline summary")
    p_status.set_defaults(func=cmd_status)

    p_add = sub.add_parser("add-idea", help="Add or update a scored opportunity")
    p_add.add_argument("--id", required=True, help="Slug ID")
    p_add.add_argument("--title", required=True, help="Short product title")
    p_add.add_argument("--ecosystem", required=True, help="Target ecosystem")
    p_add.add_argument("--target-software", required=True, help="Host software name")
    p_add.add_argument("--pain", required=True, help="Pain summary")
    p_add.add_argument("--solution", required=True, help="Proposed solution summary")
    p_add.add_argument("--score", required=True, type=float, help="Composite score (0-100)")
    p_add.add_argument("--verdict", default="", help="Optional GO/MAYBE/NO-GO verdict")
    p_add.set_defaults(func=cmd_add_idea)

    p_sel = sub.add_parser("select-idea", help="Select an idea and approve Gate 1")
    p_sel.add_argument("--id", required=True, help="Opportunity slug ID")
    p_sel.set_defaults(func=cmd_select_idea)

    p_stage = sub.add_parser("set-stage", help="Update current pipeline stage")
    p_stage.add_argument("--stage", required=True, choices=VALID_STAGES, help="Target stage")
    p_stage.set_defaults(func=cmd_set_stage)

    p_reset = sub.add_parser("reset-gates", help="Reset approval gates for a new cycle")
    p_reset.add_argument("--full", action="store_true", help="Also clear active_project, opportunities, and reset stage to IDLE")
    p_reset.set_defaults(func=cmd_reset_gates)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
