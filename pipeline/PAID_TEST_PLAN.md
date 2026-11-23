# Conversion, Trust Audit & €75 Fast-Signal Paid Search Plan

> **Spending Status:** **€0.00 spent.** Nothing is purchased or launched without explicit human approval.

---

## 1. Conversion & Trust Friction Audit (Top 4 Commercial Tools)

1. **`domstijn.github.io` Domain vs. Buyer Trust:**
   - **Finding:** EU *Steuerberater*, bookkeepers, and finance teams uploading sensitive vendor IBANs, XRechnung invoices, or CAMT.053 bank statements hesitate to enter card details on a `github.io` subdomain.
   - **External CSS note:** Every product page currently loads `https://cdn.tailwindcss.com` externally (worth replacing with bundled local/inlined CSS so DevTools confirms `0` third-party runtime CDN requests).
2. **`http://localhost:4242/verify-license` & `localStorage`-Only Unlock inside Landing Pages:**
   - **Finding:** While `docs/success.html` already auto-unlocks `localStorage` across web apps on return from Stripe, switching office PCs or clearing browser data loses local state, and individual `landing.html` pages still POST to `http://localhost:4242/verify-license` when users paste a key manually (falling back to format validation when offline).
   - **Fix:** Expose a lightweight read-only Cloudflare Worker endpoint `/api/verify-license` (or emailed backup key + downloadable `.txt` license receipt instruction) and surface Stripe's automatic VAT PDF receipt promise directly inside every €29 Pro card.
3. **Inconsistent Legal / Refund / B2B Receipt Framing Across Product Cards:**
   - `build_portfolio.py` injects the legal/14-day refund/support footer (`@domstijn`, `dom.stijn99@gmail.com`) at the bottom of `docs/` pages, **however** the individual €29 Pro cards on `BankFeedBridge` and `LemonExitBridge` omit the `"14-day refund + Stripe PDF VAT invoice"` reassurance right at the buy button, and DACH tools lack a formal street-address EU *Impressum* for German B2B compliance.
4. **English-Only UI on German-Tax Tools (`EInvoiceLocal`, `OssVatBridge`, `BankFeedBridge`):**
   - German queries (`"XRechnung XML zu DATEV CSV"`, `"BZSt OSS CSV"`, `"CAMT.053 DATEV"`) hit 100% English hero copy and English UI buttons (`lang="en"`), lowering DACH trust and Google Ads Quality Score.
5. **Over-Generous Free Tier Leakage:**
   - `EInvoiceLocal` currently gives full EN 16931 validation + clean unwatermarked A4 PDF printing for up to **3 XMLs per batch**, and `BankFeedBridge` exports **10 transactions** to Xero CSV for free—letting infrequent freelancers solve one-off files indefinitely without paying.
6. **Domain Details inside App Dropdowns:**
   - `BankFeedBridge` lists only 5 US bank names (`Wells Fargo`, `Chase`, `Bank of America`, `Citibank`) in the `<INTU.BID>` dropdown—label `3000` explicitly as `Universal / EU & International Bank (.QBO)` so EU/UK bookkeepers aren't confused.

---

## 2. Highest-ROI 1-Hour Quick Wins (Do Before Spending Ad Budget)

1. Buy **1 clean B2B umbrella domain** via Cloudflare Registrar (`~€10/yr`, e.g., `localledger.eu` or `clearledger.eu`) and deploy `docs/` on **Cloudflare Pages** (`/einvoicelocal/`, `/bankfeedbridge/`, `/ossvatbridge/`, `/lemonexitbridge/`) with `301` canonical cutover from `github.io`.
2. Add a Cloudflare Worker `/api/verify-license` route (using `STRIPE_SECRET_KEY` as a Wrangler/Worker secret) + `Download Pro License Receipt (.txt)` in `docs/success.html`.
3. Ship native **German `/de/` landing variants** for `EInvoiceLocal` and `OssVatBridge` before turning on German exact-match search keywords.
4. Tighten `EInvoiceLocal` Free limit to **1 XML preview** (or watermarked A4 print / 2-line DATEV preview) and replace muted inline text paywall warnings with a high-contrast Pro upgrade banner + Stripe VAT invoice + 14-day refund badge.
5. Clarify `3000 — Universal / EU Bank (.QBO)` in `BankFeedBridge`, and label ECB quarterly FX rate metadata transparently in `OssVatBridge`.

---

## 3. Optional €75 Fast-Signal Exact-Match Google Search Plan

- **Budget & Schedule:** **€75.00 total** across **10 days (`€7.50/day`)**, Manual CPC cap **€0.85–€1.20**, **Google Search Exact-Match ONLY** (Search Partners **OFF**, Display **OFF**).
- **Split:** `EInvoiceLocal` €25 (€2.50/d) · `BankFeedBridge` €20 (€2.00/d) · `OssVatBridge` €20 (€2.00/d) · `LemonExitBridge` €10 (€1.00/d).

| Product | Exact-Match Keyword | Lang | Headline 1 (<=30c) | Headline 2 (<=30c) | Description (<=90c) |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `EInvoiceLocal` | `[xrechnung zu pdf konverter]` | de | `XRechnung XML zu A4 PDF` | `Lokal im Browser · 29 €` | `XRechnung & ZUGFeRD XML lokal prüfen, als A4-PDF drucken & DATEV EXTF exportieren.` |
| `EInvoiceLocal` | `[xrechnung datev importieren]` | de | `XRechnung zu DATEV EXTF CSV` | `Mit BU-Schlüssel · Ohne Cloud` | `Batch-Export für XRechnung, ZUGFeRD & Peppol nach DATEV EXTF. 100 % DSGVO-konform.` |
| `EInvoiceLocal` | `[zugferd xml to pdf converter]` | en | `ZUGFeRD & XRechnung to PDF` | `Offline Browser Tool · €29` | `Validate EN 16931 XML, print A4 PDFs & export DATEV/Xero CSVs locally. Zero uploads.` |
| `BankFeedBridge` | `[camt 053 to qbo converter]` | en | `CAMT.053 XML to QuickBooks QBO` | `€29 Once · No ProperSoft SaaS` | `Convert ISO 20022 CAMT.053 & MT940 to .QBO, Xero .OFX & DATEV locally in Chrome.` |
| `BankFeedBridge` | `[mt940 to xero converter]` | en | `MT940 & CAMT.053 to Xero OFX` | `100% Local · Balance Verified` | `Flatten SEPA batches, verify cents balance & export Xero OFX/CSV or QBO. Pay €29 once.` |
| `BankFeedBridge` | `[camt 053 zu datev konverter]` | de | `CAMT.053 & MT940 zu DATEV CSV` | `100 % Lokal · Einmalig 29 €` | `SEPA-Sammler entpacken, Saldo prüfen & DATEV Bank-CSV im Browser erzeugen. Kein Upload.` |
| `OssVatBridge` | `[bzst oss csv konverter]` | de | `BZSt OSS CSV lokal erstellen` | `Stripe & Shopify · Einmal 29 €` | `Stripe Tax, Shopify & Lemon Squeezy CSVs zu BZSt BOP (;)-CSV & EU27-Audit bündeln.` |
| `OssVatBridge` | `[eu oss vat return csv tool]` | en | `EU VAT OSS CSV & XML Compiler` | `BZSt & ROS Ready · €29 Once` | `Merge Stripe Tax & Shopify CSVs locally into BZSt BOP CSV & Ireland ROS XML. No SaaS.` |
| `OssVatBridge` | `[shopify eu oss csv converter]` | en | `Shopify CSV to EU OSS Return` | `Local Browser Tool · €29 Once` | `Auto-excludes domestic & B2B rows, maps GR to EL & outputs BZSt/ROS OSS files locally.` |
| `LemonExitBridge` | `[lemon squeezy migrate to stripe]` | en | `Migrate Off Lemon Squeezy` | `PayPal MRR & trial_end Audit` | `Split PayPal vs Card MRR, compute Unix trial_end & export legacy keys locally. €29 once.` |
| `LemonExitBridge` | `[lemon squeezy paypal migration]` | en | `Lemon Squeezy PayPal Migrator` | `Zero-Upload CSV Audit · €29` | `Isolate PayPal subscriptions before shutdown, get trial_end_unix & legacy-keys.json.` |

### Negative Keywords (Mandatory Exclusions)
`free`, `kostenlos`, `gratis`, `umsonst`, `freeware`, `open source`, `github`, `python`, `pypi`, `npm`, `script`, `code`, `library`, `sdk`, `api`, `tutorial`, `anleitung`, `beispiel`, `sample`, `template`, `vorlage`, `what is`, `was ist`, `definition`, `bedeutung`, `meaning`, `schema`, `xsd`, `specification`, `gehalt`, `salary`, `jobs`, `karriere`, `course`, `kurs`, `elster login`, `bzst login`, `portal login`, `propersoft crack`

### Hard Kill Thresholds
1. **Day 3 / €22.50 Spent (~25 clicks):** Pause immediately if `file_upload + tool_run == 0` in `GROWTH_SCORECARD.md` (indicates broken ad/landing intent match).
2. **Per-Product Kill:** At **€20 spent / 25 clicks** with **`0` `checkout_click`s**, pause that campaign and reallocate to the highest activator.
3. **Day 10 / €75 Gate:** Scale only with `>= 2` paid orders (`CAC <= €37.50`) or `>= 5` `checkout_click`s; otherwise kill paid Search Ads for non-converting tools.
