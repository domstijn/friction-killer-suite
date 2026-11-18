/**
 * Zero-backend & Stripe Managed Payments license key validator (Stripe, Lemon Squeezy, Polar.sh, Gumroad).
 * Works in Browser / WebExtensions (Chrome MV3) and Node.js 18+ ESM environments.
 */

const DEFAULT_GRACE_MS = 7 * 24 * 60 * 60 * 1000;
const CACHE_KEY = "fk_license_state";
const TELEMETRY_KEY = "fk_telemetry";
const DEFAULT_TELEMETRY = { paywall_hits: 0, activation_attempts: 0, pro_activations: 0 };

function normalizeProductIds(productId) {
  if (!productId) return [];
  if (Array.isArray(productId)) {
    return productId.map((x) => String(x).trim()).filter(Boolean);
  }
  return String(productId)
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

const PROVIDERS = {
  lemonsqueezy: {
    url: "https://api.lemonsqueezy.com/v1/licenses/validate",
    buildRequest: ({ key, instanceName }) => ({
      headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
      body: new URLSearchParams({
        license_key: key,
        ...(instanceName ? { instance_name: instanceName } : {}),
      }).toString(),
    }),
    parseResponse: (data, productId) => {
      const valid = Boolean(data?.valid);
      const allowedIds = normalizeProductIds(productId);
      const pidMatch =
        allowedIds.length === 0 || allowedIds.includes(String(data?.meta?.product_id ?? "").trim());
      return {
        valid: valid && pidMatch,
        reason: !valid ? data?.error || "Invalid license key" : pidMatch ? "ok" : "Product mismatch",
        expiresAt: data?.license_key?.expires_at || null,
      };
    },
  },
  polar: {
    url: "https://api.polar.sh/v1/customer-portal/license-keys/validate",
    buildRequest: ({ key, productId }) => {
      const firstPid = normalizeProductIds(productId)[0];
      return {
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          key,
          ...(firstPid ? { organization_id: firstPid } : {}),
        }),
      };
    },
    parseResponse: (data) => {
      const active = data?.status === "granted";
      return {
        valid: active,
        reason: active ? "ok" : data?.detail || `Status: ${data?.status || "invalid"}`,
        expiresAt: data?.expires_at || null,
      };
    },
  },
  gumroad: {
    url: "https://api.gumroad.com/v2/licenses/verify",
    buildRequest: ({ key, productId }) => {
      const firstPid = normalizeProductIds(productId)[0];
      return {
        headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
        body: new URLSearchParams({
          license_key: key,
          ...(firstPid ? { product_id: firstPid } : {}),
        }).toString(),
      };
    },
    parseResponse: (data) => {
      const purchase = data?.purchase || {};
      const valid = Boolean(data?.success) && !purchase.refunded && !purchase.chargebacked;
      return {
        valid,
        reason: valid ? "ok" : data?.message || "Invalid or refunded license key",
        expiresAt: purchase.subscription_ended_at || null,
      };
    },
  },
  stripe: {
    url: () => globalThis.STRIPE_LICENSE_VERIFY_URL || "http://localhost:4242/verify-license",
    buildRequest: ({ key, productId, instanceName }) => ({
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        license_key: key,
        product_id: productId,
        instance_name: instanceName,
      }),
    }),
    parseResponse: (data, productId) => {
      const valid = Boolean(data?.valid) || data?.payment_status === "paid";
      const allowedIds = normalizeProductIds(productId);
      const returnedId = String(
        data?.product_id || data?.metadata?.product_id || data?.metadata?.slug || ""
      ).trim();
      const pidMatch = allowedIds.length === 0 || (Boolean(returnedId) && allowedIds.includes(returnedId));
      return {
        valid: valid && pidMatch,
        reason: !valid
          ? data?.error || data?.reason || "Invalid Stripe session key"
          : pidMatch
            ? "ok"
            : "Product mismatch",
        expiresAt: data?.expires_at || null,
      };
    },
  },
};

function resolveStore(customStore) {
  if (customStore) return customStore;
  if (typeof chrome !== "undefined" && chrome?.storage?.local) {
    return {
      get: (k) => new Promise((r) => chrome.storage.local.get([k], (res) => r(res[k] ?? null))),
      set: (k, v) => new Promise((r) => chrome.storage.local.set({ [k]: v }, r)),
    };
  }
  if (typeof localStorage !== "undefined") {
    return {
      get: async (k) => {
        const raw = localStorage.getItem(k);
        return raw ? JSON.parse(raw) : null;
      },
      set: async (k, v) => localStorage.setItem(k, JSON.stringify(v)),
    };
  }
  const mem = new Map();
  return {
    get: async (k) => mem.get(k) ?? null,
    set: async (k, v) => {
      mem.set(k, v);
    },
  };
}

function isWithinGrace(record, graceMs = DEFAULT_GRACE_MS) {
  if (!record?.valid || !record?.checkedAt) return false;
  if (record.expiresAt && Date.now() > Date.parse(record.expiresAt)) return false;
  return Date.now() - record.checkedAt <= graceMs;
}

async function recordTelemetry(kv, field) {
  try {
    const prev = (await kv.get(TELEMETRY_KEY)) || {};
    const next = {
      paywall_hits: Number(prev.paywall_hits || 0),
      activation_attempts: Number(prev.activation_attempts || 0),
      pro_activations: Number(prev.pro_activations || 0),
    };
    next[field] = (next[field] || 0) + 1;
    await kv.set(TELEMETRY_KEY, next);
  } catch {
    // Best-effort local telemetry
  }
}

/**
 * Return local zero-backend funnel telemetry counters.
 */
export async function getTelemetry(cacheStore = null) {
  const kv = resolveStore(cacheStore);
  const stored = (await kv.get(TELEMETRY_KEY)) || {};
  return {
    paywall_hits: Number(stored.paywall_hits ?? DEFAULT_TELEMETRY.paywall_hits),
    activation_attempts: Number(stored.activation_attempts ?? DEFAULT_TELEMETRY.activation_attempts),
    pro_activations: Number(stored.pro_activations ?? DEFAULT_TELEMETRY.pro_activations),
  };
}

/**
 * Verify a license key directly with the payment provider's public API
 * and persist the validation state with an offline grace window.
 */
export async function verifyLicense({
  key,
  provider = "lemonsqueezy",
  productId = null,
  instanceName = "default",
  store = null,
  fetchImpl = globalThis.fetch,
} = {}) {
  const cleanKey = String(key || "").trim();
  const effectiveProvider =
    cleanKey.startsWith("cs_test_") || cleanKey.startsWith("cs_live_") ? "stripe" : provider;
  const adapter = PROVIDERS[effectiveProvider];
  if (!cleanKey) return { valid: false, tier: "free", reason: "Empty license key", cached: false };
  if (!adapter) return { valid: false, tier: "free", reason: `Unsupported provider: ${effectiveProvider}`, cached: false };

  const kv = resolveStore(store);
  await recordTelemetry(kv, "activation_attempts");
  try {
    const req = adapter.buildRequest({ key: cleanKey, productId, instanceName });
    const endpointUrl = typeof adapter.url === "function" ? adapter.url() : adapter.url;
    const res = await fetchImpl(endpointUrl, { method: "POST", headers: req.headers, body: req.body });
    const data = await res.json().catch(() => ({}));
    const parsed = adapter.parseResponse(data, productId);
    if (parsed.valid) {
      await recordTelemetry(kv, "pro_activations");
    }
    const state = {
      valid: parsed.valid,
      tier: parsed.valid ? "pro" : "free",
      provider: effectiveProvider,
      reason: parsed.reason,
      expiresAt: parsed.expiresAt,
      checkedAt: Date.now(),
      keyHint: cleanKey.slice(-4),
    };
    await kv.set(CACHE_KEY, state);
    return { ...state, cached: false };
  } catch (err) {
    const cached = await kv.get(CACHE_KEY);
    if (isWithinGrace(cached)) {
      return { ...cached, cached: true, reason: "Verified from offline grace cache" };
    }
    return { valid: false, tier: "free", reason: `Network error: ${err.message}`, cached: false };
  }
}

/**
 * Gate a Pro feature using the cached license record.
 */
export async function requireProFeature(featureName, cacheStore = null, graceMs = DEFAULT_GRACE_MS) {
  const kv = resolveStore(cacheStore);
  const record = await kv.get(CACHE_KEY);
  if (isWithinGrace(record, graceMs)) {
    return { allowed: true, tier: "pro", feature: featureName, reason: "ok" };
  }
  await recordTelemetry(kv, "paywall_hits");
  return {
    allowed: false,
    tier: "free",
    feature: featureName,
    reason: record ? "License expired or re-validation required" : "Pro license required",
  };
}
