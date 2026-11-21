# Launch & Monetization Kit: DockerVolumeForge (`docker-volume-compose-tool`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **DockerVolumeForge Pro** — **€24 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VfWC3UQKBawhsd`
  - Price ID: `price_1UeBAjH2AcdDmQyRsPm3Dd3K`
  - Payment Link ID: `plink_1UeBAzH2AcdDmQyRJPcvCbrT`
  - Live Stripe Payment Link: https://buy.stripe.com/9B63cvan29ys1iwbFG6sw05
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Product Sales Page**: https://domstijn.github.io/friction-killer-suite/products/docker-volume-compose-tool/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=docker-volume-compose-tool` and activate via `docker-volume-forge --activate cs_live_...` (validated against `/verify-license` with offline session-format fallback).

## 2. Package Listing Draft (PyPI / Direct `.whl`)
- **Title**: DockerVolumeForge — Volume Rename, Clone & Compose v3 Extends Flattener
- **Short Summary (126 chars)**: Rename/clone Docker volumes safely, flatten multi-file Compose v3 extends inheritance, and batch multi-tag image pushes locally.
- **Keywords**: docker, docker-compose, docker-volume, devops, swarm, stack-deploy, cli
- **Permissions Justification**: Runs local Docker CLI commands only when `--execute` is passed; reads only user-supplied Compose YAML/JSON paths; only makes external HTTPS calls to `/verify-license` during `--activate` (with offline Stripe session fallback).

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact Stage 1 discovery issues:
- Target Thread 1 (718 reactions — Compose v3 `extends` support): https://github.com/moby/moby/issues/31101
- Target Thread 2 (594 reactions — rename Docker volume): https://github.com/moby/moby/issues/31154
- Target Thread 3 (533 reactions — multi-tag `docker push`): https://github.com/docker/cli/issues/267

**Reply Template**:
> Since `docker volume mv` and Compose v3 `extends` resolution still aren't built in natively, I wrote a zero-dependency Python CLI (`DockerVolumeForge`) that generates/runs atomic container-safe volume rename/clone steps (`docker volume create` + alpine `cp -a` + `docker stop/start` guards), flattens `extends` across base Compose files into stack-deployable v3 YAML, and batches multi-tag pushes. Free tier covers dry-run volume plans + 2-service Compose flattening: https://domstijn.github.io/friction-killer-suite/products/docker-volume-compose-tool/

## 4. Launch Post Copy (r/docker / r/devops / X)
- **Title**: Built a zero-dependency CLI to rename Docker volumes safely, flatten Compose v3 `extends`, and batch multi-tag pushes
- **Body**:
  - Addresses three multi-hundred-reaction Moby/Docker CLI gaps (`moby/moby#31101`, `moby/moby#31154`, `docker/cli#267`).
  - Parses Compose YAML/JSON without external packages, resolves single- or cross-file `extends` inheritance (deep-merging `environment`, `labels`, `deploy`, `ports`, `volumes`), and emits deployable v3 YAML.
  - Free starter tier gives dry-run volume rename plans + 2-service Compose flattening; €24 one-time Pro key (or €49 All-Access Bundle) unlocks container-safe live execution, unlimited Compose flattening, and `push-tags` batching: https://domstijn.github.io/friction-killer-suite/products/docker-volume-compose-tool/
