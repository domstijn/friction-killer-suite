# Launch & Monetization Kit: ClaudeProfileSwitch (`claude-profile-switcher`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **ClaudeProfileSwitch Pro** — **€24 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VfKeANX0phOIoi`
  - Price ID: `price_1UdzznH2AcdDmQyRNCKkNoWa`
  - Payment Link ID: `plink_1Ue006H2AcdDmQyRdQspnxtD`
  - Live Stripe Payment Link: https://buy.stripe.com/aFafZh2UA9ysf9mh006sw04
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Product Sales Page**: https://domstijn.github.io/friction-killer-suite/products/claude-profile-switcher/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=claude-profile-switcher` and activate via `claude-profile-switch --activate cs_live_...` (validated against `/verify-license` with offline session-format fallback).

## 2. Package Listing Draft (PyPI / Direct `.whl`)
- **Title**: ClaudeProfileSwitch — Multi-Account, MCP Profile & Quota Guard for Claude Code
- **Short Summary (126 chars)**: Switch isolated Claude Code & MCP profiles in 1 command, inject .env MCP secrets via .claude-profile, and guard 5h token burn.
- **Keywords**: claude-code, mcp, profile-switcher, quota-guard, cli, ai-developer-tools
- **Permissions Justification**: Operates strictly on local user config files (`~/.claude.json`, `claude_desktop_config.json`, `.claude/projects/*.jsonl`); makes zero network calls except `--activate` verification against `/verify-license` (with offline Stripe session fallback).

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact Stage 1 discovery issues:
- Target Thread 1 (1,425 reactions — multi-account switching): https://github.com/anthropics/claude-code/issues/18435
- Target Thread 2 (698 reactions — multiple connector/MCP accounts): https://github.com/anthropics/claude-code/issues/27302
- Target Thread 3 (545 reactions — 5-hour session limit exhaustion): https://github.com/anthropics/claude-code/issues/38335

**Reply Template**:
> Until multi-account & per-repo MCP profile switching ships natively, I built a zero-dependency local Python CLI (`ClaudeProfileSwitch`) that snapshots isolated `~/.claude.json` + MCP configs, auto-switches via repo `.claude-profile` (with `${ENV_VAR}` injection so secrets stay out of git), and audits local JSONL session logs against your 5-hour quota window. Free tier handles 2 profiles + basic quota checks: https://domstijn.github.io/friction-killer-suite/products/claude-profile-switcher/

## 4. Launch Post Copy (r/ClaudeAI / r/ClaudeCode / X)
- **Title**: Built a zero-dependency CLI to switch Claude Code/MCP profiles per project & monitor 5-hour JSONL quota burn
- **Body**:
  - Tired of re-authenticating across work/personal Claude accounts (#18435, #27302) and hitting sudden 5-hour session caps (#38335) without warning.
  - ClaudeProfileSwitch snapshots isolated account + `claude_desktop_config.json` bundles locally, injects `${ENV_VAR}` MCP secrets on `auto-switch`, and calculates rolling 5-hour token burn from `.jsonl` transcripts.
  - Free starter tier gives 2 saved profiles + basic quota usage; €24 one-time Pro key (or €49 All-Access Bundle) unlocks unlimited client profiles, `.claude-profile` auto-switching, and CSV burn reports: https://domstijn.github.io/friction-killer-suite/products/claude-profile-switcher/
