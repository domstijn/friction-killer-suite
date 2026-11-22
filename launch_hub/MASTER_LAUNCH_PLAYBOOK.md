# Master Launch Playbook (Stripe Managed Payments)

## Portfolio Summary (6 Shipped Products)

| Product | Ecosystem | Pro Price | Distributable Bundle | Launch Assets |
| :--- | :--- | :---: | :--- | :--- |
| **LinearBridge** (`notion-linear-prd-sync`) | browser-extension | €29 once | `projects/notion-linear-prd-sync/dist/notion-linear-prd-sync-v0.1.0.zip` | [Sales Page](../projects/notion-linear-prd-sync/launch/landing.html) / [Kit](../projects/notion-linear-prd-sync/launch/LAUNCH_KIT.md) |
| **NotionGitExport** (`notion-clean-md-exporter`) | cli-wrapper | €24 once | `projects/notion-clean-md-exporter/dist/notion-clean-md-exporter-v0.1.0.zip` | [Sales Page](../projects/notion-clean-md-exporter/launch/landing.html) / [Kit](../projects/notion-clean-md-exporter/launch/LAUNCH_KIT.md) |
| **ExtProfileLock** (`vscode-workspace-profile-config`) | ide-ai-plugin | €19 once | `projects/vscode-workspace-profile-config/dist/vscode-workspace-profile-config-v0.1.0.zip` | [Sales Page](../projects/vscode-workspace-profile-config/launch/landing.html) / [Kit](../projects/vscode-workspace-profile-config/launch/LAUNCH_KIT.md) |
| **ClaudeProfileSwitch** (`claude-profile-switcher`) | cli-wrapper | €24 once | `projects/claude-profile-switcher/dist/claude-profile-switcher-v0.1.0.zip` | [Sales Page](../projects/claude-profile-switcher/launch/landing.html) / [Kit](../projects/claude-profile-switcher/launch/LAUNCH_KIT.md) |
| **NotionGuestBridge** (`notion-guest-mcp-bridge`) | browser-extension | €29 once | `projects/notion-guest-mcp-bridge/dist/notion-guest-mcp-bridge-v0.1.0.zip` | [Sales Page](../projects/notion-guest-mcp-bridge/launch/landing.html) / [Kit](../projects/notion-guest-mcp-bridge/launch/LAUNCH_KIT.md) |
| **WebflowAssetZip** (`webflow-cms-asset-migrator`) | browser-extension | €29 once | `projects/webflow-cms-asset-migrator/dist/webflow-cms-asset-migrator-v0.1.0.zip` | [Sales Page](../projects/webflow-cms-asset-migrator/launch/landing.html) / [Kit](../projects/webflow-cms-asset-migrator/launch/LAUNCH_KIT.md) |
| **All-Access Bundle** | Multi-Product | **€49 once** (Save 32%) | All 3 Pro Keys | [Storefront](index.html) |

---

## Step 1: Provision Stripe Catalog & Payment Links (~1 min)
1. Enable Managed Payments in your Stripe Dashboard (`https://dashboard.stripe.com/settings/managed-payments`).
2. Create/sync all 4 EUR products, prices (`txcd_10103000`, `tax_behavior: inclusive`), and hosted Payment Links (`Stripe-Version: 2025-03-31.basil`):
```bash
python3 scripts/stripe_managed_payments.py provision --wire-checkout
```

## Step 2: Run Checkout, License Verify & Webhook Server (~1 min)
```bash
python3 scripts/stripe_managed_payments.py serve --port 4242
# Test redirect to Stripe Checkout:
curl -X POST -is "http://localhost:4242/create-checkout-session" -d ""
```

## Step 3: Publish & Distribute
1. **GitHub Pages Storefront (`docs/`)**: Push `main` so `https://domstijn.github.io/friction-killer-suite/` serves live product pages, `success.html` (auto-displays `?session_id=` Pro key), `cancel.html`, and direct `.zip` downloads.
2. **Marketplace Submissions**:
   - Upload `projects/notion-linear-prd-sync/dist/notion-linear-prd-sync-v0.1.0.zip` to the Chrome Web Store Developer Dashboard.
   - Package `projects/vscode-workspace-profile-config` for the VS Code Marketplace (`vsce package`).
3. **High-Intent Sniper Replies**:
   - Follow each product's `LAUNCH_KIT.md` to post helpful, non-spammy replies on the exact discovered GitHub issues and HN threads.
