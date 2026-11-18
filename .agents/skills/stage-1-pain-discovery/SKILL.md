---
name: stage-1-pain-discovery
description: >-
  Discover high-friction software pain points, propose plugin or micro-tool solutions,
  score effectiveness and commercial potential, and present the Top 3 candidates for Gate 1 approval.
  Use when starting a new product cycle or asked to find software/plugin ideas.
---

# Stage 1: Pain Discovery & Opportunity Scoring

## Goal
Find high-intent complaints about existing software with minimal token overhead, design 3 concrete plugin/micro-tool solutions, score each rigorously, and pause at **Gate 1** for user selection.

## Steps

1. **Check pipeline state** (do not read raw logs):
   ```bash
   python3 scripts/pipeline_ctl.py status
   python3 scripts/pipeline_ctl.py set-stage --stage STAGE_1_DISCOVERY
   ```

2. **Mine compact pain signals**:
   Run `scripts/mine_signals.py` against 2–3 promising software targets (or the user's chosen niche). Keep `--limit` small (6–8) to minimize context tokens.
   ```bash
   python3 scripts/mine_signals.py --target "<software>" --limit 8 --format md
   ```
   - Supplement with 1–2 targeted `search_web` queries only if an API returns empty/rate-limited results. Never dump raw HTML into context.

3. **Propose & Score 3 Candidates**:
   Formulate 3 distinct, non-bloated solutions (browser extension, IDE/AI plugin, CLI wrapper, or SaaS add-on). Score each with `scripts/score_opportunity.py --save`:
   ```bash
   python3 scripts/score_opportunity.py \
     --id "<slug>" --title "<Title>" --ecosystem "<ecosystem>" \
     --target-software "<Host>" --pain "<1-line pain>" --solution "<1-line fix>" \
     --pain-severity <1-10> --willingness-to-pay <1-10> \
     --solution-effectiveness <1-10> --build-speed <1-10> \
     --distribution-clarity <1-10> --platform-safety <1-10> \
     --save
   ```
   - Reject any idea that triggers a kill switch (`willingness_to_pay < 4`, `platform_safety < 4`, or `solution_effectiveness < 5`). Replace it before pitching.

4. **Pitch Top 3 & Stop at Gate 1**:
   Present a compact Markdown table with:
   - Slug, Title & Ecosystem
   - Host Software & Evidence URL(s)
   - 1-paragraph solution + Free vs. Pro license split
   - Effectiveness Score, Commercial (Pie) Score, Composite Score & Verdict

   Then **STOP** and call `ask_question` so the user selects 1 candidate to build (or asks to re-mine a different niche) and confirms any spec preferences.
