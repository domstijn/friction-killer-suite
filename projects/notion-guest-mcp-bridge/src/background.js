/**
 * MV3 Service Worker & testable Notion Guest Context Pack orchestration logic.
 */

import { requireProFeature, verifyLicense } from "./license_client.js";
import { buildGuestContextPack, FREE_DAILY_CAP } from "./guest_extractor.js";

const DAILY_USAGE_KEY = "ngb_daily_usage";
const QUEUE_KEY = "ngb_page_queue";
const SETTINGS_KEY = "ngb_settings";
const DAY_MS = 24 * 60 * 60 * 1000;
const DEFAULT_PRODUCT_ID = "prod_VfX0l5vMdU7VO6,prod_VeW6IYwGyYJkPv";

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

export async function getDailyUsage(store, now = Date.now()) {
  const kv = getStore(store);
  const record = await kv.get(DAILY_USAGE_KEY);
  if (!record || !record.dayStart || now - record.dayStart >= DAY_MS) {
    return { dayStart: now, count: 0 };
  }
  return { dayStart: record.dayStart, count: Number(record.count || 0) };
}

async function incrementDailyUsage(store, delta = 1, now = Date.now()) {
  if (delta <= 0) return;
  const kv = getStore(store);
  const cur = await getDailyUsage(kv, now);
  await kv.set(DAILY_USAGE_KEY, { dayStart: cur.dayStart, count: cur.count + delta });
}

export async function handlePackPage({ page, redactPii = false, store = null, now = Date.now() } = {}) {
  const kv = getStore(store);
  const proCheck = await requireProFeature("guest_mcp_pack", kv);
  const isPro = Boolean(proCheck.allowed);
  const usage = await getDailyUsage(kv, now);

  const pack = buildGuestContextPack([page], {
    isPro,
    dailyUsed: usage.count,
    freeDailyCap: FREE_DAILY_CAP,
    redactPii,
  });

  if (!pack.ok) {
    return { ...pack, message: pack.reason };
  }

  if (!isPro) {
    await incrementDailyUsage(kv, 1, now);
  }

  return {
    ...pack,
    message: `Packed '${page?.title || "Notion page"}' (${isPro ? "Pro MCP Pack" : "Free Markdown"})`,
  };
}

export async function handleQueuePage({ page, store = null } = {}) {
  const kv = getStore(store);
  const proCheck = await requireProFeature("multi_page_queue", kv);
  if (!proCheck.allowed) {
    return {
      ok: false,
      blockedByTier: true,
      message: "Multi-page guest queue requires an active Pro license key.",
    };
  }
  const existing = (await kv.get(QUEUE_KEY)) || [];
  const filtered = existing.filter((p) => p?.url !== page?.url || p?.title !== page?.title);
  filtered.push(page);
  await kv.set(QUEUE_KEY, filtered);
  return {
    ok: true,
    queuedCount: filtered.length,
    message: `Queued '${page?.title || "Page"}' (${filtered.length} page(s) in bundle)`,
  };
}

export async function handleExportQueue({ redactPii = true, clear = false, store = null } = {}) {
  const kv = getStore(store);
  const proCheck = await requireProFeature("multi_page_queue", kv);
  if (!proCheck.allowed) {
    return {
      ok: false,
      blockedByTier: true,
      message: "Exporting queued .mcp-context.json bundles requires an active Pro license key.",
    };
  }
  const queue = (await kv.get(QUEUE_KEY)) || [];
  const pack = buildGuestContextPack(queue, { isPro: true, redactPii });
  if (pack.ok && clear) {
    await kv.set(QUEUE_KEY, []);
  }
  return {
    ...pack,
    message: pack.ok ? `Exported ${pack.pageCount} queued page(s)` : pack.reason,
  };
}

if (typeof chrome !== "undefined" && chrome?.runtime?.onMessage) {
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    (async () => {
      const kv = getStore();
      const settings = (await kv.get(SETTINGS_KEY)) || {};
      if (msg?.type === "PACK_ACTIVE_PAGE") {
        return await handlePackPage({
          page: msg.page,
          redactPii: Boolean(msg.redactPii ?? settings.redactPii),
          store: kv,
        });
      }
      if (msg?.type === "QUEUE_GUEST_PAGE") {
        return await handleQueuePage({ page: msg.page, store: kv });
      }
      if (msg?.type === "EXPORT_QUEUE") {
        return await handleExportQueue({
          redactPii: Boolean(msg.redactPii ?? settings.redactPii),
          clear: Boolean(msg.clear),
          store: kv,
        });
      }
      if (msg?.type === "ACTIVATE_LICENSE") {
        const res = await verifyLicense({
          key: msg.key,
          provider: "stripe",
          productId: msg.productId || DEFAULT_PRODUCT_ID,
          store: kv,
        });
        return { ok: res.valid, ...res };
      }
      return { ok: false, error: "Unknown message type" };
    })()
      .then(sendResponse)
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true;
  });
}
