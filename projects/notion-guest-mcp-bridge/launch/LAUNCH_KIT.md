# Launch & Monetization Kit: NotionGuestBridge (`notion-guest-mcp-bridge`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **NotionGuestBridge Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VfX0l5vMdU7VO6`
  - Price ID: `price_1UeBwaH2AcdDmQyRWUw3Amvj`
  - Payment Link ID: `plink_1UeBwmH2AcdDmQyRWhS4Tnr2`
  - Live Stripe Payment Link: https://buy.stripe.com/4gMfZhcva7qk1iw6lm6sw06
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Product Sales Page**: https://domstijn.github.io/friction-killer-suite/products/notion-guest-mcp-bridge/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=notion-guest-mcp-bridge` and paste it into `src/popup.html`, validated via `verifyLicense({ key, provider: "stripe", productId: "prod_VfX0l5vMdU7VO6,prod_VeW6IYwGyYJkPv" })`.

## 2. Chrome Web Store Listing Draft (`Purple Potassium` & `Red Potassium` Safe)
- **Title**: NotionGuestBridge — Notion Guest to AI Context
- **Short Summary (126 chars)**: Export guest-accessible Notion pages and inline tables into clean Claude & Cursor Markdown or .mcp-context.json packs locally.
- **Keywords**: notion guest, notion mcp, claude context, cursor rules, markdown exporter, client portal
- **Permissions Justification**:
  - `storage`: Stores daily Free-tier count (3/day), multi-page Pro queue, and cached Stripe Pro license status locally in Chrome storage.
  - **Content Scripts / Host Permissions (`notion.so`)**: Reads headings, checkboxes, callouts, and inline database tables from the Notion page currently viewed by the user so Guest users can pack accessible pages into Claude/Cursor context without OAuth or private cookie scraping. (Does not request `scripting`, `activeTab`, or `cookies`.)
- **Screenshot Asset**: `launch/screenshot1280x800.png` (`1280x800`, 24-bit RGB, no alpha, real UI mockup showing Notion Guest view, database table, popup with PII redaction, and floating toolbar).

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact Stage 1 discovery issues:
- Target Thread 1 (99 reactions / 2026-03-12 — Guest users blocked from Notion MCP): https://github.com/makenotion/notion-mcp-server/issues/227
- Target Thread 2 (29 reactions / 2026-05-26 — Claude Notion connector URL lookup fails): https://github.com/anthropics/claude-ai-mcp/issues/356

**Reply Template**:
> Since official Notion MCP blocks guest OAuth and `token_v2` scraping isn't clean/safe in client workspaces, I built a small local Chrome MV3 extension (`NotionGuestBridge`) that extracts the Notion guest pages, callouts, and database tables you already see open in your tab straight into Claude/Cursor Markdown (with optional email/token redaction and `.mcp-context.json` bundling). Free tier handles 3 single-page packs/day if you want to try it: https://domstijn.github.io/friction-killer-suite/products/notion-guest-mcp-bridge/. Feedback welcome!

## 4. Launch Post Copy (r/Notion / IndieHackers / X)
- **Title**: Locked out of Notion MCP as a Guest on client workspaces — built a Chrome extension to pack open pages & tables for Claude/Cursor
- **Body**:
  - Notion blocks Guest accounts from official OAuth MCP (`makenotion/notion-mcp-server#227`), forcing contractors to ask clients for paid Member seats or touch fragile `token_v2` cookies.
  - NotionGuestBridge runs 100% client-side on your open Notion tab (`storage` permission only — zero cookies/remote servers): converts headings, checkboxes, callouts, and inline tables into clean AI context.
  - Free tier packs 3 single pages/day; €29 one-time Pro key (or €49 All-Access Bundle) unlocks unlimited multi-page queues, `.mcp-context.json` bundles, and client email/secret redaction: https://domstijn.github.io/friction-killer-suite/products/notion-guest-mcp-bridge/
