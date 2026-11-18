# Product & Technical Spec: NotionGitExport (`notion-clean-md-exporter`)

- **Ecosystem**: `cli-wrapper` (Zero-dependency Python 3.10+ CLI)
- **Host Software**: Notion
- **Monetization Provider**: `lemonsqueezy` (\$24 one-time Pro license key)

## 1. Pain & Evidence
- **Exact Friction**: Native Notion Markdown exports append 32-character hex UUID hashes to every filename and directory, inject non-standard `Key: Value` property text below `# Title`, and break relative internal links and asset paths when importing into Git repositories, Obsidian vaults, or Astro/Docusaurus sites.
- **Evidence URLs**:
  - `https://github.com/contentlayerdev/contentlayer/issues/174` (353 reactions requesting clean Notion content ingestion)
  - `https://github.com/inkeep/open-knowledge` & `https://github.com/mayneyao/eidos` (HN discussions highlighting Notion Markdown lock-in and portability friction)

## 2. Target Persona & Value Proposition
- **Who pays**: Technical writers, indie makers, engineering teams, and Obsidian/Astro users migrating docs out of Notion into Git-backed Markdown.
- **10x Relief**: One CLI command strips every 32-char UUID suffix, converts Notion property blocks into clean YAML frontmatter, rewrites relative links, and localizes assets in seconds.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (\$0)**:
  - Clean up to **10 Notion Markdown files** per export run (strips 32-char UUID hashes from filenames and rewrites internal Markdown links).
- **Pro Tier (\$24 one-time via Lemon Squeezy License Key)**:
  - **Unlimited** recursive workspace export (no 10-file limit).
  - **YAML Frontmatter Extraction**: Converts Notion `# Title` and `Key: Value` property blocks (`Status:`, `Tags:`, `Created:`) into clean `---` YAML frontmatter.
  - **Clean Asset Path Localization**: Renames and rewrites image/file references consistently.

## 4. Minimal Architecture & File Map
- `pyproject.toml` — Zero-dependency Python package config.
- `src/license_client.py` — Lemon Squeezy validator + 7-day offline grace cache.
- `src/exporter.py` — Core UUID stripper, relative link rewriter, YAML frontmatter converter, and tier-gated recursive exporter.
- `src/cli.py` — Command-line interface (`--input`, `--output`, `--activate`, `--pro`).
- `tests/test_cli.py` — Deterministic unit & end-to-end tests covering Free 10-file cap and Pro YAML export.

## 5. Verification Plan
1. Run `python3 projects/notion-clean-md-exporter/tests/test_cli.py` to test UUID stripping, link rewriting, YAML frontmatter conversion, Free-tier cap on 11 files, and Pro license unlock.
2. Run `python3 scripts/ship_check.py --slug notion-clean-md-exporter --package` to verify zero placeholders, passing tests, and `dist/notion-clean-md-exporter-v0.1.0.zip`.
