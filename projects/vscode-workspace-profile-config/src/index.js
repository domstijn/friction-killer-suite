/**
 * ExtProfileLock entrypoint: Free workspace audit + Pro Stripe gated sync & interpolation.
 * Supports both programmatic calls and zero-argument VS Code Command Palette invocations.
 */

import fs from "node:fs";
import path from "node:path";
import { getTelemetry, requireProFeature, verifyLicense } from "./license_client.js";
import {
  auditWorkspaceProfile,
  interpolateWorkspaceConfig,
  mergeLockConfigs,
  parseDotEnv,
} from "./profile_engine.js";

const DEFAULT_PRODUCT_ID = "prod_VeW60IB88zFfQl,prod_VeW6IYwGyYJkPv";
const FALLBACK_MEM = new Map();

export { getTelemetry };

function makePersistentStore(context = null) {
  if (context?.globalState?.get && context?.globalState?.update) {
    return {
      get: async (k) => context.globalState.get(k) ?? null,
      set: async (k, v) => {
        await context.globalState.update(k, v);
      },
    };
  }
  return {
    get: async (k) => (FALLBACK_MEM.has(k) ? FALLBACK_MEM.get(k) : null),
    set: async (k, v) => {
      FALLBACK_MEM.set(k, v);
    },
  };
}

function readWorkspaceInputs(vscodeApi) {
  const folderUri = vscodeApi?.workspace?.workspaceFolders?.[0]?.uri;
  const workspaceRoot = folderUri?.fsPath || process.cwd();

  const lockPath = path.join(workspaceRoot, ".vscode", "workspace-lock.json");
  let lockConfig = { required: [], disabled: [] };
  let hasLockFile = false;
  if (fs.existsSync(lockPath)) {
    hasLockFile = true;
    lockConfig = JSON.parse(fs.readFileSync(lockPath, "utf8"));
  }

  const envPath = path.join(workspaceRoot, ".env");
  const rawEnv = fs.existsSync(envPath) ? fs.readFileSync(envPath, "utf8") : "";

  let workspaceFilePath = null;
  let rawWorkspaceJson = "{}";
  if (fs.existsSync(workspaceRoot)) {
    const wsFile = fs
      .readdirSync(workspaceRoot)
      .find((f) => f.endsWith(".code-workspace") && !f.startsWith("extprofilelock."));
    if (wsFile) {
      workspaceFilePath = path.join(workspaceRoot, wsFile);
      rawWorkspaceJson = fs.readFileSync(workspaceFilePath, "utf8");
    }
  }

  const installedExtensions = Array.isArray(vscodeApi?.extensions?.all)
    ? vscodeApi.extensions.all
        .map((ext) => ext?.id)
        .filter((id) => typeof id === "string" && id && !id.startsWith("vscode."))
    : [];

  return {
    workspaceRoot,
    hasLockFile,
    lockConfig,
    rawEnv,
    workspaceFilePath,
    rawWorkspaceJson,
    installedExtensions,
  };
}

export async function activateLicense(
  key,
  { productId = DEFAULT_PRODUCT_ID, store = null, fetchImpl } = {}
) {
  return verifyLicense({
    key,
    provider: "stripe",
    productId,
    store: store || makePersistentStore(null),
    fetchImpl,
  });
}

export function runWorkspaceAudit({ lockConfig, installedExtensions = [], rawEnv = "" } = {}) {
  const merged = Array.isArray(lockConfig) ? mergeLockConfigs(lockConfig) : lockConfig || {};
  const audit = auditWorkspaceProfile(merged, installedExtensions);
  const envMap = parseDotEnv(rawEnv);
  return {
    ok: true,
    audit,
    envKeysCount: Object.keys(envMap).length,
  };
}

export async function runProSync({
  lockConfig,
  installedExtensions = [],
  rawEnv = "",
  rawWorkspaceJson = "{}",
  store = null,
} = {}) {
  const effectiveStore = store || makePersistentStore(null);
  const proGate = await requireProFeature("monorepo_and_interpolation", effectiveStore);
  const merged = Array.isArray(lockConfig) ? mergeLockConfigs(lockConfig) : lockConfig || {};
  const audit = auditWorkspaceProfile(merged, installedExtensions);
  const envMap = parseDotEnv(rawEnv);

  const interpolated = interpolateWorkspaceConfig(rawWorkspaceJson, envMap, {
    isPro: Boolean(proGate.allowed),
    auditResult: audit,
  });

  if (!interpolated.ok) {
    return {
      ...interpolated,
      audit,
    };
  }

  return {
    ...interpolated,
    audit,
    envMap,
  };
}

export async function activate(contextOrKey, optionsOrVscodeApi = null) {
  if (typeof contextOrKey === "string" || contextOrKey == null) {
    return activateLicense(contextOrKey, optionsOrVscodeApi || {});
  }

  const context = contextOrKey;
  let vscodeApi = optionsOrVscodeApi;
  if (!vscodeApi) {
    try {
      vscodeApi = await import("vscode");
    } catch {
      vscodeApi = null;
    }
  }

  const persistentStore = makePersistentStore(context);

  const commandHandlers = {
    "extProfileLock.auditWorkspace": async (args) => {
      const ws = args?.lockConfig ? null : readWorkspaceInputs(vscodeApi);
      const inputs = args?.lockConfig
        ? args
        : {
            lockConfig: ws.lockConfig,
            installedExtensions: ws.installedExtensions,
            rawEnv: ws.rawEnv,
          };
      const res = runWorkspaceAudit(inputs);
      if (ws && !ws.hasLockFile) {
        vscodeApi?.window?.showWarningMessage?.(
          `ExtProfileLock: No .vscode/workspace-lock.json found in ${ws.workspaceRoot}. Parsed ${res.envKeysCount} .env var(s).`
        );
      } else if (res.audit.compliant) {
        vscodeApi?.window?.showInformationMessage?.(
          `ExtProfileLock: Workspace compliant (${res.envKeysCount} .env var(s) loaded).`
        );
      } else {
        vscodeApi?.window?.showWarningMessage?.(
          `ExtProfileLock drift: install ${res.audit.toInstall.length}, disable ${res.audit.toDisable.length} extension(s).`
        );
      }
      return res;
    },
    "extProfileLock.syncProWorkspace": async (args) => {
      const ws = args?.lockConfig ? null : readWorkspaceInputs(vscodeApi);
      const inputs = args?.lockConfig
        ? { store: persistentStore, ...args }
        : {
            lockConfig: ws.lockConfig,
            installedExtensions: ws.installedExtensions,
            rawEnv: ws.rawEnv,
            rawWorkspaceJson: ws.rawWorkspaceJson,
            store: persistentStore,
          };
      const res = await runProSync(inputs);
      if (!res.ok) {
        vscodeApi?.window?.showWarningMessage?.(
          `ExtProfileLock Pro required: ${res.reason || "Activate a Pro key via ExtProfileLock: Activate Pro License."}`
        );
        return res;
      }
      if (ws) {
        const vscodeDir = path.join(ws.workspaceRoot, ".vscode");
        fs.mkdirSync(vscodeDir, { recursive: true });
        if (ws.workspaceFilePath && res.interpolatedJson) {
          fs.writeFileSync(
            path.join(vscodeDir, "extprofilelock.interpolated.code-workspace"),
            res.interpolatedJson,
            "utf8"
          );
        }
        if (res.cliCommands?.length) {
          fs.writeFileSync(
            path.join(vscodeDir, "extprofilelock-reconcile.sh"),
            "#!/usr/bin/env bash\n" + res.cliCommands.join("\n") + "\n",
            "utf8"
          );
        }
      }
      vscodeApi?.window?.showInformationMessage?.(
        `ExtProfileLock Pro synced: ${res.interpolatedKeys?.length || 0} env var(s) resolved, ${res.cliCommands?.length || 0} CLI command(s).`
      );
      return res;
    },
    "extProfileLock.activateLicense": async (args) => {
      let key = typeof args === "string" ? args : args?.key || null;
      if (!key && vscodeApi?.window?.showInputBox) {
        key = await vscodeApi.window.showInputBox({
          prompt: "Enter ExtProfileLock Stripe Pro license key (cs_live_...)",
        });
      }
      if (!key) {
        const fail = { valid: false, tier: "free", reason: "No license key provided" };
        vscodeApi?.window?.showWarningMessage?.(`ExtProfileLock: ${fail.reason}`);
        return fail;
      }
      const res = await activateLicense(key, {
        ...(typeof args === "object" && args ? args : {}),
        store: (typeof args === "object" && args?.store) || persistentStore,
      });
      if (res.valid) {
        vscodeApi?.window?.showInformationMessage?.("ExtProfileLock: Pro license activated!");
      } else {
        vscodeApi?.window?.showErrorMessage?.(`ExtProfileLock: ${res.reason || "Invalid license key"}`);
      }
      return res;
    },
  };

  const register =
    typeof vscodeApi?.commands?.registerCommand === "function"
      ? (id, fn) => vscodeApi.commands.registerCommand(id, fn)
      : (id, fn) => ({ command: id, handler: fn, dispose() {} });

  const disposables = Object.entries(commandHandlers).map(([id, fn]) => register(id, fn));
  if (Array.isArray(context?.subscriptions)) {
    context.subscriptions.push(...disposables);
  }
  return { registeredCommands: Object.keys(commandHandlers), disposables };
}

export function deactivate() {}
