# Launch & Monetization Kit: OssVatBridge (`eu-oss-vat-return-compiler`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **OssVatBridge Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_Vg2IUi88B9bJHq`
  - Price ID: `price_1UegEOH2AcdDmQyRuHlzHBAH`
  - Payment Link ID: `plink_1UegEpH2AcdDmQyRyg6cgvUZ`
  - Live Stripe Payment Link: https://buy.stripe.com/00w6oH52I7qk2mA6lm6sw0a
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Zero-Install Web App & Sales Page**: https://domstijn.github.io/friction-killer-suite/products/eu-oss-vat-return-compiler/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=eu-oss-vat-return-compiler` and paste it inside the Web App or run `eu-oss-vat-return-compiler --activate KEY` (`prod_Vg2IUi88B9bJHq,prod_VeW6IYwGyYJkPv`).

## 2. Distribution Channels & Sniper SEO Targets
- **Zero-Install Web App (Primary)**: Direct link to https://domstijn.github.io/friction-killer-suite/products/eu-oss-vat-return-compiler/ — runs 100% locally in Chrome with zero customer order CSVs leaving the browser.
- **Python CLI & Wheel (`.whl`)**: Distributed via GitHub Pages & Releases (`pip install eu_oss_vat_return_compiler-0.1.0-py3-none-any.whl`).
- **Primary Long-Tail SEO Keywords**:
  - `"Stripe Tax CSV to Germany BZSt BOP OSS CSV"`
  - `"EU VAT OSS return without Quaderno"`
  - `"Shopify Lemon Squeezy EU VAT OSS return compiler"`
- **Cross-Sell Funnel (`LemonExitBridge` &rarr; `OssVatBridge`)**: Founders migrating off Lemon Squeezy before March 31, 2027 via `LemonExitBridge` inherit direct quarterly EU VAT OSS reporting obligations on Stripe Tax / Shopify; cross-linked directly inside both product pages and the All-Access Bundle.

## 3. HN-Compliant Educational Reply Drafts (No Sales/Pricing Pitch)
**Draft for EU VAT OSS / Stripe Tax / Lemon Squeezy Migration Threads**:
> When moving off an MoR onto Stripe Tax or Shopify and compiling quarterly EU VAT OSS returns manually, four schema quirks tend to trip portal uploads: (1) Greece must use `EL` rather than ISO `GR` as MSCON; (2) domestic sales in your own Member State of Identification, non-EU orders, and zero-tax B2B reverse-charge transactions have to be stripped before aggregation; (3) refunds need to net inside the same `(MSCON, rate_type)` bucket; and (4) Germany's BZSt BOP bulk uploader rejects standard UTF-8 commas and dot decimals—it requires semicolon delimiters and comma decimals capped at 1,000 rows per file.
>
> I put together a client-side browser utility (plus offline Python CLI) that merges exported Stripe Tax / Shopify / Lemon Squeezy CSVs locally in memory, applies ECB quarterly FX rates, normalizes `GR` &rarr; `EL`, and outputs balanced BZSt BOP semicolon CSVs and ROS-style XML without uploading store data: https://domstijn.github.io/friction-killer-suite/products/eu-oss-vat-return-compiler/
