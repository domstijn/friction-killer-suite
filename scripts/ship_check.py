#!/usr/bin/env python3
"""Zero-touch Stage 2-4 verifier and distributable packager for friction-killer projects."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROJECTS_DIR = REPO_ROOT / "projects"

FORBIDDEN_PLACEHOLDERS = [
    "<TITLE>",
    "<SLUG>",
    "<ECOSYSTEM>",
    "<PROVIDER>",
    "<HOST_SOFTWARE>",
    "<TAGLINE>",
    "<PAIN_SUMMARY>",
    "<PRO_PRICE>",
]

ROOT_MANIFEST_FILES = ("manifest.json", "package.json", "pyproject.toml", "README.md")
EXCLUDED_DIR_NAMES = {"__pycache__", "tests", "launch", "dist", ".git"}
EXCLUDED_FILE_NAMES = {".DS_Store"}


def check_ecosystem_manifest(proj_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = proj_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("manifest_version") != 3:
                errors.append("manifest.json must declare manifest_version == 3")
            if not isinstance(manifest.get("permissions"), list):
                errors.append("manifest.json must declare a permissions list")
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid manifest.json: {exc}")

    pkg_path = proj_dir / "package.json"
    if pkg_path.is_file():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            if not pkg.get("engines", {}).get("vscode"):
                errors.append("package.json missing engines.vscode for VS Code/IDE extension packaging")
            commands = pkg.get("contributes", {}).get("commands")
            if not isinstance(commands, list) or len(commands) == 0:
                errors.append("package.json missing non-empty contributes.commands list")
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid package.json: {exc}")

    pyproject_path = proj_dir / "pyproject.toml"
    if pyproject_path.is_file():
        pyproject_text = pyproject_path.read_text(encoding="utf-8", errors="replace")
        if "[project.scripts]" not in pyproject_text:
            errors.append("pyproject.toml missing [project.scripts] console entrypoint")

    return errors


def check_artifacts(proj_dir: Path) -> list[str]:
    errors: list[str] = []
    required_docs = [
        proj_dir / "SPEC.md",
        proj_dir / "launch" / "landing.html",
        proj_dir / "launch" / "LAUNCH_KIT.md",
    ]
    for doc in required_docs:
        if not doc.exists():
            errors.append(f"Missing required artifact: {doc.relative_to(proj_dir)}")
            continue
        text = doc.read_text(encoding="utf-8", errors="replace")
        found = [p for p in FORBIDDEN_PLACEHOLDERS if p in text]
        if found:
            errors.append(
                f"Unreplaced placeholders in {doc.relative_to(proj_dir)}: {', '.join(found)}"
            )
    errors.extend(check_ecosystem_manifest(proj_dir))
    return errors


def run_tests(proj_dir: Path) -> tuple[list[str], list[str]]:
    tests_dir = proj_dir / "tests"
    if not tests_dir.exists():
        return [], [f"Missing tests directory: {tests_dir}"]

    test_files = sorted(
        {p for pattern in ("test_*.py", "*_test.py") for p in tests_dir.glob(pattern) if p.is_file()}
    )
    if not test_files:
        return [], [f"No test_*.py or *_test.py files found in {tests_dir}"]

    passed: list[str] = []
    errors: list[str] = []
    for test_file in test_files:
        rel = str(test_file.relative_to(proj_dir))
        proc = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=str(proj_dir),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            err_detail = (proc.stderr or proc.stdout or "").strip()
            errors.append(f"Test failed ({rel}, exit {proc.returncode}): {err_detail}")
        else:
            passed.append(rel)
    return passed, errors


def build_package(proj_dir: Path, slug: str, version: str) -> Path:
    dist_dir = proj_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dist_dir / f"{slug}-v{version}.zip"

    files_to_pack: list[Path] = []
    for fname in ROOT_MANIFEST_FILES:
        candidate = proj_dir / fname
        if candidate.is_file():
            files_to_pack.append(candidate)

    src_dir = proj_dir / "src"
    if src_dir.is_dir():
        for path in sorted(src_dir.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_DIR_NAMES for part in path.relative_to(proj_dir).parts):
                continue
            if path.name in EXCLUDED_FILE_NAMES or path.suffix == ".pyc":
                continue
            files_to_pack.append(path)

    if not files_to_pack:
        raise RuntimeError(f"No distributable files found in {proj_dir}")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files_to_pack:
            zf.write(file_path, arcname=str(file_path.relative_to(proj_dir)))

    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify project specs/launch docs, execute tests, and optionally build release zip."
    )
    parser.add_argument("--slug", required=True, help="Project slug under projects/")
    parser.add_argument("--package", action="store_true", help="Package distributable zip under dist/")
    parser.add_argument("--version", default="0.1.0", help="Package version string (default: 0.1.0)")
    parser.add_argument("--projects-dir", default=str(DEFAULT_PROJECTS_DIR), help="Parent projects directory")
    args = parser.parse_args()

    proj_dir = Path(args.projects_dir) / args.slug
    if not proj_dir.is_dir():
        print(f"Error: Project directory not found: {proj_dir}", file=sys.stderr)
        return 1

    artifact_errors = check_artifacts(proj_dir)
    passed_tests, test_errors = run_tests(proj_dir)
    all_errors = artifact_errors + test_errors

    print(f"ShipCheck [{args.slug}]: {len(passed_tests)} test(s) passed, {len(all_errors)} error(s).")
    for t in passed_tests:
        print(f"  PASS: {t}")
    for err in all_errors:
        print(f"  FAIL: {err}", file=sys.stderr)

    if all_errors:
        return 1

    if args.package:
        zip_path = build_package(proj_dir, args.slug, args.version)
        print(f"  PACKAGED: {zip_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
