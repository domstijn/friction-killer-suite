/**
 * MV3 Service Worker & testable PRD-to-Linear orchestration logic.
 */

import { requireProFeature, verifyLicense } from "./license_client.js";
import {
  enforceTierLimits,
  extractIssueKeys,
  formatStatusBadges,
  parseNotionPrd,
} from "./prd_parser.js";
import { fetchLinearStatuses, pushPrdToLinear } from "./linear_client.js";

const WEEKLY_USAGE_KEY = "lb_weekly_usage";
const SETTINGS_KEY = "lb_settings";
const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const FREE_WEEKLY_CAP = 5;

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

export async function getWeeklyUsage(store, now = Date.now()) {
  const kv = getStore(store);
  const record = await kv.get(WEEKLY_USAGE_KEY);
  if (!record || !record.weekStart || now - record.weekStart >= WEEK_MS) {
    return { weekStart: now, count: 0 };
  }
  return { weekStart: record.weekStart, count: Number(record.count || 0) };
}

async function incrementWeeklyUsage(store, delta, now = Date.now()) {
  if (delta <= 0) return;
  const kv = getStore(store);
  const current = await getWeeklyUsage(kv, now);
  await kv.set(WEEKLY_USAGE_KEY, {
    weekStart: current.weekStart,
    count: current.count + delta,
  });
}

/**
 * Execute full Notion PRD -> Tier Gate -> Linear GraphQL creation workflow.
 */
export async function handlePushPrd({
  rawText,
  pageTitle = "Untitled PRD",
  apiKey,
  teamId,
  priority = 0,
  store = null,
  fetchImpl = globalThis.fetch,
} = {}) {
  const kv = getStore(store);
  const parsedPrd = parseNotionPrd(rawText, { pageTitle });
  const proCheck = await requireProFeature("parent_epic_hierarchy", kv);
  const isPro = Boolean(proCheck.allowed);
  const usage = await getWeeklyUsage(kv);

  const tierPlan = enforceTierLimits(parsedPrd, {
    isPro,
    weeklyUsed: usage.count,
    freeWeeklyCap: FREE_WEEKLY_CAP,
  });

  if (!tierPlan.allowed) {
    return {
      ok: false,
      blockedByTier: true,
      isPro,
      tierPlan,
      createdParent: null,
      createdIssues: [],
      message: tierPlan.reason,
    };
  }

  if (tierPlan.tasksToCreate.length === 0) {
    return {
      ok: true,
      blockedByTier: false,
      isPro,
      tierPlan,
      createdParent: null,
      createdIssues: [],
      message: tierPlan.reason,
    };
  }

  const pushed = await pushPrdToLinear({
    apiKey,
    teamId,
    parsedPrd,
    tierPlan,
    priority,
    fetchImpl,
  });

  if (!isPro) {
    await incrementWeeklyUsage(kv, pushed.createdIssues.length);
  }

  const parentLabel = pushed.createdParent ? `${pushed.createdParent.identifier} + ` : "";
  return {
    ok: true,
    blockedByTier: false,
    isPro,
    tierPlan,
    createdParent: pushed.createdParent,
    createdIssues: pushed.createdIssues,
    message: `Created ${parentLabel}${pushed.createdIssues.length} Linear issue(s)`,
  };
}

/**
 * Sync live Linear status badges back onto PRD text (Pro feature).
 */
export async function handleSyncStatuses({
  rawText,
  apiKey,
  store = null,
  fetchImpl = globalThis.fetch,
} = {}) {
  const kv = getStore(store);
  const proCheck = await requireProFeature("status_badge_sync", kv);
  if (!proCheck.allowed) {
    return {
      ok: false,
      blockedByTier: true,
      message: "Status badge sync requires an active Pro license key.",
    };
  }
  const keys = extractIssueKeys(rawText);
  if (keys.length === 0) {
    return { ok: true, updatedText: rawText, statusByKey: {}, message: "No [KEY-123] tags found" };
  }
  const statusByKey = await fetchLinearStatuses({ apiKey, issueKeys: keys, fetchImpl });
  const updatedText = formatStatusBadges(rawText, statusByKey);
  return {
    ok: true,
    updatedText,
    statusByKey,
    message: `Synced ${Object.keys(statusByKey).length} issue status(es)`,
  };
}

if (typeof chrome !== "undefined" && chrome?.runtime?.onMessage) {
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    (async () => {
      const kv = getStore();
      const settings = (await kv.get(SETTINGS_KEY)) || {};
      if (msg?.type === "PUSH_PRD") {
        return await handlePushPrd({
          rawText: msg.rawText,
          pageTitle: msg.pageTitle,
          apiKey: msg.apiKey || settings.apiKey,
          teamId: msg.teamId || settings.teamId,
          priority: Number(msg.priority ?? settings.priority ?? 0),
          store: kv,
        });
      }
      if (msg?.type === "SYNC_STATUS") {
        return await handleSyncStatuses({
          rawText: msg.rawText,
          apiKey: msg.apiKey || settings.apiKey,
          store: kv,
        });
      }
      if (msg?.type === "ACTIVATE_LICENSE") {
        const res = await verifyLicense({
          key: msg.key,
          provider: "lemonsqueezy",
          productId: msg.productId || settings.productId || null,
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
