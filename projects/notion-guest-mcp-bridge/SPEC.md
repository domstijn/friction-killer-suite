# Product & Technical Spec: NotionGuestBridge (`notion-guest-mcp-bridge`)

- **Ecosystem**: `browser-extension` (Chrome MV3 Extension + ESM Core)
- **Host Software**: Notion / Claude & Cursor
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`; €29 one-time EUR tax-inclusive Pro license / €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)

## 1. Pain & Evidence
- **Exact Friction**: Official Notion MCP and OAuth APIs block Guest accounts (`"You are a guest, so you cannot connect to Notion MCP"`), locking freelancers, agencies, and external collaborators out of client docs unless clients pay for full Member seats or guests resort to fragile ToS-violating `token_v2` cookies. Meanwhile Claude's Notion connector also fails to surface nested pages by URL.
- **Evidence URLs**:
  - https://github.com/makenotion/notion-mcp-server/issues/227 (99 reactions / 2026-03-12: guest users blocked from Notion MCP)
  - https://github.com/anthropics/claude-ai-mcp/issues/356 (29 reactions / 22 comments / 2026-05-26: Notion connector URL lookup fails)
- **Why Existing Alternatives Fail**: Official Notion MCP rejects guest OAuth; upgrading costs per-seat SaaS fees; raw `token_v2` scraping violates ToS; Notion native export gives bloated raw folders without PII masking or `.mcp-context.json` bundling.

## 2. Target Persona & Value Proposition
- **Who pays**: AI freelancers, dev agencies, PM consultants, and contractors working inside client Notion workspaces as Guests.
- **10x Relief**: Extracts the exact client pages, callouts, and inline database tables the guest already sees open in their browser tab into clean Claude/Cursor Markdown and `.mcp-context.json` context packs in one click — zero Member seat upgrades or third-party servers.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (€0)**:
  - Extract up to 3 single Notion guest pages/day (up to 40 blocks/page) into clean AI-ready Markdown.
- **Pro Tier (€29 one-time EUR via Stripe Managed Payments `acct_1UdCWDH2AcdDmQyR` — or €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)**:
  - **Unlimited Guest Page Extractions & Multi-Page Queue**: Collect multiple client Notion subpages into one merged context pack.
  - **Inline Database Table Schema + `.mcp-context.json` Bundle Export**: Extracts `[role="table"]` / table views into typed rows + structured MCP JSON context.
  - **Client PII & Secret Redaction**: Automatically scrubs client emails, phone numbers, and Bearer/API tokens before pasting into external LLMs.

## 4. Minimal Architecture & File Map
- `manifest.json` — Chrome MV3 config (`"permissions": ["storage"]`, Notion host permissions only — zero unused `scripting`).
- `src/license_client.js` — Stripe Managed Payments validator (`cs_live_...` + `/verify-license`) with 7-day offline cache & bundle product ID support.
- `src/guest_extractor.js` — Guest page Markdown formatter, inline table schema builder, PII redactor, and Free/Pro `.mcp-context.json` packager.
- `src/content.js` — Floating Notion `#notionguestbridge-bar` toolbar and live Notion block/checkbox/callout/table DOM extractor.
- `src/background.js` — Service worker handling daily Free cap, Pro queue persistence, and license checks.
- `src/popup.html` & `src/popup.js` — Extension popup UI for extraction, PII redaction toggle, `.mcp-context.json` export, and Stripe Pro key activation.
- `tests/smoke_test.py` — Manifest validation + Node.js ESM tests covering DOM extraction, Free caps, PII redaction, `.mcp-context.json` export, and Stripe key activation.

## 5. Verification Plan
1. Run `python3 projects/notion-guest-mcp-bridge/tests/smoke_test.py`.
2. Run `python3 scripts/ship_check.py --slug notion-guest-mcp-bridge --package` (verifies `Purple Potassium` permissions, `Red Potassium` `1280x800` screenshot, and headless Chromium `#notionguestbridge-bar` DOM injection).
