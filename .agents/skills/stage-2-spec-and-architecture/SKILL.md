---
name: stage-2-spec-and-architecture
description: >-
  Lock the user-selected opportunity from Gate 1, scaffold the project workspace,
  and complete the 1-page technical and monetization specification (SPEC.md).
  Use immediately after Gate 1 approval.
---

# Stage 2: Spec & Architecture

## Goal
Turn the Gate 1 choice into an actionable, minimal-bloat engineering & monetization blueprint (`projects/<slug>/SPEC.md`), then flow automatically into Stage 3 unless a blocker needs user input.

## Steps

1. **Lock Selection & Update State**:
   ```bash
   python3 scripts/pipeline_ctl.py select-idea --id "<slug>"
   ```

2. **Scaffold Project Workspace**:
   Choose the appropriate `--ecosystem` (`browser-extension`, `ide-ai-plugin`, `cli-wrapper`, `saas-addon`) and `--provider` (`lemonsqueezy`, `polar`, `gumroad`):
   ```bash
   python3 scripts/scaffold_project.py \
     --slug "<slug>" \
     --title "<Title>" \
     --ecosystem "<ecosystem>" \
     --provider "<provider>" \
     --host-software "<Host Software>"
   ```

3. **Complete `projects/<slug>/SPEC.md`**:
   Fill every section concisely (under ~120 lines to stay token-lean):
   - Exact host software friction + evidence URLs from Stage 1
   - Concrete Free vs. Pro feature split (ensuring Free proves value and Pro justifies paying)
   - Minimal file architecture, API/DOM hooks, and local storage assumptions
   - Deterministic verification plan (unit tests, license-gate checks, packaging checks)

4. **Check for Blockers before Stage 3**:
   - If implementation requires a paid API key, ambiguous host-software ToS/legal compliance, or an unapproved UX choice, **STOP** and call `ask_question`.
   - Otherwise, proceed immediately to `stage-3-mvp-builder` (Lean Gatekeeper mode).
