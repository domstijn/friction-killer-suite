#!/usr/bin/env python3
"""Deterministic effectiveness & commercial potential evaluator for plugin/software ideas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure sibling import works regardless of working directory
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import pipeline_ctl  # noqa: E402

WEIGHTS = {
    "pain_severity": 0.20,
    "willingness_to_pay": 0.25,
    "solution_effectiveness": 0.15,
    "build_speed": 0.15,
    "distribution_clarity": 0.15,
    "platform_safety": 0.10,
}


def validate_score(name: str, val: float) -> float:
    num = float(val)
    if not (1.0 <= num <= 10.0):
        raise ValueError(f"Dimension '{name}' must be between 1 and 10 (got {val})")
    return num


def evaluate_idea(raw: dict[str, Any]) -> dict[str, Any]:
    dims = {k: validate_score(k, raw[k]) for k in WEIGHTS}

    composite = round(10.0 * sum(dims[k] * w for k, w in WEIGHTS.items()), 2)
    # Effectiveness & Feasibility (0-100): solution_effectiveness (40%), build_speed (35%), platform_safety (25%)
    effectiveness = round(
        10.0 * (0.40 * dims["solution_effectiveness"] + 0.35 * dims["build_speed"] + 0.25 * dims["platform_safety"]),
        2,
    )
    # Commercial Potential / Pie (0-100): willingness_to_pay (45%), pain_severity (35%), distribution_clarity (20%)
    commercial = round(
        10.0 * (0.45 * dims["willingness_to_pay"] + 0.35 * dims["pain_severity"] + 0.20 * dims["distribution_clarity"]),
        2,
    )

    kill_reasons: list[str] = []
    if dims["willingness_to_pay"] < 4:
        kill_reasons.append("willingness_to_pay < 4")
    if dims["platform_safety"] < 4:
        kill_reasons.append("platform_safety < 4")
    if dims["solution_effectiveness"] < 5:
        kill_reasons.append("solution_effectiveness < 5")

    if kill_reasons:
        verdict = f"NO-GO (Kill Switch Triggered: {', '.join(kill_reasons)})"
    elif composite >= 70.0:
        verdict = "GO"
    elif composite >= 50.0:
        verdict = "MAYBE"
    else:
        verdict = "NO-GO"

    return {
        "id": raw.get("id") or "unnamed-idea",
        "title": raw.get("title") or "Untitled Idea",
        "ecosystem": raw.get("ecosystem") or "unknown",
        "target_software": raw.get("target_software") or "unknown",
        "pain": raw.get("pain") or "",
        "solution": raw.get("solution") or "",
        "dimensions": dims,
        "effectiveness_score": effectiveness,
        "commercial_potential_score": commercial,
        "score": composite,
        "verdict": verdict,
    }


def format_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "| ID | Title | Ecosystem | Effectiveness | Commercial | Composite | Verdict |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :--- |",
    ]
    for r in results:
        lines.append(
            f"| `{r['id']}` | {r['title']} | {r['ecosystem']} | "
            f"{r['effectiveness_score']} | {r['commercial_potential_score']} | **{r['score']}** | {r['verdict']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score candidate software/plugin opportunities.")
    parser.add_argument("--json-file", help="Path to JSON file containing a candidate object or list of objects")
    parser.add_argument("--id", help="Slug ID")
    parser.add_argument("--title", help="Product title")
    parser.add_argument("--ecosystem", default="browser-extension", help="Target ecosystem")
    parser.add_argument("--target-software", default="Unknown", help="Host software")
    parser.add_argument("--pain", default="", help="Pain description")
    parser.add_argument("--solution", default="", help="Solution description")
    parser.add_argument("--pain-severity", type=float, help="1-10 score (weight 20%%)")
    parser.add_argument("--willingness-to-pay", type=float, help="1-10 score (weight 25%%)")
    parser.add_argument("--solution-effectiveness", type=float, help="1-10 score (weight 15%%)")
    parser.add_argument("--build-speed", type=float, help="1-10 score (weight 15%%)")
    parser.add_argument("--distribution-clarity", type=float, help="1-10 score (weight 15%%)")
    parser.add_argument("--platform-safety", type=float, help="1-10 score (weight 10%%)")
    parser.add_argument("--save", action="store_true", help="Save scored idea(s) into pipeline/state.json")
    parser.add_argument("--state-file", default=str(pipeline_ctl.DEFAULT_STATE_PATH), help="Path to state.json")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format")
    args = parser.parse_args()

    raw_items: list[dict[str, Any]] = []
    if args.json_file:
        loaded = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        raw_items = loaded if isinstance(loaded, list) else [loaded]
    else:
        required_dims = [
            args.pain_severity,
            args.willingness_to_pay,
            args.solution_effectiveness,
            args.build_speed,
            args.distribution_clarity,
            args.platform_safety,
        ]
        if any(v is None for v in required_dims):
            parser.error("Provide --json-file OR all 6 dimension flags (--pain-severity, --willingness-to-pay, etc.)")
        raw_items = [
            {
                "id": args.id or "candidate-idea",
                "title": args.title or "Candidate Idea",
                "ecosystem": args.ecosystem,
                "target_software": args.target_software,
                "pain": args.pain,
                "solution": args.solution,
                "pain_severity": args.pain_severity,
                "willingness_to_pay": args.willingness_to_pay,
                "solution_effectiveness": args.solution_effectiveness,
                "build_speed": args.build_speed,
                "distribution_clarity": args.distribution_clarity,
                "platform_safety": args.platform_safety,
            }
        ]

    evaluated = [evaluate_idea(item) for item in raw_items]
    evaluated.sort(key=lambda r: r["score"], reverse=True)

    if args.save:
        state_path = Path(args.state_file)
        state = pipeline_ctl.load_state(state_path)
        for item in evaluated:
            pipeline_ctl.upsert_idea(state, item)
        pipeline_ctl.save_state(state_path, state)

    if args.format == "json":
        print(json.dumps(evaluated[0] if len(evaluated) == 1 else evaluated, indent=2))
    else:
        print(format_markdown(evaluated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
