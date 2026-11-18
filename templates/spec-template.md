# Product & Technical Spec: <TITLE> (`<SLUG>`)

- **Ecosystem**: `<ECOSYSTEM>`
- **Host Software**: <HOST_SOFTWARE>
- **Monetization Provider**: `<PROVIDER>`

## 1. Pain & Evidence
- **Exact Friction**: <Describe the repetitive/broken workflow>
- **Evidence URLs**:
  - <URL 1 from Stage 1 discovery>
  - <URL 2 from Stage 1 discovery>

## 2. Target Persona & Value Proposition
- **Who pays**: <Role / Prosumer / B2B team>
- **10x Relief**: <How this tool eliminates the friction in 1 click / 1 command>

## 3. Free vs. Pro Feature Split
- **Free Tier**: <What works out-of-the-box to prove value>
- **Pro Tier (License Key Gated)**: <Batch mode / advanced export / automation / unlimited usage>

## 4. Minimal Architecture & File Map
- `src/` — Core friction-killer logic + `license_client` integration
- `tests/` — Deterministic unit/smoke tests covering core fix + Pro gate
- `launch/` — Landing page (`landing.html`) & distribution playbook (`LAUNCH_KIT.md`)

## 5. Verification Plan
1. <Exact command to run unit/smoke tests>
2. <Check free-tier behavior vs. valid/invalid license key mock>
3. <Check packaged build / manifest validity>
