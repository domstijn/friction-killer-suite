/**
 * MV3 Service Worker & testable Webflow CMS Asset Migration orchestration logic.
 */

import { requireProFeature, verifyLicense } from "./license_client.js";
import { FREE_ITEM_CAP, migrateWebflowCmsCsv } from "./cms_migrator.js";

const DEFAULT_PRODUCT_ID = "prod_VfrqznkcHJDx1M,prod_VeW6IYwGyYJkPv";

export function createMemoryStore(initial = {}) {
  const mem = new Map(Object.entries(initial));
  return {
    get: async (k) => (mem.has(k) ? mem.get(k) : null),
    set: async (k, v) => {
      mem.set(k, v);
    },
  };
}

function getStore(customStore = null) {
  if (customStore) return customStore;
  if (typeof chrome !== "undefined" && chrome?.storage?.local) {
    return {
      get: (k) => new Promise((r) => chrome.storage.local.get([k], (res) => r(res[k] ?? null))),
      set: (k, v) => new Promise((r) => chrome.storage.local.set({ [k]: v }, r)),
    };
  }
  return createMemoryStore();
}

export async function handleMigrateCsv({
  csvText,
  targetBaseUrl = "/assets/cms",
  oldPathPrefix = "/blog",
  newPathPrefix = "/posts",
  rewriteRichText = false,
  generateRedirects = false,
  store = null,
} = {}) {
  const kv = getStore(store);
  const featureName =
    rewriteRichText || generateRedirects ? "pro_richtext_and_301" : "unlimited_csv_migration";
  const proCheck = await requireProFeature(featureName, kv);
  const isPro = Boolean(proCheck.allowed);

  const result = migrateWebflowCmsCsv(csvText, {
    isPro,
    targetBaseUrl,
    oldPathPrefix,
    newPathPrefix,
    rewriteRichText,
    generateRedirects,
  });

  if (!result.ok) {
    return {
      ...result,
      message: result.reason || result.error || "Migration failed",
    };
  }

  const truncNote =
    result.truncatedItems > 0
      ? ` (${result.truncatedItems} rows truncated at Free cap of ${FREE_ITEM_CAP})`
      : "";
  const richNote =
    result.skippedRichTextUrls > 0
      ? ` — ${result.skippedRichTextUrls} inline Rich-Text CDN URLs need Pro`
      : "";

  return {
    ...result,
    message: `Mapped ${result.assetsFound} Webflow CDN asset(s) across ${result.processedItems} item(s)${truncNote}${richNote}.`,
  };
}

if (typeof chrome !== "undefined" && chrome?.runtime?.onMessage) {
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === "MIGRATE_CSV") {
      handleMigrateCsv(msg).then(sendResponse);
      return true;
    }
    if (msg?.type === "ACTIVATE_LICENSE") {
      verifyLicense({
        key: msg.key,
        provider: "stripe",
        productId: msg.productId || DEFAULT_PRODUCT_ID,
      }).then(sendResponse);
      return true;
    }
    if (msg?.type === "GET_STATUS") {
      requireProFeature("unlimited_csv_migration").then(sendResponse);
      return true;
    }
    return false;
  });
}
