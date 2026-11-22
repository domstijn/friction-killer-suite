# Launch & Monetization Kit: LemonExitBridge (`lemonsqueezy-stripe-polar-migrator`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **LemonExitBridge Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VfygILC9yvd9U8`
  - Price ID: `price_1Uecj4H2AcdDmQyR82OysTZV`
  - Payment Link ID: `plink_1UecjqH2AcdDmQyRkhdQtSWN`
  - Live Stripe Payment Link: https://buy.stripe.com/3cI6oHeDibGAf9m4de6sw09
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Zero-Install Web App & Sales Page**: https://domstijn.github.io/friction-killer-suite/products/lemonsqueezy-stripe-polar-migrator/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=lemonsqueezy-stripe-polar-migrator` and paste it inside the Web App or via `lemonsqueezy-stripe-polar-migrator --activate KEY` (`prod_VfygILC9yvd9U8,prod_VeW6IYwGyYJkPv`).

## 2. Distribution Channels (Zero Store Gatekeepers)
- **Zero-Install Web App (Primary)**: Direct link to https://domstijn.github.io/friction-killer-suite/products/lemonsqueezy-stripe-polar-migrator/ — runs 100% locally inside Chrome with zero customer PII uploads.
- **Python CLI & Wheel (`.whl`)**: Distributed via GitHub Releases & GitHub Pages (`pip install lemonsqueezy_stripe_polar_migrator-0.1.0-py3-none-any.whl`).
- **Rule Check**: Never post top-level self-promo on product subreddits that ban promotional posts; reply helpfully on Lemon Squeezy shutdown threads on IndieHackers, X, GitHub Discussions (Polar / Stripe), and SaaS founder forums.

## 3. High-Intent Answer Template (Non-Spammy)
**Template for Lemon Squeezy -> Stripe/Polar Migration Threads**:
> Two gotchas that catch founders moving off Lemon Squeezy before the March 31, 2027 shutdown: (1) PayPal subscriptions don't auto-transfer to Stripe Managed Payments or Polar, so you need a clean PayPal cohort with exact Unix `trial_end` timestamps to avoid double-charging re-subscribers, and (2) Stripe Managed Payments doesn't host legacy `XXXX-XXXX` software license keys natively.
>
> I put together a zero-install client-side tool (`LemonExitBridge`) that parses your exported Lemon Squeezy CSV right in the browser (no customer emails leave your machine), audits Card MRR vs. PayPal MRR at risk, calculates UTC `trial_end_unix`, and exports Stripe/Polar migration CSVs + a `legacy-keys.json` shim: https://domstijn.github.io/friction-killer-suite/products/lemonsqueezy-stripe-polar-migrator/ (Free tier audits full MRR + exports 15 rows).
