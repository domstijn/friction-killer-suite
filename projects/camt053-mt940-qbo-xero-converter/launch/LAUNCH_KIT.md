# Launch & Monetization Kit: BankFeedBridge (`camt053-mt940-qbo-xero-converter`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **BankFeedBridge Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VgPF3c0DrjRVFW`
  - Price ID: `price_1Uf2RZH2AcdDmQyRKHnM1WNF`
  - Payment Link ID: `plink_1Uf2RmH2AcdDmQyRRUYRtvC3`
  - Live Stripe Payment Link: https://buy.stripe.com/4gM9ATfHm5ic5yMh006sw0e
  - Success URL: `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=camt053-mt940-qbo-xero-converter`
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Zero-Install Web App & Sales Page**: https://domstijn.github.io/friction-killer-suite/products/camt053-mt940-qbo-xero-converter/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `success.html` (`localStorage["fk_bankfeed_pro_state"]` auto-unlocked) or run `camt053-mt940-qbo-xero-converter --activate KEY` (`prod_VgPF3c0DrjRVFW,prod_VeW6IYwGyYJkPv`).

## 2. Distribution Channels & High-Intent SEO Targets
- **Zero-Install Web App (Primary)**: Browser `DOMParser` & MT940 engine keeping corporate bank IBANs, balances, and payroll recipients strictly on-device.
- **Python CLI & Wheel (`.whl`)**: Distributed via PyPI (`camt053-mt940-qbo-xero-converter` once PyPI cooldown resets) & GitHub Releases.
- **Primary Long-Tail SEO Keywords**:
  - `"CAMT.053 XML to QBO Web Connect"`
  - `"CSV MT940 CAMT.053 to QBO without ProperSoft"`
  - `"MT940 deprecated CAMT.053 to Xero OFX DATEV"`

## 3. Educational Community Reply Draft (No Sales Pitch)
> When banks switch corporate feeds from SWIFT MT940 to ISO 20022 `camt.053.001.02/.08` XML, two headaches break generic scripts immediately: (1) batch SEPA payouts nest multiple `<TxDtls>` entries under a single `<Ntry>`, so naive parsers collapse distinct invoices into one lump line or invert `<CdtDbtInd>` (`CRDT`/`DBIT`) signs; and (2) QuickBooks Desktop/Online rejects standard OFX files unless `<SONRS>` and `<BANKACCTFROM>` carry a whitelisted `<INTU.BID>` (e.g. `3000` or `2430`) paired with deterministic unique `<FITID>` IDs.
>
> I put together a 100% browser-local `DOMParser` converter (+ offline Python folder CLI) that unwraps nested `<TxDtls>`, handles legacy MT940 (`?20..?33` & `C`/`D`/`RD`), verifies opening/closing balance math to `0.00`, and outputs `.qbo`, Xero `.ofx`/CSV, and DATEV bank CSVs without uploading statements off-device: https://domstijn.github.io/friction-killer-suite/products/camt053-mt940-qbo-xero-converter/
