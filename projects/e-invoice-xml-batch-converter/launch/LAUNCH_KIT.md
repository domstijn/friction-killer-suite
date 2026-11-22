# Launch & Monetization Kit: EInvoiceLocal (`e-invoice-xml-batch-converter`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **EInvoiceLocal Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_Vg3C753ZbsDlQk`
  - Price ID: `price_1Ueh6RH2AcdDmQyRWu1Na1UV`
  - Payment Link ID: `plink_1Ueh6eH2AcdDmQyRe1NX3DWw`
  - Live Stripe Payment Link: https://buy.stripe.com/bJe5kD8eU8uobXa5hi6sw0c
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Zero-Install Web App & Sales Page**: https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=e-invoice-xml-batch-converter` and paste it inside the Web App or run `e-invoice-xml-batch-converter --activate KEY` (`prod_Vg3C753ZbsDlQk,prod_VeW6IYwGyYJkPv`).

## 2. Distribution Channels & Sniper Bilingual SEO Targets
- **Zero-Install Web App (Primary)**: Direct link to https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/ — uses browser `DOMParser` with zero server uploads (GDPR/GoBD safe).
- **Python CLI & Wheel (`.whl`)**: Distributed via GitHub Pages & Releases (`pip install e_invoice_xml_batch_converter-0.1.0-py3-none-any.whl`).
- **Primary Long-Tail SEO Keywords (DE / EN / BE)**:
  - `"XRechnung XML zu DATEV CSV ohne Cloud"`
  - `"ZUGFeRD XML viewer GDPR offline"`
  - `"Peppol BIS 3.0 XML to Xero CSV batch"`

## 3. Educational Community Reply Draft (No Sales Pitch)
> Two structural quirks tend to break quick scripts when batch-processing incoming German/EU EN 16931 e-invoices: (1) half of suppliers send OASIS **UBL 2.1** (XRechnung / Peppol BIS 3.0) while the other half send UN/CEFACT **CII** (`CrossIndustryInvoice` with ZUGFeRD and `YYYYMMDD` `format="102"` dates), so single-schema XPaths miss half the inbox; and (2) German DATEV `EXTF_Buchungsstapel` requires explicit `BU-Schlüssel` codes (`9` for 19% Vorsteuer, `8` for 7%, `94` for Reverse Charge) alongside comma-decimal values and BR-CO-10 / BR-CO-15 total checks.
>
> I built a 100% browser-local `DOMParser` utility (plus an offline Python CLI for folders of `*.xml`) that handles both UBL 2.1 and CII, checks EN 16931 math, renders a clean printable A4 PDF invoice view, and outputs DATEV EXTF / Xero Bills / QuickBooks Bills CSVs without uploading supplier PDFs/XMLs to third-party clouds: https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/
