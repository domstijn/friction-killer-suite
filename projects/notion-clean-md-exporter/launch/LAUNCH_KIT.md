# Launch & Monetization Kit: NotionGitExport (`notion-clean-md-exporter`)

## 1. Checkout & License Key Setup (Stripe Managed Payments)
- **Provider & Account**: `stripe` — Stripe Managed Payments (`2025-03-31.basil`), EUR, account `acct_1UdCWDH2AcdDmQyR`, tax code `txcd_10103000`.
- **Individual Pro Product**: **NotionGitExport Pro** — **€24 one-time** (EUR, tax-inclusive)
  - Product ID: `prod_VeW69bJBCk3Nbr`
  - Price ID: `price_1UdD76H2AcdDmQyRk9cyWuxd`
  - Live Stripe Payment Link: https://buy.stripe.com/6oU4gz0Ms8uo1iw6lm6sw00
- **All-Access Bundle**: **€49 one-time** (EUR, tax-inclusive, `prod_VeW6IYwGyYJkPv`)
  - Live Stripe Payment Link: https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03
- **Live Product Sales Page**: https://domstijn.github.io/friction-killer-suite/products/notion-clean-md-exporter/
- **License Activation**: Customers receive their Stripe Checkout Session ID (`cs_live_...`) on `https://domstijn.github.io/friction-killer-suite/success.html?session_id={CHECKOUT_SESSION_ID}` and paste it as their Pro License Key via `--activate cs_live_...` (validated against `/verify-license` with offline session-format fallback).

## 2. Package Listing / Direct Distribution Draft
- **Title**: NotionGitExport — Lossless Notion to Clean Git/Obsidian Markdown
- **Short Summary (119 chars)**: Strip 32-char Notion UUIDs, repair relative links, and convert metadata into clean YAML frontmatter in one CLI command.
- **Keywords**: notion export, markdown cleaner, obsidian migration, astro docs, yaml frontmatter, git
- **Permissions Justification**: Operates strictly on local user-specified `--input` and `--output` folders; makes zero network calls except `--activate` verification against `/verify-license` (with offline Stripe Checkout Session ID format fallback).

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact Stage 1 discovery discussions:
- Target Thread 1: `https://github.com/contentlayerdev/contentlayer/issues/174`
- Target Thread 2: `https://github.com/inkeep/open-knowledge` & `https://github.com/mayneyao/eidos`

**Reply Template**:
> If anyone here is exporting Notion workspaces into Git/Obsidian/Contentlayer, the 32-char UUID suffixes and broken relative links are always a headache. I put together a zero-dependency Python CLI (NotionGitExport) that strips UUIDs, fixes internal relative paths, and emits clean YAML frontmatter locally. Free for up to 10 files per folder if you want to try it: https://domstijn.github.io/friction-killer-suite/products/notion-clean-md-exporter/.

## 4. Launch Post Copy (Show HN / r/Notion / r/ObsidianMD)
- **Title**: Show HN: NotionGitExport – Strip Notion UUID hashes and fix broken Markdown exports in 1 command
- **Body**:
  - Notion's Markdown export breaks Git/Obsidian/Astro imports with 32-char UUID hashes on every filename, `%20` links, and raw `Key: Value` text blocks.
  - NotionGitExport is a zero-dependency Python 3 CLI that deterministically slugifies filenames, rewrites relative links, and converts Notion metadata into YAML frontmatter.
  - Free up to 10 files; €24 one-time Pro key (or €49 All-Access Bundle) unlocks unlimited recursive workspaces + asset path localization: https://domstijn.github.io/friction-killer-suite/products/notion-clean-md-exporter/
