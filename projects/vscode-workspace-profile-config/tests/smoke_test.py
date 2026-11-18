import json
import subprocess
from pathlib import Path


def test_plugin_structure():
    root = Path(__file__).resolve().parent.parent
    pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
    assert pkg["main"] == "./src/index.js"
    assert pkg.get("engines", {}).get("vscode")
    assert len(pkg.get("contributes", {}).get("commands", [])) >= 3
    assert (root / "src" / "license_client.js").exists()
    assert (root / "src" / "profile_engine.js").exists()


def test_js_profile_engine_and_pro_gate():
    root = Path(__file__).resolve().parent.parent
    node_script = """
import assert from "node:assert/strict";
import { parseDotEnv, auditWorkspaceProfile, mergeLockConfigs } from "./src/profile_engine.js";
import { activate, deactivate, getTelemetry, runWorkspaceAudit, runProSync } from "./src/index.js";

const mem = new Map();
const store = {
  get: async (k) => (mem.has(k) ? mem.get(k) : null),
  set: async (k, v) => { mem.set(k, v); },
};

const rawEnv = `
# Local developer overrides
export SDK_ROOT="/Users/dev/sdk"
API_ENDPOINT="https://staging.internal"
`;
const parsedEnv = parseDotEnv(rawEnv);
assert.equal(parsedEnv.SDK_ROOT, "/Users/dev/sdk");
assert.equal(parsedEnv.API_ENDPOINT, "https://staging.internal");

const lockConfig = {
  required: ["esbenp.prettier-vscode", "dbaeumer.vscode-eslint"],
  disabled: ["ms-python.black-formatter", "tabnine.tabnine-vscode"],
};
const installed = ["dbaeumer.vscode-eslint", "tabnine.tabnine-vscode"];

// 1. Free audit works without license
const auditRes = runWorkspaceAudit({ lockConfig, installedExtensions: installed, rawEnv });
assert.equal(auditRes.ok, true);
assert.deepEqual(auditRes.audit.toInstall, ["esbenp.prettier-vscode"]);
assert.deepEqual(auditRes.audit.toDisable, ["tabnine.tabnine-vscode"]);
assert.equal(auditRes.audit.compliant, false);
assert.equal(auditRes.envKeysCount, 2);

const workspaceTemplate = JSON.stringify({
  folders: [{ path: "${env:SDK_ROOT}/core" }],
  settings: { "myExt.endpoint": "${env:API_ENDPOINT}" },
});

// 2. Pro sync blocked when unlicensed
const blocked = await runProSync({
  lockConfig,
  installedExtensions: installed,
  rawEnv,
  rawWorkspaceJson: workspaceTemplate,
  store,
});
assert.equal(blocked.ok, false);
assert.equal(blocked.blockedByTier, true);

// 3. Activate valid mocked Lemon Squeezy license
const mockFetch = async (_url, opts) => {
  const valid = String(opts?.body || "").includes("EXT-PRO-123");
  return {
    ok: true,
    status: 200,
    json: async () => ({
      valid,
      error: valid ? null : "Invalid",
      meta: { product_id: "999" },
      license_key: { expires_at: null },
    }),
  };
};

const lic = await activate("EXT-PRO-123", { productId: "999", store, fetchImpl: mockFetch });
assert.equal(lic.valid, true);
assert.equal(lic.tier, "pro");

// 4. Pro sync unlocks ${env:VAR} interpolation, monorepo merge, and CLI batch generation
const merged = mergeLockConfigs([lockConfig, { required: ["golang.go"], disabled: ["esbenp.prettier-vscode"] }]);
assert.ok(merged.required.includes("esbenp.prettier-vscode"));
assert.ok(!merged.disabled.includes("esbenp.prettier-vscode"));

const proRes = await runProSync({
  lockConfig,
  installedExtensions: installed,
  rawEnv,
  rawWorkspaceJson: workspaceTemplate,
  store,
});
assert.equal(proRes.ok, true);
assert.equal(proRes.parsedWorkspace.folders[0].path, "/Users/dev/sdk/core");
assert.equal(proRes.parsedWorkspace.settings["myExt.endpoint"], "https://staging.internal");
assert.deepEqual(proRes.cliCommands, [
  "code --install-extension esbenp.prettier-vscode",
  "code --disable-extension tabnine.tabnine-vscode",
]);

// 5. VS Code ExtensionContext command registration + bundle productId + telemetry
const mockContext = { subscriptions: [] };
const registeredIds = [];
const mockVscode = {
  commands: {
    registerCommand: (id, fn) => {
      registeredIds.push(id);
      return { command: id, fn, dispose() {} };
    },
  },
};
await activate(mockContext, mockVscode);
assert.equal(mockContext.subscriptions.length, 3);
assert.deepEqual(registeredIds, [
  "extProfileLock.auditWorkspace",
  "extProfileLock.syncProWorkspace",
  "extProfileLock.activateLicense",
]);
deactivate();

const bundleStore = {
  _m: new Map(),
  get: async function (k) { return this._m.has(k) ? this._m.get(k) : null; },
  set: async function (k, v) { this._m.set(k, v); },
};
const bundleFetch = async () => ({
  ok: true,
  status: 200,
  json: async () => ({
    valid: true,
    error: null,
    meta: { product_id: "BUNDLE-999" },
    license_key: { expires_at: null },
  }),
});
const bundleLic = await activate("BUNDLE-EXT-KEY", {
  productId: ["999", "BUNDLE-999"],
  store: bundleStore,
  fetchImpl: bundleFetch,
});
assert.equal(bundleLic.valid, true);

const tel = await getTelemetry(store);
assert.ok(tel.paywall_hits >= 1);
assert.ok(tel.activation_attempts >= 1);
assert.equal(tel.pro_activations, 1);

console.log("OK: ExtProfileLock Node.js ESM tests passed");
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        cwd=str(root),
        check=True,
    )


if __name__ == "__main__":
    test_plugin_structure()
    test_js_profile_engine_and_pro_gate()
    print("OK: ExtProfileLock smoke_test.py passed")
