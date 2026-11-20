import json
import os
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from license_client import get_telemetry, verify_license  # noqa: E402
from profile_manager import (  # noqa: E402
    audit_quota_burn,
    auto_switch_for_repo,
    list_profiles,
    save_profile,
    switch_profile,
)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_free_profile_cap_and_switching():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        claude_cfg = root / "home" / ".claude.json"
        mcp_cfg = root / "home" / "claude_desktop_config.json"
        store_dir = root / "store"

        _write_json(claude_cfg, {"accountEmail": "work@company.com"})
        _write_json(mcp_cfg, {"mcpServers": {"linear": {"token": "${LINEAR_KEY}"}, "github": {"token": "gh1"}}})
        res1 = save_profile("work", claude_cfg, mcp_cfg, store_dir, is_pro=False)
        assert res1["ok"] is True

        _write_json(claude_cfg, {"accountEmail": "personal@gmail.com"})
        _write_json(mcp_cfg, {"mcpServers": {"obsidian": {"vault": "/notes"}}})
        res2 = save_profile("personal", claude_cfg, mcp_cfg, store_dir, is_pro=False)
        assert res2["ok"] is True

        # Switch back to work and verify contents restored
        sw = switch_profile("work", claude_cfg, mcp_cfg, store_dir)
        assert sw["ok"] is True
        assert json.loads(claude_cfg.read_text())["accountEmail"] == "work@company.com"

        listing = list_profiles(store_dir)
        assert listing["count"] == 2
        assert listing["active_profile"] == "work"

        # 3rd profile blocked on Free tier
        blocked = save_profile("client-acme", claude_cfg, mcp_cfg, store_dir, is_pro=False)
        assert blocked["ok"] is False
        assert blocked["blocked_by_tier"] is True


def test_free_vs_pro_repo_autoswitch_and_quota_guard():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        claude_cfg = root / "home" / ".claude.json"
        mcp_cfg = root / "home" / "claude_desktop_config.json"
        store_dir = root / "store"
        repo_dir = root / "repo-acme"
        sessions_dir = root / "sessions"
        cache_dir = root / "cache"

        _write_json(claude_cfg, {"accountEmail": "acme@client.io"})
        _write_json(
            mcp_cfg,
            {"mcpServers": {"postgres": {"url": "${ACME_DB_URL}", "token": "${LINEAR_API_KEY}"}}},
        )

        # Free repo auto-switch blocked
        repo_dir.mkdir(parents=True)
        _write_json(repo_dir / ".claude-profile", {"profile": "client-acme", "mcp_env": {"LINEAR_API_KEY": "lin_acme_99"}})
        blocked_auto = auto_switch_for_repo(
            repo_dir, claude_cfg, mcp_cfg, store_dir, env_map={"ACME_DB_URL": "postgres://acme"}, is_pro=False
        )
        assert blocked_auto["ok"] is False
        assert blocked_auto["blocked_by_tier"] is True

        # Sample JSONL logs inside & outside 5-hour window
        sessions_dir.mkdir(parents=True)
        now_ts = 1_760_018_000.0  # reference epoch
        lines = [
            json.dumps({"timestamp": now_ts - 20_000, "usage": {"input_tokens": 999999, "output_tokens": 1}}),  # expired
            json.dumps({"timestamp": now_ts - 7_200, "usage": {"input_tokens": 120000, "cache_read_tokens": 20000, "output_tokens": 10000}}),
            json.dumps({"timestamp": "2025-10-09T17:13:20Z", "message": {"usage": {"input_tokens": 40000, "output_tokens": 10000}}}),
        ]
        # Wait: ensure second timestamp matches same window relative to now_ts
        lines[2] = json.dumps({"timestamp": now_ts - 3_600, "message": {"usage": {"input_tokens": 40000, "output_tokens": 10000}}})
        (sessions_dir / "sess_alpha.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

        free_quota = audit_quota_burn(sessions_dir, window_hours=5.0, window_token_budget=500000, now_epoch=now_ts, is_pro=False)
        assert free_quota["ok"] is True
        assert free_quota["used_tokens"] == 200000
        assert free_quota["pct_used"] == 40.0
        assert "burn_rate_tokens_per_hour" not in free_quota
        assert "csv_report" not in free_quota

        # Pro unlock via mocked Stripe verify endpoint (individual + bundle product IDs)
        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                ok = body.get("license_key", "").startswith("cs_test_")
                resp = {"valid": ok, "product_id": "prod_VeW6IYwGyYJkPv" if ok else None}
                encoded = json.dumps(resp).encode("utf-8")
                self.send_response(200 if ok else 400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, *_args):
                return

        srv = HTTPServer(("127.0.0.1", 0), _Handler)
        t = Thread(target=srv.serve_forever, daemon=True)
        t.start()
        prev_url = os.environ.get("STRIPE_LICENSE_VERIFY_URL")
        os.environ["STRIPE_LICENSE_VERIFY_URL"] = f"http://127.0.0.1:{srv.server_address[1]}/verify-license"
        try:
            lic = verify_license(
                "cs_test_a1b2c3d4e5f6g7h8i9j0k1l2m3n4",
                provider="stripe",
                product_id=["prod_NEW", "prod_VeW6IYwGyYJkPv"],
                app_slug="claude-profile-switcher",
                cache_dir=cache_dir,
            )
            assert lic["valid"] is True
            assert lic["tier"] == "pro"
        finally:
            srv.shutdown()
            srv.server_close()
            if prev_url is None:
                os.environ.pop("STRIPE_LICENSE_VERIFY_URL", None)
            else:
                os.environ["STRIPE_LICENSE_VERIFY_URL"] = prev_url

        # With Pro active: save 3rd profile, auto-switch + ${VAR} inject, and Pro quota burn projection
        assert save_profile("client-acme", claude_cfg, mcp_cfg, store_dir, is_pro=True)["ok"] is True
        pro_auto = auto_switch_for_repo(
            repo_dir, claude_cfg, mcp_cfg, store_dir, env_map={"ACME_DB_URL": "postgres://acme/prod"}, is_pro=True
        )
        assert pro_auto["ok"] is True
        assert pro_auto["interpolated_vars"] == ["ACME_DB_URL", "LINEAR_API_KEY"]
        updated_mcp = json.loads(mcp_cfg.read_text())
        assert updated_mcp["mcpServers"]["postgres"]["url"] == "postgres://acme/prod"
        assert updated_mcp["mcpServers"]["postgres"]["token"] == "lin_acme_99"

        pro_quota = audit_quota_burn(sessions_dir, window_hours=5.0, window_token_budget=500000, now_epoch=now_ts, is_pro=True)
        assert pro_quota["used_tokens"] == 200000
        assert pro_quota["burn_rate_tokens_per_hour"] == 100000.0
        assert pro_quota["estimated_minutes_to_exhaustion"] == 180.0
        assert "sess_alpha,2,160000,20000,20000,200000" in pro_quota["csv_report"]


def test_cli_end_to_end_and_offline_stripe_session():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        claude_cfg = root / ".claude.json"
        mcp_cfg = root / "claude_desktop_config.json"
        store_dir = root / "store"
        cache_dir = root / "cache"
        sessions_dir = root / "sessions"
        cli_path = SRC_DIR / "cli.py"

        _write_json(claude_cfg, {"accountEmail": "p1@dev.io"})
        _write_json(mcp_cfg, {"mcpServers": {"fetch": {}}})
        sessions_dir.mkdir(parents=True)
        now_ts = 1_760_018_000.0
        (sessions_dir / "s1.jsonl").write_text(
            json.dumps({"timestamp": now_ts - 1800, "usage": {"input_tokens": 25000, "output_tokens": 5000}}) + "\n",
            encoding="utf-8",
        )

        # Save 2 free profiles then hit cap on 3rd via CLI subprocess
        for prof in ("p1", "p2"):
            subprocess.run(
                [
                    sys.executable, str(cli_path),
                    "--cache-dir", str(cache_dir),
                    "--store-dir", str(store_dir),
                    "--claude-config", str(claude_cfg),
                    "--mcp-config", str(mcp_cfg),
                    "save", "--name", prof,
                ],
                check=True,
                capture_output=True,
            )

        proc_blocked = subprocess.run(
            [
                sys.executable, str(cli_path),
                "--cache-dir", str(cache_dir),
                "--store-dir", str(store_dir),
                "--claude-config", str(claude_cfg),
                "--mcp-config", str(mcp_cfg),
                "save", "--name", "p3",
            ],
            capture_output=True,
            text=True,
        )
        assert proc_blocked.returncode == 2
        assert json.loads(proc_blocked.stdout)["blocked_by_tier"] is True

        # Activate offline Stripe Checkout Session key (unreachable localhost verify server triggers format fallback)
        env = dict(os.environ)
        env["STRIPE_LICENSE_VERIFY_URL"] = "http://127.0.0.1:9/verify-license"
        subprocess.run(
            [
                sys.executable, str(cli_path),
                "--cache-dir", str(cache_dir),
                "--activate", "cs_live_AbCdEfGhIjKlMnOpQrStUvWxYz123456",
            ],
            check=True,
            capture_output=True,
            env=env,
        )

        # Save 3rd profile + CSV quota export now succeed
        subprocess.run(
            [
                sys.executable, str(cli_path),
                "--cache-dir", str(cache_dir),
                "--store-dir", str(store_dir),
                "--claude-config", str(claude_cfg),
                "--mcp-config", str(mcp_cfg),
                "save", "--name", "p3",
            ],
            check=True,
            capture_output=True,
        )
        csv_proc = subprocess.run(
            [
                sys.executable, str(cli_path),
                "--cache-dir", str(cache_dir),
                "quota", "--sessions-dir", str(sessions_dir),
                "--now-epoch", str(now_ts), "--csv",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert "session,events,input_tokens,cache_read_tokens,output_tokens,total_tokens" in csv_proc.stdout
        assert "s1,1,25000,0,5000,30000" in csv_proc.stdout

        tel = get_telemetry("claude-profile-switcher", cache_dir)
        assert tel["paywall_hits"] >= 1
        assert tel["pro_activations"] >= 1


if __name__ == "__main__":
    test_free_profile_cap_and_switching()
    test_free_vs_pro_repo_autoswitch_and_quota_guard()
    test_cli_end_to_end_and_offline_stripe_session()
    print("OK: ClaudeProfileSwitch test_cli.py passed")
