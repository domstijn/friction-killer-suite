# Friction-Killer Software & Plugin Factory

Mission: Discover high-friction pain points in existing software, evaluate effectiveness & commercial potential, build lean MVPs with zero-backend license-key monetization (Polar / Lemon Squeezy / Gumroad), and prepare complete launch & distribution kits.

## Token-Saving Rules (Strict)

1. **Never dump raw payloads**: Never read raw HTML/API dumps into context. Run `python3 scripts/mine_signals.py` or filter CLI output first.
2. **State first**: Start any pipeline turn with `python3 scripts/pipeline_ctl.py status` instead of reading full project histories.
3. **One skill per stage**: Only read and load the `.agents/skills/stage-*` `SKILL.md` for the active stage.
4. **Delegate heavy isolation**: Use `research` for broad read-only surveys or `browser` (`Model="flash"`) for UI verification when needed.

## Lean Gatekeeper Flow & Checkpoints

- **Stage 1 (`stage-1-pain-discovery`)**: Mine pain signals -> Score & rank via `scripts/score_opportunity.py --save` -> Pitch Top 3 with 1-paragraph specs -> **STOP at Gate 1** (`ask_question`) for user selection.
- **Stage 2 (`stage-2-spec-and-architecture`)**: Lock choice (`pipeline_ctl.py select-idea`), scaffold (`scaffold_project.py`), write `projects/<slug>/SPEC.md` -> Proceed automatically to Stage 3 unless a blocker needs user input.
- **Stage 3 (`stage-3-mvp-builder`)**: Implement MVP + zero-backend license gate (`license_client.js`/`.py`) -> Run deterministic tests -> Proceed automatically to Stage 4 once tests pass.
- **Stage 4 (`stage-4-launch-and-monetize`)**: Customize `projects/<slug>/launch/landing.html` and `LAUNCH_KIT.md` -> Run `python3 scripts/ship_check.py --slug <slug> --package` -> **STOP at Gate 2** (`ask_question`) for final review, checkout IDs & publishing.

## Continuous Self-Improvement (10% Kaizen)

Reserve ~10% effort per cycle to remove workflow friction and raise ROI: inspect `pipeline/kaizen.json`, automate repeated manual checks into `scripts/`, and log upgrades in `pipeline/kaizen.json`.

## Emergency Human-Input Trigger

Immediately pause and call `ask_question` at any stage if you hit: paid API/account requirements, host-software ToS/legal ambiguity, or an irreversible external action.
