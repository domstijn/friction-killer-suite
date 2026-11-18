"""Lossless Notion Markdown export cleaner: strips UUIDs, rewrites links, and emits YAML frontmatter."""

from __future__ import annotations

import re
import shutil
import urllib.parse
from pathlib import Path
from typing import Any

UUID_SUFFIX_RE = re.compile(r"(?:\s+|%20)[0-9a-fA-F]{32}$")
META_LINE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 _-]{0,30}):\s+(.+)$")
MD_LINK_RE = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")


def _slugify_segment(text: str) -> str:
    cleaned = UUID_SUFFIX_RE.sub("", text).strip()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", cleaned.lower()).strip("-")
    return slug or "untitled"


def strip_notion_uuid(name: str) -> str:
    """Strip 32-char Notion hex UUID suffixes and slugify filenames or relative paths."""
    decoded = urllib.parse.unquote(name.strip())
    parts = [p for p in decoded.replace("\\", "/").split("/") if p and p != "."]
    if not parts:
        return "untitled"

    cleaned_parts: list[str] = []
    for idx, part in enumerate(parts):
        is_last = idx == len(parts) - 1
        if is_last and "." in part and not part.startswith("."):
            stem, ext = part.rsplit(".", 1)
            cleaned_parts.append(f"{_slugify_segment(stem)}.{ext.lower()}")
        else:
            cleaned_parts.append(_slugify_segment(part))
    return "/".join(cleaned_parts)


def _rewrite_relative_links(body: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        label = match.group(1)
        target = match.group(2).strip()
        lower = target.lower()
        if lower.startswith(("http://", "https://", "mailto:", "#")):
            return match.group(0)
        path_part, anchor = (target.split("#", 1) + [""])[:2]
        clean_path = strip_notion_uuid(path_part) if path_part else ""
        rebuilt = f"{clean_path}#{anchor}" if anchor else clean_path
        return f"{label}({rebuilt})"

    return MD_LINK_RE.sub(_replace, body)


def _yaml_escape(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def clean_markdown_content(raw_md: str, convert_frontmatter: bool = False) -> str:
    """Rewrite internal Notion links and optionally convert top title + metadata into YAML frontmatter."""
    lines = raw_md.splitlines()
    title: str | None = None
    metadata: dict[str, Any] = {}
    body_start_idx = 0

    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    if idx < len(lines) and lines[idx].startswith("# "):
        title = lines[idx][2:].strip()
        idx += 1
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        meta_idx = idx
        while meta_idx < len(lines):
            m = META_LINE_RE.match(lines[meta_idx].strip())
            if not m:
                break
            key = re.sub(r"[^a-z0-9]+", "_", m.group(1).strip().lower()).strip("_")
            val = m.group(2).strip()
            metadata[key] = val
            meta_idx += 1
        if convert_frontmatter:
            body_start_idx = meta_idx
            while body_start_idx < len(lines) and not lines[body_start_idx].strip():
                body_start_idx += 1

    body_text = "\n".join(lines[body_start_idx:]) if convert_frontmatter and title else raw_md
    rewritten_body = _rewrite_relative_links(body_text).rstrip() + "\n"

    if not convert_frontmatter or not title:
        return rewritten_body

    fm_lines = ["---", f"title: {_yaml_escape(title)}"]
    for key, val in metadata.items():
        if key == "tags" and "," in val:
            tags_list = ", ".join(_yaml_escape(t.strip()) for t in val.split(",") if t.strip())
            fm_lines.append(f"{key}: [{tags_list}]")
        else:
            fm_lines.append(f"{key}: {_yaml_escape(val)}")
    fm_lines.append("---")
    return "\n".join(fm_lines) + "\n\n" + rewritten_body.lstrip("\n")


def export_workspace(
    input_dir: Path | str,
    output_dir: Path | str,
    is_pro: bool = False,
    free_file_cap: int = 10,
) -> dict[str, Any]:
    """Export a Notion Markdown directory into clean, Git-ready Markdown."""
    src_root = Path(input_dir)
    dst_root = Path(output_dir)
    if not src_root.is_dir():
        raise FileNotFoundError(f"Input directory not found: {src_root}")

    all_files = sorted(p for p in src_root.rglob("*") if p.is_file())
    md_files = [p for p in all_files if p.suffix.lower() == ".md"]

    if not is_pro and len(md_files) > free_file_cap:
        return {
            "ok": False,
            "blocked_by_tier": True,
            "processed": 0,
            "total_markdown": len(md_files),
            "files": [],
            "reason": (
                f"Free tier is capped at {free_file_cap} Markdown files per run "
                f"(found {len(md_files)}). Activate a Pro license for unlimited recursive "
                "workspace export and YAML frontmatter."
            ),
        }

    dst_root.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []

    for src_file in all_files:
        rel_str = src_file.relative_to(src_root).as_posix()
        clean_rel = strip_notion_uuid(rel_str)
        dest_file = dst_root / clean_rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        if src_file.suffix.lower() == ".md":
            raw = src_file.read_text(encoding="utf-8", errors="replace")
            cleaned = clean_markdown_content(raw, convert_frontmatter=is_pro)
            dest_file.write_text(cleaned, encoding="utf-8")
            exported.append(clean_rel)
        elif is_pro:
            shutil.copy2(src_file, dest_file)

    return {
        "ok": True,
        "blocked_by_tier": False,
        "processed": len(exported),
        "files": exported,
        "reason": "Pro workspace export complete" if is_pro else "Free export complete",
    }
