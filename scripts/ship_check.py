#!/usr/bin/env python3
"""Zero-touch Stage 2-4 verifier and distributable packager (.zip, .vsix, .whl)."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
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
    categories = html.escape(",".join(pkg.get("categories") or ["Other"]))
    vscode_engine = html.escape(str((pkg.get("engines") or {}).get("vscode") or "^1.85.0"))

    assets = [
        '    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>'
    ]
    if (proj_dir / "README.md").is_file():
        assets.append(
            '    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>'
        )
    assets_xml = "\n".join(assets)

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
        f"    <Categories>{categories}</Categories>\n"
        "    <GalleryFlags>Public</GalleryFlags>\n"
        "    <Properties>\n"
        f'      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{vscode_engine}" />\n'
        "    </Properties>\n"
        "  </Metadata>\n"
        "  <Installation>\n"
        '    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>\n'
        "  </Installation>\n"
        "  <Dependencies/>\n"
        "  <Assets>\n"
        f"{assets_xml}\n"
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
    has_init = False
    for path in sorted(src_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        rel = path.relative_to(src_dir).as_posix()
        if rel == "__init__.py":
            has_init = True
        entries.append((f"{dist_name}/{rel}", path.read_bytes()))
    if not has_init:
        entries.insert(0, (f"{dist_name}/__init__.py", b""))
    top_levels = [dist_name]

    metadata_txt = (
        "Metadata-Version: 2.1\n"
        f"Name: {pkg_name}\n"
        f"Version: {pkg_ver}\n"
        f"Summary: {summary}\n"
        f"Requires-Python: {req_py}\n"
    ).encode("utf-8")
    wheel_txt = (
        "Wheel-Version: 1.0\n"
        "Generator: friction-killer-ship-check (0.2.0)\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode("utf-8")

    entries.append((f"{dist_info}/METADATA", metadata_txt))
    entries.append((f"{dist_info}/WHEEL", wheel_txt))
    entries.append((f"{dist_info}/top_level.txt", ("\n".join(top_levels) + "\n").encode("utf-8")))

    scripts = proj_meta.get("scripts") or {}
    if isinstance(scripts, dict) and scripts:
        ep_lines = ["[console_scripts]"]
        for cmd, target in scripts.items():
            ns_target = target if target.startswith(f"{dist_name}.") else f"{dist_name}.{target}"
            ep_lines.append(f"{cmd} = {ns_target}")
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


def _find_chrome_binary() -> str | None:
    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac_chrome.is_file():
        return str(mac_chrome)
    for name in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _verify_wheel_artifact(whl_path: Path) -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(whl_path) as zf:
            zf.extractall(root)
        ep_files = list(root.glob("*.dist-info/entry_points.txt"))
        if not ep_files:
            return [f"{whl_path.name}: missing entry_points.txt inside wheel"]
        ep_text = ep_files[0].read_text(encoding="utf-8")
        cmd_target = None
        for line in ep_text.splitlines():
            if "=" in line and not line.strip().startswith("["):
                cmd_name, target = [p.strip() for p in line.split("=", 1)]
                cmd_target = (cmd_name, target)
                break
        if not cmd_target or ":" not in cmd_target[1]:
            return [f"{whl_path.name}: invalid [console_scripts] target in entry_points.txt"]
        cmd_name, mod_func = cmd_target
        mod_name, func_name = mod_func.split(":", 1)
        cache_dir = root / "cache"
        for extra_args in (["--help"], ["--pro", "--cache-dir", str(cache_dir)], ["--telemetry", "--cache-dir", str(cache_dir)]):
            runner = (
                f"import sys; sys.path.insert(0, {str(root)!r}); "
                f"import {mod_name} as m; "
                f"sys.argv = [{cmd_name!r}] + {extra_args!r}; "
                f"raise SystemExit(m.{func_name}())"
            )
            proc = subprocess.run([sys.executable, "-c", runner], capture_output=True, text=True)
            if proc.returncode != 0:
                errors.append(
                    f"{whl_path.name}: entrypoint {mod_func} {extra_args} exited {proc.returncode}: {proc.stderr or proc.stdout}"
                )
            elif extra_args == ["--help"] and len((proc.stdout or "").strip()) < 20:
                errors.append(f"{whl_path.name}: --help output unexpectedly empty")
    return errors


def _verify_vsix_artifact(vsix_path: Path) -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(vsix_path) as zf:
            zf.extractall(root)
        ext_dir = root / "extension"
        pkg_path = ext_dir / "package.json"
        if not pkg_path.is_file():
            return [f"{vsix_path.name}: missing extension/package.json"]
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        main_rel = str(pkg.get("main") or "").lstrip("./")
        main_path = ext_dir / main_rel
        if not main_path.is_file():
            return [f"{vsix_path.name}: missing entrypoint {main_rel}"]

        ws_dir = root / "workspace"
        (ws_dir / ".vscode").mkdir(parents=True)
        (ws_dir / ".vscode" / "workspace-lock.json").write_text(
            json.dumps({"required": ["esbenp.prettier-vscode"], "disabled": ["tabnine.tabnine-vscode"]}),
            encoding="utf-8",
        )
        (ws_dir / ".env").write_text('SDK_ROOT="/tmp/sdk"\n', encoding="utf-8")
        (ws_dir / "demo.code-workspace").write_text(
            json.dumps({"folders": [{"path": "${env:SDK_ROOT}/app"}]}),
            encoding="utf-8",
        )
        expected_cmds = [c["command"] for c in pkg.get("contributes", {}).get("commands", []) if c.get("command")]
        node_test = """
const assert = require("node:assert/strict");
const Module = require("node:module");
const path = require("node:path");

const extDir = process.argv[1];
const mainFile = process.argv[2];
const wsDir = process.argv[3];
const expectedCmds = JSON.parse(process.argv[4]);

const registered = new Map();
const messages = [];
const store = new Map();
const mockVscode = {
  workspace: { workspaceFolders: [{ uri: { fsPath: wsDir } }] },
  extensions: { all: [{ id: "tabnine.tabnine-vscode" }] },
  commands: {
    registerCommand(id, fn) {
      registered.set(id, fn);
      return { dispose() {} };
    },
  },
  window: {
    showInformationMessage(m) { messages.push(["info", m]); },
    showWarningMessage(m) { messages.push(["warn", m]); },
    showErrorMessage(m) { messages.push(["err", m]); },
    async showInputBox() { return ""; },
  },
};

const origLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === "vscode") return mockVscode;
  return origLoad.apply(this, arguments);
};

(async () => {
  const ext = require(path.join(extDir, mainFile));
  assert.equal(typeof ext.activate, "function", "Missing exports.activate");
  const ctx = {
    subscriptions: [],
    globalState: { get: (k) => store.get(k), update: async (k, v) => { store.set(k, v); } },
  };
  await ext.activate(ctx);
  for (const id of expectedCmds) {
    assert.ok(registered.has(id), "Unregistered command: " + id);
    if (!id.toLowerCase().includes("activate")) {
      await registered.get(id)();
    }
  }
  assert.ok(messages.length >= 1, "Expected VS Code UI notification on zero-arg command call");
  if (typeof ext.deactivate === "function") await ext.deactivate();
  console.log("OK: VSIX host load & zero-arg command verification passed");
})();
"""
        proc = subprocess.run(
            ["node", "-e", node_test, str(ext_dir), main_rel, str(ws_dir), json.dumps(expected_cmds)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            errors.append(f"{vsix_path.name}: VS Code host simulation failed: {proc.stderr or proc.stdout}")
    return errors


def _verify_chrome_mv3_artifact(proj_dir: Path, zip_path: Path) -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(root)
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        paths_to_check: list[str] = []
        sw = manifest.get("background", {}).get("service_worker")
        if sw:
            paths_to_check.append(sw)
        popup = manifest.get("action", {}).get("default_popup")
        if popup:
            paths_to_check.append(popup)
        for cs in manifest.get("content_scripts", []):
            paths_to_check.extend(cs.get("js", []))
        paths_to_check.extend((manifest.get("icons") or {}).values())

        for rel in paths_to_check:
            p = root / rel
            if not p.is_file() or p.stat().st_size == 0:
                errors.append(f"{zip_path.name}: missing or empty manifest asset '{rel}'")

        for js_file in (root / "src").rglob("*.js") if (root / "src").is_dir() else []:
            chk = subprocess.run(["node", "--check", str(js_file)], capture_output=True, text=True)
            if chk.returncode != 0:
                errors.append(f"{zip_path.name}: JS syntax check failed for {js_file.name}: {chk.stderr}")

        shot = proj_dir / "launch" / "screenshot1280x800.png"
        if shot.is_file():
            if shot.stat().st_size < 40000:
                errors.append(
                    f"{shot.name}: file size {shot.stat().st_size}B < 40000B (risk of blank/wireframe CWS Red Potassium)"
                )
            if shutil.which("sips"):
                sips = subprocess.run(
                    ["sips", "-g", "pixelWidth", "-g", "pixelHeight", "-g", "hasAlpha", str(shot)],
                    capture_output=True,
                    text=True,
                )
                out = sips.stdout or ""
                if "pixelWidth: 1280" not in out or "pixelHeight: 800" not in out or "hasAlpha: no" not in out:
                    errors.append(f"{shot.name}: must be 1280x800 without alpha (got: {out.strip()})")

        chrome_bin = _find_chrome_binary()
        content_js = root / "src" / "content.js"
        if chrome_bin and content_js.is_file():
            fixture = root / "notion_dom_fixture.html"
            fixture.write_text(
                "<!DOCTYPE html><html><head><title>Mobile PRD | Notion</title></head><body>"
                '<div class="notion-page-block"><h1>Mobile PRD</h1></div>'
                '<div data-block-id="b1" class="notion-sub_header-block"><h2>API Layer</h2></div>'
                '<div data-block-id="b2" class="notion-to_do-block"><div role="checkbox" aria-checked="false"></div>Ship guard</div>'
                f'<script>{content_js.read_text(encoding="utf-8")}</script>'
                "</body></html>",
                encoding="utf-8",
            )
            dom_proc = subprocess.run(
                [chrome_bin, "--headless", "--disable-gpu", "--dump-dom", f"file://{fixture}"],
                capture_output=True,
                text=True,
            )
            if dom_proc.returncode != 0 or 'id="linearbridge-bar"' not in (dom_proc.stdout or ""):
                errors.append(
                    f"{zip_path.name}: headless Chromium DOM test failed to inject #linearbridge-bar on Notion fixture"
                )
    return errors


def verify_packaged_artifacts(proj_dir: Path, slug: str, artifacts: list[Path]) -> list[str]:
    """Independently execute & validate built distributable packages (.whl, .vsix, MV3 .zip)."""
    errors: list[str] = []
    for art in artifacts:
        if art.suffix == ".whl":
            errors.extend(_verify_wheel_artifact(art))
        elif art.suffix == ".vsix":
            errors.extend(_verify_vsix_artifact(art))
        elif art.suffix == ".zip" and (proj_dir / "manifest.json").is_file():
            errors.extend(_verify_chrome_mv3_artifact(proj_dir, art))
    return errors


def check_project(proj_dir: Path, args: argparse.Namespace) -> int:
    slug = proj_dir.name
    artifact_errors = check_artifacts(proj_dir)
    passed_tests, test_errors = run_tests(proj_dir)
    pkg_errors: list[str] = []
    packaged: list[Path] = []

    if not (artifact_errors or test_errors) and args.package:
        packaged = build_package(proj_dir, slug, args.version)
        pkg_errors = verify_packaged_artifacts(proj_dir, slug, packaged)

    all_errors = artifact_errors + test_errors + pkg_errors
    print(f"ShipCheck [{slug}]: {len(passed_tests)} test(s) passed, {len(all_errors)} error(s).")
    for t in passed_tests:
        print(f"  PASS: {t}")
    for err in all_errors:
        print(f"  FAIL: {err}", file=sys.stderr)
    if all_errors:
        return 1
    for artifact in packaged:
        print(f"  PACKAGED & E2E-VERIFIED: {artifact}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify project specs/launch docs, execute tests, and optionally build & E2E-verify packages."
    )
    parser.add_argument("--slug", help="Project slug under projects/")
    parser.add_argument("--all", action="store_true", help="Verify (and optionally package) every project under projects/")
    parser.add_argument("--package", action="store_true", help="Package and E2E-verify distributables under dist/")
    parser.add_argument("--version", default="0.1.0", help="Package version string (default: 0.1.0)")
    parser.add_argument("--projects-dir", default=str(DEFAULT_PROJECTS_DIR), help="Parent projects directory")
    args = parser.parse_args()

    if not args.all and not args.slug:
        parser.error("Provide --slug or --all")

    projects_dir = Path(args.projects_dir)
    if args.all:
        targets = sorted(
            p for p in projects_dir.iterdir() if p.is_dir() and not p.name.startswith(".") and (p / "SPEC.md").is_file()
        )
        if not targets:
            print(f"Error: No projects found under {projects_dir}", file=sys.stderr)
            return 1
        rc = 0
        for proj_dir in targets:
            if check_project(proj_dir, args) != 0:
                rc = 1
        return rc

    proj_dir = projects_dir / args.slug
    if not proj_dir.is_dir():
        print(f"Error: Project directory not found: {proj_dir}", file=sys.stderr)
        return 1
    return check_project(proj_dir, args)


if __name__ == "__main__":
    raise SystemExit(main())
