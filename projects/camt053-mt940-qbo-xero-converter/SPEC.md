# Product & Technical Spec: BankFeedBridge (`camt053-mt940-qbo-xero-converter`)

- **Ecosystem**: `saas-addon`
- **Host Software**: ISO 20022 CAMT.053 & MT940 -> QuickBooks (.QBO), Xero (.OFX/CSV) & DATEV
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `acct_1UdCWDH2AcdDmQyR`, EUR, `txcd_10103000`)

## 1. Pain & Evidence
- **Exact Friction**: The 2025–2026 global SWIFT ISO 20022 migration phases out legacy flat-text **MT940** statements in favor of deeply nested **CAMT.053** XML (`camt.053.001.02` / `.08`). QuickBooks has zero native CAMT.053 XML importer and rejects generic `.ofx` files lacking a whitelisted `<INTU.BID>` Bank ID or deterministic unique `<FITID>` tags, while Excel flattens `<NtryDtls><TxDtls>` batch breakdowns and breaks `<CdtDbtInd>` (`CRDT`/`DBIT`) debit/credit signs.
- **Verified Alternatives & Why They Fail**:
  - ProperSoft (`ProperConvert`) charges $19.99–$49.98/mo ($180–$450/yr) and MoneyThumb charges up to $599/yr recurring; cloud bank-statement converters require uploading confidential corporate IBANs, balances, and counterparty details off-device.

## 2. Target Persona & Value Proposition
- **Who pays**: QuickBooks/Xero bookkeepers, corporate treasurers, EU SMB founders, and *Steuerberater* converting corporate CAMT.053 XML & legacy MT940 bank statements offline without $180–$599/yr SaaS fees.
- **10x Relief**: Drop ISO 20022 `camt.053` XML and SWIFT MT940 files directly into Chrome (zero uploads) or run the offline Python `.whl` CLI on a statement folder to flatten nested `<TxDtls>` batches, reconcile opening/closing balances in integer cents (`variance == 0`), and export QuickBooks Web Connect (`.qbo` with `<INTU.BID>` + SHA-256 `<FITID>`), Xero `.ofx`, Xero CSV, and DATEV bank CSVs.

## 3. Free vs. Pro Feature Split
- **Free Tier**: Parses both CAMT.053 XML and MT940 statements, flattens nested batches, reconciles opening/closing balances, and previews/downloads Xero CSV for up to `FREE_TX_LIMIT = 10` transactions per batch (matching ProperSoft's 10-tx trial).
- **Pro Tier (€29 one-time / €49 All-Access Bundle, Stripe Checkout `cs_live_...` or `BANKFEED-...`)**: Unlocks unlimited transactions, multi-statement folder batching (`--out-dir`), QuickBooks Web Connect `.qbo` (with `<INTU.BID>` preset selector), Xero `.ofx`, DATEV bank CSV, and reconciliation JSON.

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 621 / setuptools config (`camt053-mt940-qbo-xero-converter = "cli:main"`) for zero-dep `.whl` distribution
- `src/addon.py` — Pure stdlib namespace-agnostic CAMT.053 XML + MT940 parser, integer-cent balance reconciler, `.qbo`/`.ofx`/Xero CSV/DATEV exporters
- `src/cli.py` — CLI wrapper supporting repeatable files/folders (`--input`, `--out-dir`, `--intu-bid`, `--account-type`, `--datev-account`, `--activate`, `--pro`, `--telemetry`, `--sample-camt053`, `--sample-mt940`)
- `src/license_client.py` — Zero-backend license verifier (`cs_live_...` / offline cache)
- `tests/test_addon.py` — Deterministic tests covering CAMT.053 nested `TxDtls`, MT940 `?20..?33` & `C`/`D`/`RD`, `.qbo` `<INTU.BID>` & `<FITID>`, `.ofx`/Xero CSV/DATEV, Free 10-tx cap, and Pro `--out-dir` unlock
- `launch/landing.html` — Standalone Tailwind landing page + `#live-app` browser `DOMParser` CAMT.053 + MT940 compiler
- `launch/LAUNCH_KIT.md` — Stripe Managed Payments metadata, SEO keywords, and non-spammy bookkeeping community reply draft

## 5. Verification Plan
1. Run `python3 -m unittest discover -s projects/camt053-mt940-qbo-xero-converter/tests -v`
2. Verify Free tier enforces `FREE_TX_LIMIT = 10` and Pro exporters raise `PermissionError` / CLI `--out-dir` exits `2` until activated
3. Run `python3 scripts/ship_check.py --slug camt053-mt940-qbo-xero-converter --package` and `node --check` on Web App JS
