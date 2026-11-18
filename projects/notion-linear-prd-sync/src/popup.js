import { requireProFeature, verifyLicense } from "./license_client.js";

const SETTINGS_KEY = "lb_settings";

const storage = {
  get: (k) =>
    typeof chrome !== "undefined" && chrome?.storage?.local
      ? new Promise((r) => chrome.storage.local.get([k], (res) => r(res[k] ?? null)))
      : Promise.resolve(null),
  set: (k, v) =>
    typeof chrome !== "undefined" && chrome?.storage?.local
      ? new Promise((r) => chrome.storage.local.set({ [k]: v }, r))
      : Promise.resolve(),
};

const apiKeyEl = document.getElementById("api-key");
const teamIdEl = document.getElementById("team-id");
const priorityEl = document.getElementById("priority");
const prdTextEl = document.getElementById("prd-text");
const licenseKeyEl = document.getElementById("license-key");
const tierBadgeEl = document.getElementById("tier-badge");
const statusEl = document.getElementById("status");

function setStatus(msg) {
  statusEl.textContent = msg;
}

async function refreshTierBadge() {
  const pro = await requireProFeature("parent_epic_hierarchy");
  if (pro.allowed) {
    tierBadgeEl.textContent = "Pro Active";
    tierBadgeEl.classList.add("pro");
  } else {
    tierBadgeEl.textContent = "Free Tier (5/wk)";
    tierBadgeEl.classList.remove("pro");
  }
}

async function loadInitial() {
  const saved = (await storage.get(SETTINGS_KEY)) || {};
  if (saved.apiKey) apiKeyEl.value = saved.apiKey;
  if (saved.teamId) teamIdEl.value = saved.teamId;
  if (saved.priority !== undefined) priorityEl.value = String(saved.priority);
  await refreshTierBadge();
}

async function saveSettings() {
  const payload = {
    apiKey: apiKeyEl.value.trim(),
    teamId: teamIdEl.value.trim(),
    priority: Number(priorityEl.value || 0),
  };
  await storage.set(SETTINGS_KEY, payload);
  setStatus("Settings saved locally.");
  return payload;
}

document.getElementById("save-btn")?.addEventListener("click", saveSettings);

document.getElementById("grab-btn")?.addEventListener("click", async () => {
  if (!chrome?.tabs?.query) return;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return setStatus("No active Notion tab found.");
  chrome.tabs.sendMessage(tab.id, { type: "EXTRACT_PRD" }, (res) => {
    if (chrome.runtime.lastError || !res?.rawText) {
      setStatus("Open a Notion page to grab its PRD.");
      return;
    }
    prdTextEl.value = res.rawText;
    setStatus(`Grabbed PRD: ${res.pageTitle}`);
  });
});

document.getElementById("push-btn")?.addEventListener("click", async () => {
  const settings = await saveSettings();
  const rawText = prdTextEl.value.trim();
  if (!rawText) return setStatus("Paste or grab a Notion PRD first.");
  setStatus("Pushing to Linear...");
  chrome.runtime.sendMessage(
    { type: "PUSH_PRD", rawText, ...settings },
    (res) => setStatus(res?.message || res?.error || "Done")
  );
});

document.getElementById("sync-btn")?.addEventListener("click", async () => {
  const settings = await saveSettings();
  const rawText = prdTextEl.value.trim();
  if (!rawText) return setStatus("Paste or grab a Notion PRD first.");
  setStatus("Syncing statuses...");
  chrome.runtime.sendMessage(
    { type: "SYNC_STATUS", rawText, apiKey: settings.apiKey },
    (res) => {
      if (res?.ok && res.updatedText) prdTextEl.value = res.updatedText;
      setStatus(res?.message || res?.error || "Done");
    }
  );
});

document.getElementById("activate-btn")?.addEventListener("click", async () => {
  const key = licenseKeyEl.value.trim();
  setStatus("Validating Lemon Squeezy license...");
  const res = await verifyLicense({ key, provider: "lemonsqueezy" });
  await refreshTierBadge();
  setStatus(res.valid ? "Pro license activated!" : res.reason);
});

loadInitial();
