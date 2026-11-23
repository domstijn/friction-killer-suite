# Product & Technical Spec: ShopMetaShift (`woo-shopify-metafield-migrator`)

- **Ecosystem**: `saas-addon`
- **Host Software**: WooCommerce to Shopify / Matrixify CSV
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `acct_1UdCWDH2AcdDmQyR`, EUR, `txcd_10103000`)

## 1. Pain & Evidence
- **Exact Friction**: Agencies and merchants migrating WooCommerce variable catalogs to Shopify hit three hard native CSV failures: (1) Shopify drops variant-level custom `Meta:` fields and requires strict typed `Variant Metafield: custom.key [type]` columns, (2) Shopify caps native options at 3 (`Option1`–`Option3`) breaking 4+ attribute products, and (3) WooCommerce exports flat/variation rows referencing `id:<ID>` or parent `SKU` alongside `/product/<slug>/` & `/product-category/...` URLs that cause 404 SEO losses without `301-redirects.csv`.
- **Verified Alternatives & Why They Fail**:
  - Matrixify charges $20–$200/mo recurring SaaS fees; Cart2Cart / LitExtension charge $79–$299+ per migration and require live WordPress/Shopify API tokens. Native Shopify CSV templates drop variant metafields and fail on >3 attributes.

## 2. Target Persona & Value Proposition
- **Who pays**: Shopify agencies, freelance e-commerce developers, and DTC store owners migrating WooCommerce CSV catalogs cleanly in 60 seconds without $20–$200/mo subscriptions or granting third-party API credentials.
- **10x Relief**: Drop any WooCommerce Product Export CSV directly into Chrome (100% browser-local, zero server uploads) or pass CSVs to the offline Python `.whl` CLI to join `variable` + `variation` rows (`id:<ID>` or parent `SKU`), promote >3 overflow attributes, auto-type `Meta:` columns (`number_integer`, `number_decimal`, `boolean`, `date`, `url`, `json`, `multi_line_text_field`, `single_line_text_field`), normalize EU comma decimals & units to grams, and export Shopify Admin CSV, Matrixify CSV, and `shopify-301-redirects.csv`.

## 3. Free vs. Pro Feature Split
- **Free Tier**: Parses, validates, auto-types metafields, detects >3 attribute overflow, and previews/downloads Shopify Admin CSV for up to `FREE_PRODUCT_LIMIT = 15` parent/standalone products.
- **Pro Tier (€29 one-time / €49 All-Access Bundle, Stripe Checkout `cs_live_...` or `SHOPMETA-...`)**: Unlocks unlimited products/SKUs plus full exports for **Matrixify Multi-Row CSV**, **301 Redirects CSV**, **Shopify Admin Unlimited CSV**, and JSON Audit Report (`--out-dir` in CLI & Pro buttons in Web App).

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 621 / setuptools config (`woo-shopify-metafield-migrator = "cli:main"`) for zero-dep `.whl` distribution
- `src/addon.py` — Pure stdlib WooCommerce-to-Shopify parent/variation joiner, >3-option overflow handler, metafield type inferencer & CSV/redirect exporter
- `src/cli.py` — CLI wrapper supporting repeatable CSV inputs (`--input`), `--out-dir`, `--weight-unit`, `--overflow-mode`, `--no-category-redirects`, `--activate`, `--pro`, `--telemetry`, `--sample-csv`
- `src/license_client.py` — Zero-backend license verifier (`cs_live_...` / offline cache)
- `tests/test_addon.py` — Deterministic tests covering variable/variation joining, EU decimals/units, >3 attribute modes, metafield auto-typing, 301 redirects, Free 15-product cap, and Pro unlock
- `launch/landing.html` — Standalone Tailwind landing page + `#live-app` browser CSV parser & exporter
- `launch/LAUNCH_KIT.md` — Stripe Managed Payments metadata, SEO targets, and non-spammy migration community reply draft

## 5. Verification Plan
1. Run `python3 -m unittest discover -s projects/woo-shopify-metafield-migrator/tests -v`
2. Verify Free tier caps output at `FREE_PRODUCT_LIMIT = 15` and Pro exporters raise `PermissionError` / CLI `--out-dir` exits `2` until activated
3. Run `python3 scripts/ship_check.py --slug woo-shopify-metafield-migrator --package` and `node --check` on Web App JS
