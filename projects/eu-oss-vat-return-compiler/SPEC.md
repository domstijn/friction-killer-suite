# Product & Technical Spec: OssVatBridge (`eu-oss-vat-return-compiler`)

- **Ecosystem**: `saas-addon`
- **Host Software**: Stripe Tax / Shopify / Lemon Squeezy -> EU VAT OSS (Germany BZSt BOP / Ireland ROS / EU27)
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `acct_1UdCWDH2AcdDmQyR`, EUR, `txcd_10103000`)

## 1. Pain & Evidence
- **Exact Friction**: SaaS founders and e-commerce merchants migrating off Merchant-of-Record platforms (Lemon Squeezy shutdown March 31, 2027) onto Stripe Tax or Shopify suddenly inherit quarterly **EU VAT One-Stop-Shop (OSS)** filing. Raw exports dump un-aggregated per-transaction rows across mixed currencies (`USD`, `GBP`, `SEK`, `EUR`) with dot decimals, comma delimiters, `GR` country codes (OSS requires `EL`), domestic home-state rows, non-EU rows, and B2B reverse-charge rows—failing Germany BZSt BOP (`;` delimiter, comma decimal, 1,000-row cap) and Ireland ROS XML schemas.
- **Verified Alternatives & Why They Fail**:
  - Incumbents (Quaderno \$49–\$149/mo, Lovat \$35–\$115/mo, GoodVat, Anrok/Taxually \$99–\$299/mo) lock quarterly file formatting behind recurring monthly SaaS fees and permanent live OAuth credentials.
  - Best 2-minute free escape hatch: raw Stripe Tax/Shopify CSVs in Excel/Google Sheets require manual FX normalization, `GR->EL` normalization, B2B/home-state filtering, refund netting, and German semicolon/comma formatting every quarter.

## 2. Target Persona & Value Proposition
- **Who pays**: EU SaaS founders, solo developers, and cross-border DTC/Shopify merchants who refuse \$35–\$299/mo recurring VAT compliance SaaS to file 4 quarterly OSS CSV/XML uploads per year.
- **10x Relief**: Drag-and-drop multiple CSVs (Stripe Tax + Shopify + Lemon Squeezy) in Chrome (100% browser-local, zero PII uploaded) or run `eu-oss-vat-return-compiler`, and immediately compile balanced EU27 Member-State VAT totals + ready-to-upload Germany BZSt/BOP semicolon CSV and Ireland ROS XML.

## 3. Free vs. Pro Feature Split
- **Free Tier**: Parses & previews up to `FREE_ROW_LIMIT = 15` transactions with live EU27 Member-State VAT breakdown, FX normalization, and exclusion counters (`DOMESTIC_HOME_STATE`, `NON_EU`, `B2B_REVERSE_CHARGE`).
- **Pro Tier (€29 one-time / €49 All-Access Bundle, Stripe Checkout `cs_live_...`)**: Unlocks unlimited rows, multi-CSV platform merging, refund netting, and exports for **Germany BZSt/BOP (`;`-CSV)**, **Ireland ROS XML**, and **EU27 Audit CSV** (web downloads + `--out-dir` CLI).

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 621 / setuptools config (`eu-oss-vat-return-compiler = "cli:main"`) for zero-dep `.whl` distribution
- `src/addon.py` — Pure stdlib EU27 OSS compiler (`parse_transactions_csv`, `compile_oss_return`, `render_bzst_bop_csv`, `render_ros_xml`, `render_eu27_audit_csv`, `EU27_STANDARD_RATES`, `DEFAULT_ECB_FX_TO_EUR`, `Decimal` `ROUND_HALF_UP`)
- `src/cli.py` — CLI wrapper (`--input`, `--home-country`, `--quarter`, `--seller-vat`, `--out-dir`, `--activate`, `--sample`) enforcing `require_pro_feature`
- `src/license_client.py` — Zero-backend license verifier (`cs_live_...` / offline cache)
- `tests/test_addon.py` — Deterministic tests covering multi-CSV ingestion, FX conversion, `GR->EL`, exclusions, refund netting, BZSt `;` / ROS XML validity, Free 15-row cap, and Pro unlock
- `launch/landing.html` — Standalone Tailwind landing page + `#live-app` 100% browser-local EU VAT OSS compiler + Stripe checkout wiring
- `launch/LAUNCH_KIT.md` — Stripe Managed Payments metadata, SEO targets, non-spammy distribution drafts, `LemonExitBridge` cross-sell

## 5. Verification Plan
1. Run `python3 -m unittest discover -s projects/eu-oss-vat-return-compiler/tests -v` and `python3 projects/eu-oss-vat-return-compiler/tests/test_addon.py`
2. Verify Free tier enforces `FREE_ROW_LIMIT = 15`, Pro export raises/blocks when unlicensed, and valid `cs_live_...` unlocks full exports
3. Run `python3 scripts/ship_check.py --slug eu-oss-vat-return-compiler --package` and validate `.whl` + `.zip` + `node --check` on embedded Web App JS
