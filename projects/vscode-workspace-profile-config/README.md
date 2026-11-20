# ExtProfileLock

**Enforce repo-level VS Code extension locks, interpolate `.env` variables into `.code-workspace` files, and eliminate profile drift across projects.**

Built for teams and developers tired of conflicting linters, formatters, and AI assistants across repositories ([microsoft/vscode#40239](https://github.com/microsoft/vscode/issues/40239)) and lack of `${env:VAR}` support inside `.code-workspace` configs ([microsoft/vscode#44755](https://github.com/microsoft/vscode/issues/44755)).

## Features

- **Workspace Extension Lock Auditing (`ExtProfileLock: Audit Workspace Profile`)**: Compare installed extensions against a repo-committed `.vscode/workspace-lock.json` file to spot missing required extensions and active conflicting extensions.
- **Local `.env` Parsing**: Parse `.env` variables cleanly (`export KEY="VALUE"`, comments, quotes) directly on your machine with zero network calls.
- **Pro CLI Toggle Batches & `${env:VAR}` Interpolation (`ExtProfileLock: Sync Pro Workspace & Interpolate Env`)**: Generate exact `code --install-extension` / `code --disable-extension` commands, merge multi-folder monorepo lock configs, and interpolate `${env:VAR}` placeholders into `.code-workspace` JSON.

## Example `.vscode/workspace-lock.json`

```json
{
  "required": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint"
  ],
  "disabled": [
    "ms-python.black-formatter",
    "tabnine.tabnine-vscode"
  ]
}
```

## Free vs. Pro

- **Free Starter Tier**: Single-root `.vscode/workspace-lock.json` extension drift audit and local `.env` parsing.
- **Pro Tier (€19 one-time or €49 All-Access Bundle)**: Automated `code --install-extension` / `--disable-extension` batch commands, `.code-workspace` `${env:VAR}` interpolation, and monorepo lockfile merging.

Test interactively in your browser or get a Pro license key at [https://domstijn.github.io/friction-killer-suite/products/vscode-workspace-profile-config/](https://domstijn.github.io/friction-killer-suite/products/vscode-workspace-profile-config/).
