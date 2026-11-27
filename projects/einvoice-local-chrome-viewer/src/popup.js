document.getElementById("open-viewer-btn")?.addEventListener("click", () => {
  const url = chrome.runtime.getURL("src/viewer.html");
  chrome.tabs.create({ url });
});
