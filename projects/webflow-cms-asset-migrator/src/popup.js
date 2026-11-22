import { requireProFeature, verifyLicense } from "./license_client.js";

const DEFAULT_PRODUCT_ID = "prod_VfrqznkcHJDx1M,prod_VeW6IYwGyYJkPv";

const csvFileEl = document.getElementById("csv-file");
const csvInputEl = document.getElementById("csv-input");
const targetBaseEl = document.getElementById("target-base");
const oldPrefixEl = document.getElementById("old-prefix");
const newPrefixEl = document.getElementById("new-prefix");
const rewriteRichEl = document.getElementById("rewrite-richtext");
const redirectsEl = document.getElementById("generate-redirects");
const outputEl = document.getElementById("output-preview");
const tierBadgeEl = document.getElementById("tier-badge");
const licenseKeyEl = document.getElementById("license-key");
const statusEl = document.getElementById("status");

let lastResult = null;

function setStatus(msg) {
  statusEl.textContent = msg;
}

async function refreshTierBadge() {
  const pro = await requireProFeature("unlimited_csv_migration");
  if (pro.allowed) {
    tierBadgeEl.textContent = "Pro Active";
    tierBadgeEl.classList.add("pro");
  } else {
    tierBadgeEl.textContent = "Free Tier (15 rows)";
    tierBadgeEl.classList.remove("pro");
  }
}

csvFileEl?.addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  csvInputEl.value = await file.text();
  setStatus(`Loaded ${file.name}`);
});

document.getElementById("scan-tab-btn")?.addEventListener("click", () => {
  if (!chrome?.tabs?.query) return;
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    if (!tab?.id) return setStatus("No active Webflow tab found.");
    chrome.tabs.sendMessage(tab.id, { type: "EXTRACT_WEBFLOW_CMS" }, (res) => {
      if (chrome.runtime.lastError || !res?.csvText) {
        setStatus("Open a Webflow CMS page or upload your exported CSV.");
        return;
      }
      csvInputEl.value = res.csvText;
      setStatus("Extracted CMS table from active Webflow tab.");
    });
  });
});

document.getElementById("migrate-btn")?.addEventListener("click", () => {
  chrome.runtime.sendMessage(
    {
      type: "MIGRATE_CSV",
      csvText: csvInputEl.value,
      targetBaseUrl: targetBaseEl.value,
      oldPathPrefix: oldPrefixEl.value,
      newPathPrefix: newPrefixEl.value,
      rewriteRichText: Boolean(rewriteRichEl?.checked),
      generateRedirects: Boolean(redirectsEl?.checked),
    },
    (res) => {
      lastResult = res;
      if (res?.ok) {
        outputEl.value = res.rewrittenCsv;
      }
      setStatus(res?.message || res?.error || "Done");
    }
  );
});

document.getElementById("copy-csv-btn")?.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(lastResult?.rewrittenCsv || outputEl.value || "");
    setStatus("Copied rewritten CSV.");
  } catch {
    setStatus("Copy manually from the preview box.");
  }
});

document.getElementById("copy-extra-btn")?.addEventListener("click", async () => {
  const parts = [];
  if (lastResult?.assetManifest) {
    parts.push("// Asset Manifest\n" + JSON.stringify(lastResult.assetManifest, null, 2));
  }
  if (lastResult?.redirectsCsv) {
    parts.push("// 301-redirects.csv\n" + lastResult.redirectsCsv);
  }
  const combined = parts.join("\n\n");
  if (!combined) return setStatus("Run migration first.");
  outputEl.value = combined;
  try {
    await navigator.clipboard.writeText(combined);
    setStatus("Copied asset manifest & 301 redirects.");
  } catch {
    setStatus("Manifest shown in preview box.");
  }
});

document.getElementById("activate-btn")?.addEventListener("click", async () => {
  const key = licenseKeyEl.value.trim();
  setStatus("Validating Stripe Pro license...");
  const res = await verifyLicense({ key, provider: "stripe", productId: DEFAULT_PRODUCT_ID });
  await refreshTierBadge();
  setStatus(res.valid ? "Pro license activated!" : res.reason);
});

refreshTierBadge();
