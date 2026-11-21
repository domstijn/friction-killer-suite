"""Zero-dependency Docker volume migration planner, Compose v3 extends flattener, and multi-tag batcher."""

from __future__ import annotations

import copy
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, Callable

FREE_SERVICE_LIMIT = 2
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")


def _validate_identifier(val: str, label: str) -> str:
    clean = (val or "").strip()
    if not SAFE_NAME_RE.match(clean):
        raise ValueError(f"Invalid {label}: '{val}'")
    return clean


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for idx, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if idx == 0 or line[idx - 1].isspace():
                return line[:idx]
    return line


def _split_top_level(text: str, sep: str = ",") -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    in_s = False
    in_d = False
    for ch in text:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif not in_s and not in_d:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth = max(0, depth - 1)
            elif ch == sep and depth == 0:
                parts.append("".join(cur).strip())
                cur = []
                continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if not s:
        return ""
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    lower = s.lower()
    if lower in ("null", "~"):
        return None
    if lower == "true":
        return True
    if lower == "false":
        return False
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_parse_scalar(x) for x in _split_top_level(inner)] if inner else []
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        out: dict[str, Any] = {}
        if inner:
            for item in _split_top_level(inner):
                if ":" in item:
                    k, v = item.split(":", 1)
                    out[str(_parse_scalar(k))] = _parse_scalar(v)
        return out
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _split_kv(text: str) -> tuple[str, str | None] | None:
    in_s = False
    in_d = False
    for idx, ch in enumerate(text):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == ":" and not in_s and not in_d:
            nxt = text[idx + 1 : idx + 2]
            if nxt == "" or nxt.isspace():
                key = str(_parse_scalar(text[:idx]))
                rest = text[idx + 1 :].strip()
                return key, (rest if rest else None)
    return None


def parse_compose_text(raw_text: str) -> dict[str, Any]:
    """Parse JSON or standard indentation-based YAML (Compose v2/v3 subset)."""
    stripped = (raw_text or "").strip()
    if not stripped:
        return {}
    if stripped.startswith("{"):
        parsed = json.loads(stripped)
        if not isinstance(parsed, dict):
            raise ValueError("Compose root must be a JSON object")
        return parsed

    tokens: list[tuple[int, str]] = []
    for raw_line in stripped.splitlines():
        cleaned = _strip_comment(raw_line).rstrip()
        if not cleaned.strip():
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        tokens.append((indent, cleaned.strip()))

    def _parse_block(idx: int, min_indent: int) -> tuple[Any, int]:
        if idx >= len(tokens):
            return {}, idx
        indent, content = tokens[idx]
        if content.startswith("- ") or content == "-":
            items: list[Any] = []
            list_indent = indent
            while idx < len(tokens):
                cur_ind, cur_txt = tokens[idx]
                if cur_ind < list_indent or not (cur_txt.startswith("- ") or cur_txt == "-"):
                    break
                if cur_ind > list_indent:
                    break
                after = cur_txt[2:].strip() if cur_txt.startswith("- ") else ""
                idx += 1
                if not after:
                    child, idx = _parse_block(idx, list_indent + 1)
                    items.append(child)
                    continue
                kv = _split_kv(after)
                if kv is not None:
                    k, v = kv
                    entry: dict[str, Any] = {}
                    if v is not None:
                        entry[k] = _parse_scalar(v)
                    else:
                        sub, idx = _parse_block(idx, list_indent + 2)
                        entry[k] = sub
                    if idx < len(tokens) and tokens[idx][0] >= list_indent + 2:
                        extra, idx = _parse_block(idx, list_indent + 2)
                        if isinstance(extra, dict):
                            entry.update(extra)
                    items.append(entry)
                else:
                    items.append(_parse_scalar(after))
            return items, idx

        mapping: dict[str, Any] = {}
        map_indent = indent
        while idx < len(tokens):
            cur_ind, cur_txt = tokens[idx]
            if cur_ind < min_indent or cur_ind < map_indent:
                break
            if cur_txt.startswith("- ") or cur_txt == "-":
                break
            kv = _split_kv(cur_txt)
            if kv is None:
                raise ValueError(f"Unsupported YAML syntax near: {cur_txt}")
            k, v = kv
            idx += 1
            if v is not None:
                mapping[k] = _parse_scalar(v)
            else:
                if idx < len(tokens) and (
                    tokens[idx][0] > cur_ind
                    or (tokens[idx][0] == cur_ind and tokens[idx][1].startswith("- "))
                ):
                    child, idx = _parse_block(idx, cur_ind)
                    mapping[k] = child
                else:
                    mapping[k] = {}
        return mapping, idx

    parsed, _ = _parse_block(0, 0)
    if not isinstance(parsed, dict):
        raise ValueError("Compose root must evaluate to a mapping")
    return parsed


def _format_scalar(val: Any) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    text = str(val)
    if (
        text == ""
        or ":" in text
        or "#" in text
        or text.startswith(("{", "[", "-", "*", "&", "!", "%"))
        or text.lower() in ("true", "false", "null", "yes", "no")
        or re.fullmatch(r"-?\d+(?:\.\d+)?", text)
    ):
        return json.dumps(text)
    return text


def dump_compose_yaml(data: Any, indent: int = 0) -> str:
    """Serialize Compose mappings and lists into clean, readable YAML."""
    pad = "  " * indent
    lines: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            key_str = _format_scalar(k)
            if isinstance(v, dict) and v:
                lines.append(f"{pad}{key_str}:")
                lines.append(dump_compose_yaml(v, indent + 1))
            elif isinstance(v, list) and v:
                lines.append(f"{pad}{key_str}:")
                lines.append(dump_compose_yaml(v, indent + 1))
            elif isinstance(v, dict):
                lines.append(f"{pad}{key_str}: {{}}")
            elif isinstance(v, list):
                lines.append(f"{pad}{key_str}: []")
            else:
                lines.append(f"{pad}{key_str}: {_format_scalar(v)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item:
                first = True
                for k, v in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    first = False
                    if isinstance(v, (dict, list)) and v:
                        lines.append(f"{prefix}{_format_scalar(k)}:")
                        lines.append(dump_compose_yaml(v, indent + 2))
                    else:
                        lines.append(f"{prefix}{_format_scalar(k)}: {_format_scalar(v)}")
            elif isinstance(item, list) and item:
                lines.append(f"{pad}-")
                lines.append(dump_compose_yaml(item, indent + 1))
            else:
                lines.append(f"{pad}- {_format_scalar(item)}")
    else:
        lines.append(f"{pad}{_format_scalar(data)}")
    return "\n".join(lines)


def _merge_env(base_env: Any, child_env: Any) -> Any:
    def _to_dict(raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return dict(raw)
        if isinstance(raw, list):
            out: dict[str, Any] = {}
            for entry in raw:
                text = str(entry)
                if "=" in text:
                    k, v = text.split("=", 1)
                    out[k] = v
                else:
                    out[text] = ""
            return out
        return {}

    if isinstance(base_env, dict) or isinstance(child_env, dict):
        merged = _to_dict(base_env)
        merged.update(_to_dict(child_env))
        return merged
    combined: list[Any] = []
    for item in (base_env or []) + (child_env or []):
        if item not in combined:
            combined.append(item)
    return combined


def _merge_service_configs(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(parent)
    for key, val in child.items():
        if key == "extends":
            continue
        if key == "environment" and key in merged:
            merged[key] = _merge_env(merged[key], val)
        elif key in ("ports", "volumes", "depends_on") and isinstance(merged.get(key), list) and isinstance(val, list):
            combined = list(merged[key])
            for item in val:
                if item not in combined:
                    combined.append(copy.deepcopy(item))
            merged[key] = combined
        elif isinstance(merged.get(key), dict) and isinstance(val, dict):
            merged[key] = _merge_service_configs(merged[key], val)
        else:
            merged[key] = copy.deepcopy(val)
    merged.pop("extends", None)
    return merged


def flatten_compose_extends(
    compose_input: dict[str, Any] | str,
    base_files: dict[str, dict[str, Any] | str] | None = None,
    is_pro: bool = False,
) -> dict[str, Any]:
    """Resolve Docker Compose extends inheritance into v3 stack-deployable YAML."""
    root = (
        copy.deepcopy(compose_input)
        if isinstance(compose_input, dict)
        else parse_compose_text(compose_input)
    )
    services = root.get("services")
    if not isinstance(services, dict) or not services:
        return {"ok": False, "blocked_by_tier": False, "reason": "No services mapping found in Compose file."}

    if not is_pro and len(services) > FREE_SERVICE_LIMIT:
        return {
            "ok": False,
            "blocked_by_tier": True,
            "service_count": len(services),
            "free_limit": FREE_SERVICE_LIMIT,
            "reason": (
                f"Free tier supports up to {FREE_SERVICE_LIMIT} services per Compose file. "
                "Activate a Pro license key for unlimited service flattening, container-safe volume migration, "
                "and multi-tag push batches."
            ),
        }

    parsed_bases: dict[str, dict[str, Any]] = {}
    for fname, raw_base in (base_files or {}).items():
        parsed_bases[str(fname)] = (
            copy.deepcopy(raw_base) if isinstance(raw_base, dict) else parse_compose_text(raw_base)
        )

    cache: dict[tuple[str, str], dict[str, Any]] = {}

    def _resolve(file_key: str, svc_name: str, stack: set[tuple[str, str]]) -> dict[str, Any]:
        node = (file_key, svc_name)
        if node in cache:
            return copy.deepcopy(cache[node])
        if node in stack:
            raise ValueError(f"Circular Compose extends detected at {file_key}:{svc_name}")

        doc = root if file_key == "__root__" else parsed_bases.get(file_key)
        if not isinstance(doc, dict):
            raise FileNotFoundError(f"Referenced Compose base file not provided: {file_key}")
        svc_map = doc.get("services") or {}
        if svc_name not in svc_map:
            raise KeyError(f"Extended service '{svc_name}' not found in {file_key}")

        raw_svc = copy.deepcopy(svc_map[svc_name])
        extends_spec = raw_svc.get("extends")
        if not extends_spec:
            raw_svc.pop("extends", None)
            cache[node] = raw_svc
            return copy.deepcopy(raw_svc)

        if isinstance(extends_spec, str):
            target_file = file_key
            target_svc = extends_spec.strip()
        elif isinstance(extends_spec, dict):
            target_svc = str(extends_spec.get("service") or "").strip()
            target_file = str(extends_spec.get("file") or "").strip() or file_key
        else:
            raise ValueError(f"Unsupported extends format on service '{svc_name}'")

        parent = _resolve(target_file, target_svc, stack | {node})
        resolved = _merge_service_configs(parent, raw_svc)
        cache[node] = resolved
        return copy.deepcopy(resolved)

    flattened_services: dict[str, Any] = {}
    extended_count = 0
    for svc_name, svc_cfg in services.items():
        if isinstance(svc_cfg, dict) and "extends" in svc_cfg:
            extended_count += 1
        flattened_services[svc_name] = _resolve("__root__", svc_name, set())

    out_doc = copy.deepcopy(root)
    if str(out_doc.get("version", "")).startswith("2"):
        out_doc["version"] = "3.8"
    out_doc.setdefault("version", "3.8")
    out_doc["services"] = flattened_services

    return {
        "ok": True,
        "blocked_by_tier": False,
        "service_count": len(flattened_services),
        "flattened_extends_count": extended_count,
        "flattened_dict": out_doc,
        "flattened_yaml": dump_compose_yaml(out_doc) + "\n",
    }


def plan_volume_migration(
    old_volume: str,
    new_volume: str,
    mode: str = "rename",
    attached_containers: list[str] | None = None,
    execute: bool = False,
    is_pro: bool = False,
    runner: Callable[[list[str]], Any] | None = None,
) -> dict[str, Any]:
    """Generate and optionally execute atomic container-safe Docker volume rename/clone."""
    src = _validate_identifier(old_volume, "source volume")
    dst = _validate_identifier(new_volume, "target volume")
    if src == dst:
        raise ValueError("Source and target volume names must differ.")
    if mode not in ("rename", "clone"):
        raise ValueError(f"Unsupported mode '{mode}'. Choose 'rename' or 'clone'.")

    containers = [_validate_identifier(c, "container") for c in (attached_containers or []) if str(c).strip()]
    if not is_pro and (execute or containers):
        return {
            "ok": False,
            "blocked_by_tier": True,
            "reason": (
                "Executing live volume migrations and stopping/restarting attached containers "
                "requires an active Pro license key. Free tier runs dry-run plans."
            ),
        }

    argv_steps: list[list[str]] = []
    if containers:
        argv_steps.append(["docker", "stop", *containers])
    argv_steps.append(["docker", "volume", "create", dst])
    argv_steps.append(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{src}:/from:ro",
            "-v",
            f"{dst}:/to",
            "alpine:3.20",
            "sh",
            "-c",
            "cd /from && cp -a . /to",
        ]
    )
    if mode == "rename":
        argv_steps.append(["docker", "volume", "rm", src])
    if containers:
        argv_steps.append(["docker", "start", *containers])

    commands = [shlex.join(step) for step in argv_steps]
    executed_steps: list[str] = []
    if execute:
        exec_fn = runner or (lambda cmd: subprocess.run(cmd, check=True, capture_output=True, text=True))
        for step, rendered in zip(argv_steps, commands):
            exec_fn(step)
            executed_steps.append(rendered)

    return {
        "ok": True,
        "blocked_by_tier": False,
        "mode": mode,
        "old_volume": src,
        "new_volume": dst,
        "attached_containers": containers,
        "commands": commands,
        "executed": bool(execute),
        "executed_steps": executed_steps,
    }


def build_multi_tag_push(
    image_repo: str,
    tags: list[str],
    source_tag: str = "latest",
    is_pro: bool = False,
    execute: bool = False,
    runner: Callable[[list[str]], Any] | None = None,
) -> dict[str, Any]:
    """Generate and optionally run batched multi-tag docker tag + docker push commands (Pro)."""
    if not is_pro:
        return {
            "ok": False,
            "blocked_by_tier": True,
            "reason": "Multi-tag docker push batching requires an active Pro license key.",
        }

    repo = _validate_identifier(image_repo, "image repository")
    src_tag = _validate_identifier(source_tag, "source tag")
    clean_tags = [_validate_identifier(t, "tag") for t in tags if str(t).strip()]
    if not clean_tags:
        raise ValueError("Provide at least one target tag.")

    argv_steps: list[list[str]] = []
    src_ref = f"{repo}:{src_tag}"
    for tag in clean_tags:
        dst_ref = f"{repo}:{tag}"
        if tag != src_tag:
            argv_steps.append(["docker", "tag", src_ref, dst_ref])
        argv_steps.append(["docker", "push", dst_ref])

    commands = [shlex.join(step) for step in argv_steps]
    executed_steps: list[str] = []
    if execute:
        exec_fn = runner or (lambda cmd: subprocess.run(cmd, check=True, capture_output=True, text=True))
        for step, rendered in zip(argv_steps, commands):
            exec_fn(step)
            executed_steps.append(rendered)

    return {
        "ok": True,
        "blocked_by_tier": False,
        "image_repo": repo,
        "tags": clean_tags,
        "commands": commands,
        "executed": bool(execute),
        "executed_steps": executed_steps,
    }
