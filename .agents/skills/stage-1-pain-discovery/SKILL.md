---
name: stage-1-pain-discovery
description: >-
  Discover high-friction software pain points, verify existing supply/competitors,
  score effectiveness, commercial potential & DIY resistance, and present Top 3 candidates at Gate 1.
  Use when starting a new product cycle or asked to find software/plugin ideas.
---

# Stage 1: Pain Discovery, Supply Verification & Opportunity Scoring

## Goal
Find recent, un-saturated pain points with minimal token overhead, verify that native flags or free open-source tools don't already solve >=80% of the friction, score rigorously, and pause at **Gate 1** for user selection.

## Steps

1. **Check pipeline state** (do not read raw logs):
   ```bash
   python3 scripts/pipeline_ctl.py status
   python3 scripts/pipeline_ctl.py set-stage --stage STAGE_1_DISCOVERY
   ```

2. **Mine recent pain signals & inspect existing supply**:
   - Check `pipeline/MARKET_RADAR.md` first — if the Radar Agent (`fb4a3e59-d8d5-40c7-97b7-e1c8983cfb6f`) already has verified `GO` commercial opportunities queued, reuse them directly instead of burning tokens re-mining from scratch.
   Prefer `--since-year 2024` (or `2025`) and `--check-existing` so old 2017–2019 mega-issues with built-in/comment workarounds are filtered down and existing GitHub/OSS tools are surfaced automatically.
   ```bash
   python3 scripts/mine_signals.py --targets "<s1>,<s2>" --since-year 2024 --check-existing --limit 6 --format md
   ```
   - Before pitching ANY idea, verify live competition via `search_web` / Marketplace / Chrome Web Store / GitHub so you know what native flags, official free plugins, or OSS tools exist.

3. **Propose & Score 3 Non-CLI / Commercial-Buyer Candidates**:
   Deprioritize `"dev-config"` audiences (MCP JSON tweakers, CLI/SDK config wrappers) whose reflex is to combine a free GitHub repo with a token; prioritize `"commercial"` / `"b2b-operator"` workflows (agency operations, e-commerce sellers, finance/invoicing, CRM/recruiting) where users pay for 1-click UI reliability. Score each via `scripts/score_opportunity.py --save`:
   ```bash
   python3 scripts/score_opportunity.py \
     --id "<slug>" --title "<Title>" --ecosystem "<ecosystem>" \
     --target-software "<Host>" --pain "<1-line pain>" --solution "<1-line fix>" \
     --existing-alternatives "<Verified alternatives & why they fail>" \
     --free-escape-hatch "<Best 2-min free workaround & why it fails >=50%>" \
     --buyer-persona "<commercial|b2b-operator|prosumer|dev-config>" \
     --pain-severity <1-10> --willingness-to-pay <1-10> \
     --existing-alternative-saturation <1-10> --diy-resistance <1-10> \
     --solution-effectiveness <1-10> --build-speed <1-10> \
     --distribution-clarity <1-10> --platform-safety <1-10> \
     --save
   ```
   - **`free_escape_hatch` Rule**: Before scoring any idea `GO`, test the **"Best 2-Minute Free Workaround"** (even if not mentioned in the issue comments yet — e.g., native export button, shared PAT + community OSS repo, or manual copy-paste). If that free escape hatch works for `>=50%` of users without breaking, score `existing_alternative_saturation <= 4` (**automatic `NO-GO`**).
   - **`buyer_persona` Filter**: Deprioritize `"dev-config"` audiences; any `"dev-config"` candidate with `willingness_to_pay < 6.5` triggers automatic `NO-GO`.
   - **Mandatory Kill Switches** (reject & replace any idea triggering `NO-GO`):
     - `ecosystem == "browser-extension"` while Chrome Web Store is at its `2/2` extension limit (`LinearBridge` + `NotionGuestBridge` in review; omit `--cws-slot-available` until approved) — build as a zero-install **`saas-addon` browser web app** or **`ide-ai-plugin` (`.vsix`)** for VS Code Marketplace instead
     - `willingness_to_pay < 4` (or `< 6.5` when `--buyer-persona dev-config`)
     - `platform_safety < 4`
     - `solution_effectiveness < 5`
     - `existing_alternative_saturation < 5` (native export, shared PAT + OSS repo, or 2-min free escape hatch solves `>=50%`)
     - `diy_resistance < 5` (replaceable by a <15-line shell script or alias)

4. **Pitch Top 3 & Stop at Gate 1**:
   Present a compact Markdown table containing:
   - Slug, Title & Ecosystem
   - Host Software & Recent Evidence URL(s)
   - **Existing Alternatives & Best Free Escape Hatch** *(verified via live search, including off-thread workarounds)*
   - 1-paragraph solution + Free vs. Pro license split
   - Effectiveness, Commercial, Saturation, DIY-Res & Composite Score + Verdict

   Then **STOP** and call `ask_question` so the user selects 1 candidate to build (or asks to re-mine a different niche).
