import json
import subprocess
from pathlib import Path


def test_manifest_and_files():
    root = Path(__file__).resolve().parent.parent
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert manifest["name"] == "WebflowAssetZip"
    assert "storage" in manifest["permissions"]
    assert "scripting" not in manifest["permissions"]
    assert "https://*.webflow.com/*" in manifest["host_permissions"]
    for rel in (
        "src/icon128.png",
        "src/license_client.js",
        "src/cms_migrator.js",
        "src/content.js",
        "src/background.js",
        "src/popup.html",
        "src/popup.js",
    ):
        assert (root / rel).exists(), f"Missing {rel}"


def test_js_cms_migrator_and_stripe_gate():
    root = Path(__file__).resolve().parent.parent
    node_script = """
import assert from "node:assert/strict";
import { FREE_ITEM_CAP, migrateWebflowCmsCsv } from "./src/cms_migrator.js";
import { getTelemetry, verifyLicense } from "./src/license_client.js";
import { createMemoryStore, handleMigrateCsv } from "./src/background.js";

const header = "Name,Slug,Hero Image,Post Body";
const rows = Array.from({ length: 20 }, (_, i) => {
  const n = i + 1;
  const body = `"<p>Launch post ${n}</p><img src=\\"https://uploads-ssl.webflow.com/abc123/inline_${n}.png\\">"`;
  return `Post ${n},post-${n},https://cdn.prod.website-files.com/abc123/hero_${n}.webp,${body}`;
});
const sampleCsv = [header, ...rows].join("\\n");

// 1. Free tier maps direct media URLs up to 15 items and blocks Rich-Text + 301s
const store = createMemoryStore();
const freeRes = await handleMigrateCsv({
  csvText: sampleCsv,
  targetBaseUrl: "https://assets.acme.co/cms/",
  store,
});
assert.equal(freeRes.ok, true);
assert.equal(freeRes.isPro, false);
assert.equal(freeRes.totalItems, 20);
assert.equal(freeRes.processedItems, FREE_ITEM_CAP);
assert.equal(freeRes.truncatedItems, 5);
assert.equal(freeRes.assetsFound, 15);
assert.equal(freeRes.skippedRichTextUrls, 15);
assert.ok(freeRes.rewrittenCsv.includes("https://assets.acme.co/cms/post-1-hero-image-01.webp"));
assert.ok(freeRes.rewrittenCsv.includes("https://uploads-ssl.webflow.com/abc123/inline_1.png"));

const proBlocked = await handleMigrateCsv({
  csvText: sampleCsv,
  rewriteRichText: true,
  generateRedirects: true,
  store,
});
assert.equal(proBlocked.ok, false);
assert.equal(proBlocked.blockedByTier, true);

// 2. Activate Pro via mocked Stripe /verify-license (individual + bundle productId)
const mockFetch = async (_url, opts) => {
  const body = JSON.parse(opts.body);
  const valid = body.license_key === "cs_live_ValidWebflowAssetKey1234";
  return {
    ok: true,
    status: 200,
    json: async () => ({ valid, product_id: "prod_VeW6IYwGyYJkPv" }),
  };
};
const lic = await verifyLicense({
  key: "cs_live_ValidWebflowAssetKey1234",
  provider: "stripe",
  productId: ["prod_WEBFLOW", "prod_VeW6IYwGyYJkPv"],
  store,
  fetchImpl: mockFetch,
});
assert.equal(lic.valid, true);
assert.equal(lic.tier, "pro");

// 3. Pro unlocks all 20 items, inline Rich-Text <img> CDN rewriting, and 301-redirects.csv
const proRes = await handleMigrateCsv({
  csvText: sampleCsv,
  targetBaseUrl: "https://assets.acme.co/cms",
  oldPathPrefix: "/blog",
  newPathPrefix: "/posts",
  rewriteRichText: true,
  generateRedirects: true,
  store,
});
assert.equal(proRes.ok, true);
assert.equal(proRes.isPro, true);
assert.equal(proRes.processedItems, 20);
assert.equal(proRes.truncatedItems, 0);
assert.equal(proRes.assetsFound, 40);
assert.equal(proRes.skippedRichTextUrls, 0);
assert.ok(proRes.rewrittenCsv.includes("https://assets.acme.co/cms/post-20-post-body-01.png"));
assert.ok(!proRes.rewrittenCsv.includes("uploads-ssl.webflow.com"));
assert.ok(!proRes.rewrittenCsv.includes("cdn.prod.website-files.com"));
assert.ok(proRes.redirectsCsv.includes("/blog/post-1,/posts/post-1,301"));
assert.ok(proRes.redirectsCsv.includes("/blog/post-20,/posts/post-20,301"));

const tel = await getTelemetry(store);
assert.ok(tel.paywall_hits >= 1);
assert.equal(tel.pro_activations, 1);

console.log("OK: WebflowAssetZip Node.js ESM tests passed");
"""
    subprocess.run(["node", "--input-type=module", "-e", node_script], cwd=str(root), check=True)


if __name__ == "__main__":
    test_manifest_and_files()
    test_js_cms_migrator_and_stripe_gate()
    print("OK: WebflowAssetZip smoke_test.py passed")
