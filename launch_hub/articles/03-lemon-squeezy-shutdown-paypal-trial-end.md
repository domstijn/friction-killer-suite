---
title: "Surviving the Lemon Squeezy March 31, 2027 Shutdown: PayPal vs. Card MRR Splits, trial_end_unix, and Legacy License Key Bridges"
tags: ["lemonsqueezy", "stripe", "polar", "saas"]
---

# Surviving the Lemon Squeezy March 31, 2027 Shutdown: Splitting PayPal vs. Card MRR, Preserving `trial_end_unix`, and Bridging Legacy License Keys

Lemon Squeezy closed new store sign-ups on **November 16, 2026** and ends all billing and subscription renewals on **March 31, 2027**. If you run a micro-SaaS, WordPress plugin, VS Code extension, or desktop app on Lemon Squeezy, waiting until Q1 2027 turns a clean export into a customer-churn crisis.

Moving to **Stripe Managed Payments** or **Polar.sh** looks straightforward on paper—until you export your Lemon Squeezy CSV and hit three operational traps that guided Card migration tools don't solve for you:

1. **PayPal billing agreements do not transfer automatically**—they must be split into a dedicated re-authorization cohort.
2. **Re-subscribing mid-cycle without an exact `trial_end_unix` timestamp double-charges customers** who already prepaid for the month or year.
3. **Stripe Managed Payments does not host Lemon Squeezy's `XXXX-XXXX` license key verification API**, threatening to lock out paying desktop/plugin users.

Here is the exact technical playbook for auditing your store export, isolating PayPal MRR at risk, computing UTC `trial_end_unix`, and shipping a zero-downtime legacy license key shim.

---

## 1. The Three Migration Traps in Raw Lemon Squeezy Exports

A raw Lemon Squeezy Subscriptions / Orders CSV combines active Card subscribers, PayPal subscribers, canceled trials, and legacy license keys in one flat table.

| Migration Track | Payment Method | Transfers Automatically? | Required Engineering Action |
|---|---|---|---|
| `stripe_card_transfer` | `card` (Visa, Mastercard, Amex, Link) | Yes (eligible Stripe guided transfer) | Audit active MRR, normalize `renews_at` -> `trial_end_unix`, verify variant mapping |
| `paypal_manual_reauth` | `paypal` | **No** | Isolate into separate cohort CSV; email targeted checkout link with `trial_end = trial_end_unix` |
| `legacy_license_bridge` | Any (`license_key` present) | **No** (Stripe Managed Payments lacks native `XXXX-XXXX` key hosting) | Export `lemon.legacy_keys.v1` JSON map + deploy static/edge lookup shim |

### Trap 1: Silently Dropping Active PayPal MRR

When filtering active subscriptions (`status` in `{"active", "on_trial", "past_due", "paused"}`), inspect `payment_method` / `gateway` / `card_brand` for `"paypal"`. Even if PayPal represents only 15–25% of your MRR, failing to isolate it before March 31, 2027 means those renewals silently die on shutdown day.

### Trap 2: Double-Billing Customers During Re-Auth (`trial_end_unix`)

If a customer renewed their annual or monthly PayPal subscription on March 10 and you ask them to re-subscribe in Stripe or Polar on March 20, charging them immediately at checkout causes chargebacks and support tickets.

Instead, pass their remaining prepaid period via **`trial_end`** (UTC Unix timestamp in seconds) computed deterministically from Lemon Squeezy's `renews_at` (or `ends_at` / `trial_ends_at`):

```python
from datetime import datetime, timezone

def iso_to_unix(date_str: str) -> int:
    """Convert ISO-8601 date or timestamp into UTC UNIX seconds for Stripe/Polar trial_end."""
    text = str(date_str or "").strip()
    if not text:
        return 0
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        dt = datetime.strptime(text[:10], "%Y-%m-%d")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())
```

### Example Split Output (`stripe_polar_csv` vs. `paypal_cohort_csv`)

**Main Stripe / Polar Migration CSV:**
```csv
customer_email,customer_name,product_variant,status,payment_method,mrr,currency,renews_at,trial_end_unix,migration_track
alex@acme.dev,Alex Rivera,Pro Monthly,active,card,29.00,USD,2027-04-12T10:00:00Z,1807524000,stripe_card_transfer
nina@studio.de,Nina Weber,Pro Annual,active,paypal,19.00,EUR,2027-08-01T00:00:00Z,1817078400,paypal_manual_reauth
```

**Isolated PayPal Re-Auth Cohort CSV:**
```csv
customer_email,customer_name,product_variant,mrr,renews_at,trial_end_unix,action_required
nina@studio.de,Nina Weber,Pro Annual,19.00,2027-08-01T00:00:00Z,1817078400,Email PayPal re-auth link before 2027-03-31
```

When generating the Stripe Checkout Session for `nina@studio.de`, pass `subscription_data[trial_end]=1817078400`. Stripe authorizes her new payment method immediately ($0 due today) and only captures the next renewal on `2027-08-01`.

---

## 2. Bridging Legacy `XXXX-XXXX` License Keys Without Keeping a Backend Alive

If your app validates license keys against `api.lemonsqueezy.com/v1/licenses/validate`, those calls will fail after March 31, 2027. Rather than forcing thousands of existing desktop or plugin users to swap keys on day one, freeze your active Lemon Squeezy keys into a deterministic JSON lookup map (`lemon.legacy_keys.v1`):

```json
{
  "schema": "lemon.legacy_keys.v1",
  "shutdown_deadline": "2027-03-31",
  "total_keys": 2,
  "keys": {
    "LS-9921-AB44-CC88": {
      "valid": true,
      "customer_email": "alex@acme.dev",
      "product_variant": "Pro Monthly",
      "activation_limit": 3,
      "expires_at": "2027-04-12T10:00:00Z"
    },
    "LS-4410-ZZ12-QW99": {
      "valid": true,
      "customer_email": "nina@studio.de",
      "product_variant": "Pro Annual",
      "activation_limit": 5,
      "expires_at": "2027-08-01T00:00:00Z"
    }
  }
}
```

You can serve this JSON behind a 15-line Cloudflare Worker (or edge route) that checks incoming keys against `legacy-keys.json` first and falls back to Stripe Checkout Session / Polar license validation for new customers:

```javascript
import legacyKeys from "./legacy-keys.json";

export async function validateLicense(key) {
  const legacy = legacyKeys.keys[key];
  if (legacy && legacy.valid) {
    return { valid: true, source: "lemon_legacy_bridge", ...legacy };
  }
  // Route new cs_live_... or Polar keys to your new billing provider
  return verifyStripeOrPolarKey(key);
}
```

---

## 3. Auditing Your Store Export Locally (Zero Customer PII Uploads)

Never upload raw customer emails, MRR figures, and license keys to an unverified web service. If you want to audit your Lemon Squeezy CSV export right inside Chrome (0 network requests) or via an offline Python CLI:

- **LemonExitBridge (Browser Web App & Offline Python CLI)**: [Lemon Squeezy to Stripe / Polar Migrator](https://domstijn.github.io/friction-killer-suite/products/lemonsqueezy-stripe-polar-migrator/?ref=src.devto-lemon)

Drop your Lemon Squeezy Subscriptions/Customers CSV to compute safe Card MRR vs. PayPal MRR at risk, generate `trial_end_unix` columns, isolate your `paypal_manual_reauth` cohort CSV, and export your `lemon.legacy_keys.v1` JSON bundle locally.
