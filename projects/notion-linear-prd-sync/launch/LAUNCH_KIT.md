# Launch & Monetization Kit: LinearBridge (`notion-linear-prd-sync`)

## 1. Checkout & License Key Setup (Lemon Squeezy)
1. Create a product named **LinearBridge Pro** in your Lemon Squeezy dashboard priced at **\$29 one-time**.
2. Enable **License Keys** on the product (suggested activation limit: `3` devices).
3. Copy your Lemon Squeezy **Product ID** and **Checkout URL**.
4. Update before publishing:
   - `projects/notion-linear-prd-sync/launch/landing.html`: replace `#CHECKOUT_URL_HERE` with your live Lemon Squeezy checkout URL.
   - `projects/notion-linear-prd-sync/src/popup.js`: pass `productId: "YOUR_LEMON_SQUEEZY_PRODUCT_ID"` into `verifyLicense(...)` so keys from unrelated products are rejected.

## 2. Chrome Web Store Listing Draft
- **Title**: LinearBridge — Notion PRD to Linear Issues
- **Short Summary (127 chars)**: Turn Notion PRD headings and checklists into Linear parent epics and sub-issues in one click—zero Zapier or backend servers.
- **Keywords**: notion, linear, prd, issue tracker, sub-issues, product management, productivity
- **Permissions Justification**:
  - `storage`: Stores user's Linear Personal API Key, Team ID, weekly Free-tier counter, and Lemon Squeezy license cache locally.
  - `activeTab` / `scripting`: Reads headings and checklist blocks from the active Notion tab only when the user triggers extraction.
  - Host permissions (`notion.so`, `api.linear.app`, `api.lemonsqueezy.com`): Injects the Notion action bar, sends GraphQL mutations directly to Linear, and validates Pro license keys.

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact workflow friction surfaced during Stage 1 discovery:
- Target Thread 1 (Linear workflow integration demand): `https://github.com/anthropics/claude-code/issues/12925`
- Target Thread 2 (Linear context-switching friction): `https://news.ycombinator.com/item?id=41960188`

**Reply Template**:
> We hit this exact friction moving specs from Notion into Linear—native integration is read-only link unfurling, and Zapier polling felt overkill for simple PRD checklists. Built a tiny local-first Chrome extension called LinearBridge that parses Notion headings/checkboxes straight into Linear parent + sub-issues using your own API key (nothing stored on third-party servers). Free tier handles 5 issues/week if you want to try it: [landing page URL]. Happy to hear feedback!

## 4. Launch Post Copy (Show HN / r/Linear / X)
- **Title**: Show HN: LinearBridge – Turn Notion PRDs into Linear epics & sub-issues in 1 click (no Zapier)
- **Body**:
  - Linear's built-in Notion integration only unfurls read-only links, so product/eng teams end up copy-pasting PRD checklists manually or maintaining brittle webhook/Zapier scripts.
  - LinearBridge is a lightweight Chrome MV3 extension that runs 100% client-side with your own Linear API key: parses H2/H3 sections + task checkboxes, skips already-tagged `[ENG-123]` lines, creates a Parent Epic + child sub-issues, and syncs live status badges back.
  - Free starter tier gives 5 issues/week; one-time \$29 Lemon Squeezy license key unlocks unlimited PRD epics, sub-issues, and status badge sync.
