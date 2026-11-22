# Product & Technical Spec: EInvoiceLocal (`e-invoice-xml-batch-converter`)

- **Ecosystem**: `saas-addon`
- **Host Software**: EU B2B E-Invoicing (XRechnung / ZUGFeRD / Peppol XML -> DATEV / Xero / QuickBooks)
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `acct_1UdCWDH2AcdDmQyR`, EUR, `txcd_10103000`)

## 1. Pain & Evidence
- **Exact Friction**: Mandatory 2025–2027 EU & German/Belgian EN 16931 e-invoicing laws force SMBs and *Steuerberater* to receive raw UBL 2.1 and UN/CEFACT CII XML invoices (XRechnung, ZUGFeRD, Peppol BIS 3.0). Chrome/Excel dump raw tags without validating EN 16931 math rules, cloud viewers violate GDPR/GoBD privacy rules, and ERPs like Lexoffice/SevDesk/DATEV UO charge €19–€79/mo recurring.
- **Verified Alternatives & Why They Fail**:
  - Live browser tool Docfaro handles basic XML-to-Excel/DATEV preview, but lacks unified Xero/QBO Bills export, printable clean A4 PDF view with `@media print`, explicit EN 16931 math rule (`BR-CO-10`/`BR-CO-15`) reporting, and an offline `pip`-installable batch directory CLI.

## 2. Target Persona & Value Proposition
- **Who pays**: EU freelancers, SMB founders, bookkeepers, and *Steuerberater* needing GDPR-safe, 100% offline EN 16931 XML rendering + multi-file DATEV/Xero/QuickBooks import without €19–€79/mo SaaS subscriptions.
- **10x Relief**: Drop batches of UBL 2.1 and CII `.xml` files directly into Chrome (zero uploads) or point the CLI at a folder to validate EN 16931 totals, render printable A4 PDF invoices, and generate DATEV `EXTF` (with automatic `BU-Schlüssel`), Xero Bills CSV, and QuickBooks Bills CSV.

## 3. Free vs. Pro Feature Split
- **Free Tier**: Validates EN 16931 math, computes `BU-Schlüssel` codes, and renders printable A4 invoice views for up to `FREE_INVOICE_LIMIT = 3` XML invoices per batch.
- **Pro Tier (€29 one-time / €49 All-Access Bundle, Stripe Checkout `cs_live_...`)**: Unlocks unlimited XML batches and exports for **DATEV EXTF Buchungsstapel CSV**, **Xero Bills CSV**, and **QuickBooks Bills CSV** (Web App downloads + CLI `--out-dir` directory batching).

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 621 / setuptools config (`e-invoice-xml-batch-converter = "cli:main"`) for zero-dep `.whl` distribution
- `src/addon.py` — Pure stdlib dual UBL 2.1 + CII XML parser, EN 16931 validator, DATEV `BU-Schlüssel` mapper & EXTF/Xero/QBO exporters
- `src/cli.py` — CLI wrapper supporting repeatable `.xml` files and directory scanning (`--input`, `--out-dir`, `--activate`, `--pro`, `--sample-ubl`, `--sample-cii`)
- `src/license_client.py` — Zero-backend license verifier (`cs_live_...` / offline cache)
- `tests/test_addon.py` — Deterministic tests covering UBL 2.1, CII date normalization, EN 16931 failure detection, DATEV `BU-Schlüssel`/Xero/QBO CSVs, Free 3-XML cap, and Pro directory unlock
- `launch/landing.html` — Standalone Tailwind landing page + `#live-app` browser `DOMParser` batch validator + printable A4 view
- `launch/LAUNCH_KIT.md` — Stripe Managed Payments metadata, DE/EN SEO targets, educational non-spammy distribution template

## 5. Verification Plan
1. Run `python3 -m unittest discover -s projects/e-invoice-xml-batch-converter/tests -v`
2. Verify Free tier enforces `FREE_INVOICE_LIMIT = 3` and Pro exporters raise `PermissionError` / exit non-zero until activated
3. Run `python3 scripts/ship_check.py --slug e-invoice-xml-batch-converter --package` and `node --check` on Web App JS
