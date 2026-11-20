"""Core profile switching, MCP secret injection, and 5-hour JSONL quota guard logic."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FREE_PROFILE_LIMIT = 2
ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _validate_profile_name(name: str) -> str:
    clean = (name or "").strip()
    if not SAFE_NAME_PATTERN.match(clean):
        raise ValueError(
            f"Invalid profile name '{name}'. Use 1-64 alphanumeric, dot, underscore, or hyphen characters."
        )
    return clean


def _profiles_root(store_dir: Path | str) -> Path:
    return Path(store_dir) / "profiles"


def _read_active_profile(store_dir: Path | str) -> str | None:
    active_file = Path(store_dir) / "active_profile.txt"
    if not active_file.is_file():
        return None
    val = active_file.read_text(encoding="utf-8").strip()
    return val or None


def _write_active_profile(store_dir: Path | str, name: str) -> None:
    base = Path(store_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / "active_profile.txt").write_text(f"{name}\n", encoding="utf-8")


def _count_mcp_servers(json_path: Path) -> int:
    if not json_path.is_file():
        return 0
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    if isinstance(data, dict) and isinstance(data.get("mcpServers"), dict):
        return len(data["mcpServers"])
    return 0


def save_profile(
    name: str,
    claude_config_path: Path | str,
    mcp_config_path: Path | str | None,
    store_dir: Path | str,
    is_pro: bool = False,
) -> dict[str, Any]:
    """Snapshot claude.json and claude_desktop_config.json into a named profile."""
    profile_name = _validate_profile_name(name)
    profiles_dir = _profiles_root(store_dir)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(p.name for p in profiles_dir.iterdir() if p.is_dir())

    if not is_pro and profile_name not in existing and len(existing) >= FREE_PROFILE_LIMIT:
        return {
            "ok": False,
            "blocked_by_tier": True,
            "profile": profile_name,
            "saved_count": len(existing),
            "free_limit": FREE_PROFILE_LIMIT,
            "reason": (
                f"Free tier supports up to {FREE_PROFILE_LIMIT} saved profiles. "
                "Activate a Pro license key for unlimited profiles, per-repo .claude-profile auto-switching, "
                "and 5-hour quota burn projection."
            ),
        }

    target_dir = profiles_dir / profile_name
    target_dir.mkdir(parents=True, exist_ok=True)
    saved_files: list[str] = []

    claude_src = Path(claude_config_path)
    if claude_src.is_file():
        shutil.copy2(claude_src, target_dir / "claude.json")
        saved_files.append("claude.json")

    if mcp_config_path is not None:
        mcp_src = Path(mcp_config_path)
        if mcp_src.is_file():
            shutil.copy2(mcp_src, target_dir / "claude_desktop_config.json")
            saved_files.append("claude_desktop_config.json")

    if not saved_files:
        return {
            "ok": False,
            "blocked_by_tier": False,
            "profile": profile_name,
            "reason": "No source config files found to snapshot.",
        }

    return {
        "ok": True,
        "blocked_by_tier": False,
        "profile": profile_name,
        "snapshot_dir": str(target_dir),
        "saved_files": saved_files,
        "is_pro": is_pro,
    }


def switch_profile(
    name: str,
    claude_config_path: Path | str,
    mcp_config_path: Path | str | None,
    store_dir: Path | str,
) -> dict[str, Any]:
    """Restore a saved profile snapshot onto local Claude Code and Desktop configs."""
    profile_name = _validate_profile_name(name)
    snapshot_dir = _profiles_root(store_dir) / profile_name
    if not snapshot_dir.is_dir():
        return {"ok": False, "profile": profile_name, "reason": f"Profile '{profile_name}' not found."}

    restored_files: list[str] = []
    snap_claude = snapshot_dir / "claude.json"
    if snap_claude.is_file():
        dst_claude = Path(claude_config_path)
        dst_claude.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snap_claude, dst_claude)
        restored_files.append(str(dst_claude))

    snap_mcp = snapshot_dir / "claude_desktop_config.json"
    if mcp_config_path is not None and snap_mcp.is_file():
        dst_mcp = Path(mcp_config_path)
        dst_mcp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snap_mcp, dst_mcp)
        restored_files.append(str(dst_mcp))

    _write_active_profile(store_dir, profile_name)
    return {
        "ok": True,
        "active_profile": profile_name,
        "restored_files": restored_files,
    }


def list_profiles(store_dir: Path | str) -> dict[str, Any]:
    """List saved profiles, active profile marker, and MCP server count per profile."""
    profiles_dir = _profiles_root(store_dir)
    active = _read_active_profile(store_dir)
    entries: list[dict[str, Any]] = []
    if profiles_dir.is_dir():
        for d in sorted(profiles_dir.iterdir()):
            if not d.is_dir():
                continue
            mcp_count = _count_mcp_servers(d / "claude_desktop_config.json") or _count_mcp_servers(
                d / "claude.json"
            )
            entries.append(
                {
                    "name": d.name,
                    "active": d.name == active,
                    "has_claude_config": (d / "claude.json").is_file(),
                    "has_mcp_config": (d / "claude_desktop_config.json").is_file(),
                    "mcp_servers": mcp_count,
                }
            )
    return {
        "ok": True,
        "active_profile": active,
        "count": len(entries),
        "profiles": entries,
    }


def _interpolate_value(
    val: Any,
    env_vars: dict[str, str],
    interpolated: set[str],
    unresolved: set[str],
) -> Any:
    if isinstance(val, str):

        def _repl(match: re.Match[str]) -> str:
            key = match.group(1)
            if key in env_vars:
                interpolated.add(key)
                return env_vars[key]
            unresolved.add(key)
            return match.group(0)

        return ENV_PATTERN.sub(_repl, val)
    if isinstance(val, list):
        return [_interpolate_value(item, env_vars, interpolated, unresolved) for item in val]
    if isinstance(val, dict):
        return {k: _interpolate_value(v, env_vars, interpolated, unresolved) for k, v in val.items()}
    return val


def auto_switch_for_repo(
    repo_dir: Path | str,
    claude_config_path: Path | str,
    mcp_config_path: Path | str | None,
    store_dir: Path | str,
    env_map: dict[str, str] | None = None,
    is_pro: bool = False,
) -> dict[str, Any]:
    """Activate repo-bound .claude-profile and interpolate ${VAR} secrets into MCP config (Pro)."""
    if not is_pro:
        return {
            "ok": False,
            "blocked_by_tier": True,
            "reason": (
                "Per-repo .claude-profile auto-switching and ${ENV_VAR} MCP secret injection "
                "require an active Pro license key."
            ),
        }

    cfg_path = Path(repo_dir) / ".claude-profile"
    if not cfg_path.is_file():
        return {"ok": False, "blocked_by_tier": False, "reason": f"Missing .claude-profile in {repo_dir}"}

    try:
        repo_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "blocked_by_tier": False, "reason": f"Invalid .claude-profile JSON: {exc}"}

    profile_name = str(repo_cfg.get("profile") or "").strip()
    if not profile_name:
        return {"ok": False, "blocked_by_tier": False, "reason": ".claude-profile missing 'profile' field."}

    switched = switch_profile(profile_name, claude_config_path, mcp_config_path, store_dir)
    if not switched.get("ok"):
        return switched

    merged_env = dict(os.environ)
    if env_map:
        merged_env.update({str(k): str(v) for k, v in env_map.items()})
    raw_mcp_env = repo_cfg.get("mcp_env") or {}
    if isinstance(raw_mcp_env, dict):
        merged_env.update({str(k): str(v) for k, v in raw_mcp_env.items()})

    interpolated_vars: set[str] = set()
    unresolved_vars: set[str] = set()
    updated_configs: list[str] = []

    candidates = [Path(claude_config_path)]
    if mcp_config_path is not None:
        candidates.append(Path(mcp_config_path))

    for cfg_file in candidates:
        if not cfg_file.is_file():
            continue
        parsed = json.loads(cfg_file.read_text(encoding="utf-8"))
        updated = _interpolate_value(parsed, merged_env, interpolated_vars, unresolved_vars)
        cfg_file.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
        updated_configs.append(str(cfg_file))

    return {
        "ok": True,
        "blocked_by_tier": False,
        "active_profile": profile_name,
        "updated_configs": updated_configs,
        "interpolated_vars": sorted(interpolated_vars),
        "unresolved_vars": sorted(unresolved_vars),
    }


def _parse_epoch_seconds(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        ts = float(value)
        return ts / 1000.0 if ts > 1e12 else ts
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            num = float(text)
            return num / 1000.0 if num > 1e12 else num
        except ValueError:
            pass
        try:
            iso = text[:-1] + "+00:00" if text.endswith("Z") else text
            dt = datetime.fromisoformat(iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            return None
    return None


def _extract_tokens(record: dict[str, Any]) -> tuple[int, int, int]:
    usage = record.get("usage")
    if not isinstance(usage, dict):
        msg = record.get("message")
        usage = msg.get("usage") if isinstance(msg, dict) and isinstance(msg.get("usage"), dict) else record

    inp = int(usage.get("input_tokens") or 0)
    cache_read = int(usage.get("cache_read_tokens") or usage.get("cache_read_input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    return inp, cache_read, out


def audit_quota_burn(
    sessions_dir: Path | str,
    window_hours: float = 5.0,
    window_token_budget: int = 500000,
    now_epoch: float | None = None,
    is_pro: bool = False,
) -> dict[str, Any]:
    """Scan local JSONL session logs to measure 5-hour token burn and project Pro exhaustion."""
    root = Path(sessions_dir)
    if not root.is_dir():
        return {"ok": False, "reason": f"Sessions directory not found: {sessions_dir}"}

    ref_now = float(now_epoch) if now_epoch is not None else time.time()
    window_start = ref_now - (float(window_hours) * 3600.0)

    total_input = 0
    total_cache = 0
    total_output = 0
    earliest_ts: float | None = None
    per_session: dict[str, dict[str, Any]] = {}

    for jsonl_file in sorted(root.rglob("*.jsonl")):
        session_name = jsonl_file.stem
        for line in jsonl_file.read_text(encoding="utf-8", errors="replace").splitlines():
            clean = line.strip()
            if not clean:
                continue
            try:
                rec = json.loads(clean)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue

            ts = None
            for ts_key in ("timestamp", "ts", "created_at"):
                if ts_key in rec:
                    ts = _parse_epoch_seconds(rec[ts_key])
                    if ts is not None:
                        break
            if ts is None or ts < window_start or ts > ref_now:
                continue

            inp, cache_read, out = _extract_tokens(rec)
            row_total = inp + cache_read + out
            if row_total <= 0:
                continue

            if earliest_ts is None or ts < earliest_ts:
                earliest_ts = ts

            total_input += inp
            total_cache += cache_read
            total_output += out

            bucket = per_session.setdefault(
                session_name,
                {
                    "session": session_name,
                    "events": 0,
                    "input_tokens": 0,
                    "cache_read_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                },
            )
            bucket["events"] += 1
            bucket["input_tokens"] += inp
            bucket["cache_read_tokens"] += cache_read
            bucket["output_tokens"] += out
            bucket["total_tokens"] += row_total

    used_tokens = total_input + total_cache + total_output
    remaining_tokens = max(0, int(window_token_budget) - used_tokens)
    pct_used = round((used_tokens / window_token_budget) * 100.0, 2) if window_token_budget > 0 else 0.0

    result: dict[str, Any] = {
        "ok": True,
        "is_pro": is_pro,
        "window_hours": window_hours,
        "used_tokens": used_tokens,
        "window_token_budget": window_token_budget,
        "remaining_tokens": remaining_tokens,
        "pct_used": pct_used,
    }

    if not is_pro:
        result["pro_upgrade_hint"] = (
            "Activate Pro for 5-hour burn-rate exhaustion projection, per-session breakdown, and CSV export."
        )
        return result

    if used_tokens > 0 and earliest_ts is not None:
        span_hours = max((ref_now - earliest_ts) / 3600.0, 1.0 / 60.0)
        burn_rate = round(used_tokens / span_hours, 2)
    else:
        burn_rate = 0.0

    eta_minutes = round((remaining_tokens / burn_rate) * 60.0, 1) if burn_rate > 0 else None
    breakdown = sorted(per_session.values(), key=lambda x: x["total_tokens"], reverse=True)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["session", "events", "input_tokens", "cache_read_tokens", "output_tokens", "total_tokens"])
    for row in breakdown:
        writer.writerow(
            [
                row["session"],
                row["events"],
                row["input_tokens"],
                row["cache_read_tokens"],
                row["output_tokens"],
                row["total_tokens"],
            ]
        )

    result.update(
        {
            "burn_rate_tokens_per_hour": burn_rate,
            "estimated_minutes_to_exhaustion": eta_minutes,
            "per_session_breakdown": breakdown,
            "csv_report": buf.getvalue(),
        }
    )
    return result
