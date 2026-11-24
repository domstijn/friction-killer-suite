# Friction-Killer Suite — Growth & Validation Scorecard

- **Updated (UTC):** `2026-11-24T08:02:01+00:00`
- **Window:** Last `14` days
- **Objective Decision Gate:** **COLLECTING DATA (NEED >= 200 QUALIFIED VISITORS)**
  - *Current human funnel sample is too small (12 page_view(s)) for a Day 14 verdict; continue targeted outreach and daily tracking.*

---

## 1. Verified Human Funnel (Cloudflare EU D1 Worker — Bots Filtered Out)

| Metric | Count | Rate vs. Page Views |
| :--- | :---: | :---: |
| **Human `page_view`** | **12** | 100% |
| **Real `file_upload`** | **0** | 0.0% |
| **Interactive `tool_run`** | **2** | 16.7% |
| **Total Activations (`file_upload` + `tool_run`)** | **2** | **16.7%** |
| **Pro `paywall_hit`** | **0** | 0.0% |
| **Stripe `checkout_click`** | **0** | **0.0%** |
| **User `feedback_click`** | **0** | - |

### By Product / Page
| Slug | `page_view` | `file_upload` | `tool_run` | `paywall_hit` | `checkout_click` | `feedback_click` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `hub` | 3 | 0 | 0 | 0 | 0 | 0 |
| `e-invoice-xml-batch-converter` | 3 | 0 | 1 | 0 | 0 | 0 |
| `eu-oss-vat-return-compiler` | 2 | 0 | 0 | 0 | 0 | 0 |
| `claude-profile-switcher` | 1 | 0 | 0 | 0 | 0 | 0 |
| `lemonsqueezy-stripe-polar-migrator` | 1 | 0 | 0 | 0 | 0 | 0 |
| `notion-linear-prd-sync` | 1 | 0 | 0 | 0 | 0 | 0 |
| `camt053-mt940-qbo-xero-converter` | 1 | 0 | 1 | 0 | 0 | 0 |

### Referrers
| Referrer Host | Events |
| :--- | :---: |
| `direct` | 11 |
| `github.com` | 2 |
| `bing.com` | 1 |

---

## 2. Live Stripe Revenue (`acct_1UdCWDH2AcdDmQyR`)

| Metric | Value | Notes |
| :--- | :---: | :--- |
| **Net Revenue Balance** | **€0.00** | Verified live Stripe balance |
| **Paid Orders** | **0** | Completed live PaymentIntents / paid sessions |
| **Total Checkout Sessions Created** | 19 | Includes unpaid/expired & crawler link previews |
| **Currently Open Unpaid Sessions** | 10 | Exclude from revenue metrics |

---

## 3. Channel Baselines (Noise-Flagged — Never Confuse Scraper Clones with Sales)

- **GitHub (`domstijn/friction-killer-suite`):** `0` stars · `0` forks · `12` repo views (`8` uniques, 14d) · `243` clones (`108` uniques — *mostly automated GitHub cloners/mirror bots*)
- **VS Code Marketplace (`friction-killer.vscode-workspace-profile-config`):** `43.0` `downloadCount` *(includes automated scanner pulls)*

### Releases
| Tag | Created (UTC) | Assets | Total Downloads (incl. bots) |
| :--- | :--- | :---: | :---: |
| `v0.4.0` | 2026-11-23T20:05:06Z | 25 | 11 |
| `v0.3.0` | 2026-11-22T21:28:01Z | 21 | 22 |
| `v0.1.0` | 2026-11-18T18:13:20Z | 15 | 0 |

### PyPI Packages (`4` Live / `5` Pending Rate-Limit Cooldown)
| Package | Registry Status | Downloads (7d) | Downloads (30d) |
| :--- | :--- | :---: | :---: |
| `eu-oss-vat-return-compiler` | LIVE (HTTP 200) | n/a | n/a |
| `amazon-settlement-xero-qbo-splitter` | LIVE (HTTP 200) | n/a | n/a |
| `e-invoice-xml-batch-converter` | LIVE (HTTP 200) | 65 | 65 |
| `lemonsqueezy-stripe-polar-migrator` | LIVE (HTTP 200) | n/a | n/a |
| `stripe-payout-xero-qbo-splitter` | PENDING (429 cooldown) | n/a | n/a |
| `notion-clean-md-exporter` | PENDING (429 cooldown) | n/a | n/a |
| `claude-profile-switch` | PENDING (429 cooldown) | n/a | n/a |
| `woo-shopify-metafield-migrator` | PENDING (429 cooldown) | n/a | n/a |
| `camt053-mt940-qbo-xero-converter` | PENDING (429 cooldown) | n/a | n/a |
