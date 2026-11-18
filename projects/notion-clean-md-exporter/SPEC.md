# Product & Technical Spec: NotionGitExport (`notion-clean-md-exporter`)

- **Ecosystem**: `cli-wrapper` (Zero-dependency Python 3.10+ CLI)
- **Host Software**: Notion
- **Monetization Provider**: `stripe` (Stripe Managed Payments, `2025-03-31.basil`, EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`)

## 1. Pain & Evidence
- **Exact Friction**: Native Notion Markdown exports append 32-character hex UUID hashes to every filename and directory, inject non-standard `Key: Value` property text below `# Title`, and break relative internal links and asset paths when importing into Git repositories, Obsidian vaults, or Astro/Docusaurus sites.
- **Evidence URLs**:
  - `https://github.com/contentlayerdev/contentlayer/issues/174` (353 reactions requesting clean Notion content ingestion)
  - `https://github.com/inkeep/open-knowledge` & `https://github.com/mayneyao/eidos` (HN discussions highlighting Notion Markdown lock-in and portability friction)

## 2. Target Persona & Value Proposition
- **Who pays**: Technical writers, indie makers, engineering teams, and Obsidian/Astro users migrating docs out of Notion into Git-backed Markdown.
- **10x Relief**: One CLI command strips every 32-char UUID suffix, converts Notion property blocks into clean YAML frontmatter, rewrites relative links, and localizes assets in seconds.

## 3. Free vs. Pro Feature Split & Stripe Managed Payments
- **Free Starter Tier (€0)**:
  - Clean up to **10 Notion Markdown files** per export run (strips 32-char UUID hashes from filenames and rewrites internal Markdown links).
- **Pro Tier (€24 one-time via Stripe Managed Payments, EUR, tax-inclusive; or €49 All-Access Bundle)**:
  - **Unlimited** recursive workspace export (no 10-file limit).
  - **YAML Frontmatter Extraction**: Converts Notion `# Title` and `Key: Value` property blocks (`Status:`, `Tags:`, `Created:`) into clean `---` YAML frontmatter.
  - **Clean Asset Path Localization**: Renames and rewrites image/file references consistently.
- **Live Stripe Configuration**:
  - **Product ID**: `prod_VeW69bJBCk3Nbr` | **Price ID**: `price_1UdD76H2AcdDmQyRk9cyWuxd` (€24 one-time, EUR, tax-inclusive)
  - **Live Stripe Payment Link**: https://buy.stripe.com/6oU4gz0Ms8uo1iw6lm6sw00
  - **All-Access Bundle (€49 one-time, `prod_VeW6IYwGyYJkPv`)**: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
  - **Live Product Sales Page**: https://domstijn.github.io/friction-killer-suite/products/notion-clean-md-exporter/
  - **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}` and paste it as their Pro License Key (validated against `/verify-license` with offline session-format fallback).

## 4. Minimal Architecture & File Map
- `pyproject.toml` — Zero-dependency Python package config.
- `src/license_client.py` — Stripe Checkout Session ID (`cs_live_...`) validator (`/verify-license` with offline session-format fallback) + 7-day offline grace cache.
- `src/exporter.py` — Core UUID stripper, relative link rewriter, YAML frontmatter converter, and tier-gated recursive exporter.
- `src/cli.py` — Command-line interface (`--input`, `--output`, `--activate`, `--pro`).
- `tests/test_cli.py` — Deterministic unit & end-to-end tests covering Free 10-file cap and Pro YAML export.

## 5. Verification Plan
1. Run `python3 projects/notion-clean-md-exporter/tests/test_cli.py` to test UUID stripping, link rewriting, YAML frontmatter conversion, Free-tier cap on 11 files, and Pro license unlock.
2. Run `python3 scripts/ship_check.py --slug notion-clean-md-exporter --package` to verify zero placeholders, passing tests, and `dist/notion-clean-md-exporter-v0.1.0.zip`.
