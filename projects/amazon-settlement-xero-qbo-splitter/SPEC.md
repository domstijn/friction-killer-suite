# Product & Technical Spec: AmzSettlementBridge (`amazon-settlement-xero-qbo-splitter`)

- **Ecosystem**: `saas-addon`
- **Host Software**: Amazon Seller Central Flat-File V2 -> Xero / QuickBooks Online / DATEV
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `acct_1UdCWDH2AcdDmQyR`, EUR, `txcd_10103000`)

## 1. Pain & Evidence
- **Exact Friction**: Amazon Seller Central 14-day payouts arrive as Net deposits while Flat-File V2 (`.txt`/`.tsv`) exports dump thousands of ungrouped lines across 40+ FBA fulfillment, referral commission, storage, PPC advertising, promotion, refund, Marketplace Facilitator tax withholdings, and rolling Account-Level Reserves (`Previous Reserve Amount Balance` vs. `Current Reserve Amount`). Booking net bank deposits corrupts VAT/COGS/GoBD, while manual Excel pivot tables break on cent rounding and summary header double-counting.
- **Verified Alternatives & Why They Fail**:
  - Incumbents (A2X $29–$199/mo, Link My Books $17–$199/mo, Taxomate, Synder $52–$150+/mo) enforce recurring monthly order-volume subscriptions and permanent SP-API + accounting OAuth credentials.
  - Zero commercial 100% browser-local tools handle multi-settlement Flat-File V2 `.txt`/`.tsv` parsing into zero-variance Xero, QuickBooks, and DATEV EXTF journals.

## 2. Target Persona & Value Proposition
- **Who pays**: Amazon FBA/FBM sellers and e-commerce CPAs/Steuerberater who refuse $17–$199/mo subscriptions just to book bi-weekly settlements cleanly.
- **10x Relief**: Drop raw Flat-File V2 `.txt`/`.tsv` exports into Chrome (100% browser-local, zero SP-API credentials) or run `amazon-settlement-xero-qbo-splitter` to compile integer-cent balanced (`Debits == Credits`, Drift `€0.00`) Xero, QBO, and DATEV EXTF journals.

## 3. Free vs. Pro Feature Split
- **Free Tier**: Parses & audits 1 settlement up to `FREE_ROW_LIMIT = 15` itemized rows locally with full 8-bucket & zero-drift balance verification.
- **Pro Tier (€29 one-time / €49 All-Access Bundle, Stripe Checkout `cs_live_...`)**: Unlocks unlimited settlement rows, multi-settlement batching, and exports for **Xero Manual Journal CSV**, **QuickBooks Online Journal CSV**, and **DATEV EXTF CSV** (web downloads + `--out-dir` CLI).

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 621 / setuptools config (`amazon-settlement-xero-qbo-splitter = "cli:main"`) for zero-dep `.whl` distribution
- `src/addon.py` — Pure stdlib Flat-File V2 parser, integer-cent 8-bucket double-entry engine, and Xero/QBO/DATEV exporters
- `src/cli.py` — CLI wrapper (`--input`, `--out-dir`, `--activate`, `--pro`, `--telemetry`, `--sample`) enforcing `require_pro_feature`
- `src/license_client.py` — Zero-backend license verifier (`cs_live_...` / offline cache)
- `tests/test_addon.py` — Deterministic tests covering TSV summary row skipping, reserve netting, `drift == "0.00"`, multi-settlement batching, Free cap, Pro block/unlock, and Xero/QBO/DATEV CSV validity
- `launch/landing.html` — Standalone Tailwind landing page + `#live-app` 100% browser-local settlement splitter + Stripe checkout wiring
- `launch/LAUNCH_KIT.md` — Stripe Managed Payments metadata, SEO keywords, non-spammy distribution template

## 5. Verification Plan
1. Run `python3 -m unittest discover -s projects/amazon-settlement-xero-qbo-splitter/tests -v`
2. Verify Free tier enforces 1 settlement / 15 rows and Pro exports raise `PermissionError` / block until activated
3. Run `python3 scripts/ship_check.py --slug amazon-settlement-xero-qbo-splitter --package` and `node --check` on Web App JS
