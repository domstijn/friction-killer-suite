---
name: stage-4-launch-and-monetize
description: >-
  Customize the sales landing page, license checkout configuration, marketplace assets,
  and sniper distribution copy, package the build, and pause at Gate 2 for user launch review.
  Use after Stage 3 MVP tests pass.
---

# Stage 4: Launch & Monetization Kit (Gate 2)

## Goal
Prepare everything needed to market, distribute, and sell the verified MVP, then loop the user in at **Gate 2** for checkout credentials and publishing.

## Steps

1. **Advance Stage**:
   ```bash
   python3 scripts/pipeline_ctl.py set-stage --stage STAGE_4_LAUNCH
   ```

2. **Customize Sales Landing Page & Launch Kit**:
   - Edit `projects/<slug>/launch/landing.html`: replace remaining placeholders (`<TAGLINE>`, `<PAIN_SUMMARY>`, `<PRO_PRICE>`, `<HOST_SOFTWARE>`, and feature bullets) with sharp, benefit-driven copy grounded in Stage 1 pain signals.
   - Edit `projects/<slug>/launch/LAUNCH_KIT.md`: fill out:
     - Exact Stripe Managed Payments / Polar.sh / Gumroad checkout & license key setup steps
     - Marketplace listing fields (title, <=132-char description, keywords, permission justification)
     - Non-spammy "Reply-to-Pain" outreach drafts pointing to the exact Stage 1 complaint URLs
     - Launch copy (only suggest Show HN if the storefront provides an interactive zero-signup playground users can run live in the browser; otherwise target native marketplaces, Reddit, and GitHub issues)

3. **Package Native Distributable Builds**:
   - Run `python3 scripts/ship_check.py --slug <slug> --package` to generate `.zip` plus native marketplace artifacts (`.vsix` for VS Code plugins, PEP 427 `.whl` for Python CLI wrappers).

4. **Present Results & Stop at Gate 2**:
   Provide a concise summary linking to:
   - Implemented files and exact test results observed
   - `projects/<slug>/launch/landing.html`
   - `projects/<slug>/launch/LAUNCH_KIT.md`

   Then call `ask_question` to confirm next steps (e.g., insert live Polar/Lemon Squeezy/Gumroad checkout URL & Product ID, adjust MVP/copy, mark `COMPLETED`, or reset for the next product idea).
