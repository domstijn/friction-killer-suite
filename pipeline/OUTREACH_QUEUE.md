# Cash-Inflow Outreach Queue (`pipeline/OUTREACH_QUEUE.md`)

> **Verification Status:** GitHub Issue URLs below were verified live via `gh api` on `2026-11-23` (`state == "open"`, `locked == false`). Web forum threads (Shopify Community, Reddit, Hacker News) should have community self-promotion rules checked again before posting (note: on Shopify Community outside Ask & Offer and on `r/SaaS`, post only pure technical help if direct tool links violate board rules).

---

## Priority 1: `EInvoiceLocal` (`e-invoice-xml-batch-converter`)
- **Live URL:** https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/
- **Verified Live GitHub Issues (`open`, `locked=false`):**
  1. **RechnungsFee `#598`** (*[Feature-Request] Anzeigetool für X-Rechnungen*, updated `2026-11-23`, `0` comments)
     - **URL:** https://github.com/nicolettas-muggelbude/RechnungsFee/issues/598
     - **Draft Reply (DE):**
       > Für reine XRechnung-XMLs (ohne eingebettetes PDF wie bei ZUGFeRD) scheitern einfache XSLT- oder Browser-Ansichten oft daran, dass XRechnung sowohl als OASIS UBL 2.1 (`Invoice`/`CreditNote`) als auch als UN/CEFACT CII (`CrossIndustryInvoice`) vorliegen kann und Summenregeln wie EN 16931 BR-CO-10/BR-CO-15 separat geprüft werden müssen. Wenn ihr XMLs vorab schnell lokal im Browser prüfen und als druckbares A4-PDF (inkl. DATEV-EXTF-Export) rendern wollt, ohne Rechnungsdaten auf fremde Server hochzuladen, könnt ihr dafür EInvoiceLocal nutzen (läuft 100 % lokal in Chrome, bis zu 3 XMLs kostenlos, Pro/Offline-CLI €29): https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/
  2. **Le-Space/belege `#932`** (*The BU key by where the vendor sits*, updated `2026-11-21`, `0` comments)
     - **URL:** https://github.com/Le-Space/belege/issues/932
     - **Draft Reply (DE):**
       > Deriving DATEV `BU-Schlüssel` from PDF OCR flags breaks quickly on § 13b reverse-charge (`AE`) and exempt (`E`/`O`/`Z`) cases because text heuristics miss line-level VAT categories and tax-rate splits. For incoming XRechnung/ZUGFeRD/Peppol invoices, parsing structured UBL 2.1 or UN/CEFACT CII XML maps `BT-118`/`BT-151` VAT category codes and rates deterministically to DATEV EXTF `BU-Schlüssel` (`9`, `8`, `94`, `0`) after validating `BR-CO-10`/`BR-CO-15` totals. If you want a standalone fallback for batch-converting incoming XMLs to DATEV EXTF CSV locally in Chrome (3 XMLs free) or via an offline `.whl` CLI (€29 Pro), see EInvoiceLocal: https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/
  3. **paperless-ngx-erechnung `#12`** (*Add multi layer eInvoice validation*, updated `2026-11-23`, `6` comments)
     - **URL:** https://github.com/bitbetterde/paperless-ngx-erechnung/issues/12
     - **Draft Reply:**
       > Watch out for two traps when building lightweight EN 16931 checks in Python without Java KoSIT: UBL 2.1 and UN/CEFACT CII encode allowances/charges differently, and naive parsers miss calculation mismatches like `BR-CO-10` and `BR-CO-15` on mixed tax rates. If you want an offline Python/browser check alongside Paperless-ngx—handling UBL 2.1 + CII parsing, BR-CO-10/15 math checks, A4 PDF print, and DATEV EXTF CSV locally (free up to 3 XMLs, €29 Pro CLI)—EInvoiceLocal covers those cases client-side: https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/
  4. **Stirling-PDF `#2025`** (*Generate a PDF file from a XRechnung XML file*, updated `2026-10-21`, `5` comments)
     - **URL:** https://github.com/Stirling-Tools/Stirling-PDF/issues/2025
     - **Draft Reply:**
       > Ad-hoc XSLT scripts often break on German XRechnung files because incoming invoices split across OASIS UBL 2.1 and UN/CEFACT CII namespaces while multi-page tables and EN 16931 `BR-CO-10`/`BR-CO-15` checks must align before PDF rendering. Until native Stirling-PDF support ships, EInvoiceLocal handles UBL 2.1 + CII validation and printable A4 PDF rendering 100% locally inside Chrome with zero server uploads (free 3 XMLs, €29 Pro / `.whl` CLI): https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/
  5. **ZUGFeRD/quba-viewer `#194`** (*Quba Viewer 2.0.0 crashes on opening ZUGFeRD PDF*, updated `2026-11-13`, `1` comment)
     - **URL:** https://github.com/ZUGFeRD/quba-viewer/issues/194
     - **Draft Reply:**
       > That `libjcef.so` `std::__facet_shims` SIGSEGV occurs when JCEF C++ locale initialization clashes with non-C system locales (`LC_ALL=C` avoids it as noted). If anyone hits that desktop runtime blocker and just needs to inspect UBL 2.1 / CII XMLs, verify EN 16931 math, or print A4 PDF without Java/Electron dependencies, EInvoiceLocal runs 100% in Chrome with zero uploads (free up to 3 XMLs, €29 Pro): https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/

---

## Priority 2: `BankFeedBridge` (`camt053-mt940-qbo-xero-converter`)
- **Live URL:** https://domstijn.github.io/friction-killer-suite/products/camt053-mt940-qbo-xero-converter/
- **Verified Live GitHub Issues (`open`, `locked=false`):**
  1. **Moneten `#23`** (*Import CAMT.053 and MT940 files*, updated `2026-11-12`, `2` comments)
     - **URL:** https://github.com/MonetenApp/Moneten/issues/23
     - **Draft Reply:**
       > When flattening CAMT.053 `<NtryDtls><TxDtls>` batches, fall back to entry-level `<Ntry>/<Amt>` and `<CdtDbtInd>` only when `<TxDtls>` omits its own `<AmtDtls>`, and assert `opening_cents + sum(tx_cents) - closing_cents == 0` in integer cents so partial batch lines never drift. Keying duplicates solely on `<AcctSvcrRef>` drops child entries or causes duplicates on overlapping statements. For anyone needing clean `.ofx`/CSV/DATEV/`.qbo` (`<INTU.BID>` + deterministic `<FITID>`) output right away locally, BankFeedBridge handles these exact edge cases (free up to 10 tx, €29 Pro): https://domstijn.github.io/friction-killer-suite/products/camt053-mt940-qbo-xero-converter/
  2. **Budgie `#1745`** (*feat(sync): CAMT.053 and MT940 statement import*, updated `2026-11-08`, `1` comment)
     - **URL:** https://github.com/budgie-at/budgie/issues/1745
     - **Draft Reply:**
       > Alongside MT940 `:86:` `?20..?33` vs `/TAG/` splitting and `:61:` `RD`/`RC` reversal signs, watch for CAMT.053 `<Ntry>` blocks containing multiple `<TxDtls>` under one `<AcctSvcrRef>`—hashing `(IBAN + BookgDt + TxDtls index + EndToEndId + cents)` avoids collapsing batch children, and integer-cent `OPBD`->`CLBD` variance checks catch float drift cleanly. If users want local `.qbo`/`.ofx`/Xero CSV/DATEV conversion immediately while native sync is built, BankFeedBridge runs 100% locally (free 10 tx, €29 Pro): https://domstijn.github.io/friction-killer-suite/products/camt053-mt940-qbo-xero-converter/
  3. **Firefly III `#13127`** (*CAMT.052 import: Preserve ultimate creditor*, updated `2026-11-21`, `17` comments)
     - **URL:** https://github.com/firefly-iii/firefly-iii/issues/13127
  4. **Securo `#1205`** (*Use statement balance/date range on import*, updated `2026-10-18`, `0` comments)
     - **URL:** https://github.com/securo-finance/securo/issues/1205
  5. **ERPNext `#47648`** (*Import Bank Statement & customizable bank formats*, updated `2026-08-12`, `5` comments)
     - **URL:** https://github.com/frappe/erpnext/issues/47648

---

## Priority 3: `OssVatBridge` (`eu-oss-vat-return-compiler`)
- **Live URL:** https://domstijn.github.io/friction-killer-suite/products/eu-oss-vat-return-compiler/
- **Verified Live Threads (`open`, `locked=false` on GH):**
  1. **erp-mafia/accounted `#3803`** (*OSS underlag: no file for Skatteverket's e-service*, updated `2026-11-23`, `0` comments)
     - **URL:** https://github.com/erp-mafia/accounted/issues/3803
  2. **kasuken/.github `#8`** (*Get EU VAT / OSS advice and standard Stripe Tax setup*, updated `2026-11-04`, `0` comments)
     - **URL:** https://github.com/kasuken/.github/issues/8
  3. **spy4x/financy `#116`** (*chore: register NeatSoft for EU and UK VAT*, updated `2026-11-03`, `0` comments)
     - **URL:** https://github.com/spy4x/financy/issues/116
  4. **Shopify Community — OSS Tax report in Shopify?**
     - **URL:** https://community.shopify.com/t/oss-one-stop-shop-tax-report-in-shopify/398875 *(Direct helpful reply allowed; check thread status before posting.)*
  5. **Reddit `r/SaaS` — Bootstrapped SaaS international subscriptions & Stripe VAT**
     - **URL:** https://www.reddit.com/r/SaaS/comments/1vrx95f/bootstrapped_saas_international_subscriptions_and/ *(Respect strict `r/SaaS` self-promo rules: lead with pure Stripe + EU OSS explanation; omit link if account has recent promo.)*

---

## Priority 4: `LemonExitBridge` & `ShopMetaShift` + Secondary Backlog
- **`LemonExitBridge`:** https://domstijn.github.io/friction-killer-suite/products/lemonsqueezy-stripe-polar-migrator/
  - HN `50518944` (*"Lemon Squeezy is winding down"*, `2026-11-16`): https://news.ycombinator.com/item?id=50518944
  - HN `47286108` (*"Escaping the LemonSqueezy Nightmare"*, `2026-03-07`): https://news.ycombinator.com/item?id=47286108
  - Reddit `r/SaaS` (*"Lemon Squeezy is shutting down on March 31, 2027"*, `2026-11`): https://www.reddit.com/r/SaaS/comments/1xxscwu/lemon_squeezy_is_shutting_down_on_march_31_2027/
  - *(Note: `polarsource/polar-migrate#10` was checked via `gh api` on 2026-11-23 and is `locked: true` — skipped.)*
- **`ShopMetaShift`:** https://domstijn.github.io/friction-killer-suite/products/woo-shopify-metafield-migrator/
  - Shopify Community (*Note: Shopify Community bans self-promoting third-party apps outside Ask & Offer — post technical CSV guidance only on general threads or use Ask & Offer*):
    - https://community.shopify.com/t/import-products-from-woocommerce/630809
    - https://community.shopify.com/t/feature-request-native-csv-import-support-for-variant-metafields/607347
    - https://community.shopify.com/t/migrating-from-woocommerce-to-shopify-looking-for-advice/653418
- **Secondary Existing Threads (`StripePayoutBridge` & `WebflowAssetZip`):**
  - HN `49083943` (*S2Q — Stripe payouts into QuickBooks*): https://news.ycombinator.com/item?id=49083943
  - GitHub `rtCamp/stripe-xero-csv`: https://github.com/rtCamp/stripe-xero-csv
  - GitHub `Russell-Pollari/stripe2qbo`: https://github.com/Russell-Pollari/stripe2qbo
  - HN `49609645` (*Export Webflow/Framer sites with CMS intact*): https://news.ycombinator.com/item?id=49609645
