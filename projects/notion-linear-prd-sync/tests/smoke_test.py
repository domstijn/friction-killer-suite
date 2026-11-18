import json
import subprocess
from pathlib import Path


def test_manifest_and_files():
    root = Path(__file__).resolve().parent.parent
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert manifest["name"] == "LinearBridge"
    assert "storage" in manifest["permissions"]
    assert "https://api.linear.app/*" in manifest["host_permissions"]
    assert "https://api.lemonsqueezy.com/*" in manifest["host_permissions"]
    for rel in (
        "src/license_client.js",
        "src/prd_parser.js",
        "src/linear_client.js",
        "src/content.js",
        "src/background.js",
        "src/popup.html",
        "src/popup.js",
    ):
        assert (root / rel).exists(), f"Missing {rel}"


def test_js_unit_and_workflow():
    root = Path(__file__).resolve().parent.parent
    node_script = """
import assert from "node:assert/strict";
import { parseNotionPrd, enforceTierLimits, formatStatusBadges } from "./src/prd_parser.js";
import { getTelemetry, verifyLicense } from "./src/license_client.js";
import { fetchLinearStatuses } from "./src/linear_client.js";
import { createMemoryStore, handlePushPrd, handleSyncStatuses } from "./src/background.js";

const samplePrd = `
# Mobile Billing V2
Streamline checkout and retries.

## API Layer
- [ ] Implement webhook signature guard
- [ ] Add idempotency keys [ENG-10]
- [x] Already shipped item

## Frontend
* [ ] Build retry banner
- [ ] Track conversion events
- [ ] Export CSV receipts
- [ ] Notify Slack on failures
- [ ] Add dark-mode receipt modal
`;

// 1. parseNotionPrd checks
const parsed = parseNotionPrd(samplePrd);
assert.equal(parsed.title, "Mobile Billing V2");
assert.deepEqual(parsed.sections, ["API Layer", "Frontend"]);
assert.equal(parsed.tasks.length, 8);
assert.equal(parsed.tasks[1].existingIssueKey, "ENG-10");
assert.equal(parsed.tasks[2].completed, true);

// 2. enforceTierLimits Free vs Pro checks
const freePlan = enforceTierLimits(parsed, { isPro: false, weeklyUsed: 0, freeWeeklyCap: 5 });
assert.equal(freePlan.allowed, true);
assert.equal(freePlan.createParentEpic, false);
assert.equal(freePlan.tasksToCreate.length, 5);
assert.equal(freePlan.truncatedCount, 1);

const proPlan = enforceTierLimits(parsed, { isPro: true, weeklyUsed: 5, freeWeeklyCap: 5 });
assert.equal(proPlan.allowed, true);
assert.equal(proPlan.createParentEpic, true);
assert.equal(proPlan.tasksToCreate.length, 6);

// 3. handlePushPrd end-to-end: Free cap on 6th push -> License activate -> Pro Parent + Sub-issues
let issueCounter = 100;
const capturedInputs = [];

const mockFetch = async (url, opts) => {
  if (url.includes("api.lemonsqueezy.com")) {
    const bodyStr = String(opts?.body || "");
    const valid = bodyStr.includes("PRO-KEY-VALID");
    return {
      ok: true,
      status: 200,
      json: async () => ({
        valid,
        error: valid ? null : "Invalid license key",
        meta: { product_id: "12345" },
        license_key: { expires_at: null },
      }),
    };
  }
  if (url.includes("api.linear.app/graphql")) {
    const payload = JSON.parse(opts.body);
    if (payload.query.includes("IssueCreate")) {
      capturedInputs.push(payload.variables.input);
      issueCounter += 1;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            issueCreate: {
              success: true,
              issue: {
                id: `uuid-${issueCounter}`,
                identifier: `ENG-${issueCounter}`,
                title: payload.variables.input.title,
                url: `https://linear.app/team/issue/ENG-${issueCounter}`,
              },
            },
          },
        }),
      };
    }
    if (payload.query.includes("IssuesByFilter")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          data: {
            issues: {
              nodes: [{ identifier: "ENG-101", state: { name: "In Progress" } }],
            },
          },
        }),
      };
    }
  }
  throw new Error(`Unexpected fetch URL: ${url}`);
};

const store = createMemoryStore();
const freeRes = await handlePushPrd({
  rawText: samplePrd,
  apiKey: "lin_api_test",
  teamId: "team-1",
  store,
  fetchImpl: mockFetch,
});
assert.equal(freeRes.ok, true);
assert.equal(freeRes.isPro, false);
assert.equal(freeRes.createdParent, null);
assert.equal(freeRes.createdIssues.length, 5);

const blockedRes = await handlePushPrd({
  rawText: "- [ ] Sixth issue blocked on free tier",
  apiKey: "lin_api_test",
  teamId: "team-1",
  store,
  fetchImpl: mockFetch,
});
assert.equal(blockedRes.ok, false);
assert.equal(blockedRes.blockedByTier, true);

// Activate valid Lemon Squeezy license
const lic = await verifyLicense({
  key: "PRO-KEY-VALID",
  provider: "lemonsqueezy",
  productId: "12345",
  store,
  fetchImpl: mockFetch,
});
assert.equal(lic.valid, true);
assert.equal(lic.tier, "pro");

capturedInputs.length = 0;
const proRes = await handlePushPrd({
  rawText: samplePrd,
  apiKey: "lin_api_test",
  teamId: "team-1",
  priority: 2,
  store,
  fetchImpl: mockFetch,
});
assert.equal(proRes.ok, true);
assert.equal(proRes.isPro, true);
assert.ok(proRes.createdParent?.id);
assert.equal(proRes.createdIssues.length, 6);
assert.equal(capturedInputs[0].title, "[PRD] Mobile Billing V2");
assert.equal(capturedInputs[1].parentId, proRes.createdParent.id);
assert.equal(capturedInputs[1].priority, 2);

// 4. formatStatusBadges + fetchLinearStatuses + handleSyncStatuses
const statuses = await fetchLinearStatuses({
  apiKey: "lin_api_test",
  issueKeys: ["ENG-101"],
  fetchImpl: mockFetch,
});
assert.equal(statuses["ENG-101"], "In Progress");

const badged = formatStatusBadges("- [ ] Ship billing [ENG-101]", statuses);
assert.equal(badged, "- [ ] Ship billing [ENG-101: In Progress]");

const syncRes = await handleSyncStatuses({
  rawText: "- [ ] Ship billing [ENG-101: Todo]",
  apiKey: "lin_api_test",
  store,
  fetchImpl: mockFetch,
});
assert.equal(syncRes.ok, true);
assert.equal(syncRes.updatedText, "- [ ] Ship billing [ENG-101: In Progress]");

// 5. Bundle productId array validation + zero-backend telemetry verification
const bundleStore = createMemoryStore();
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
const bundleLic = await verifyLicense({
  key: "BUNDLE-KEY-VALID",
  provider: "lemonsqueezy",
  productId: ["12345", "BUNDLE-999"],
  store: bundleStore,
  fetchImpl: bundleFetch,
});
assert.equal(bundleLic.valid, true);
assert.equal(bundleLic.tier, "pro");

const tel = await getTelemetry(store);
assert.ok(tel.paywall_hits >= 1);
assert.ok(tel.activation_attempts >= 1);
assert.equal(tel.pro_activations, 1);

console.log("OK: LinearBridge Node.js ESM tests passed");
"""
    subprocess.run(
        ["node", "--input-type=module", "-e", node_script],
        cwd=str(root),
        check=True,
    )


if __name__ == "__main__":
    test_manifest_and_files()
    test_js_unit_and_workflow()
    print("OK: LinearBridge smoke_test.py passed")
