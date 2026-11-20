# Product & Technical Spec: ClaudeProfileSwitch (`claude-profile-switcher`)

- **Ecosystem**: `cli-wrapper` (Zero-dependency Python 3 CLI + PEP 427 `.whl`)
- **Host Software**: Claude Code / Claude Desktop
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`; €24 one-time EUR tax-inclusive Pro license / €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)

## 1. Pain & Evidence
- **Exact Friction**: Developers and AI power users have no built-in way to isolate or switch multiple Claude Code / Claude Desktop accounts and MCP server profiles across client, work, and personal repos, and frequently hit abrupt 5-hour session rate limits with zero local token-burn visibility.
- **Evidence URLs**:
  - https://github.com/anthropics/claude-code/issues/18435 (1,425 reactions / 249 comments: multi-account profile switching)
  - https://github.com/anthropics/claude-code/issues/27302 (698 reactions / 323 comments: isolated connector/MCP accounts)
  - https://github.com/anthropics/claude-code/issues/38335 (545 reactions / 876 comments: unexpected 5-hour session limit exhaustion)

## 2. Target Persona & Value Proposition
- **Who pays**: AI engineers, freelance consultants, and polyglot product teams juggling personal Pro/Max accounts alongside employer/client Claude accounts and project-specific MCP secrets.
- **10x Relief**: One local CLI command snapshots/swaps isolated `~/.claude.json` + `claude_desktop_config.json` bundles, auto-binds repos via `.claude-profile` with `${ENV_VAR}` secret injection, and computes 5-hour JSONL token burn before you get rate-limited mid-task.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (€0)**:
  - `save`, `switch`, `list`: Snapshot and switch up to 2 named profiles (`work`, `personal`) across `~/.claude.json` and `claude_desktop_config.json`.
  - `quota`: Compute total 5-hour session token usage (`used_tokens`, `window_token_budget`, `pct_used`) from local JSONL session logs.
- **Pro Tier (€24 one-time EUR via Stripe Managed Payments `acct_1UdCWDH2AcdDmQyR` — or €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)**:
  - **Unlimited Saved Profiles**: Save and switch 3+ client/team/environment profiles.
  - **Per-Repo `.claude-profile` Auto-Switch & `${ENV_VAR}` MCP Injection**: Read repo `.claude-profile` JSON (`profile` + `mcp_env`), activate the matching profile, and interpolate `${VAR}` secrets into `mcpServers` configs safely without committing secrets.
  - **5-Hour Burn-Rate Projection & CSV Export**: Estimate `burn_rate_tokens_per_hour`, `estimated_minutes_to_exhaustion`, `per_session_breakdown`, and export audit-ready CSV token reports.

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 621 package metadata exposing `claude-profile-switch = "cli:main"` and `py-modules = ["cli", "profile_manager", "license_client"]`.
- `src/license_client.py` — Zero-backend Stripe Managed Payments (`cs_live_...` / `cs_test_...`) + `/verify-license` license validator with 7-day offline grace cache & bundle product ID support.
- `src/profile_manager.py` — Profile snapshotting/switching, Free 2-profile cap, `.claude-profile` + `${VAR}` MCP interpolator, and JSONL 5-hour token burn analyzer + CSV generator.
- `src/cli.py` — `argparse` CLI exposing `--activate <KEY>`, `save`, `switch`, `list`, `auto-switch`, and `quota`.
- `tests/test_cli.py` — Unit + CLI subprocess tests covering Free cap, Pro unlock, `.claude-profile` env interpolation, and JSONL burn-rate/CSV output.

## 5. Verification Plan
1. Run `python3 projects/claude-profile-switcher/tests/test_cli.py` (all unit & CLI tests pass).
2. Run `python3 scripts/ship_check.py --slug claude-profile-switcher --package` (zero placeholders, all tests green, `.zip` and `.whl` packaged).
