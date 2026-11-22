# Commercial ROI & Follow-the-Money Market Radar

- **Radar Agent Conversation ID:** `fb4a3e59-d8d5-40c7-97b7-e1c8983cfb6f`
- **Peer Builder Agent Conversation ID:** `1b7fc9cb-b155-4489-bbd3-454f2a96958d`
- **Scan Timestamp:** `2026-11-22T16:29:14+01:00`
- **Portfolio Baseline:** 8 projects tracked in `pipeline/state.json` (active completed project: `stripe-payout-xero-qbo-splitter` / `StripePayoutBridge`; 9 Stripe products live in `pipeline/stripe_catalog.json` including All-Access Bundle)
- **Active Distribution Constraint (Kaizen Cycle 10):** Chrome Web Store is at its `2/2` extension quota (`LinearBridge` + `NotionGuestBridge`). All Top 5 candidates target **Zero-Install 100% Client-Side Browser Web Apps (`saas-addon`)** deployed to GitHub Pages (`docs/`) paired with zero-dependency Python `.whl` CLIs.

---

## Top 5 Ranked Commercial Opportunities

| Rank | ID | Product Title | Ecosystem | Persona | Incumbent SaaS Unbundled | Eff. | Comm. | Sat. | DIY-Res | Composite | Verdict |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `e-invoice-xml-batch-converter` | **EInvoiceLocal**: XRechnung, ZUGFeRD & Peppol UBL/CII XML Validator, Printable PDF & DATEV/Xero Batch Converter | `saas-addon` | `commercial` | Lexoffice / SevDesk / DATEV UO (€19–€79/mo) | 88.25 | 89.25 | 8.5 | 8.5 | **88.5** | **GO** |
| **2** | `camt053-mt940-qbo-xero-converter` | **BankFeedBridge**: ISO 20022 CAMT.053 XML & MT940 to QuickBooks (`.QBO`), Xero (`.OFX`/CSV) & DATEV Converter | `saas-addon` | `commercial` | ProperSoft ($19.99–$49.98/mo), MoneyThumb ($24.95/pack–$599/yr) | 88.25 | 88.0 | 8.5 | 8.5 | **87.75** | **GO** |
| **3** | `eu-oss-vat-return-compiler` | **OssVatBridge**: Stripe, Shopify & Lemon Squeezy to EU VAT OSS Portal Bulk CSV/XML Compiler | `saas-addon` | `commercial` | Quaderno ($49–$149/mo), Lovat ($35–$115/mo), Hellotax/Anrok ($99–$299/mo) | 88.25 | 86.75 | 8.0 | 8.5 | **87.0** | **GO** |
| **4** | `amazon-settlement-xero-qbo-splitter` | **AmzSettlementBridge**: Amazon Seller Flat-File V2 (`.TXT`/`.TSV`) to Xero, QuickBooks & DATEV Clearing Journal Compiler | `saas-addon` | `commercial` | A2X ($29–$199/mo), Link My Books ($17–$199/mo), Synder ($52–$150+/mo) | 86.5 | 86.75 | 8.0 | 8.5 | **86.5** | **GO** |
| **5** | `woo-shopify-metafield-migrator` | **ShopMetaShift**: WooCommerce-to-Shopify Variant Metafield, >3-Option Overflow & 301 Redirect CSV Compiler | `saas-addon` | `commercial` | Matrixify ($20–$200/mo), Cart2Cart/LitExtension ($79–$299+) | 84.5 | 83.0 | 8.0 | 8.0 | **83.25** | **GO** |

> **Pipeline Overlap Note:** None of these 5 slugs have been built in `pipeline/state.json` `projects` yet. `#1 e-invoice-xml-batch-converter` (updated from 86.0 to 88.5 with verified DATEV EXTF `BU-Schlüssel` & dual UBL/CII math validation) and `#5 woo-shopify-metafield-migrator` (83.25) already appear in `opportunities`; `#2`, `#3`, and `#4` are net-new opportunities discovered in this scan.

---

## Deep-Dive Specs (Top 5)

### 1. `e-invoice-xml-batch-converter` (`EInvoiceLocal`) — **88.5 GO**
- **Follow-the-Money Driver:** Mandatory 2025–2026 EU & German B2B e-invoicing laws (*Wachstumschancengesetz* EN 16931 XRechnung/ZUGFeRD, Belgium Peppol 2026, EU ViDA) force SMBs, freelancers, and *Steuerberater* to receive and process raw UBL/CII `.xml` invoices, while GoBD/GDPR rules forbid uploading confidential supplier IBANs, VAT IDs, and line-item pricing to random third-party cloud converters.
- **Verified Competitors & Pricing:** Lexoffice, SevDesk, and DATEV Unternehmen online charge €19–€79/mo recurring; browser tools like Docfaro focus on basic preview/CSV split without unified DATEV `EXTF_Buchungsstapel` `BU-Schlüssel` tax-key mapping, and cloud converters (e.g., Zeit.io, PDF24 online) require off-device processing or only render one file at a time.
- **Why the 2-Minute Free Escape Hatch Fails:** Opening an XRechnung `.xml` in Chrome/Edge or Excel dumps raw `<cbc:...>` / `<cac:...>` tags, fails across dual **UBL 2.1 vs. UN/CEFACT CII** XML syntaxes, cannot verify EN 16931 line-net + VAT = gross math rules, and cannot batch-consolidate hundreds of XML invoices into a balanced DATEV `EXTF_Buchungsstapel.csv` or Xero Bills CSV.
- **1-Paragraph Solution & Free/Pro Split:** A 100% local in-browser Web App (+ Python `.whl` CLI) that parses and validates EN 16931 rules across both UBL 2.1 and CII XML invoices in memory, renders clean printable A4 HTML/PDF invoice views, and batch-compiles directories of XMLs into DATEV `EXTF_Buchungsstapel.csv` (with automatic `BU-Schlüssel` tax keys), Xero Bills CSV, and QuickBooks CSV. **Free:** Validate & render up to 3 XML invoices/batch. **Pro (€29 one-time / €49 Bundle):** Unlimited XML batch consolidation, DATEV EXTF / Xero / QBO batch exports, and CLI folder processing.

### 2. `camt053-mt940-qbo-xero-converter` (`BankFeedBridge`) — **87.75 GO**
- **Follow-the-Money Driver:** The 2025–2026 global SWIFT ISO 20022 migration phases out legacy flat-text **MT940** statements in favor of deeply nested **CAMT.053** XML bank-to-customer statements, stranding QuickBooks and Xero bookkeepers who refuse to pay ProperSoft ($19.99–$49.98/mo) or MoneyThumb ($24.95/5-pack to $599/yr) just to load bank statements locally.
- **Verified Competitors & Pricing:** ProperSoft (`ProperConvert`) charges $19.99/mo ($179.99/yr) single-user or $49.98/mo ($449.97/yr) team; MoneyThumb charges $24.95/bundle up to $599.95/yr; cloud converters (QuickFinSync, ValidateFin, BankConvert) force corporate treasurers to upload raw bank balances and counterparty IBANs to cloud servers.
- **Why the 2-Minute Free Escape Hatch Fails:** QuickBooks Online and QuickBooks Desktop have zero native CAMT.053 XML importer and reject generic `.ofx` files lacking a whitelisted `<INTU.BID>` Bank ID or deterministic unique `<FITID>` tags; opening CAMT.053 XML in Excel flattens nested `<NtryDtls>` batch breakdowns and breaks `<CdtDbtInd>` (`CRDT`/`DBIT`) debit/credit signs.
- **1-Paragraph Solution & Free/Pro Split:** A 100% client-side Browser Web App (+ Python `.whl` CLI) that parses multi-account ISO 20022 `camt.053.001.02`/`.08` XML and legacy MT940 statements locally, flattens SEPA `EndToEndId` / IBAN / remittance metadata, and outputs QuickBooks Web Connect (`.qbo` with valid `<INTU.BID>` lookup and SHA-derived `<FITID>`), Xero (`.ofx` / CSV), and DATEV bank batch CSVs. **Free:** Convert up to 10 transactions per file (matching ProperSoft's trial cap). **Pro (€29 one-time / €49 Bundle):** Unlimited rows, multi-statement batch merge, `.qbo` bank-ID selector, and DATEV/Xero exports.

### 3. `eu-oss-vat-return-compiler` (`OssVatBridge`) — **87.0 GO**
- **Follow-the-Money Driver:** Businesses migrating off Merchant-of-Record platforms (Lemon Squeezy wind-down) to Stripe Tax or Shopify suddenly inherit quarterly **EU VAT One Stop Shop (OSS)** filing obligations—and face $49–$299/mo SaaS lock-in just to generate 4 quarterly portal upload files per year.
- **Verified Competitors & Pricing:** Quaderno ($49–$149/mo), Lovat Compliance ($35–$115/mo), Hellotax / Taxually / Anrok ($99–$299/mo) all charge monthly recurring subscriptions and require permanent live OAuth credentials to Stripe/Shopify.
- **Why the 2-Minute Free Escape Hatch Fails:** Raw Stripe Tax and Shopify exports list individual per-charge rows across mixed currencies (USD/GBP/SEK) using dot decimals and comma delimiters; national OSS portals (Germany BZSt/BOP with 1,000-row caps, semicolon `;` delimiters, comma decimals, and strict UTF-8; Ireland ROS XML; Finland MyTax CSV) immediately reject un-aggregated Stripe/Shopify CSVs.
- **1-Paragraph Solution & Free/Pro Split:** A 100% local in-browser Web App (+ Python `.whl` CLI) that ingests Stripe Tax, Shopify, and Lemon Squeezy transaction CSVs, normalizes foreign currencies to EUR via ECB quarterly/daily FX tables, aggregates taxable bases and VAT by EU27 Member State of Consumption and rate tier (Standard/Reduced), and exports ready-to-upload Germany BZSt/BOP `;`-CSV, Ireland ROS XML, and EU27 OSS audit ledgers. **Free:** Parse & preview up to 15 rows + Member-State summary. **Pro (€29 one-time / €49 Bundle):** Unlimited rows, multi-CSV merge, BZSt/BOP CSV + ROS XML exports, and credit-note/refund netting.

### 4. `amazon-settlement-xero-qbo-splitter` (`AmzSettlementBridge`) — **86.5 GO**
- **Follow-the-Money Driver:** Natural sister-product expansion following `StripePayoutBridge`: Amazon FBA sellers and e-commerce CPAs reject paying $29–$199/mo recurring + granting permanent SP-API & Xero/QBO OAuth access to A2X or Link My Books for bi-weekly settlement journal creation.
- **Verified Competitors & Pricing:** A2X ($29–$199/mo), Link My Books ($17–$199/mo), Synder ($52–$150+/mo) gate volume by monthly order tiers and require live API connections.
- **Why the 2-Minute Free Escape Hatch Fails:** Amazon Seller Central Flat-File V2 (`.txt`/`.tsv`) dumps thousands of multi-row order/SKU lines across 40+ fee codes (`FBAPerUnitFulfillmentFee`, `Commission`, `StorageFee`, `Advertising`) plus rolling **Account-Level Reserves** (previous reserve release vs. current reserve holdback); manual Excel pivot tables regularly break on multi-currency/cent rounding mismatches.
- **1-Paragraph Solution & Free/Pro Split:** A 100% local in-browser Web App (+ Python `.whl` CLI) that ingests Amazon Flat-File V2 `.txt`/`.tsv` settlements, aggregates 40+ fee/tax/refund/reserve codes into a zero-variance clearing journal, and exports Xero Manual Journal CSV, QuickBooks Journal CSV, and DATEV `EXTF` CSV. **Free:** Preview 1 settlement up to 15 rows. **Pro (€29 one-time / €49 Bundle):** Unlimited rows, multi-settlement batching, rolling reserve carry-forward ledger, and accounting CSV exports.

### 5. `woo-shopify-metafield-migrator` (`ShopMetaShift`) — **83.25 GO**
- **Follow-the-Money Driver:** Agencies and Shopify merchants migrating WooCommerce catalogs refuse Matrixify's recurring SaaS lock-in ($20–$200/mo) or $79–$299+ store-credential migration tools when they simply need deterministic CSV restructuring and SEO URL preservation.
- **Verified Competitors & Pricing:** Matrixify ($20–$200/mo), DataEase, Altera, Cart2Cart / LitExtension ($79–$299+ per store migration).
- **Why the 2-Minute Free Escape Hatch Fails:** Shopify's native Product CSV importer drops variant-level custom fields entirely, enforces a hard 3-option limit, and splits variable products into broken standalone SKUs unless parent/child handles, typed `Variant Metafield: custom.key [type]` columns, and `/product/` to `/products/` 301 redirects are generated cleanly.
- **1-Paragraph Solution & Free/Pro Split:** A 100% local in-browser Web App (+ Python `.whl` CLI) that converts WooCommerce product/variation CSVs into Shopify Admin & Matrixify-compliant multi-row CSVs with typed metafield headers, >3 attribute overflow mapping, and `301-redirects.csv`. **Free:** Up to 15 parent/variant products. **Pro (€29 one-time / €49 Bundle):** Unlimited SKUs, custom metafield typing, >3 option flattening, and 301 redirect map export.

---

## Hard Kill-Switch Audit (Rejected Candidates)

| Candidate | Buyer Persona | Saturation | Verdict & Kill Reason |
| :--- | :---: | :---: | :--- |
| `har-pii-sanitizer` (HAR Cookie/PII Scrubber) | `dev-config` | 3.5 | **NO-GO:** Chrome 130+ introduced native `Export HAR (sanitized)` by default, stripping `Cookie`, `Set-Cookie`, and `Authorization` headers in 1 click (solves >=50% for free). |
| `hubspot-jira-bulk-csv-exporter` | `b2b-operator` | 3.0 | **NO-GO:** HubSpot free-tier native Data Management export (`Imports & Exports`) and Jira JQL `Export to CSV` + a 15-line REST pagination script solve >=80% of cases without $49–$99/mo apps. |
| `claude-project-sync` | `dev-config` | 3.5 | **NO-GO:** `buyer_persona='dev-config'` (`willingness_to_pay < 6.5`) and free Chrome extensions (*Claude Project Downloader*, *Claude Exporter*) already export full projects in 1 click. |
| `ai-agent-undo-shield` | `dev-config` | 4.0 | **NO-GO:** `buyer_persona='dev-config'` (`willingness_to_pay < 6.5`) and native `.claude/settings.local.json` `permissions.deny` + free OSS hooks solve >=50% in 2 minutes. |

---

## Recommended Next Build Sequence for Builder Agent

1. **Build First (`88.5 GO`): `e-invoice-xml-batch-converter` (`EInvoiceLocal`)** — Highest urgency forced statutory deadline (Belgium Peppol B2B live Jan 1, 2026; Germany EN 16931 receipt active Jan 1, 2025 & issuance Jan 1, 2027), strong GoBD/GDPR local-first moat, zero CWS quota dependency (`saas-addon` + `.whl` CLI), and natural cross-sell inside our existing `StripePayoutBridge` / `All-Access Bundle` accounting storefront.
2. **Build Second (`87.75 GO`): `camt053-mt940-qbo-xero-converter` (`BankFeedBridge`)** — Direct forced SWIFT ISO 20022 MT940 deprecation wave with high-WTP QuickBooks/Xero/DATEV bookkeepers fleeing ProperSoft ($180–$450/yr) and MoneyThumb ($599/yr).
3. **Build Third (`87.0 GO`): `eu-oss-vat-return-compiler` (`OssVatBridge`)** — Direct post-`LemonExitBridge` cross-sell capturing Lemon Squeezy / Stripe / Shopify merchants facing quarterly EU OSS filing crunches without paying $49–$299/mo to Quaderno/Lovat/Anrok.

---

## High-Intent Buyer Forums, SEO Wedges & 2026 Compliance Watchlist

### Distribution & Buyer Channels (Top 3)
- **`EInvoiceLocal` (`#1`):** `r/Steuerberater`, `r/selbststaendig`, DATEV Community, Lexware Office forums, Belgian SME/VAT accountant communities. Sniper SEO: `"XRechnung XML zu DATEV CSV ohne Cloud"`, `"ZUGFeRD XML viewer GDPR offline"`, `"Peppol BIS 3.0 XML to Excel CSV batch"`.
- **`BankFeedBridge` (`#2`):** `r/Bookkeeping`, Intuit QuickBooks Community (`INTU.BID` / Web Connect error threads), Xero Central forums. Sniper SEO: `"CAMT.053 XML to QBO Web Connect"`, `"CSV to QBO without ProperSoft"`, `"MT940 deprecated CAMT.053 to Xero OFX"`.
- **`OssVatBridge` (`#3`):** `r/SaaS`, `r/microsaas`, IndieHackers, Shopify Community EU VAT threads, and direct `LemonExitBridge` post-migration users. Sniper SEO: `"Stripe Tax CSV to Germany BZSt BOP OSS CSV"`, `"EU VAT OSS return without Quaderno"`, `"Lemon Squeezy shutdown Stripe Tax EU VAT OSS"`.

### 2026–2027 Compliance & API Shifts Watchlist
- **Belgium Mandatory B2B Peppol E-Invoicing (Jan 1, 2026) & Germany B2B Issuance (Jan 1, 2027):** *Active Tailwind* — Prioritizes Peppol BIS Billing 3.0 UBL `.xml` parsing inside `EInvoiceLocal` alongside German XRechnung (UBL/CII) and ZUGFeRD.
- **Lemon Squeezy Shutdown (Nov 16, 2026 Cutoff / March 31, 2027 EOL):** *Active Tailwind* — Direct funnel synergy between Builder's active `LemonExitBridge` and Radar `#3` `OssVatBridge`.
- **Shopify Scripts EOL (June 30, 2026) & Additional Scripts Deprecation (Aug 2026):** *Watchlist (Low Zero-Backend Fit)* — Requires Shopify Functions / Partner App OAuth rather than zero-backend static web apps.
- **UK HMRC MTD for Income Tax (April 2026):** *Watchlist (API Gate)* — HMRC mandates recognized OAuth API bridging software + Fraud Prevention Headers for quarterly submissions, limiting standalone static CSV tools.
