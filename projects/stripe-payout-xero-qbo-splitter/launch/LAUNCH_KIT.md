# Launch & Monetization Kit: StripePayoutBridge (`stripe-payout-xero-qbo-splitter`)

## 1. Checkout & License Key Setup (Stripe Managed Payments — EUR)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **StripePayoutBridge Pro** — **€29 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VfyImk6C1cdbcU`
  - Price ID: `price_1UecM1H2AcdDmQyRk7COB7ah`
  - Payment Link ID: `plink_1UecMjH2AcdDmQyRKddLVTBf`
  - Live Stripe Payment Link: https://buy.stripe.com/7sY9AT9iYh0U8KY39a6sw08
- **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Zero-Install Web App & Sales Page**: https://domstijn.github.io/friction-killer-suite/products/stripe-payout-xero-qbo-splitter/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}&slug=stripe-payout-xero-qbo-splitter` and paste it directly inside the Web App or via `stripe-payout-xero-qbo-splitter --activate <KEY>` (`prod_VfyImk6C1cdbcU,prod_VeW6IYwGyYJkPv`).

## 2. Distribution Channels (Zero Store Gatekeepers)
- **Zero-Install Web App (Primary Distribution)**: Direct link to https://domstijn.github.io/friction-killer-suite/products/stripe-payout-xero-qbo-splitter/ — works immediately on macOS/Windows/Linux in Chrome/Safari with zero download or browser-store review delay.
- **Python CLI & Wheel (`.whl`)**: Distributed directly via GitHub Releases & GitHub Pages (`pip install stripe_payout_xero_qbo_splitter-0.1.0-py3-none-any.whl`).
- **Rule Check**: Never post top-level self-promotional posts on product subreddits that ban promo; prioritize helpful answers on Xero Central, Intuit QuickBooks Community, IndieHackers Finance threads, and GitHub accounting/Stripe payout issues.

## 3. High-Intent Answer Templates (Non-Spammy)
**Template for Stripe -> Xero/QBO/DATEV Clearing Reconciliation Questions**:
> Since Stripe deposits lump-sum net payouts (gross sales minus processing fees, refunds, disputes, and FX fees), importing net bank feed lines breaks VAT and GoBD reporting, while recurring tools like A2X/Synder cost $29-$199/mo and require live OAuth.
>
> I put together a zero-install client-side tool (`StripePayoutBridge`) that takes your Stripe/PayPal itemized payout CSV right inside your browser (no financial CSV leaves your computer), verifies zero-cent drift per `payout_id`, and splits each payout into balanced double-entry journals (`Debits == Credits`) ready for **Xero Manual Journal CSV**, **QuickBooks Journal CSV**, or **DATEV Buchungsstapel CSV**: https://domstijn.github.io/friction-killer-suite/products/stripe-payout-xero-qbo-splitter/ (Free tier reconciles 1 payout batch).
