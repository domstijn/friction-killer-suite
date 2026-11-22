# Launch & Monetization Kit: AmzSettlementBridge (`amazon-settlement-xero-qbo-splitter`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **AmzSettlementBridge Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_Vg2d5RyhHCcgKb`
  - Price ID: `price_1UegYDH2AcdDmQyR3BtJxnPh`
  - Payment Link ID: `plink_1UegYQH2AcdDmQyRvfHDd0kD`
  - Live Stripe Payment Link: https://buy.stripe.com/bJefZh66M2601iw6lm6sw0b
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Zero-Install Web App & Sales Page**: https://domstijn.github.io/friction-killer-suite/products/amazon-settlement-xero-qbo-splitter/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=amazon-settlement-xero-qbo-splitter` and paste it inside the Web App or run `amazon-settlement-xero-qbo-splitter --activate KEY` (`prod_Vg2d5RyhHCcgKb,prod_VeW6IYwGyYJkPv`).

## 2. Distribution Channels & Sniper SEO Targets
- **Zero-Install Web App (Primary)**: Direct link to https://domstijn.github.io/friction-killer-suite/products/amazon-settlement-xero-qbo-splitter/ — parses Amazon Flat-File V2 `.txt`/`.tsv` exports 100% locally inside Chrome with zero SP-API OAuth credentials.
- **Python CLI & Wheel (`.whl`)**: Distributed via GitHub Pages & Releases (`pip install amazon_settlement_xero_qbo_splitter-0.1.0-py3-none-any.whl`).
- **Primary Long-Tail SEO Keywords**:
  - `"Amazon settlement flat file V2 to Xero CSV without A2X"`
  - `"Amazon Seller payout journal QuickBooks without Link My Books"`
  - `"Amazon Flat-File V2 TSV to DATEV EXTF Buchungsstapel"`

## 3. HN / Bookkeeping Community Reply Draft (Educational, No Sales Pitch)
> If you're reconciling Amazon Seller Central payouts into Xero, QuickBooks, or DATEV from Flat-File V2 `.tsv` exports manually rather than granting an API connector OAuth access, three schema quirks usually break pivot tables: (1) row 2 is a summary header carrying `total-amount` with an empty `amount` field, so naive CSV sums either miss or double-count it; (2) `MarketplaceFacilitatorTax-Principal` / `ItemWithheldTax` and `RefundCommission` lines have to be split away from gross sales vs. selling fees to keep VAT returns clean; and (3) `Previous Reserve Amount Balance` releases (+) and `Current Reserve Amount` holdbacks (-) must go to a rolling clearing reserve asset/liability line or Debits won't equal your bank deposit.
>
> I put together a client-side browser utility (plus offline Python CLI) that parses Flat-File V2 `.txt`/`.tsv` exports in memory, skips the summary header double-count, verifies Debits == Credits in integer cents, and maps directly to Xero, QuickBooks, and DATEV EXTF CSVs: https://domstijn.github.io/friction-killer-suite/products/amazon-settlement-xero-qbo-splitter/
