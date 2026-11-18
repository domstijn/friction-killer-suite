# Product & Technical Spec: LinearBridge (`notion-linear-prd-sync`)

- **Ecosystem**: `browser-extension` (Chrome Manifest V3)
- **Host Software**: Notion & Linear
- **Monetization Provider**: `lemonsqueezy` (\$29 one-time Pro license key)

## 1. Pain & Evidence
- **Exact Friction**: Linear's native Notion integration is strictly read-only link unfurling. Product managers and tech leads must manually copy-paste Notion PRD sections and checklists into Linear issues or pay for fragile Zapier/Make polling scenarios that break on schema edits.
- **Evidence URLs**:
  - `https://github.com/anthropics/claude-code/issues/12925` (156 reactions on direct Linear workflow integration)
  - `https://news.ycombinator.com/item?id=41960188` (Linear context-switching & capture friction)

## 2. Target Persona & Value Proposition
- **Who pays**: Engineering Leads, Product Managers, and Startups running specs in Notion and sprints in Linear.
- **10x Relief**: Injects a zero-backend **"Push PRD to Linear"** bar directly inside Notion that turns headings and task checklists into structured Linear issues with 1 click using the user's own Linear API key—no Zapier tax, no third-party server storing company PRDs.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (\$0)**:
  - Push up to **5 open checklist items/week** from any Notion PRD into flat Linear issues.
  - Automatically skips completed (`[x]`) items and lines already tagged with `[KEY-123]`.
- **Pro Tier (\$29 one-time via Lemon Squeezy License Key)**:
  - **Unlimited** PRD pushes per week (no 5-issue cap).
  - **Parent Epic + Sub-Issue Hierarchy**: Automatically creates a Parent Linear issue for the Notion PRD and links every checklist item as a child sub-issue (`parentId`) carrying its H2/H3 section context.
  - **1-Click Status Badge Sync**: Pulls live Linear statuses back to format `[ENG-101: In Progress]` badges cleanly.
  - **Priority Presets**: Set Urgent/High/Medium/Low priority across generated sub-issues.

## 4. Minimal Architecture & File Map
- `manifest.json` — Chrome MV3 config (`storage`, `activeTab`, `scripting`, Notion + Linear + Lemon Squeezy host permissions).
- `src/license_client.js` — Zero-backend Lemon Squeezy validator + 7-day offline grace cache.
- `src/prd_parser.js` — Parses Notion/Markdown headings & checklists, deduplicates `[KEY-123]` tags, enforces Free vs. Pro limits, and formats status badges.
- `src/linear_client.js` — Linear GraphQL client (`issueCreate` for Parent + `parentId` sub-issues, plus status queries).
- `src/content.js` — Lightweight floating `#linearbridge-bar` injected on `notion.so` pages to extract DOM headings/todos and trigger sync.
- `src/background.js` — MV3 service worker & testable `handlePushPrd` / `handleSyncStatuses` orchestrator.
- `src/popup.html` & `src/popup.js` — Settings & quick-push popup (Linear API key, Team ID, Priority, Lemon Squeezy license activation).
- `tests/smoke_test.py` — Validates `manifest.json` and runs Node.js ESM unit + end-to-end mocked workflow tests.

## 5. Verification Plan
1. Run `python3 projects/notion-linear-prd-sync/tests/smoke_test.py` to validate Manifest V3 structure and run the Node.js ESM test suite covering `parseNotionPrd`, `enforceTierLimits`, `handlePushPrd` (Free cap vs. Pro Parent+Sub-issue unlock via mocked Lemon Squeezy + Linear APIs), and `formatStatusBadges`.
2. Run `python3 scripts/ship_check.py --slug notion-linear-prd-sync --package` to verify zero unreplaced placeholders, 100% test pass, and clean `dist/notion-linear-prd-sync-v0.1.0.zip` archive generation.
