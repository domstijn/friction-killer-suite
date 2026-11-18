# Launch & Monetization Kit: ExtProfileLock (`vscode-workspace-profile-config`)

## 1. Checkout & License Key Setup (Lemon Squeezy)
1. Create a product named **ExtProfileLock Pro** in Lemon Squeezy priced at **\$19 one-time**.
2. Enable **License Keys** (3 device activations).
3. Run `python3 scripts/configure_checkout.py --slug vscode-workspace-profile-config --checkout-url "YOUR_CHECKOUT_URL" --product-id "YOUR_PRODUCT_ID"` to inject your live IDs and rebuild the release `.zip`.

## 2. VS Code Marketplace Listing Draft
- **Title**: ExtProfileLock — Declarative Extension Locks & .env Sync
- **Short Summary (119 chars)**: Enforce repo-level VS Code extension locks, interpolate .env variables into .code-workspace files, and avoid profile drift.
- **Keywords**: vscode profile, workspace extensions, dotenv, monorepo, code-workspace, developer productivity
- **Permissions Justification**: Reads only local `.vscode/workspace-lock.json`, `.env`, and `.code-workspace` files; only makes external HTTPS calls to `api.lemonsqueezy.com` during Pro key activation.

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact Stage 1 discovery GitHub issues:
- Target Thread 1 (1,181+ reactions): `https://github.com/microsoft/vscode/issues/40239`
- Target Thread 2 (`.code-workspace` env interpolation): `https://github.com/microsoft/vscode/issues/44755`

**Reply Template**:
> Until VS Code supports declarative extension toggling and `${env:VAR}` interpolation inside `.code-workspace` natively, I built a lightweight tool (ExtProfileLock) that reads a repo-committed `workspace-lock.json` + `.env` to detect extension conflicts, interpolate workspace paths, and generate exact `code --install-extension` / `--disable-extension` commands. Free tier handles single-repo drift checks: [landing page URL].

## 4. Launch Post Copy (Show HN / r/vscode / X)
- **Title**: Show HN: ExtProfileLock – Declarative extension locks & `${env:VAR}` workspace sync for VS Code
- **Body**:
  - Built for developers tired of `microsoft/vscode#40239` (no repo-level enable/disable extension config) and `#44755` (no `${env:VAR}` interpolation in `.code-workspace`).
  - Free tier audits installed extensions against `workspace-lock.json` and parses `.env`.
  - \$19 one-time Lemon Squeezy Pro key unlocks automated CLI batch generation, monorepo lockfile merging, and `.code-workspace` interpolation.
