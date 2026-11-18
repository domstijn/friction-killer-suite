# Launch & Monetization Kit: NotionGitExport (`notion-clean-md-exporter`)

## 1. Checkout & License Key Setup (Lemon Squeezy)
1. Create a product named **NotionGitExport Pro** in Lemon Squeezy priced at **\$24 one-time**.
2. Enable **License Keys** (3 activations) and attach `dist/notion-clean-md-exporter-v0.1.0.zip` as the instant download file.
3. Run `python3 scripts/configure_checkout.py --slug notion-clean-md-exporter --checkout-url "<URL>" --product-id "<ID>"` to update `landing.html` and `src/cli.py`.

## 2. Package Listing / Direct Distribution Draft
- **Title**: NotionGitExport — Lossless Notion to Clean Git/Obsidian Markdown
- **Short Summary (119 chars)**: Strip 32-char Notion UUIDs, repair relative links, and convert metadata into clean YAML frontmatter in one CLI command.
- **Keywords**: notion export, markdown cleaner, obsidian migration, astro docs, yaml frontmatter, git
- **Permissions Justification**: Operates strictly on local user-specified `--input` and `--output` folders; makes zero network calls except `--activate` to `api.lemonsqueezy.com`.

## 3. "Reply-to-Pain" Sniper Outreach (Non-Spammy)
Reference the exact Stage 1 discovery discussions:
- Target Thread 1: `https://github.com/contentlayerdev/contentlayer/issues/174`
- Target Thread 2: `https://github.com/inkeep/open-knowledge` & `https://github.com/mayneyao/eidos`

**Reply Template**:
> If anyone here is exporting Notion workspaces into Git/Obsidian/Contentlayer, the 32-char UUID suffixes and broken relative links are always a headache. I put together a zero-dependency Python CLI (NotionGitExport) that strips UUIDs, fixes internal relative paths, and emits clean YAML frontmatter locally. Free for up to 10 files per folder if you want to try it: [landing page URL].

## 4. Launch Post Copy (Show HN / r/Notion / r/ObsidianMD)
- **Title**: Show HN: NotionGitExport – Strip Notion UUID hashes and fix broken Markdown exports in 1 command
- **Body**:
  - Notion's Markdown export breaks Git/Obsidian/Astro imports with 32-char UUID hashes on every filename, `%20` links, and raw `Key: Value` text blocks.
  - NotionGitExport is a zero-dependency Python 3 CLI that deterministically slugifies filenames, rewrites relative links, and converts Notion metadata into YAML frontmatter.
  - Free up to 10 files; \$24 one-time Pro key unlocks unlimited recursive workspaces + asset path localization.
