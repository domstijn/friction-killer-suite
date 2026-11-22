# Product & Technical Spec: WebflowAssetZip (`webflow-cms-asset-migrator`)

- **Ecosystem**: `browser-extension` (Chrome MV3 Extension + ESM Core)
- **Host Software**: Webflow CMS (to Framer / WordPress / Next.js)
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`; €29 one-time EUR tax-inclusive Pro license / €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)

## 1. Pain & Evidence
- **Exact Friction**: Webflow CMS CSV exports keep all image columns and inline Rich-Text HTML `<img>` / `srcset` URLs hotlinked to `uploads-ssl.webflow.com` or `cdn.prod.website-files.com`. Once Webflow hosting is canceled during migration to Framer, WordPress, or Next.js, every hotlinked media asset turns into a `404` and URL slug transitions break SEO unless a `301-redirects.csv` map is generated.
- **Evidence**: Stage 1 commercial discovery across Webflow-to-Framer / Next.js migration guides (`gr8rstudio.com`, `framexport.io`, `webflow.com` Asset Exporter gaps).
- **Why Existing Alternatives Fail**: Native Webflow `Export CSV` only outputs expiring/hosted CDN links; *Webflow Asset Exporter* dumps raw unnamed files without mapping to CMS slugs, rewriting CSV columns, rewriting Rich-Text HTML `<img>` tags, or generating `301` redirect rules.

## 2. Target Persona & Value Proposition
- **Who pays**: Webflow agencies, freelance web designers, and migration teams moving client CMS collections to Framer, WordPress, or Cloudflare R2/S3.
- **10x Relief**: Parses exported Webflow CMS CSVs or open Webflow CMS Designer views in one click, maps every Webflow CDN image to deterministic `{slug}-{field}-{idx}.{ext}` filenames, rewrites CSV & inline Rich-Text HTML URLs to the new target host, and generates a `301-redirects.csv` import file locally in Chrome.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (€0)**:
  - Audits the full Webflow CMS CSV (row count, direct media CDN URLs, inline Rich-Text `<img>` hotlinks) and rewrites direct media columns for up to `15` CMS items (`FREE_ITEM_CAP = 15`).
- **Pro Tier (€29 one-time EUR via Stripe Managed Payments `acct_1UdCWDH2AcdDmQyR` — or €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)**:
  - **Unlimited CMS Items**: No `15`-item cap across large multi-hundred-row Webflow collections.
  - **Deep Rich-Text HTML `<img>` & `srcset` Rewriting**: Extracts and rewrites inline Webflow CDN URLs embedded inside HTML Rich-Text bodies.
  - **`301-redirects.csv` Pack & Deterministic Asset Manifest**: Outputs full `{slug}-{field}-{idx}.{ext}` download mapping and `/old-prefix/{slug}` -> `/new-prefix/{slug}` 301 redirect CSV.

## 4. Minimal Architecture & File Map
- `manifest.json` — Chrome MV3 config (`"permissions": ["storage"]`, `webflow.com` host permissions only — zero unused `scripting`).
- `src/license_client.js` — Stripe Managed Payments validator (`cs_live_...` + `/verify-license`) with 7-day offline cache & bundle product ID support.
- `src/cms_migrator.js` — RFC-4180 CSV parser/serializer, Webflow CDN extractor, Rich-Text `<img>`/`srcset` rewriter, slug asset renamer, Free item cap, and `301-redirects.csv` generator.
- `src/background.js` — Service worker orchestrating Free vs. Pro CSV migration and license verification.
- `src/content.js` — Floating `#webflowassetzip-bar` toolbar and DOM CMS collection extractor on Webflow pages.
- `src/popup.html` & `src/popup.js` — Popup UI for CSV upload/paste, target CDN base URL, Pro toggles, output copy/download, and Stripe key activation.
- `tests/smoke_test.py` — Manifest validation + Node.js ESM tests covering Free cap, Pro gates, Rich-Text CDN rewriting, `301-redirects.csv`, and Stripe activation.

## 5. Verification Plan
1. Run `python3 projects/webflow-cms-asset-migrator/tests/smoke_test.py`.
2. Run `python3 scripts/ship_check.py --slug webflow-cms-asset-migrator --package` (verifies `Purple Potassium` permissions, `Red Potassium` `1280x800` screenshot, and headless Chromium `#webflowassetzip-bar` DOM injection).
