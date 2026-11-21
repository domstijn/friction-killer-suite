import { requireProFeature, verifyLicense } from "./license_client.js";

const DEFAULT_PRODUCT_ID = "prod_VfX0l5vMdU7VO6,prod_VeW6IYwGyYJkPv";

const previewEl = document.getElementById("context-preview");
const redactEl = document.getElementById("redact-pii");
const licenseKeyEl = document.getElementById("license-key");
const tierBadgeEl = document.getElementById("tier-badge");
const statusEl = document.getElementById("status");

function setStatus(msg) {
  statusEl.textContent = msg;
}

async function refreshTierBadge() {
  const pro = await requireProFeature("guest_mcp_pack");
  if (pro.allowed) {
    tierBadgeEl.textContent = "Pro Active";
    tierBadgeEl.classList.add("pro");
  } else {
    tierBadgeEl.textContent = "Free Tier (3/day)";
    tierBadgeEl.classList.remove("pro");
  }
}

function withActiveNotionPage(callback) {
  if (!chrome?.tabs?.query) return;
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    if (!tab?.id) return setStatus("No active Notion tab found.");
    chrome.tabs.sendMessage(tab.id, { type: "EXTRACT_GUEST_PAGE" }, (page) => {
      if (chrome.runtime.lastError || !page?.blocks) {
        setStatus("Open a Notion page you have guest access to.");
        return;
      }
      callback(page);
    });
  });
}

document.getElementById("extract-btn")?.addEventListener("click", () => {
  withActiveNotionPage((page) => {
    chrome.runtime.sendMessage(
      { type: "PACK_ACTIVE_PAGE", page, redactPii: Boolean(redactEl?.checked) },
      (res) => {
        if (res?.ok && res.markdown) previewEl.value = res.mcpContextJson || res.markdown;
        setStatus(res?.message || res?.error || "Done");
      }
    );
  });
});

document.getElementById("copy-btn")?.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(previewEl.value || "");
    setStatus("Copied context pack to clipboard.");
  } catch {
    setStatus("Select text and copy manually.");
  }
});

document.getElementById("queue-btn")?.addEventListener("click", () => {
  withActiveNotionPage((page) => {
    chrome.runtime.sendMessage({ type: "QUEUE_GUEST_PAGE", page }, (res) => {
      setStatus(res?.message || res?.error || "Done");
    });
  });
});

document.getElementById("export-btn")?.addEventListener("click", () => {
  chrome.runtime.sendMessage(
    { type: "EXPORT_QUEUE", redactPii: Boolean(redactEl?.checked), clear: false },
    (res) => {
      if (res?.ok && (res.mcpContextJson || res.markdown)) {
        previewEl.value = res.mcpContextJson || res.markdown;
      }
      setStatus(res?.message || res?.error || "Done");
    }
  );
});

document.getElementById("activate-btn")?.addEventListener("click", async () => {
  const key = licenseKeyEl.value.trim();
  setStatus("Validating Stripe Pro license...");
  const res = await verifyLicense({ key, provider: "stripe", productId: DEFAULT_PRODUCT_ID });
  await refreshTierBadge();
  setStatus(res.valid ? "Pro license activated!" : res.reason);
});

refreshTierBadge();
