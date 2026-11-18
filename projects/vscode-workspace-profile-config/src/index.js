/**
 * ExtProfileLock entrypoint: Free workspace audit + Pro Lemon Squeezy gated sync & interpolation.
 * Supports both programmatic activation and VS Code ExtensionContext command registration.
 */

import { getTelemetry, requireProFeature, verifyLicense } from "./license_client.js";
import {
  auditWorkspaceProfile,
  interpolateWorkspaceConfig,
  mergeLockConfigs,
  parseDotEnv,
} from "./profile_engine.js";

const DEFAULT_PRODUCT_ID = null;

export { getTelemetry };

export async function activateLicense(
  key,
  { productId = DEFAULT_PRODUCT_ID, store = null, fetchImpl } = {}
) {
  return verifyLicense({
    key,
    provider: "lemonsqueezy",
    productId,
    store,
    fetchImpl,
  });
}

export function runWorkspaceAudit({ lockConfig, installedExtensions = [], rawEnv = "" } = {}) {
  const merged = Array.isArray(lockConfig) ? mergeLockConfigs(lockConfig) : lockConfig;
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
  const proGate = await requireProFeature("monorepo_and_interpolation", store);
  const merged = Array.isArray(lockConfig) ? mergeLockConfigs(lockConfig) : lockConfig;
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

  const commandHandlers = {
    "extProfileLock.auditWorkspace": (args) => runWorkspaceAudit(args || {}),
    "extProfileLock.syncProWorkspace": (args) => runProSync(args || {}),
    "extProfileLock.activateLicense": async (args) => {
      if (typeof args === "string") return activateLicense(args);
      if (args?.key) return activateLicense(args.key, args);
      if (vscodeApi?.window?.showInputBox) {
        const key = await vscodeApi.window.showInputBox({ prompt: "Enter ExtProfileLock Pro license key" });
        if (key) return activateLicense(key);
      }
      return { valid: false, tier: "free", reason: "No license key provided" };
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
