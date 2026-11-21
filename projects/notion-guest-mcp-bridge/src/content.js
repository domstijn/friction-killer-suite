/**
 * Lightweight Notion DOM extractor and floating NotionGuestBridge toolbar.
 */

(() => {
  if (typeof document === "undefined" || document.getElementById("notionguestbridge-bar")) return;

  function cleanText(el) {
    return (el?.innerText || el?.textContent || "").replace(/\s+/g, " ").trim();
  }

  function extractTablesFromDom() {
    const tables = [];
    const domTables = document.querySelectorAll("table, [role='table']");
    domTables.forEach((tbl, idx) => {
      const headers = Array.from(tbl.querySelectorAll("th, [role='columnheader']"))
        .map(cleanText)
        .filter(Boolean);
      const rows = [];
      tbl.querySelectorAll("tbody tr, [role='row']").forEach((tr) => {
        const cells = Array.from(tr.querySelectorAll("td, [role='cell'], [role='gridcell']"))
          .map(cleanText);
        if (cells.length > 0 && cells.some(Boolean)) {
          rows.push(cells);
        }
      });
      if (headers.length > 0 || rows.length > 0) {
        tables.push({
          title: `Database Table ${idx + 1}`,
          headers: headers.length > 0 ? headers : rows[0].map((_, i) => `Col ${i + 1}`),
          rows,
        });
      }
    });
    return tables;
  }

  function extractGuestPageFromDom() {
    const titleEl = document.querySelector(".notion-page-block h1") || document.querySelector("h1");
    const pageTitle =
      cleanText(titleEl) ||
      document.title.replace(/\s*\|\s*Notion$/, "").trim() ||
      "Untitled Client Page";

    const blocks = [];
    const blockEls = document.querySelectorAll("[data-block-id]");

    for (const block of blockEls) {
      const heading = block.querySelector("h1, h2, h3, [role='heading']");
      if (heading && heading.closest("[data-block-id]") === block) {
        const tag = heading.tagName.toLowerCase();
        let level = tag === "h3" ? 3 : 2;
        if (block.classList.contains("notion-sub_sub_header-block")) level = 3;
        const text = cleanText(heading);
        if (text && text !== pageTitle) blocks.push({ type: "heading", level, text });
        continue;
      }

      const checkbox = block.querySelector('input[type="checkbox"], [role="checkbox"]');
      if (checkbox && checkbox.closest("[data-block-id]") === block) {
        const text = cleanText(block);
        if (text) {
          const checked = checkbox.matches('input[type="checkbox"]')
            ? Boolean(checkbox.checked)
            : checkbox.getAttribute("aria-checked") === "true";
          blocks.push({ type: "todo", checked, text });
        }
        continue;
      }

      if (block.classList.contains("notion-callout-block")) {
        const text = cleanText(block);
        if (text) blocks.push({ type: "callout", text });
        continue;
      }

      if (block.classList.contains("notion-code-block")) {
        const text = (block.querySelector("pre, code")?.textContent || cleanText(block)).trim();
        if (text) blocks.push({ type: "code", text });
        continue;
      }

      if (!block.querySelector("[data-block-id]")) {
        const text = cleanText(block);
        if (text && text !== pageTitle) blocks.push({ type: "paragraph", text });
      }
    }

    return {
      title: pageTitle,
      url: typeof location !== "undefined" ? location.href : "",
      blocks,
      tables: extractTablesFromDom(),
    };
  }

  function makeBtn(label, primary = false) {
    const btn = document.createElement("button");
    btn.textContent = label;
    btn.style.cssText = [
      "border:none",
      "border-radius:6px",
      "padding:6px 10px",
      "font-size:12px",
      "font-weight:600",
      "cursor:pointer",
      primary
        ? "background:#4f46e5;color:#fff;"
        : "background:#1e293b;color:#e2e8f0;border:1px solid #334155;",
    ].join(";");
    return btn;
  }

  const bar = document.createElement("div");
  bar.id = "notionguestbridge-bar";
  bar.setAttribute("data-fk-bar", "notion-guest-mcp-bridge");
  bar.style.cssText = [
    "position:fixed",
    "right:20px",
    "bottom:20px",
    "z-index:99999",
    "display:flex",
    "align-items:center",
    "gap:8px",
    "padding:8px 10px",
    "border-radius:10px",
    "background:#0f172a",
    "border:1px solid #334155",
    "box-shadow:0 10px 25px rgba(0,0,0,0.35)",
    "font-family:-apple-system,BlinkMacSystemFont,sans-serif",
  ].join(";");

  const packBtn = makeBtn("Pack Guest Page", true);
  const queueBtn = makeBtn("+ Queue Page (Pro)", false);
  const statusEl = document.createElement("span");
  statusEl.style.cssText = "font-size:11px;color:#94a3b8;max-width:210px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";

  function sendAction(type) {
    if (typeof chrome === "undefined" || !chrome?.runtime?.sendMessage) return;
    const page = extractGuestPageFromDom();
    statusEl.textContent = "Extracting...";
    chrome.runtime.sendMessage({ type, page }, async (res) => {
      if (chrome.runtime.lastError) {
        statusEl.textContent = chrome.runtime.lastError.message;
        return;
      }
      if (res?.ok && res?.markdown) {
        try {
          await navigator.clipboard?.writeText(res.markdown);
        } catch {}
      }
      statusEl.textContent = res?.message || (res?.ok ? "Copied context pack!" : res?.error || "Failed");
    });
  }

  packBtn.addEventListener("click", () => sendAction("PACK_ACTIVE_PAGE"));
  queueBtn.addEventListener("click", () => sendAction("QUEUE_GUEST_PAGE"));

  bar.append(packBtn, queueBtn, statusEl);
  document.body.appendChild(bar);

  if (typeof chrome !== "undefined" && chrome?.runtime?.onMessage) {
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
      if (msg?.type === "EXTRACT_GUEST_PAGE") {
        sendResponse(extractGuestPageFromDom());
      }
    });
  }
})();
