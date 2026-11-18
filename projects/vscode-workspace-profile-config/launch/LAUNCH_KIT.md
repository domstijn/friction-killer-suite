# Launch & Monetization Kit: ExtProfileLock (`vscode-workspace-profile-config`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, tax code `txcd_10103000`, account `acct_1UdCWDH2AcdDmQyR`)
- **Individual Pro Price**: €19 one-time (EUR, tax-inclusive)
  - Product ID: `prod_VeW60IB88zFfQl`
  - Price ID: `price_1UdD78H2AcdDmQyRnk5p0xaw`
  - Live Stripe Payment Link: https://buy.stripe.com/5kQ3cv52I11Wgdq2566sw01
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Product Sales Page**: https://domstijn.github.io/friction-killer-suite/products/vscode-workspace-profile-config/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}` and paste it as their Pro License Key (validated against `/verify-license` with offline session-format fallback).

## 2. VS Code Marketplace Listing Draft
- **Title**: ExtProfileLock — Declarative Extension Locks & .env Sync
- **Short Summary (119 chars)**: Enforce repo-level VS Code extension locks, interpolate .env variables into .code-workspace files, and avoid profile drift.
- **Keywords**: vscode profile, workspace extensions, dotenv, monorepo, code-workspace, developer productivity
- **Permissions Justification**: Reads only local `.vscode/workspace-lock.json`, `.env`, and `.code-workspace` files; only makes external HTTPS calls to the Stripe license verification endpoint (`/verify-license`) during Pro key activation, with offline `cs_live_...` session-format fallback.

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact Stage 1 discovery GitHub issues:
- Target Thread 1 (1,181+ reactions): `https://github.com/microsoft/vscode/issues/40239`
- Target Thread 2 (`.code-workspace` env interpolation): `https://github.com/microsoft/vscode/issues/44755`

**Reply Template**:
> Until VS Code supports declarative extension toggling and `${env:VAR}` interpolation inside `.code-workspace` natively, I built a lightweight tool (ExtProfileLock) that reads a repo-committed `workspace-lock.json` + `.env` to detect extension conflicts, interpolate workspace paths, and generate exact `code --install-extension` / `--disable-extension` commands. Free tier handles single-repo drift checks: https://domstijn.github.io/friction-killer-suite/products/vscode-workspace-profile-config/

## 4. Launch Post Copy (Show HN / r/vscode / X)
- **Title**: Show HN: ExtProfileLock – Declarative extension locks & `${env:VAR}` workspace sync for VS Code
- **Body**:
  - Built for developers tired of `microsoft/vscode#40239` (no repo-level enable/disable extension config) and `#44755` (no `${env:VAR}` interpolation in `.code-workspace`).
  - Free tier audits installed extensions against `workspace-lock.json` and parses `.env`.
  - €19 one-time Pro license key via Stripe Managed Payments (or €49 All-Access Bundle) unlocks automated CLI batch generation, monorepo lockfile merging, and `.code-workspace` interpolation.
