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

from forge_engine import (  # noqa: E402
    build_multi_tag_push,
    flatten_compose_extends,
    plan_volume_migration,
)
from license_client import get_telemetry, verify_license  # noqa: E402


def test_free_tier_volume_dry_run_and_two_service_compose():
    # Free volume rename dry-run generates deterministic docker commands
    plan = plan_volume_migration("27722c3065e2f0", "pgdata_prod", mode="rename", is_pro=False)
    assert plan["ok"] is True
    assert len(plan["commands"]) == 3
    assert "docker volume create pgdata_prod" in plan["commands"][0]
    assert "docker volume rm 27722c3065e2f0" in plan["commands"][2]

    # Free execute=True or attached container guard is blocked
    blocked_exec = plan_volume_migration("vol_a", "vol_b", execute=True, is_pro=False)
    assert blocked_exec["ok"] is False and blocked_exec["blocked_by_tier"] is True

    blocked_ctr = plan_volume_migration("vol_a", "vol_b", attached_containers=["db"], is_pro=False)
    assert blocked_ctr["ok"] is False and blocked_ctr["blocked_by_tier"] is True

    # Free 2-service Compose flattening works
    compose_two = """
version: "2.4"
services:
  base-api:
    image: ghcr.io/acme/api:1.0
    environment:
      LOG_LEVEL: info
      PORT: "8080"
    ports:
      - "8080:8080"
  web:
    extends: base-api
    environment:
      LOG_LEVEL: debug
    volumes:
      - data:/app/data
"""
    flat = flatten_compose_extends(compose_two, is_pro=False)
    assert flat["ok"] is True
    assert flat["flattened_dict"]["version"] == "3.8"
    web = flat["flattened_dict"]["services"]["web"]
    assert "extends" not in web
    assert web["image"] == "ghcr.io/acme/api:1.0"
    assert web["environment"]["LOG_LEVEL"] == "debug"
    assert web["environment"]["PORT"] == "8080"
    assert "extends:" not in flat["flattened_yaml"]


def test_free_caps_and_pro_unlock_features():
    base_yaml = """
services:
  common-svc:
    image: alpine:3.20
    environment:
      APP_ENV: prod
    labels:
      tier: backend
    deploy:
      replicas: 2
"""
    compose_three = """
version: "2.4"
services:
  api:
    extends:
      file: base.yml
      service: common-svc
    environment:
      SERVICE: api
    deploy:
      replicas: 4
  worker:
    extends:
      file: base.yml
      service: common-svc
    environment:
      SERVICE: worker
  cron:
    image: busybox:latest
"""
    # Free tier blocks >2 services & blocks push-tags
    blocked_cmp = flatten_compose_extends(compose_three, base_files={"base.yml": base_yaml}, is_pro=False)
    assert blocked_cmp["ok"] is False and blocked_cmp["blocked_by_tier"] is True

    blocked_push = build_multi_tag_push("ghcr.io/acme/api", ["v1.4.2", "latest"], is_pro=False)
    assert blocked_push["ok"] is False and blocked_push["blocked_by_tier"] is True

    # Unlock via mocked Stripe verify-license (supports individual + All-Access Bundle product ID)
    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = Path(tmp) / "cache"

        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                ok = body.get("license_key", "").startswith("cs_live_")
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
                "cs_live_AbCdEfGhIjKlMnOpQrStUvWxYz123456",
                provider="stripe",
                product_id=["prod_NEW", "prod_VeW6IYwGyYJkPv"],
                app_slug="docker-volume-compose-tool",
                cache_dir=cache_dir,
            )
            assert lic["valid"] is True and lic["tier"] == "pro"
        finally:
            srv.shutdown()
            srv.server_close()
            if prev_url is None:
                os.environ.pop("STRIPE_LICENSE_VERIFY_URL", None)
            else:
                os.environ["STRIPE_LICENSE_VERIFY_URL"] = prev_url

    # Pro features execute cleanly
    flat_pro = flatten_compose_extends(compose_three, base_files={"base.yml": base_yaml}, is_pro=True)
    assert flat_pro["ok"] is True
    assert flat_pro["service_count"] == 3
    assert flat_pro["flattened_dict"]["services"]["api"]["deploy"]["replicas"] == 4
    assert flat_pro["flattened_dict"]["services"]["api"]["environment"]["APP_ENV"] == "prod"

    executed = []
    mig = plan_volume_migration(
        "old_db",
        "new_db",
        mode="clone",
        attached_containers=["postgres"],
        execute=True,
        is_pro=True,
        runner=lambda cmd: executed.append(cmd),
    )
    assert mig["ok"] is True and mig["executed"] is True
    assert executed[0] == ["docker", "stop", "postgres"]
    assert executed[-1] == ["docker", "start", "postgres"]

    pushed = build_multi_tag_push("ghcr.io/acme/api", ["v1.4.2", "v1", "latest"], source_tag="latest", is_pro=True)
    assert pushed["ok"] is True
    assert pushed["commands"] == [
        "docker tag ghcr.io/acme/api:latest ghcr.io/acme/api:v1.4.2",
        "docker push ghcr.io/acme/api:v1.4.2",
        "docker tag ghcr.io/acme/api:latest ghcr.io/acme/api:v1",
        "docker push ghcr.io/acme/api:v1",
        "docker push ghcr.io/acme/api:latest",
    ]


def test_cli_subprocess_and_offline_stripe_key():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache_dir = root / "cache"
        compose_path = root / "docker-compose.yml"
        out_path = root / "docker-compose.v3.yml"
        cli_path = SRC_DIR / "cli.py"

        compose_path.write_text(
            "version: '2.4'\nservices:\n  s1:\n    image: alpine\n  s2:\n    image: alpine\n  s3:\n    image: alpine\n",
            encoding="utf-8",
        )

        # Free 3-service flatten blocked via CLI exit code 2
        blocked = subprocess.run(
            [sys.executable, str(cli_path), "--cache-dir", str(cache_dir), "flatten-compose", "--input", str(compose_path)],
            capture_output=True,
            text=True,
        )
        assert blocked.returncode == 2
        assert json.loads(blocked.stdout)["blocked_by_tier"] is True

        # Offline Stripe Checkout Session key activation
        env = dict(os.environ)
        env["STRIPE_LICENSE_VERIFY_URL"] = "http://127.0.0.1:9/verify-license"
        subprocess.run(
            [
                sys.executable, str(cli_path),
                "--cache-dir", str(cache_dir),
                "--activate", "cs_live_ZzYyXxWwVvUuTtSsRrQqPpOoNnMm1234",
            ],
            check=True,
            capture_output=True,
            env=env,
        )

        # Pro flatten + push-tags now succeed
        subprocess.run(
            [
                sys.executable, str(cli_path),
                "--cache-dir", str(cache_dir),
                "flatten-compose", "--input", str(compose_path),
                "--output", str(out_path), "--yaml",
            ],
            check=True,
            capture_output=True,
        )
        assert 'version: "3.8"' in out_path.read_text(encoding="utf-8")

        push_proc = subprocess.run(
            [
                sys.executable, str(cli_path),
                "--cache-dir", str(cache_dir),
                "push-tags", "--repo", "ghcr.io/acme/web", "--tags", "1.0.0,latest",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(push_proc.stdout)["ok"] is True

        tel = get_telemetry("docker-volume-compose-tool", cache_dir)
        assert tel["paywall_hits"] >= 1
        assert tel["pro_activations"] >= 1


if __name__ == "__main__":
    test_free_tier_volume_dry_run_and_two_service_compose()
    test_free_caps_and_pro_unlock_features()
    test_cli_subprocess_and_offline_stripe_key()
    print("OK: DockerVolumeForge test_cli.py passed")
