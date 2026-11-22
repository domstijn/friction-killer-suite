/**
 * Lightweight Webflow CMS DOM extractor & floating WebflowAssetZip toolbar.
 */

(() => {
  if (typeof document === "undefined" || document.getElementById("webflowassetzip-bar")) return;

  function cleanText(el) {
    return (el?.innerText || el?.textContent || "").replace(/\s+/g, " ").trim();
  }

  function csvEscape(val) {
    const s = String(val ?? "");
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }

  function extractWebflowDomToCsv() {
    const rows = [["Name", "Slug", "Hero Image", "Body"]];
    const items = document.querySelectorAll(
      '[data-automation-id*="cms-item"], .wf-cms-item, .w-dyn-item, table tbody tr'
    );

    if (items.length > 0) {
      items.forEach((item, idx) => {
        const nameEl = item.querySelector("h1, h2, h3, a, td");
        const name = cleanText(nameEl) || `CMS Item ${idx + 1}`;
        const slug = name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-+|-+$/g, "") || `item-${idx + 1}`;
        const img = item.querySelector("img");
        const heroUrl = img?.getAttribute("src") || "";
        const body = item.innerHTML ? item.innerHTML.replace(/\s+/g, " ").trim() : "";
        rows.push([name, slug, heroUrl, body]);
      });
    } else {
      const imgs = Array.from(document.querySelectorAll("img"))
        .map((img) => img.getAttribute("src") || "")
        .filter((u) => /webflow\.com|website-files\.com/i.test(u));
      const title = cleanText(document.querySelector("h1")) || document.title || "Webflow Page";
      const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "page-1";
      if (imgs.length > 0) {
        rows.push([title, slug, imgs[0], document.body?.innerHTML?.slice(0, 1200) || ""]);
      } else {
        rows.push([title, slug, "", ""]);
      }
    }

    return rows.map((r) => r.map(csvEscape).join(",")).join("\n");
  }

  const bar = document.createElement("div");
  bar.id = "webflowassetzip-bar";
  bar.setAttribute("data-fk-bar", "webflow-cms-asset-migrator");
  bar.style.cssText = [
    "position:fixed",
    "right:20px",
    "bottom:20px",
    "z-index:2147483647",
    "display:flex",
    "align-items:center",
    "gap:8px",
    "padding:8px 12px",
    "border-radius:10px",
    "background:#0f172a",
    "color:#f8fafc",
    "border:1px solid #334155",
    "box-shadow:0 10px 30px rgba(0,0,0,0.35)",
    "font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif",
    "font-size:12px",
  ].join(";");

  const label = document.createElement("span");
  label.textContent = "WebflowAssetZip";
  label.style.fontWeight = "700";

  const scanBtn = document.createElement("button");
  scanBtn.textContent = "Scan CMS Assets";
  scanBtn.style.cssText =
    "border:none;border-radius:6px;padding:6px 10px;font-size:12px;font-weight:600;cursor:pointer;background:#4f46e5;color:#fff;";

  const statusSpan = document.createElement("span");
  statusSpan.style.color = "#94a3b8";

  scanBtn.addEventListener("click", () => {
    const csvText = extractWebflowDomToCsv();
    if (typeof chrome !== "undefined" && chrome?.runtime?.sendMessage) {
      chrome.runtime.sendMessage(
        { type: "MIGRATE_CSV", csvText, targetBaseUrl: "/assets/cms" },
        (res) => {
          statusSpan.textContent = res?.message || "Scanned — open popup";
        }
      );
    } else {
      statusSpan.textContent = `Extracted ${csvText.split("\n").length - 1} item(s)`;
    }
  });

  bar.append(label, scanBtn, statusSpan);
  (document.body || document.documentElement).appendChild(bar);

  if (typeof chrome !== "undefined" && chrome?.runtime?.onMessage) {
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
      if (msg?.type === "EXTRACT_WEBFLOW_CMS") {
        sendResponse({ csvText: extractWebflowDomToCsv() });
      }
    });
  }
})();
