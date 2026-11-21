import json
import subprocess
from pathlib import Path


def test_manifest_and_files():
    root = Path(__file__).resolve().parent.parent
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert manifest["name"] == "NotionGuestBridge"
    assert "storage" in manifest["permissions"]
    assert "scripting" not in manifest["permissions"]
    assert "https://www.notion.so/*" in manifest["host_permissions"]
    for rel in (
        "src/icon128.png",
        "src/license_client.js",
        "src/guest_extractor.js",
        "src/content.js",
        "src/background.js",
        "src/popup.html",
        "src/popup.js",
    ):
        assert (root / rel).exists(), f"Missing {rel}"


def test_js_guest_extractor_and_stripe_gate():
    root = Path(__file__).resolve().parent.parent
    node_script = """
import assert from "node:assert/strict";
import { buildGuestContextPack, redactClientPii } from "./src/guest_extractor.js";
import { getTelemetry, verifyLicense } from "./src/license_client.js";
import { createMemoryStore, handleExportQueue, handlePackPage, handleQueuePage } from "./src/background.js";

const samplePage = {
  title: "Client API Onboarding (Guest View)",
  url: "https://www.notion.so/acme/Client-API-Onboarding",
  blocks: [
    { type: "heading", level: 2, text: "Endpoints" },
    { type: "todo", checked: false, text: "Connect staging key lin_api_SecretToken123 for jane@client.co" },
    { type: "callout", text: "Guest accounts cannot authorize official OAuth MCP." },
    { type: "code", lang: "bash", text: "curl -H 'Authorization: Bearer mySecretToken99999' https://api.client.co" },
  ],
  tables: [
    {
      title: "Service Matrix",
      headers: ["Service", "Owner Email", "Env"],
      rows: [["Billing API", "ops@client.co", "Prod"]],
    },
  ],
};

// 1. Free tier works up to 3 pages/day and enforces PII + queue gates
const store = createMemoryStore();
for (let i = 0; i < 3; i++) {
  const res = await handlePackPage({ page: samplePage, store, now: 1700000000000 });
  assert.equal(res.ok, true);
  assert.equal(res.isPro, false);
  assert.equal(res.tablesIncluded, 0);
  assert.equal(res.mcpContextJson, null);
  assert.ok(res.markdown.includes("Client API Onboarding"));
}

const capBlocked = await handlePackPage({ page: samplePage, store, now: 1700000000000 });
assert.equal(capBlocked.ok, false);
assert.equal(capBlocked.blockedByTier, true);

const piiBlocked = await handlePackPage({ page: samplePage, redactPii: true, store, now: 1700000000000 });
assert.equal(piiBlocked.blockedByTier, true);

const qBlocked = await handleQueuePage({ page: samplePage, store });
assert.equal(qBlocked.blockedByTier, true);

// 2. Activate Pro via mocked Stripe /verify-license (individual + bundle productId)
const mockFetch = async (_url, opts) => {
  const body = JSON.parse(opts.body);
  const valid = body.license_key === "cs_live_ValidGuestBridgeKey12345678";
  return {
    ok: true,
    status: 200,
    json: async () => ({ valid, product_id: "prod_VeW6IYwGyYJkPv" }),
  };
};
const lic = await verifyLicense({
  key: "cs_live_ValidGuestBridgeKey12345678",
  provider: "stripe",
  productId: ["prod_GUEST", "prod_VeW6IYwGyYJkPv"],
  store,
  fetchImpl: mockFetch,
});
assert.equal(lic.valid, true);
assert.equal(lic.tier, "pro");

// 3. Pro unlocks multi-page queue, PII redaction, tables, and .mcp-context.json bundle
assert.equal(redactClientPii("Email jane@client.co key lin_api_AbCdEfGhIjKl"), "Email [EMAIL_REDACTED] key [SECRET_REDACTED]");
await handleQueuePage({ page: samplePage, store });
await handleQueuePage({
  page: { title: "Release Checklist", url: "https://www.notion.so/acme/Checklist", blocks: [{ type: "paragraph", text: "Verify webhook" }], tables: [] },
  store,
});
const exported = await handleExportQueue({ redactPii: true, store });
assert.equal(exported.ok, true);
assert.equal(exported.pageCount, 2);
assert.equal(exported.redactedPii, true);
assert.equal(exported.tablesIncluded, 1);
assert.ok(!exported.markdown.includes("jane@client.co"));
assert.ok(!exported.markdown.includes("ops@client.co"));
assert.ok(!exported.markdown.includes("lin_api_SecretToken123"));
assert.ok(exported.mcpContextJson.includes("mcp.guest.context/v1"));

// 4. Block-cap truncation check on Free tier
const manyBlocks = Array.from({ length: 50 }, (_, i) => ({ type: "paragraph", text: `Line ${i}` }));
const trunc = buildGuestContextPack([{ title: "Long", blocks: manyBlocks, tables: [] }], { isPro: false });
assert.equal(trunc.ok, true);
assert.equal(trunc.truncatedBlocks, 10);

const tel = await getTelemetry(store);
assert.ok(tel.paywall_hits >= 1);
assert.equal(tel.pro_activations, 1);

console.log("OK: NotionGuestBridge Node.js ESM tests passed");
"""
    subprocess.run(["node", "--input-type=module", "-e", node_script], cwd=str(root), check=True)


if __name__ == "__main__":
    test_manifest_and_files()
    test_js_guest_extractor_and_stripe_gate()
    print("OK: NotionGuestBridge smoke_test.py passed")
