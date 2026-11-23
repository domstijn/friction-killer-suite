# Launch & Monetization Kit: ShopMetaShift (`woo-shopify-metafield-migrator`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **ShopMetaShift Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VgOLfg5TiKHhLU`
  - Price ID: `price_1Uf1Z2H2AcdDmQyRZiTbmdRo`
  - Payment Link ID: `plink_1Uf1ZGH2AcdDmQyRh6FDkQQO`
  - Live Stripe Payment Link: https://buy.stripe.com/6oU8wPan2fWQ8KY4de6sw0d
  - Success URL: `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=woo-shopify-metafield-migrator`
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Zero-Install Web App & Sales Page**: https://domstijn.github.io/friction-killer-suite/products/woo-shopify-metafield-migrator/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `success.html` (`localStorage["fk_shopmeta_pro_state"]` auto-unlocked) or run `woo-shopify-metafield-migrator --activate KEY` (`prod_VgOLfg5TiKHhLU,prod_VeW6IYwGyYJkPv`).

## 2. Distribution Channels & High-Intent SEO Targets
- **Zero-Install Web App (Primary)**: Browser CSV parser with zero uploads of supplier cost (`_wc_cog_cost`) or catalog data.
- **Python CLI & Wheel (`.whl`)**: Distributed via PyPI (`woo-shopify-metafield-migrator` once PyPI cooldown resets) & GitHub Releases.
- **Primary Long-Tail SEO Keywords**:
  - `"WooCommerce to Shopify variant metafields CSV without Matrixify"`
  - `"Shopify 3 option limit WooCommerce CSV overflow"`
  - `"WooCommerce to Shopify 301 redirects CSV"`

## 3. Educational Community Reply Draft (No Sales Pitch)
> When importing a WooCommerce Product CSV into Shopify Admin, three things usually break silently: (1) WooCommerce links `variation` rows via either `id:<ID>` or parent `SKU`, and Shopify drops the parent if product columns (`Title`, `Body`, `Vendor`) are repeated or missing on variant rows 2..N; (2) any fourth product attribute hits Shopify's 3-option cap unless promoted to `Variant Metafield: custom.attr [single_line_text_field]` (or merged into `Option3`); and (3) WooCommerce `/product/<slug>/` + `/product-category/...` URLs need a matching 301 CSV before DNS cutover.
>
> I put together an offline, browser-local CSV compiler (+ Python `.whl` CLI) that handles parent/variation stitching, EU comma decimals -> grams, metafield type inference (`number_integer`, `boolean`, `date`, `json`), and 301 generation without sharing store API keys: https://domstijn.github.io/friction-killer-suite/products/woo-shopify-metafield-migrator/
