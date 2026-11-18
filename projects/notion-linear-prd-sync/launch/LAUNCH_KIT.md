# Launch & Monetization Kit: LinearBridge (`notion-linear-prd-sync`)

## 1. Checkout & License Key Setup (Stripe Managed Payments)
- **Monetization Provider**: `stripe` (Stripe Managed Payments, API version `2025-03-31.basil`, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`, EUR tax-inclusive).
- **Individual Pro Tier (€29 one-time, EUR)**:
  - Product ID: `prod_VeW6ffGaCfNzue`
  - Price ID: `price_1UdD76H2AcdDmQyRffNvQkTq`
  - Live Stripe Payment Link: `https://buy.stripe.com/dRmcN5eDibGA8KYaBC6sw02`
- **All-Access Bundle (€49 one-time, EUR)**:
  - Product ID: `prod_VeW6IYwGyYJkPv`
  - Live Stripe Payment Link: `https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03`
- **Live Product Sales Page**: `https://domstijn.github.io/friction-killer-suite/products/notion-linear-prd-sync/`
- **License Activation Flow**:
  - Customers complete Stripe Checkout and receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}`.
  - Customers paste that Session ID as their Pro License Key in `src/popup.html`, where `src/popup.js` calls `verifyLicense({ key, provider: "stripe", productId: "prod_VeW6ffGaCfNzue,prod_VeW6IYwGyYJkPv" })` (validated against `/verify-license` with offline session-format fallback).

## 2. Chrome Web Store Listing Draft
- **Title**: LinearBridge — Notion PRD to Linear Issues
- **Short Summary (127 chars)**: Turn Notion PRD headings and checklists into Linear parent epics and sub-issues in one click—zero Zapier or backend servers.
- **Keywords**: notion, linear, prd, issue tracker, sub-issues, product management, productivity
- **Permissions Justification**:
  - `storage`: Stores user's Linear Personal API Key, Team ID, weekly Free-tier counter, and Stripe Pro license cache locally.
  - `activeTab` / `scripting`: Reads headings and checklist blocks from the active Notion tab only when the user triggers extraction.
  - Host permissions (`notion.so`, `api.linear.app`, license verification endpoint): Injects the Notion action bar, sends GraphQL mutations directly to Linear, and validates Pro license keys (`/verify-license` with offline session-format fallback).

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact workflow friction surfaced during Stage 1 discovery:
- Target Thread 1 (Linear workflow integration demand): `https://github.com/anthropics/claude-code/issues/12925`
- Target Thread 2 (Linear context-switching friction): `https://news.ycombinator.com/item?id=41960188`

**Reply Template**:
> We hit this exact friction moving specs from Notion into Linear—native integration is read-only link unfurling, and Zapier polling felt overkill for simple PRD checklists. Built a tiny local-first Chrome extension called LinearBridge that parses Notion headings/checkboxes straight into Linear parent + sub-issues using your own API key (nothing stored on third-party servers). Free tier handles 5 issues/week if you want to try it: https://domstijn.github.io/friction-killer-suite/products/notion-linear-prd-sync/. Happy to hear feedback!

## 4. Launch Post Copy (Show HN / r/Linear / X)
- **Title**: Show HN: LinearBridge – Turn Notion PRDs into Linear epics & sub-issues in 1 click (no Zapier)
- **Body**:
  - Linear's built-in Notion integration only unfurls read-only links, so product/eng teams end up copy-pasting PRD checklists manually or maintaining brittle webhook/Zapier scripts.
  - LinearBridge is a lightweight Chrome MV3 extension that runs 100% client-side with your own Linear API key: parses H2/H3 sections + task checkboxes, skips already-tagged `[ENG-123]` lines, creates a Parent Epic + child sub-issues, and syncs live status badges back.
  - Free starter tier gives 5 issues/week; one-time €29 Stripe Pro license key (or €49 All-Access Bundle) unlocks unlimited PRD epics, sub-issues, and status badge sync at https://domstijn.github.io/friction-killer-suite/products/notion-linear-prd-sync/.
