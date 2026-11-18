/**
 * Lightweight Notion DOM extractor and floating LinearBridge toolbar.
 */

(() => {
  if (typeof document === "undefined" || document.getElementById("linearbridge-bar")) return;

  function extractNotionPrdMarkdown() {
    const titleEl =
      document.querySelector(".notion-page-block h1") ||
      document.querySelector("h1");
    const pageTitle = titleEl?.innerText?.trim() || document.title.replace(/\s*\|\s*Notion$/, "").trim() || "Untitled PRD";

    const lines = [`# ${pageTitle}`];
    const blocks = document.querySelectorAll("[data-block-id]");

    for (const block of blocks) {
      const heading = block.querySelector("h1, h2, h3");
      if (heading) {
        const tag = heading.tagName.toLowerCase();
        const prefix = tag === "h1" ? "#" : tag === "h2" ? "##" : "###";
        const text = heading.innerText.trim();
        if (text && text !== pageTitle) lines.push(`${prefix} ${text}`);
        continue;
      }

      const checkbox = block.querySelector('input[type="checkbox"]');
      if (checkbox) {
        const text = block.innerText.replace(/\s+/g, " ").trim();
        if (text) {
          lines.push(`- [${checkbox.checked ? "x" : " "}] ${text}`);
        }
      }
    }

    return { pageTitle, rawText: lines.join("\n") };
  }

  function createButton(label, primary = false) {
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
  bar.id = "linearbridge-bar";
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

  const pushBtn = createButton("Push PRD to Linear", true);
  const syncBtn = createButton("Sync Statuses", false);
  const statusEl = document.createElement("span");
  statusEl.style.cssText = "font-size:11px;color:#94a3b8;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";

  function sendAction(type) {
    if (typeof chrome === "undefined" || !chrome?.runtime?.sendMessage) return;
    const { pageTitle, rawText } = extractNotionPrdMarkdown();
    statusEl.textContent = "Working...";
    chrome.runtime.sendMessage({ type, pageTitle, rawText }, (res) => {
      if (chrome.runtime.lastError) {
        statusEl.textContent = chrome.runtime.lastError.message;
        return;
      }
      statusEl.textContent = res?.message || (res?.ok ? "Done" : res?.error || "Failed");
    });
  }

  pushBtn.addEventListener("click", () => sendAction("PUSH_PRD"));
  syncBtn.addEventListener("click", () => sendAction("SYNC_STATUS"));

  bar.append(pushBtn, syncBtn, statusEl);
  document.body.appendChild(bar);

  if (typeof chrome !== "undefined" && chrome?.runtime?.onMessage) {
    chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
      if (msg?.type === "EXTRACT_PRD") {
        sendResponse(extractNotionPrdMarkdown());
      }
    });
  }
})();
