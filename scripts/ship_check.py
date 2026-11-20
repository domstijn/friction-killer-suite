#!/usr/bin/env python3
"""Zero-touch Stage 2-4 verifier and distributable packager (.zip, .vsix, .whl)."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import subprocess
import sys
import tomllib
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
            elif "scripting" in manifest.get("permissions", []):
                src_dir = proj_dir / "src"
                uses_scripting = src_dir.is_dir() and any(
                    "chrome.scripting" in p.read_text(encoding="utf-8", errors="replace")
                    for p in src_dir.rglob("*.js")
                )
                if not uses_scripting:
                    errors.append(
                        "manifest.json declares 'scripting' permission without chrome.scripting usage in src/ (CWS Purple Potassium)"
                    )
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


def collect_dist_files(proj_dir: Path) -> list[Path]:
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
    return files_to_pack


def build_package(proj_dir: Path, slug: str, version: str) -> list[Path]:
    dist_dir = proj_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dist_dir / f"{slug}-v{version}.zip"

    files_to_pack = collect_dist_files(proj_dir)
    if not files_to_pack:
        raise RuntimeError(f"No distributable files found in {proj_dir}")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files_to_pack:
            zf.write(file_path, arcname=str(file_path.relative_to(proj_dir)))

    artifacts = [zip_path]

    pkg_path = proj_dir / "package.json"
    if pkg_path.is_file():
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        if pkg.get("engines", {}).get("vscode"):
            artifacts.append(build_vsix_package(proj_dir, slug, version, pkg, files_to_pack))

    pyproject_path = proj_dir / "pyproject.toml"
    if pyproject_path.is_file():
        artifacts.append(build_wheel_package(proj_dir, version, pyproject_path))

    return artifacts


def build_vsix_package(
    proj_dir: Path,
    slug: str,
    version: str,
    pkg: dict,
    files_to_pack: list[Path],
) -> Path:
    vsix_path = proj_dir / "dist" / f"{slug}-{version}.vsix"
    ext_id = html.escape(str(pkg.get("name") or slug))
    publisher = html.escape(str(pkg.get("publisher") or "friction-killer"))
    display_name = html.escape(str(pkg.get("displayName") or slug))
    description = html.escape(str(pkg.get("description") or display_name))
    ver = html.escape(str(pkg.get("version") or version))

    content_types = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension=".json" ContentType="application/json"/>\n'
        '  <Default Extension=".js" ContentType="application/javascript"/>\n'
        '  <Default Extension=".md" ContentType="text/markdown"/>\n'
        '  <Default Extension=".png" ContentType="image/png"/>\n'
        '  <Default Extension=".vsixmanifest" ContentType="text/xml"/>\n'
        '</Types>\n'
    )
    vsix_manifest = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">\n'
        "  <Metadata>\n"
        f'    <Identity Language="en-US" Id="{ext_id}" Version="{ver}" Publisher="{publisher}"/>\n'
        f"    <DisplayName>{display_name}</DisplayName>\n"
        f'    <Description xml:space="preserve">{description}</Description>\n'
        "  </Metadata>\n"
        "  <Installation>\n"
        '    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>\n'
        "  </Installation>\n"
        "  <Dependencies/>\n"
        "  <Assets>\n"
        '    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>\n'
        "  </Assets>\n"
        "</PackageManifest>\n"
    )

    with zipfile.ZipFile(vsix_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("extension.vsixmanifest", vsix_manifest)
        for file_path in files_to_pack:
            zf.write(file_path, arcname=f"extension/{file_path.relative_to(proj_dir).as_posix()}")

    return vsix_path


def build_wheel_package(proj_dir: Path, version: str, pyproject_path: Path) -> Path:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    proj_meta = data.get("project") or {}
    pkg_name = str(proj_meta.get("name") or proj_dir.name)
    pkg_ver = str(proj_meta.get("version") or version)
    summary = str(proj_meta.get("description") or pkg_name)
    req_py = str(proj_meta.get("requires-python") or ">=3.10")
    dist_name = re.sub(r"[-_.]+", "_", pkg_name)
    whl_path = proj_dir / "dist" / f"{dist_name}-{pkg_ver}-py3-none-any.whl"
    dist_info = f"{dist_name}-{pkg_ver}.dist-info"

    src_dir = proj_dir / "src"
    entries: list[tuple[str, bytes]] = []
    top_levels: list[str] = []
    for path in sorted(src_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = path.relative_to(src_dir).as_posix()
        entries.append((rel, path.read_bytes()))
        if path.suffix == ".py" and "/" not in rel and path.stem != "__init__":
            top_levels.append(path.stem)

    metadata_txt = (
        "Metadata-Version: 2.1\n"
        f"Name: {pkg_name}\n"
        f"Version: {pkg_ver}\n"
        f"Summary: {summary}\n"
        f"Requires-Python: {req_py}\n"
    ).encode("utf-8")
    wheel_txt = (
        "Wheel-Version: 1.0\n"
        "Generator: friction-killer-ship-check (0.1.0)\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode("utf-8")

    entries.append((f"{dist_info}/METADATA", metadata_txt))
    entries.append((f"{dist_info}/WHEEL", wheel_txt))
    if top_levels:
        entries.append((f"{dist_info}/top_level.txt", ("\n".join(top_levels) + "\n").encode("utf-8")))

    scripts = proj_meta.get("scripts") or {}
    if isinstance(scripts, dict) and scripts:
        ep_lines = ["[console_scripts]"] + [f"{cmd} = {target}" for cmd, target in scripts.items()]
        entries.append((f"{dist_info}/entry_points.txt", ("\n".join(ep_lines) + "\n").encode("utf-8")))

    record_lines: list[str] = []
    with zipfile.ZipFile(whl_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, payload in entries:
            zf.writestr(arcname, payload)
            digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")
            record_lines.append(f"{arcname},sha256={digest},{len(payload)}")
        record_lines.append(f"{dist_info}/RECORD,,")
        zf.writestr(f"{dist_info}/RECORD", ("\n".join(record_lines) + "\n").encode("utf-8"))

    return whl_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify project specs/launch docs, execute tests, and optionally build release packages."
    )
    parser.add_argument("--slug", required=True, help="Project slug under projects/")
    parser.add_argument("--package", action="store_true", help="Package distributables under dist/")
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
        for artifact in build_package(proj_dir, args.slug, args.version):
            print(f"  PACKAGED: {artifact}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
