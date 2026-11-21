"use strict";

let modulePromise = null;

function loadEsm() {
  if (!modulePromise) {
    modulePromise = import("./index.js");
  }
  return modulePromise;
}

exports.activate = async function activate(context) {
  let vscodeApi = null;
  try {
    vscodeApi = require("vscode");
  } catch {
    vscodeApi = globalThis.__EXT_PROFILE_LOCK_VSCODE__ || null;
  }
  const mod = await loadEsm();
  return await mod.activate(context, vscodeApi);
};

exports.deactivate = async function deactivate() {
  const mod = await loadEsm();
  if (typeof mod.deactivate === "function") {
    return await mod.deactivate();
  }
};
