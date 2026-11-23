#!/usr/bin/env python3
"""Zero-dependency Python stdlib PyPI wheel validator & uploader for active GO CLI packages."""

from __future__ import annotations

import argparse
import base64
import configparser
import email.parser
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = REPO_ROOT / "docs" / "downloads"

ACTIVE_GO_PYTHON_SLUGS = [
    "eu-oss-vat-return-compiler",
    "amazon-settlement-xero-qbo-splitter",
    "e-invoice-xml-batch-converter",
    "lemonsqueezy-stripe-polar-migrator",
    "stripe-payout-xero-qbo-splitter",
    "notion-clean-md-exporter",
    "claude-profile-switcher",
    "woo-shopify-metafield-migrator",
]

PYPI_NAME_OVERRIDES = {
    "claude-profile-switcher": "claude-profile-switch",
}

PYPI_UPLOAD_URL = "https://upload.pypi.org/legacy/"
TEST_PYPI_UPLOAD_URL = "https://test.pypi.org/legacy/"


def _norm_dist(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name)


def _sha256_b64(payload: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode("ascii")


def load_pypi_token() -> str:
    """Resolve PYPI_API_TOKEN from env, .env, or ~/.pypirc without ever logging the secret."""
    env_tok = os.environ.get("PYPI_API_TOKEN", "").strip()
    if env_tok:
        return env_tok

    dotenv_path = REPO_ROOT / ".env"
    if dotenv_path.is_file():
        for raw_line in dotenv_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "PYPI_API_TOKEN":
                tok = v.strip().strip('"').strip("'")
                if tok:
                    return tok

    pypirc_path = Path.home() / ".pypirc"
    if pypirc_path.is_file():
        cp = configparser.ConfigParser()
        cp.read(pypirc_path, encoding="utf-8")
        if cp.has_option("pypi", "password"):
            tok = cp.get("pypi", "password").strip()
            if tok:
                return tok
    return ""


def prepare_upload_wheel(whl_path: Path, target_pkg_name: str | None, tmp_dir: Path) -> Path:
    """Copy or clone a wheel cleanly under target_pkg_name with recalculated RECORD hashes."""
    if not target_pkg_name:
        return whl_path

    with zipfile.ZipFile(whl_path, "r") as zf:
        names = zf.namelist()
        meta_member = next((n for n in names if n.endswith(".dist-info/METADATA")), None)
        if not meta_member:
            raise ValueError(f"{whl_path.name}: missing METADATA")
        raw_meta = zf.read(meta_member).decode("utf-8")
        parsed = email.parser.Parser().parsestr(raw_meta)
        old_name = (parsed.get("Name") or "").strip()
        version = (parsed.get("Version") or "0.1.0").strip()
        if not old_name or old_name == target_pkg_name:
            return whl_path

        old_dist_info = meta_member.split("/", 1)[0]
        new_dist = _norm_dist(target_pkg_name)
        new_dist_info = f"{new_dist}-{version}.dist-info"
        out_whl = tmp_dir / f"{new_dist}-{version}-py3-none-any.whl"

        updated_meta = re.sub(
            r"(?m)^Name:\s*.*$", f"Name: {target_pkg_name}", raw_meta, count=1
        ).replace(f"pip install {old_name}", f"pip install {target_pkg_name}").encode("utf-8")

        entries: list[tuple[str, bytes]] = []
        for member in names:
            if member.endswith(".dist-info/RECORD"):
                continue
            payload = updated_meta if member == meta_member else zf.read(member)
            new_member = (
                f"{new_dist_info}/{member.split('/', 1)[1]}"
                if member.startswith(f"{old_dist_info}/")
                else member
            )
            entries.append((new_member, payload))

    record_lines: list[str] = []
    with zipfile.ZipFile(out_whl, "w", compression=zipfile.ZIP_DEFLATED) as out_zf:
        for arcname, payload in entries:
            out_zf.writestr(arcname, payload)
            record_lines.append(f"{arcname},sha256={_sha256_b64(payload)},{len(payload)}")
        record_lines.append(f"{new_dist_info}/RECORD,,")
        out_zf.writestr(f"{new_dist_info}/RECORD", ("\n".join(record_lines) + "\n").encode("utf-8"))

    return out_whl


def validate_wheel(whl_path: Path) -> dict[str, object]:
    """Verify Metadata 2.1 fields and all RECORD SHA-256 checksums inside a wheel."""
    if not whl_path.is_file():
        raise FileNotFoundError(f"Wheel not found: {whl_path}")

    with zipfile.ZipFile(whl_path, "r") as zf:
        names = zf.namelist()
        meta_member = next((n for n in names if n.endswith(".dist-info/METADATA")), None)
        rec_member = next((n for n in names if n.endswith(".dist-info/RECORD")), None)
        if not meta_member or not rec_member:
            raise ValueError(f"{whl_path.name}: missing METADATA or RECORD")

        meta_text = zf.read(meta_member).decode("utf-8")
        msg = email.parser.Parser().parsestr(meta_text)
        body = (msg.get_payload() or "").strip()

        for req_hdr in ("Name", "Version", "Summary", "Description-Content-Type"):
            if not (msg.get(req_hdr) or "").strip():
                raise ValueError(f"{whl_path.name}: missing required Metadata header {req_hdr}")
        if not body:
            raise ValueError(f"{whl_path.name}: empty long description body")

        rec_text = zf.read(rec_member).decode("utf-8")
        checked = 0
        for line in rec_text.splitlines():
            if not line.strip():
                continue
            parts = line.split(",")
            if len(parts) != 3:
                raise ValueError(f"{whl_path.name}: invalid RECORD line: {line}")
            arcname, digest_field, size_field = parts
            if not digest_field and not size_field:
                continue
            payload = zf.read(arcname)
            expected_digest = f"sha256={_sha256_b64(payload)}"
            if digest_field != expected_digest or size_field != str(len(payload)):
                raise ValueError(f"{whl_path.name}: checksum mismatch for {arcname}")
            checked += 1

    return {
        "name": (msg.get("Name") or "").strip(),
        "version": (msg.get("Version") or "").strip(),
        "summary": (msg.get("Summary") or "").strip(),
        "metadata_version": (msg.get("Metadata-Version") or "2.1").strip(),
        "author": (msg.get("Author") or "").strip(),
        "author_email": (msg.get("Author-email") or "").strip(),
        "license": (msg.get("License") or "").strip(),
        "home_page": (msg.get("Home-page") or "").strip(),
        "requires_python": (msg.get("Requires-Python") or "").strip(),
        "description_content_type": (msg.get("Description-Content-Type") or "text/markdown").strip(),
        "project_urls": msg.get_all("Project-URL") or [],
        "classifiers": msg.get_all("Classifier") or [],
        "description": body,
        "checked_records": checked,
    }


def upload_wheel_pypi(whl_path: Path, meta: dict[str, object], token: str, repo_url: str) -> tuple[int, str]:
    """Upload a validated .whl file to PyPI Legacy Upload endpoint using RFC 7578 multipart/form-data."""
    whl_bytes = whl_path.read_bytes()
    fields: list[tuple[str, str]] = [
        (":action", "file_upload"),
        ("protocol_version", "1"),
        ("metadata_version", str(meta["metadata_version"])),
        ("name", str(meta["name"])),
        ("version", str(meta["version"])),
        ("filetype", "bdist_wheel"),
        ("pyversion", "py3"),
        ("sha256_digest", hashlib.sha256(whl_bytes).hexdigest()),
        ("md5_digest", hashlib.md5(whl_bytes).hexdigest()),
        ("blake2_256_digest", hashlib.blake2b(whl_bytes, digest_size=32).hexdigest()),
        ("summary", str(meta["summary"])),
        ("description", str(meta["description"])),
        ("description_content_type", str(meta["description_content_type"])),
        ("author", str(meta["author"])),
        ("author_email", str(meta["author_email"])),
        ("license", str(meta["license"])),
        ("home_page", str(meta["home_page"])),
        ("requires_python", str(meta["requires_python"])),
    ]
    for url_entry in meta["project_urls"]:  # type: ignore[attr-defined]
        fields.append(("project_urls", str(url_entry)))
    for cls_entry in meta["classifiers"]:  # type: ignore[attr-defined]
        fields.append(("classifiers", str(cls_entry)))

    boundary = f"----FrictionKillerPyPI{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for k, v in fields:
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{k}"\r\n\r\n'
                f"{v}\r\n"
            ).encode("utf-8")
        )
    chunks.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="content"; filename="{whl_path.name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        + whl_bytes
        + f"\r\n--{boundary}--\r\n".encode("utf-8")
    )
    body_bytes = b"".join(chunks)

    auth_b64 = base64.b64encode(f"__token__:{token}".encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        repo_url,
        data=body_bytes,
        method="POST",
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "FrictionKiller-PyPI-Publisher/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after:
            body = f"(Retry-After: {retry_after}s) {body}"
        return exc.code, body


def is_version_published(pkg_name: str, version: str) -> bool:
    """Return True when pkg_name==version already has published files on PyPI."""
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return bool(data.get("releases", {}).get(version, []))
    except (urllib.error.HTTPError, OSError, ValueError, TypeError):
        return False


def check_pypi_available(pkg_name: str) -> str:
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=8) as resp:
            return f"EXISTS (HTTP {resp.status})"
    except urllib.error.HTTPError as exc:
        return "AVAILABLE" if exc.code == 404 else f"HTTP {exc.code}"
    except OSError as exc:
        return f"NET_ERR ({exc})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate & upload Friction-Killer .whl CLIs to PyPI.")
    parser.add_argument("--dry-run", action="store_true", help="Validate wheels & PyPI names without uploading")
    parser.add_argument("--test-pypi", action="store_true", help="Upload to TestPyPI instead of PyPI")
    parser.add_argument("--slug", action="append", default=[], help="Optional specific slug(s) to process")
    args = parser.parse_args()

    slugs = args.slug or ACTIVE_GO_PYTHON_SLUGS
    token = "" if args.dry_run else load_pypi_token()
    if not args.dry_run and not token:
        print("Error: Missing PYPI_API_TOKEN (set env var, .env PYPI_API_TOKEN=..., or ~/.pypirc).", file=sys.stderr)
        return 1

    repo_url = TEST_PYPI_UPLOAD_URL if args.test_pypi else PYPI_UPLOAD_URL
    failures = 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for slug in slugs:
            dist_name = _norm_dist(slug)
            src_whl = DOWNLOADS_DIR / f"{dist_name}-0.1.0-py3-none-any.whl"
            target_name = PYPI_NAME_OVERRIDES.get(slug)
            upload_whl = prepare_upload_wheel(src_whl, target_name, tmp_dir)
            meta = validate_wheel(upload_whl)

            if args.dry_run:
                avail = check_pypi_available(str(meta["name"]))
                print(
                    f"DRY-RUN OK: {meta['name']} v{meta['version']} ({upload_whl.name}, "
                    f"{meta['checked_records']} RECORD hashes verified, PyPI={avail})"
                )
                continue

            if not args.test_pypi and is_version_published(str(meta["name"]), str(meta["version"])):
                print(f"SKIPPED (already live on PyPI): https://pypi.org/project/{meta['name']}/{meta['version']}/")
                continue

            status, resp_body = upload_wheel_pypi(upload_whl, meta, token, repo_url)
            if status in (200, 201):
                print(f"PUBLISHED: https://pypi.org/project/{meta['name']}/{meta['version']}/ (HTTP {status})")
            elif status == 400 and "File already exists" in resp_body:
                print(f"SKIPPED (already exists on PyPI): {meta['name']}=={meta['version']}")
            elif status == 429:
                print(
                    f"RATE-LIMITED {meta['name']} -> HTTP 429: {resp_body[:300]}\n"
                    "Hint: PyPI limits new-project creation bursts; re-run `python3 scripts/publish_pypi.py` later to resume remaining packages.",
                    file=sys.stderr,
                )
                failures += 1
                break
            else:
                print(f"FAILED {meta['name']} -> HTTP {status}: {resp_body[:300]}", file=sys.stderr)
                failures += 1

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
