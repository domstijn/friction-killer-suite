# Product & Technical Spec: ExtProfileLock (`vscode-workspace-profile-config`)

- **Ecosystem**: `ide-ai-plugin` (VS Code Extension / Node ESM Core)
- **Host Software**: VS Code
- **Monetization Provider**: `lemonsqueezy` (\$19 one-time Pro license key)

## 1. Pain & Evidence
- **Exact Friction**: VS Code lacks a declarative repo-committed config to automatically enable/disable conflicting extensions per project, and `.code-workspace` files do not support `${env:VAR}` interpolation while GUI-launched VS Code windows cache stale shell environments.
- **Evidence URLs**:
  - `https://github.com/microsoft/vscode/issues/40239` (1,181 reactions / 437 comments requesting declarative workspace extension enable/disable config)
  - `https://github.com/microsoft/vscode/issues/44755` (`.code-workspace` environment variable interpolation & GUI shell env caching)

## 2. Target Persona & Value Proposition
- **Who pays**: Full-stack developers, polyglot teams, and engineering leads switching between client/monorepo projects with conflicting formatters, linters, and AI assistants.
- **10x Relief**: Commits one `.vscode/workspace-lock.json` file alongside `.env` so every teammate gets deterministic extension state and interpolated `.code-workspace` paths in seconds.

## 3. Free vs. Pro Feature Split
- **Free Starter Tier (\$0)**:
  - Audit a single-root `.vscode/workspace-lock.json` against installed extensions (reports missing required & active conflicting extensions) and parse local `.env` variables.
- **Pro Tier (\$19 one-time via Lemon Squeezy License Key)**:
  - **Executable CLI Toggle Batches**: Generates ready-to-run `code --install-extension` / `--disable-extension` commands to reconcile workspace drift.
  - **`.code-workspace` `${env:VAR}` Interpolation**: Resolves local `.env` secrets/paths directly into workspace configs without committing machine-specific paths.
  - **Multi-Folder Monorepo Lock Merging**: Combines required/disabled extension lists across monorepo sub-packages.

## 4. Minimal Architecture & File Map
- `package.json` — VS Code extension manifest & Node ESM entry.
- `src/license_client.js` — Lemon Squeezy validator + 7-day offline grace cache.
- `src/profile_engine.js` — `.env` parser, workspace lock auditor, monorepo lock merger, `${env:VAR}` interpolator, and VS Code CLI batch generator.
- `src/index.js` — Main module wiring `activate`, `runWorkspaceAudit`, and Pro-gated `runProSync`.
- `tests/smoke_test.py` — Validates `package.json` and runs Node.js ESM tests covering Free audit, Pro gate, mocked Lemon Squeezy unlock, and `${env:VAR}` interpolation.

## 5. Verification Plan
1. Run `python3 projects/vscode-workspace-profile-config/tests/smoke_test.py` to test `.env` parsing, extension drift auditing, Free-tier gate enforcement, Lemon Squeezy activation, and Pro `.code-workspace` interpolation.
2. Run `python3 scripts/ship_check.py --slug vscode-workspace-profile-config --package` to verify zero placeholders, passing tests, and `dist/vscode-workspace-profile-config-v0.1.0.zip`.
