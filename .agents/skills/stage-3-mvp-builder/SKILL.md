---
name: stage-3-mvp-builder
description: >-
  Implement and verify the friction-killer MVP and wire in the zero-backend license key gate
  from SPEC.md with minimal token overhead. Use right after Stage 2 spec completion.
---

# Stage 3: MVP Implementation & Verification

## Goal
Build a lean, reliable MVP that eliminates the target friction and enforces the Free/Pro license key boundary, verified by automated tests.

## Steps

1. **Advance Stage**:
   ```bash
   python3 scripts/pipeline_ctl.py set-stage --stage STAGE_3_BUILD
   ```

2. **Implement Core Logic & License Gate**:
   - Read `projects/<slug>/SPEC.md` (and only the files in `projects/<slug>/src/`).
   - Implement the core friction-killer workflow cleanly without extra dependencies where standard libraries/APIs suffice.
   - Wire Pro features to `requireProFeature` / `require_pro_feature` and `verifyLicense` / `verify_license` from the scaffolded `license_client` module.
   - Keep code modular, small, and dependency-light.

3. **Write & Run Deterministic Tests**:
   - Expand `projects/<slug>/tests/` to cover:
     1. Core friction-reduction behavior (happy path + key edge cases)
     2. Free tier behavior works without a license
     3. Pro feature is blocked when unlicensed and unlocked when given a valid mocked/cached license
   - Run the test suite via `run_command`. Fix any failures before proceeding (escalate with `ask_question` if stuck after 2 failed attempts or if a missing external secret blocks verification).
   - If visual browser/extension UI verification is required, delegate to the `browser` subagent (`Model="flash"`).

4. **Proceed to Stage 4**:
   Once all tests pass cleanly, transition directly to `stage-4-launch-and-monetize`.
