# Product & Technical Spec: StripePayoutBridge (`stripe-payout-xero-qbo-splitter`)

- **Ecosystem**: `saas-addon` (Zero-Install Browser Web App + Python CLI `.whl`)
- **Host Software**: Stripe & PayPal to Xero / QuickBooks / DATEV
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`; €29 one-time EUR tax-inclusive Pro license / €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)

## 1. Pain & Evidence
- **Exact Friction**: Stripe and PayPal deposit net lump sums into business bank accounts after deducting processing fees, refunds, disputes, and multi-currency FX markups. Recording net bank deposits directly as revenue violates VAT and German GoBD accounting rules, forcing founders and bookkeepers to manually slice flat transaction CSVs in Excel before importing into Xero, QuickBooks, or DATEV.
- **Evidence**: Stage 1 commercial finance discovery across Stripe/PayPal payout clearing reconciliation threads (Xero, QuickBooks Online Multi-Currency, and DATEV Buchungsstapel GoBD workflows).
- **Why Existing Alternatives Fail**: Automated subledger connectors (*A2X*, *Synder*, *Link My Books*) charge **\$29–\$199/mo recurring** with transaction caps and demand full live OAuth access to both Stripe and accounting software. Meanwhile Stripe's native *Itemized Payout Reconciliation CSV* is an ungrouped flat transaction log that Xero/QBO/DATEV cannot directly import as balanced double-entry journals.

## 2. Target Persona & Value Proposition
- **Who pays**: SaaS founders, e-commerce sellers, agencies, fractional CFOs, and EU/US bookkeepers using Stripe/PayPal with Xero, QuickBooks Online, or DATEV.
- **10x Relief**: Runs 100% locally inside the user's browser (zero financial CSVs leave their computer, zero recurring OAuth SaaS fees) or via CLI, grouping itemized payout CSV rows by `payout_id` into balanced double-entry clearing account journals (`Gross Sales - Refunds - Disputes - Processing Fees - FX Fees == Net Bank Deposit`) and exporting Xero Manual Journal CSV, QuickBooks Online Journal CSV, and DATEV Buchungsstapel CSV in 1 click.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (€0)**:
  - Runs full CSV balance-drift audit across all detected payout batches and reconciles **1 payout batch** (up to `25` transactions, `FREE_BATCH_CAP = 1`, `FREE_TX_CAP = 25`) to **Xero Manual Journal CSV**.
- **Pro Tier (€29 one-time EUR via Stripe Managed Payments `acct_1UdCWDH2AcdDmQyR` — or €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)**:
  - **Unlimited Payout Batches & Transactions**: Reconcile an entire month, quarter, or fiscal year in one pass.
  - **QuickBooks Online Journal CSV & DATEV Buchungsstapel CSV**: Full multi-format exports including semicolon-delimited DATEV GoBD (`Umsatz;Soll/Haben-Kennzeichen;Konto;Gegenkonto`) files.
  - **FX Markup & Refund/Chargeback Splitting**: Dedicated ledger lines for multi-currency conversion fees, disputes, and tax liabilities.

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 427 console entrypoint `stripe-payout-xero-qbo-splitter = "cli:main"` for wheel packaging.
- `src/license_client.py` — Stripe Managed Payments key validator (`cs_live_...` + `/verify-license`) with 7-day offline cache.
- `src/cli.py` — Itemized payout CSV parser, per-payout batch aggregator, double-entry debit/credit balancer, Xero/QBO/DATEV CSV formatters, and CLI.
- `src/addon.py` — Clean re-exports (`reconcile_payout_batches`, `parse_payout_csv`, `FREE_BATCH_CAP`, `FREE_TX_CAP`).
- `tests/test_addon.py` — Unit & Pro-gate tests covering Free batch cap, balance assertion (`Debits == Credits`), Xero/QBO/DATEV exports, and Stripe key activation.
- `launch/landing.html` — Standalone zero-install in-browser Web App (`#live-app`) + checkout & download hub.
- `launch/LAUNCH_KIT.md` — Stripe Managed Payments IDs and accountant/bookkeeper distribution templates.

## 5. Verification Plan
1. Run `python3 projects/stripe-payout-xero-qbo-splitter/tests/test_addon.py`.
2. Run `python3 scripts/ship_check.py --slug stripe-payout-xero-qbo-splitter --package` (verifies PEP 427 `.whl` namespaced install, `--help`, `--pro`, `--telemetry`, and `.zip` packaging).
