# Product & Technical Spec: LemonExitBridge (`lemonsqueezy-stripe-polar-migrator`)

- **Ecosystem**: `saas-addon` (Zero-Install Browser Web App + Python CLI `.whl`)
- **Host Software**: Lemon Squeezy to Stripe Managed Payments & Polar.sh
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`; €29 one-time EUR tax-inclusive Pro license / €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)

## 1. Pain & Evidence
- **Exact Friction**: Lemon Squeezy closed new store sign-ups on Nov 16, 2026 and ends all billing and renewals on **March 31, 2027**. While Stripe provides a guided transfer path for eligible Card subscriptions, PayPal billing agreements do **not** transfer, Stripe Managed Payments does **not** natively host legacy `XXXX-XXXX` software license keys, and raw Lemon Squeezy CSV exports dump unlinked order histories without prorated `trial_end` Unix timestamps.
- **Evidence**: Stage 1 forced-deadline migration research across Lemon Squeezy shutdown docs, PayPal subscriber re-auth limitations, and Polar / Stripe migration threads.
- **Why Existing Alternatives Fail**: Native dashboard CSV exports flatten orders without isolating at-risk PayPal MRR or bridging active software license keys; rewriting custom proration scripts and re-auth CSV segments manually risks double-charging customers or locking out paid desktop/extension users.

## 2. Target Persona & Value Proposition
- **Who pays**: Indie founders, micro-SaaS operators, WordPress/Figma/VS Code plugin sellers, and digital product creators migrating off Lemon Squeezy before March 31, 2027.
- **10x Relief**: Runs 100% locally inside your browser (zero customer PII or revenue CSVs leave your machine) or via Python CLI, auditing transferable Card MRR vs. non-transferable PayPal MRR, computing exact UTC Unix `trial_end` timestamps from `renews_at`, and generating Stripe/Polar migration CSVs, a PayPal Re-Auth Cohort CSV, and a drop-in Legacy License Key JSON bundle in one click.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (€0)**:
  - Runs the full Store Shutdown Audit across all rows (Card MRR, PayPal MRR at risk, active license keys) and exports up to `15` rows (`FREE_ROW_CAP = 15`) into the Stripe/Polar migration CSV.
- **Pro Tier (€29 one-time EUR via Stripe Managed Payments `acct_1UdCWDH2AcdDmQyR` — or €49 All-Access Bundle `prod_VeW6IYwGyYJkPv`)**:
  - **Unlimited Customer & Subscription Rows**: Process an entire store export with zero cap.
  - **PayPal Prorated Re-Auth Cohort CSV**: Isolates active PayPal subscribers with exact Unix `trial_end` timestamps so they aren't double-charged on re-subscription.
  - **Legacy License Key JSON / Worker Shim Bundle**: Exports every active license key (`valid`, `product_variant`, `activation_limit`, `expires_at`) into a drop-in JSON lookup bundle.

## 4. Minimal Architecture & File Map
- `pyproject.toml` — PEP 427 console entrypoint `lemonsqueezy-stripe-polar-migrator = "cli:main"`.
- `src/license_client.py` — Stripe Managed Payments key validator (`cs_live_...` + `/verify-license`) with 7-day offline cache.
- `src/cli.py` — Lemon Squeezy CSV parser, Card vs. PayPal MRR auditor, UTC Unix `trial_end` calculator, Legacy Key JSON packager & CLI.
- `src/addon.py` — Re-exports `FREE_ROW_CAP`, `parse_lemonsqueezy_csv`, `iso_to_unix`, `build_migration_pack`.
- `tests/test_addon.py` — Deterministic unit & Pro-gate tests covering Free row cap, MRR audit, PayPal `trial_end`, Legacy Key JSON bundle, and Stripe activation.
- `launch/landing.html` — Standalone zero-install in-browser Web App (`#live-app`) + checkout & download hub.
- `launch/LAUNCH_KIT.md` — Stripe Managed Payments IDs and migration outreach copy.

## 5. Verification Plan
1. Run `python3 projects/lemonsqueezy-stripe-polar-migrator/tests/test_addon.py`.
2. Run `python3 scripts/ship_check.py --slug lemonsqueezy-stripe-polar-migrator --package` (verifies PEP 427 `.whl` namespaced install, `--help`, `--pro`, `--telemetry`, and `.zip` packaging).
