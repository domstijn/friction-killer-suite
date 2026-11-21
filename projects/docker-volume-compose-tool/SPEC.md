# Product & Technical Spec: DockerVolumeForge (`docker-volume-compose-tool`)

- **Ecosystem**: `cli-wrapper` (Zero-dependency Python 3 CLI + PEP 427 `.whl`)
- **Host Software**: Docker / Docker Compose
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`; €24 one-time EUR tax-inclusive Pro license / €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)

## 1. Pain & Evidence
- **Exact Friction**: Docker still lacks a native `docker volume mv` / clone command, `docker stack deploy` (Compose v3+) fails when services use `extends:` inheritance, and `docker push` cannot batch multiple image tags cleanly in one command.
- **Evidence URLs**:
  - https://github.com/moby/moby/issues/31101 (718 reactions / 173 comments: Compose v3 / stack deploy `extends` support)
  - https://github.com/moby/moby/issues/31154 (594 reactions / 47 comments: rename Docker volume)
  - https://github.com/docker/cli/issues/267 (533 reactions / 62 comments: push multiple tags with `docker push`)

## 2. Target Persona & Value Proposition
- **Who pays**: DevOps engineers, platform teams, and backend developers migrating unnamed/legacy Docker data volumes safely and flattening modular Compose files for Swarm/production stack deploys.
- **10x Relief**: One local zero-dependency CLI generates or executes container-safe atomic volume clone/rename migrations, flattens multi-file Compose `extends` inheritance into clean v3 stack YAML, and produces multi-tag push batches.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (€0)**:
  - `rename-volume` (dry-run mode): Generates exact `docker volume create` + `alpine:3.20` `cp -a` + `docker volume rm` shell plan.
  - `flatten-compose`: Resolves `extends` inheritance and outputs flattened YAML/JSON for up to 2 services per Compose file.
- **Pro Tier (€24 one-time EUR via Stripe Managed Payments `acct_1UdCWDH2AcdDmQyR` — or €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)**:
  - **Container-Safe Execution & Attached-Container Stop/Restart Guards**: Pauses/stops attached containers before copying data, executes the atomic volume rename/clone, and restarts containers cleanly (`execute=True` / `attached_containers`).
  - **Unlimited Multi-Service Compose v3 `extends` Flattener**: Deep-merges `environment`, `labels`, `deploy`, `ports`, and `volumes` across unlimited services and external base Compose files.
  - **Multi-Tag `docker tag` + `docker push` Batch Generator**: Emits or executes `docker tag` and `docker push` batches across arbitrary tag lists in 1 command.

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 621 package metadata exposing `docker-volume-forge = "cli:main"` and `py-modules = ["cli", "forge_engine", "license_client"]`.
- `src/license_client.py` — Zero-backend Stripe Managed Payments (`cs_live_...` / `cs_test_...`) + `/verify-license` license validator with 7-day offline grace cache & bundle product ID support.
- `src/forge_engine.py` — Volume migration planner/executor, zero-dependency Compose YAML/JSON `extends` flattener & deep-merger, and multi-tag batch pusher.
- `src/cli.py` — `argparse` CLI exposing `--activate <KEY>`, `--pro`, `--telemetry`, `rename-volume`, `flatten-compose`, and `push-tags`.
- `tests/test_cli.py` — Unit + CLI subprocess tests covering Free 2-service/dry-run limits, Pro license unlock, Compose deep merge, and multi-tag batches.

## 5. Verification Plan
1. Run `python3 projects/docker-volume-compose-tool/tests/test_cli.py` (all unit & CLI tests pass).
2. Run `python3 scripts/ship_check.py --slug docker-volume-compose-tool --package` (zero placeholders, all tests green, `.zip` and `.whl` packaged).
