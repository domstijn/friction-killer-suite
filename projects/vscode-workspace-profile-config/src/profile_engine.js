/**
 * Core VS Code workspace lock auditor, .env parser, and Pro .code-workspace interpolator.
 */

const ENV_PLACEHOLDER_RE = /\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}/g;

/**
 * Parse .env file contents into a key-value map.
 */
export function parseDotEnv(rawEnv = "") {
  const result = {};
  for (const rawLine of String(rawEnv).split(/\r?\n/)) {
    let line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    if (line.startsWith("export ")) line = line.slice(7).trim();
    const eqIdx = line.indexOf("=");
    if (eqIdx <= 0) continue;
    const key = line.slice(0, eqIdx).trim();
    let val = line.slice(eqIdx + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    result[key] = val;
  }
  return result;
}

/**
 * Merge multiple monorepo workspace-lock configs cleanly.
 */
export function mergeLockConfigs(configs = []) {
  const required = new Set();
  const disabled = new Set();
  for (const cfg of configs) {
    for (const ext of cfg?.required || []) required.add(String(ext).trim());
    for (const ext of cfg?.disabled || []) disabled.add(String(ext).trim());
  }
  for (const ext of required) {
    disabled.delete(ext);
  }
  return { required: [...required], disabled: [...disabled] };
}

/**
 * Audit installed VS Code extensions against a workspace-lock.json spec.
 */
export function auditWorkspaceProfile(lockConfig = {}, installedExtensions = []) {
  const installedSet = new Set(installedExtensions.map((e) => String(e).trim().toLowerCase()));
  const required = (lockConfig.required || []).map((e) => String(e).trim()).filter(Boolean);
  const disabled = (lockConfig.disabled || []).map((e) => String(e).trim()).filter(Boolean);

  const toInstall = required.filter((ext) => !installedSet.has(ext.toLowerCase()));
  const toDisable = disabled.filter((ext) => installedSet.has(ext.toLowerCase()));

  return {
    toInstall,
    toDisable,
    compliant: toInstall.length === 0 && toDisable.length === 0,
  };
}

/**
 * Build deterministic VS Code CLI commands from an audit result.
 */
export function buildCliCommands(auditResult = {}) {
  const commands = [];
  for (const ext of auditResult.toInstall || []) {
    commands.push(`code --install-extension ${ext}`);
  }
  for (const ext of auditResult.toDisable || []) {
    commands.push(`code --disable-extension ${ext}`);
  }
  return commands;
}

/**
 * Interpolate ${env:VAR} inside .code-workspace JSON and generate CLI batches (Pro feature).
 */
export function interpolateWorkspaceConfig(
  rawWorkspaceJson,
  envMap = {},
  { isPro = false, auditResult = null } = {}
) {
  if (!isPro) {
    return {
      ok: false,
      blockedByTier: true,
      reason:
        "Pro license required for .code-workspace ${env:VAR} interpolation and CLI batch generation.",
    };
  }

  const missingVars = [];
  const workspaceJson = String(rawWorkspaceJson || "{}").replace(
    ENV_PLACEHOLDER_RE,
    (full, varName) => {
      if (Object.prototype.hasOwnProperty.call(envMap, varName)) {
        return String(envMap[varName]).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
      }
      if (!missingVars.includes(varName)) missingVars.push(varName);
      return full;
    }
  );

  let parsedWorkspace = null;
  try {
    parsedWorkspace = JSON.parse(workspaceJson);
  } catch {
    parsedWorkspace = null;
  }

  return {
    ok: true,
    blockedByTier: false,
    workspaceJson,
    parsedWorkspace,
    missingVars,
    cliCommands: buildCliCommands(auditResult || {}),
  };
}
