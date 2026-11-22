# Launch & Monetization Kit: WebflowAssetZip (`webflow-cms-asset-migrator`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **WebflowAssetZip Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VfrqznkcHJDx1M`
  - Price ID: `price_1UeW6bH2AcdDmQyRGVHg3TxQ`
  - Payment Link ID: `plink_1UeW6qH2AcdDmQyRemgYPJ35`
  - Live Stripe Payment Link: https://buy.stripe.com/7sY5kD0Ms260aT65hi6sw07
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Product Sales Page**: https://domstijn.github.io/friction-killer-suite/products/webflow-cms-asset-migrator/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=webflow-cms-asset-migrator` and paste it into `src/popup.html`, validated via `verifyLicense({ key, provider: "stripe", productId: "prod_VfrqznkcHJDx1M,prod_VeW6IYwGyYJkPv" })`.

## 2. Chrome Web Store Listing Draft (`Purple Potassium` & `Red Potassium` Safe)
- **Title**: WebflowAssetZip — Webflow CMS Asset & 301 Migrator
- **Short Summary (126 chars)**: Download Webflow CMS CSV & Rich-Text CDN assets by slug, rewrite URLs for Framer/WP/S3, and generate 301 redirect maps.
- **Keywords**: webflow cms export, webflow to framer, cdn url rewriter, rich text image migration, 301 redirects csv
- **Permissions Justification**:
  - `storage`: Stores local Pro license activation status and offline grace cache inside `chrome.storage.local`.
  - **Content Scripts / Host Permissions (`webflow.com`)**: Reads CMS item lists rendered on `webflow.com` to build CSV manifests locally inside Chrome. Does not declare `scripting`, `activeTab`, or `cookies`, and sends zero CMS data to external servers.
- **Screenshot Asset**: `launch/screenshot1280x800.png` (`1280x800`, 24-bit RGB, no alpha, real UI showing Before -> After URL rewrites, asset manifest, `301-redirects.csv`, and popup controls).

## 3. High-Intent Distribution Channels (Marketplaces & Question Replies)
- Never post top-level self-promotional posts on product subreddits (`r/Notion`, `r/vscode`, etc.) that ban promotional posts.
- Prioritize:
  1. **Chrome Web Store** official listing submission
  2. Direct, transparent answers on Webflow Community Forum / Framer Community threads where agencies ask how to migrate `uploads-ssl.webflow.com` Rich-Text `<img>` links and keep SEO redirects without broken images
  3. **Show HN / Portfolio Interactive Demo** linking to https://domstijn.github.io/friction-killer-suite/#playground

**Reply Template for Migration Questions**:
> One thing that catches almost everyone leaving Webflow is that native CMS CSV exports leave both image columns and inline Rich-Text `<img>` tags pointing to `uploads-ssl.webflow.com` — once hosting cancels, those turn into 404s. I packaged a local Chrome MV3 extension (`WebflowAssetZip`) that parses the exported CSV, renames media assets deterministically by item slug, rewrites inline Rich-Text CDN URLs to your new Framer/R2/S3/WordPress base path, and generates a `301-redirects.csv` file locally in the browser. Free tier covers 15 CMS items if you want to test it on a sample export: https://domstijn.github.io/friction-killer-suite/products/webflow-cms-asset-migrator/.
