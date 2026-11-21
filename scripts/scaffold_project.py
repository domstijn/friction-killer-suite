#!/usr/bin/env python3
"""Scaffold a new friction-killer project with license gating, starter code, tests, and launch kit."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
DEFAULT_PROJECTS_DIR = REPO_ROOT / "projects"

ECOSYSTEMS = ["browser-extension", "ide-ai-plugin", "cli-wrapper", "saas-addon"]
PROVIDERS = ["polar", "lemonsqueezy", "gumroad"]


def render_template(src: Path, dest: Path, replacements: dict[str, str]) -> None:
    content = src.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")


def scaffold_browser_extension(proj_dir: Path, slug: str, title: str, provider: str) -> None:
    shutil.copy2(TEMPLATES_DIR / "license-validator" / "license_client.js", proj_dir / "src" / "license_client.js")
    manifest = {
        "manifest_version": 3,
        "name": title,
        "version": "0.1.0",
        "description": f"Lightweight friction-killer extension ({slug}).",
        "permissions": ["storage"],
        "action": {"default_popup": "src/popup.html", "default_title": title},
        "background": {"service_worker": "src/background.js", "type": "module"},
    }
    (proj_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (proj_dir / "src" / "background.js").write_text(
        f'import {{ requireProFeature }} from "./license_client.js";\n\n'
        f'chrome.runtime.onInstalled.addListener(() => {{\n'
        f'  console.log("{title} installed");\n'
        f'}});\n\n'
        f'export async function checkPro() {{\n'
        f'  return requireProFeature("batch_export");\n'
        f'}}\n',
        encoding="utf-8",
    )
    (proj_dir / "src" / "popup.html").write_text(
        f'<!DOCTYPE html>\n<html>\n<head><meta charset="utf-8"><title>{title}</title></head>\n'
        f'<body>\n  <h3>{title}</h3>\n'
        f'  <input id="license-key" placeholder="Paste {provider} license key" />\n'
        f'  <button id="activate-btn">Activate Pro</button>\n'
        f'  <p id="status"></p>\n'
        f'  <script type="module" src="popup.js"></script>\n'
        f'</body>\n</html>\n',
        encoding="utf-8",
    )
    (proj_dir / "src" / "popup.js").write_text(
        f'import {{ verifyLicense }} from "./license_client.js";\n\n'
        f'document.getElementById("activate-btn")?.addEventListener("click", async () => {{\n'
        f'  const key = document.getElementById("license-key").value;\n'
        f'  const res = await verifyLicense({{ key, provider: "{provider}" }});\n'
        f'  document.getElementById("status").textContent = res.valid ? "Pro active" : res.reason;\n'
        f'}});\n',
        encoding="utf-8",
    )
    (proj_dir / "tests" / "smoke_test.py").write_text(
        'import json\nfrom pathlib import Path\n\n'
        'def test_manifest_and_files():\n'
        '    root = Path(__file__).resolve().parent.parent\n'
        '    manifest = json.loads((root / "manifest.json").read_text())\n'
        '    assert manifest["manifest_version"] == 3\n'
        '    assert (root / "src" / "license_client.js").exists()\n'
        '    assert (root / "src" / "background.js").exists()\n\n'
        'if __name__ == "__main__":\n'
        '    test_manifest_and_files()\n'
        '    print("OK: browser-extension smoke test passed")\n',
        encoding="utf-8",
    )


def scaffold_ide_plugin(proj_dir: Path, slug: str, title: str, provider: str) -> None:
    shutil.copy2(TEMPLATES_DIR / "license-validator" / "license_client.js", proj_dir / "src" / "license_client.js")
    cmd_prefix = "".join(word.capitalize() for word in slug.split("-")) or "Extension"
    cmd_prefix = cmd_prefix[0].lower() + cmd_prefix[1:]
    pkg = {
        "name": slug,
        "displayName": title,
        "publisher": "friction-killer",
        "version": "0.1.0",
        "engines": {"vscode": "^1.85.0"},
        "categories": ["Other"],
        "activationEvents": ["onStartupFinished"],
        "type": "module",
        "main": "./src/extension.cjs",
        "contributes": {
            "commands": [
                {"command": f"{cmd_prefix}.runAction", "title": f"{title}: Run Pro Action"},
                {"command": f"{cmd_prefix}.activateLicense", "title": f"{title}: Activate Pro License"},
            ]
        },
        "scripts": {"test": "python3 tests/smoke_test.py"},
    }
    (proj_dir / "package.json").write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    (proj_dir / "src" / "extension.cjs").write_text(
        '"use strict";\n\n'
        'let modPromise = null;\n'
        'exports.activate = async function activate(context) {\n'
        '  let vscodeApi = null;\n'
        '  try { vscodeApi = require("vscode"); } catch { vscodeApi = null; }\n'
        '  modPromise = modPromise || import("./index.js");\n'
        '  const mod = await modPromise;\n'
        '  return await mod.activate(context, vscodeApi);\n'
        '};\n'
        'exports.deactivate = async function deactivate() {\n'
        '  if (!modPromise) return;\n'
        '  const mod = await modPromise;\n'
        '  if (typeof mod.deactivate === "function") return await mod.deactivate();\n'
        '};\n',
        encoding="utf-8",
    )
    (proj_dir / "src" / "index.js").write_text(
        f'import {{ getTelemetry, verifyLicense, requireProFeature }} from "./license_client.js";\n\n'
        f'export {{ getTelemetry }};\n\n'
        f'export async function activateLicense(key, options = {{}}) {{\n'
        f'  return verifyLicense({{ key, provider: "{provider}", ...options }});\n'
        f'}}\n\n'
        f'export async function runProAction(store = null) {{\n'
        f'  return requireProFeature("pro_automation", store);\n'
        f'}}\n\n'
        f'export async function activate(contextOrKey, optionsOrVscodeApi = null) {{\n'
        f'  if (typeof contextOrKey === "string" || contextOrKey == null) {{\n'
        f'    return activateLicense(contextOrKey, optionsOrVscodeApi || {{}});\n'
        f'  }}\n'
        f'  const context = contextOrKey;\n'
        f'  let vscodeApi = optionsOrVscodeApi;\n'
        f'  if (!vscodeApi) {{\n'
        f'    try {{ vscodeApi = await import("vscode"); }} catch {{ vscodeApi = null; }}\n'
        f'  }}\n'
        f'  const register = typeof vscodeApi?.commands?.registerCommand === "function"\n'
        f'    ? (id, fn) => vscodeApi.commands.registerCommand(id, fn)\n'
        f'    : (id, fn) => ({{ command: id, handler: fn, dispose() {{}} }});\n'
        f'  const disposables = [\n'
        f'    register("{cmd_prefix}.runAction", async () => {{\n'
        f'      const res = await runProAction();\n'
        f'      if (res.allowed) vscodeApi?.window?.showInformationMessage?.("{title}: Pro ready");\n'
        f'      else vscodeApi?.window?.showWarningMessage?.("{title}: Pro license required");\n'
        f'      return res;\n'
        f'    }}),\n'
        f'    register("{cmd_prefix}.activateLicense", async (k) => {{\n'
        f'      const key = typeof k === "string" ? k : await vscodeApi?.window?.showInputBox?.({{ prompt: "Enter Pro license key" }});\n'
        f'      const res = await activateLicense(key);\n'
        f'      if (res.valid) vscodeApi?.window?.showInformationMessage?.("{title}: Pro activated!");\n'
        f'      else vscodeApi?.window?.showWarningMessage?.(res.reason || "Invalid license key");\n'
        f'      return res;\n'
        f'    }}),\n'
        f'  ];\n'
        f'  if (Array.isArray(context?.subscriptions)) context.subscriptions.push(...disposables);\n'
        f'  return {{ disposables }};\n'
        f'}}\n\n'
        f'export function deactivate() {{}}\n',
        encoding="utf-8",
    )
    (proj_dir / "tests" / "smoke_test.py").write_text(
        'import json\nfrom pathlib import Path\n\n'
        'def test_plugin_structure():\n'
        '    root = Path(__file__).resolve().parent.parent\n'
        '    pkg = json.loads((root / "package.json").read_text())\n'
        '    assert pkg["main"] in ("./src/extension.cjs", "./src/index.js")\n'
        '    assert pkg.get("engines", {}).get("vscode")\n'
        '    assert len(pkg.get("contributes", {}).get("commands", [])) >= 1\n'
        '    assert (root / "src" / "extension.cjs").exists()\n'
        '    assert (root / "src" / "license_client.js").exists()\n\n'
        'if __name__ == "__main__":\n'
        '    test_plugin_structure()\n'
        '    print("OK: ide-ai-plugin smoke test passed")\n',
        encoding="utf-8",
    )


def scaffold_python_project(proj_dir: Path, slug: str, title: str, provider: str, ecosystem: str) -> None:
    shutil.copy2(TEMPLATES_DIR / "license-validator" / "license_client.py", proj_dir / "src" / "license_client.py")
    (proj_dir / "src" / "__init__.py").write_text("", encoding="utf-8")

    if ecosystem == "cli-wrapper":
        (proj_dir / "pyproject.toml").write_text(
            f'[build-system]\nrequires = ["setuptools>=61.0"]\nbuild-backend = "setuptools.build_meta"\n\n'
            f'[project]\nname = "{slug}"\nversion = "0.1.0"\ndescription = "{title}"\nrequires-python = ">=3.10"\n\n'
            f'[project.scripts]\n{slug} = "cli:main"\n\n'
            f'[tool.setuptools]\npackage-dir = {{"" = "src"}}\npy-modules = ["cli", "license_client"]\n',
            encoding="utf-8",
        )
        entry_name = "cli.py"
        test_name = "test_cli.py"
        entry_code = (
            f'#!/usr/bin/env python3\nimport argparse\nimport sys\nfrom pathlib import Path\n\n'
            f'sys.path.insert(0, str(Path(__file__).resolve().parent))\n'
            f'from license_client import require_pro_feature, verify_license\n\n'
            f'def run_core(input_text: str) -> str:\n'
            f'    return input_text.strip()\n\n'
            f'def main() -> int:\n'
            f'    p = argparse.ArgumentParser(description="{title}")\n'
            f'    p.add_argument("--activate", help="Activate {provider} license key")\n'
            f'    p.add_argument("--pro", action="store_true", help="Check Pro status")\n'
            f'    args = p.parse_args()\n'
            f'    if args.activate:\n'
            f'        print(verify_license(args.activate, provider="{provider}", app_slug="{slug}"))\n'
            f'        return 0\n'
            f'    if args.pro:\n'
            f'        print(require_pro_feature("pro_cli", app_slug="{slug}"))\n'
            f'        return 0\n'
            f'    print("{title} free tier ready")\n'
            f'    return 0\n\n'
            f'if __name__ == "__main__":\n'
            f'    raise SystemExit(main())\n'
        )
        test_code = (
            'import sys\nfrom pathlib import Path\n\n'
            'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))\n'
            'from cli import run_core\n'
            'from license_client import require_pro_feature\n\n'
            'def test_cli_smoke():\n'
            '    assert run_core(" hello ") == "hello"\n'
            '    res = require_pro_feature("pro_cli", app_slug="__nonexistent_test__")\n'
            '    assert res["allowed"] is False\n\n'
            'if __name__ == "__main__":\n'
            '    test_cli_smoke()\n'
            '    print("OK: cli-wrapper smoke test passed")\n'
        )
    else:
        entry_name = "addon.py"
        test_name = "test_addon.py"
        entry_code = (
            f'"""Core SaaS add-on handler for {title}."""\n\n'
            f'from license_client import require_pro_feature, verify_license\n\n'
            f'def handle_event(payload: dict) -> dict:\n'
            f'    return {{"status": "ok", "items": len(payload.get("items", []))}}\n\n'
            f'def unlock_pro(license_key: str) -> dict:\n'
            f'    return verify_license(license_key, provider="{provider}", app_slug="{slug}")\n\n'
            f'def check_pro_gate() -> dict:\n'
            f'    return require_pro_feature("batch_sync", app_slug="{slug}")\n'
        )
        test_code = (
            'import sys\nfrom pathlib import Path\n\n'
            'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))\n'
            'from addon import handle_event, check_pro_gate\n\n'
            'def test_addon_smoke():\n'
            '    assert handle_event({"items": [1, 2]})["items"] == 2\n'
            '    assert check_pro_gate()["allowed"] is False\n\n'
            'if __name__ == "__main__":\n'
            '    test_addon_smoke()\n'
            '    print("OK: saas-addon smoke test passed")\n'
        )

    (proj_dir / "src" / entry_name).write_text(entry_code, encoding="utf-8")
    (proj_dir / "tests" / test_name).write_text(test_code, encoding="utf-8")


def scaffold_project(
    slug: str,
    title: str,
    ecosystem: str,
    provider: str,
    host_software: str,
    projects_dir: Path,
) -> Path:
    proj_dir = projects_dir / slug
    for sub in ("src", "tests", "launch"):
        (proj_dir / sub).mkdir(parents=True, exist_ok=True)

    replacements = {
        "<TITLE>": title,
        "<SLUG>": slug,
        "<ECOSYSTEM>": ecosystem,
        "<PROVIDER>": provider,
        "<HOST_SOFTWARE>": host_software,
    }

    render_template(TEMPLATES_DIR / "spec-template.md", proj_dir / "SPEC.md", replacements)
    render_template(TEMPLATES_DIR / "landing-page" / "index.html", proj_dir / "launch" / "landing.html", replacements)
    render_template(TEMPLATES_DIR / "launch-kit-template.md", proj_dir / "launch" / "LAUNCH_KIT.md", replacements)

    if ecosystem == "browser-extension":
        scaffold_browser_extension(proj_dir, slug, title, provider)
    elif ecosystem == "ide-ai-plugin":
        scaffold_ide_plugin(proj_dir, slug, title, provider)
    else:
        scaffold_python_project(proj_dir, slug, title, provider, ecosystem)

    return proj_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a friction-killer project from templates.")
    parser.add_argument("--slug", required=True, help="Project directory slug (lowercase-hyphenated)")
    parser.add_argument("--title", required=True, help="Human-readable product title")
    parser.add_argument("--ecosystem", required=True, choices=ECOSYSTEMS, help="Target software ecosystem")
    parser.add_argument("--provider", default="lemonsqueezy", choices=PROVIDERS, help="License/payment provider")
    parser.add_argument("--host-software", default="Host Software", help="Host software being improved")
    parser.add_argument("--projects-dir", default=str(DEFAULT_PROJECTS_DIR), help="Parent projects directory")
    args = parser.parse_args()

    try:
        proj_dir = scaffold_project(
            slug=args.slug,
            title=args.title,
            ecosystem=args.ecosystem,
            provider=args.provider,
            host_software=args.host_software,
            projects_dir=Path(args.projects_dir),
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Scaffolded '{args.title}' ({args.ecosystem}, {args.provider}) -> {proj_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
