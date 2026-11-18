# Master Launch Playbook (15-Minute Go-Live Checklist)

## Portfolio Summary (3 Shipped Products)

| Product | Ecosystem | Pro Price | Distributable Bundle | Launch Assets |
| :--- | :--- | :---: | :--- | :--- |
| **LinearBridge** (`notion-linear-prd-sync`) | browser-extension | $29 once | `projects/notion-linear-prd-sync/dist/notion-linear-prd-sync-v0.1.0.zip` | [Sales Page](../projects/notion-linear-prd-sync/launch/landing.html) / [Kit](../projects/notion-linear-prd-sync/launch/LAUNCH_KIT.md) |
| **NotionGitExport** (`notion-clean-md-exporter`) | cli-wrapper | $24 once | `projects/notion-clean-md-exporter/dist/notion-clean-md-exporter-v0.1.0.zip` | [Sales Page](../projects/notion-clean-md-exporter/launch/landing.html) / [Kit](../projects/notion-clean-md-exporter/launch/LAUNCH_KIT.md) |
| **ExtProfileLock** (`vscode-workspace-profile-config`) | ide-ai-plugin | $19 once | `projects/vscode-workspace-profile-config/dist/vscode-workspace-profile-config-v0.1.0.zip` | [Sales Page](../projects/vscode-workspace-profile-config/launch/landing.html) / [Kit](../projects/vscode-workspace-profile-config/launch/LAUNCH_KIT.md) |
| **All-Access Bundle** | Multi-Product | **\$49 once** (Save 32%) | All 3 Pro Keys | [Storefront](index.html) |

---

## Step 1: Create Lemon Squeezy Products (~5 mins)
1. Create 3 single products in Lemon Squeezy with **License Keys enabled** (3 device activations):
   - **LinearBridge Pro** — \$29 one-time
   - **NotionGitExport Pro** — \$24 one-time
   - **ExtProfileLock Pro** — \$19 one-time
2. Create 1 **All-Access Bundle** product at **\$49 one-time** and pass `--bundle-url` to `configure_checkout.py`.

## Step 2: Wire Live Checkout URLs & Rebuild Site/Zips (~2 mins)
```bash
python3 scripts/configure_checkout.py --slug notion-linear-prd-sync --checkout-url "https://YOUR_STORE.lemonsqueezy.com/buy/..." --product-id "PRODUCT_ID"
python3 scripts/configure_checkout.py --slug notion-clean-md-exporter --checkout-url "https://YOUR_STORE.lemonsqueezy.com/buy/..." --product-id "PRODUCT_ID"
python3 scripts/configure_checkout.py --slug vscode-workspace-profile-config --checkout-url "https://YOUR_STORE.lemonsqueezy.com/buy/..." --product-id "PRODUCT_ID"
python3 scripts/configure_checkout.py --bundle-url "https://YOUR_STORE.lemonsqueezy.com/buy/BUNDLE_LINK"
```

## Step 3: Publish & Distribute (~8 mins)
1. **GitHub Pages Storefront (`docs/`)**: Push `main` so `https://domstijn.github.io/friction-killer-suite/` serves live checkout buttons and direct `.zip` downloads.
2. **Marketplace Submissions**:
   - Upload `projects/notion-linear-prd-sync/dist/notion-linear-prd-sync-v0.1.0.zip` to the Chrome Web Store Developer Dashboard.
   - Package `projects/vscode-workspace-profile-config` for the VS Code Marketplace (`vsce package`).
3. **High-Intent Sniper Replies**:
   - Follow each product's `LAUNCH_KIT.md` to post helpful, non-spammy replies on the exact discovered GitHub issues and HN threads.
