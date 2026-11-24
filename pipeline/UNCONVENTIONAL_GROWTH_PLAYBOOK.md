# Unconventional B2B Growth & Client-Acquisition Playbook

> **Why UGC Fails Here (And What Replaces It):**
> Nobody scrolls TikTok hoping to convert ISO 20022 `CAMT.053` XMLs or debug EN 16931 `BR-CO-10` tax errors. B2B finance & ops tools are **high-urgency panic-search products**: buyers search exact error codes, broken incumbent names, or regulatory deadlines the exact hour their import fails. Every asset below is wired with `?ref=src.<channel>` attribution into our EU Cloudflare D1 funnel (`GROWTH_SCORECARD.md`).

---

## Rank 1: Programmatic "Panic-Search" + Localized DACH Footprint (Deployed Live Tonight)

Instead of competing on broad keywords, capture exact error strings, format pairs, and German/EU compliance searches:

- **Native German (`/de/`) Storefront:**
  - `/de/` (`?ref=src.de-hub`), `/de/xrechnung-zugferd-konverter/`, `/de/camt053-mt940-datev-konverter/`, `/de/bzst-oss-csv-konverter/`
- **20 Technical Troubleshooting Guides (`/guides/`):**
  - `quickbooks-error-ol-222-camt053-fix`, `camt053-to-quickbooks-qbo-converter`, `mt940-sta-to-xero-ofx-csv`, `ing-rabobank-abn-amro-camt053-xero-qbo`, `sparkasse-volksbank-camt053-datev-csv`, `propersoft-bank2qbo-alternative-local`, `sepa-batch-ntrydtls-txdtls-reconciliation`, `xrechnung-xml-zu-pdf-und-datev-extf`, `en16931-br-co-10-br-co-15-validation-errors`, `zugferd-xml-datev-bu-schluessel-mapping`, `peppol-bis-3-xml-to-pdf-xero-csv`, `quba-viewer-alternative-browser-einvoice`, `bzst-oss-csv-gr-el-greece-error-fix`, `stripe-tax-shopify-eu-oss-vat-return`, `ireland-ros-eu-oss-xml-generator`, `lemon-squeezy-shutdown-paypal-stripe-migration`, `lemon-squeezy-to-polar-legacy-license-keys`, `woocommerce-to-shopify-metafields-matrixify-csv`, `amazon-settlement-report-v2-xero-quickbooks`, `stripe-payout-reconciliation-xero-quickbooks`
- **"Trojan Horse" Zero-Paywall Diagnostic Calculators (`/tools/`):**
  - **2026 EU-27 VAT Rates & BZSt `GR→EL` Checker:** `https://domstijn.github.io/friction-killer-suite/tools/eu-oss-vat-rates-2026/`
  - **Lemon Squeezy Shutdown PayPal MRR Risk Calculator:** `https://domstijn.github.io/friction-killer-suite/tools/lemon-squeezy-shutdown-calculator/`
  - **DATEV `BU-Schlüssel` & EN 16931 Lookup:** `https://domstijn.github.io/friction-killer-suite/tools/datev-bu-schluessel-lookup/`
- **Open Sample Test Fixtures (`/samples/`):**
  - Real valid `.xml`, `.sta`, and `.csv` test files (`sample-xrechnung-3.0-ubl.xml`, `sample-zugferd-cii-en16931.xml`, `sample-peppol-bis3-invoice.xml`, `sample-camt053-001-08-sepa-batch.xml`, `sample-swift-mt940-statement.sta`, `sample-eu-oss-stripe-shopify.csv`).
- **AI / GEO Citation Index:** `/llms.txt` & `/llms-full.txt` indexed via `robots.txt` & IndexNow.

---

## Rank 2: Live GitHub Buyer Radar + Open-Source Curated Awesome-Lists (`gh api` Verified)

### A. Automated Buyer Radar CLI (`scripts/find_buyers.py`)
Run `python3 scripts/find_buyers.py --days 14 --save pipeline/FRESH_BUYER_SIGNALS.md` before any manual reply sprint to pull newly updated `open`, `locked=false` issues across `XRechnung`, `ZUGFeRD`, `CAMT.053`, `MT940`, `BZSt OSS`, `Lemon Squeezy migrate`, `WooCommerce Shopify metafields`, and `ProperSoft` (pre-tagged `?ref=src.gh-sniper`).

### B. 14 Active, Unarchived Awesome-List PR Targets (`gh api` verified, `archived: false`)
1. `vinta/awesome-python` (336k★) — CLI file/e-invoice converters
2. `hesreallyhim/awesome-claude-code` (58.7k★) — `ClaudeProfileSwitch` ([url](https://domstijn.github.io/friction-killer-suite/products/claude-profile-switcher/?ref=src.gh-awesome-claude))
3. `viatsko/awesome-vscode` (29.2k★) — `ExtProfileLock` ([url](https://domstijn.github.io/friction-killer-suite/products/vscode-workspace-profile-config/?ref=src.gh-awesome-vscode))
4. `mundimark/awesome-markdown` (1.9k★) — `NotionGitExport` ([url](https://domstijn.github.io/friction-killer-suite/products/notion-clean-md-exporter/?ref=src.gh-awesome-md))
5. `spencerpauly/awesome-notion` (851★) — `NotionLinear` & `NotionGitExport` & `NotionGuestBridge`
6. `lukecav/awesome-woocommerce` (447★) — `ShopMetaShift` ([url](https://domstijn.github.io/friction-killer-suite/products/woo-shopify-metafield-migrator/?ref=src.gh-awesome-woo))
7. `alexanderop/awesome-local-first` (249★) — Zero-upload browser Web Apps (`EInvoiceLocal`, `BankFeedBridge`)
8. `dalys/awesome-linear` (147★) — `LinearBridge` ([url](https://domstijn.github.io/friction-killer-suite/products/notion-linear-prd-sync/?ref=src.gh-awesome-linear))
9. `awelist/awesome-fintech` (27★) — `BankFeedBridge`, `OssVatBridge`
10. `Webflow-Examples/awesome-webflow` (25★) — `WebflowAssetZip` ([url](https://domstijn.github.io/friction-killer-suite/products/webflow-cms-asset-migrator/?ref=src.gh-awesome-webflow))
11. `friends-of-shopify/Awesome-Shopify` (8★) — `ShopMetaShift`
12. `awelist/awesome-stripe` (4★) — `StripePayoutBridge`, `LemonExitBridge`, `OssVatBridge`
13. `causa-prima-ai/awesome-invoicing` (2★) — `EInvoiceLocal`
14. `e-invoice-be/awesome-peppol` (0★) — `EInvoiceLocal` (Peppol BIS 3.0 UBL viewer/exporter)

*(Note: `agarrharr/awesome-cli-apps` was checked via `gh api` on 2026-11-24 and found `archived: true` — excluded.)*

---

## Rank 3: "Alternative-To" High-Intent Incumbent Intercept Listings

Submit free product listings targeting people already searching for expensive subscriptions or broken tools:

| Target Directory | Incumbent Replaced | Our Tool & Tracked Link | Key Positioning Hook |
| :--- | :--- | :--- | :--- |
| `alternativeto.net/software/propersoft-conversion-tools/` (`manage-item/`) | ProperSoft Bank2QBO / CSV2QBO (\$19.99–\$49/mo) | **BankFeedBridge** (`?ref=src.alternativeto`) | €29 once vs \$239–\$599/yr; browser-local CAMT.053 & MT940 with `<INTU.BID>` & OPBD/CLBD audit |
| `alternativeto.net/software/matrixify/` | Matrixify / Cart2Cart one-off cutovers | **ShopMetaShift** (`?ref=src.alternativeto`) | Free 15-product / €29 unlimited WooCommerce >3-option Matrixify + 301 Redirect CSV without live Admin API keys |
| `alternativeto.net/software/taxjar/` & `synder/` | TaxJar / Taxamo / Synder / A2X | **OssVatBridge** & **StripePayoutBridge** (`?ref=src.alternativeto`) | Zero OAuth token; BZSt BOP CSV (`GR→EL`), Ireland ROS XML, Stripe/Amazon clearing journals for €29 once |
| `saashub.com/submit` | ProperSoft, Quba Viewer, A2X, Matrixify | Suite + top 4 converters (`?ref=src.saashub`) | Zero-subscription local-first Chrome apps + PyPI CLIs |
| `omr.com/de/reviews/` & `trusted.de` | German XML upload viewers & Steuersoftware | **EInvoiceLocal** & **OssVatBridge** (`/de/.../?ref=src.omrreviews`) | 100% DSGVO-konform im Browser (ohne Cloud-Upload) + DATEV EXTF |
| `sourceforge.net/software/vendors/`, `g2.com/sellers`, `capterra.com/vendors` | ProperSoft, Synder, LitExtension | All commercial converters (`?ref=src.g2` / `?ref=src.sourceforge`) | Permanent organic SERP comparison pages at €0 cash cost |

---

## Rank 4: B2B Channel Multiplier ("1 Practice = 10–100 Client Workflows")

Anchor page: `https://domstijn.github.io/friction-killer-suite/partners/?ref=src.partner`

### Target Communities & Directories
- **DACH *Steuerberater* & DATEV:** `datev-community.de`, `ditax.ag`, `taxpunk.de`, `ae-net.at` (Pitch: DSGVO 0-upload `EInvoiceLocal` + `BankFeedBridge` + free `/tools/datev-bu-schluessel-lookup/`)
- **EU/UK Xero & QBO Advisors:** `a2xaccounting.com/directory`, `linkmybooks.com/partners`, `accountingweb.co.uk/any-answers`, `accountancyvanmorgen.nl` (Pitch: `BankFeedBridge` ING/Rabobank/ABN/Sparkasse CAMT.053 + `OssVatBridge`)
- **Shopify & Webflow Agencies:** `liquidweekly.com`, `ionlyspeakliquid.com`, `shopify.com/partners/directory`, `webflow.com/certified-partners` (Pitch: `ShopMetaShift` & `WebflowAssetZip` without client Admin API sharing)

### Partner Email Template (DE)
> **Betreff:** Kurze Frage zu Ihrem E-Rechnungs- & Bankimport-Workflow (0-Upload im Browser / Kanzlei-Suite)
>
> Hallo [Vorname / Nachname],
>
> viele Steuerberatungen und DATEV-Berater stehen bei kleineren Mandanten ohne eigenes ERP vor zwei Engpässen: reine XRechnung-/ZUGFeRD-XMLs lesbar prüfen und als DATEV `EXTF_Buchungsstapel.csv` inkl. BU-Schlüssel verbuchen (`EInvoiceLocal`), sowie Sparkasse/VR `CAMT.053`-/`MT940`-Auszüge oder BZSt-OSS-CSVs ohne teure Monats-Abos aufbereiten (`BankFeedBridge`, `OssVatBridge`).
>
> Der Unterschied zu Cloud-Portalen: Alle Tools laufen zu **100 % lokal direkt im Chrome-Tab** (im DevTools-Netzwerk-Tab verifizierbar, kein Server-Upload, kein zusätzlicher AVV nötig) — für einmalig 29 € pro Tool oder 49 € für alle 13 Werkzeuge inkl. automatischer Stripe USt-Rechnung.
>
> Kostenlos im Browser & Kanzleiinfos: https://domstijn.github.io/friction-killer-suite/partners/?ref=src.partner
> Auf Wunsch schicke ich Ihnen gerne Testdateien oder prüfe ein anonymisiertes Bank-/XML-Format für Ihre Kanzlei direkt mit.
>
> Viele Grüße
> Stijn Dom (`@domstijn`) · Friction-Killer Suite

### Partner Email Template (EN)
> **Subject:** Zero-upload browser tools for client CAMT.053 bank feeds, EU OSS & store migrations
>
> Hi [First Name],
>
> Noticed your work in [Community / Directory] helping clients with [EU e-commerce / QuickBooks / Xero / Shopify migrations].
>
> We built a zero-upload, browser-local utility suite for practices that repeatedly hit messy client CSV/XML exports without wanting another \$20–\$200/mo SaaS connector or OAuth hurdle:
> - **BankFeedBridge & Payout Tools:** Converts ING / Rabobank / ABN AMRO / Sparkasse `CAMT.053` & `MT940` into QuickBooks `.qbo`, Xero `.ofx`/CSV, and DATEV CSV, plus Stripe Payout & Amazon V2 settlement clearing journals.
> - **OssVatBridge & EInvoiceLocal:** Compiles BZSt BOP `;`-CSVs (`GR→EL` fix) & Ireland ROS XML locally, and converts XRechnung / ZUGFeRD / Peppol XMLs to A4 PDF & accounting CSVs.
> - **ShopMetaShift & WebflowAssetZip:** Converts WooCommerce >3-attribute variable CSVs to Matrixify MERGE + `301-redirects.csv` locally without live store Admin keys.
>
> Every tool runs 100% in Chrome memory (verifiable in DevTools Network tab) or air-gapped Python `.whl` CLI — €29 once per tool or €49 for all 13 tools (Stripe PDF VAT invoice + 14-day refund included): https://domstijn.github.io/friction-killer-suite/partners/?ref=src.partner
>
> Happy to verify a tricky anonymized client XML/CSV format if helpful.
>
> Best,
> Stijn Dom (`@domstijn`) · Friction-Killer Suite

---

## Rank 5: Technical Syndication ("Pain-Hijack" Articles) & 30s YouTube Search Demos

### A. 3 Ready-to-Publish Articles (`launch_hub/articles/`)
1. [01-camt053-quickbooks-ol222-fitid.md](file:///Users/stijndom/Documents/antigravity/joyful-newton/launch_hub/articles/01-camt053-quickbooks-ol222-fitid.md) → Publish on Dev.to, Hashnode, Medium, GitHub Gist (`?ref=src.devto-ol222`)
2. [02-xrechnung-datev-bu-schluessel-br-co-10.md](file:///Users/stijndom/Documents/antigravity/joyful-newton/launch_hub/articles/02-xrechnung-datev-bu-schluessel-br-co-10.md) → Cross-post in DE/EN dev & DATEV-Tech blogs (`?ref=src.devto-xrechnung`)
3. [03-lemon-squeezy-shutdown-paypal-trial-end.md](file:///Users/stijndom/Documents/antigravity/joyful-newton/launch_hub/articles/03-lemon-squeezy-shutdown-paypal-trial-end.md) → Publish on IndieHackers, Dev.to, Hashnode (`?ref=src.devto-lemon`)

### B. Four 30-Second Faceless YouTube Search Proof Demos (Screen Capture + DevTools Proof)
1. **`Fix QuickBooks Error OL-222 on European CAMT.053 XML Statements in 20 Seconds (Offline, 0 Uploads)`**
   - *Query:* `quickbooks error ol-222 camt.053 xml to qbo`
   - *Storyboard:* 0-5s OL-222 popup headline -> 5-15s Open Chrome DevTools Network tab (`0 requests`), drop `sample-camt053-001-08-sepa-batch.xml` -> 15-25s Show SEPA batch unwrapped + `€0.00 OK` variance -> 25-30s Click `Download .QBO` + URL overlay `?ref=src.yt-ol222`.
2. **`Convert SWIFT MT940 (.sta) with :61: Reversals & :86: SEPA Tags to Xero CSV / QBO / DATEV (0 Cloud Uploads)`**
   - *Query:* `convert swift mt940 sta file to qbo xero csv offline`
   - *Link:* `https://domstijn.github.io/friction-killer-suite/products/camt053-mt940-qbo-xero-converter/?ref=src.yt-mt940`
3. **`XRechnung & ZUGFeRD XML zu DATEV EXTF (BU-Schlüssel 9/8/94) & A4 PDF — 100% Offline (0 Cloud-Uploads)`**
   - *Query:* `xrechnung zugferd xml datev extf bu schluessel pdf konvertieren`
   - *Link:* `https://domstijn.github.io/friction-killer-suite/de/xrechnung-zugferd-konverter/?ref=src.yt-xrechnung`
4. **`Lemon Squeezy Shutdown (March 31, 2027): Split PayPal vs. Card MRR & Compute trial_end_unix Offline`**
   - *Query:* `lemon squeezy shutdown migrate subscriptions stripe polar paypal`
   - *Link:* `https://domstijn.github.io/friction-killer-suite/products/lemonsqueezy-stripe-polar-migrator/?ref=src.yt-lemon`
