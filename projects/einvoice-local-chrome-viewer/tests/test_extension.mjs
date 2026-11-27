import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";

const require = createRequire(import.meta.url);
const EXT_DIR = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SRC_CORE = path.resolve(EXT_DIR, "..", "e-invoice-xml-batch-converter", "src", "einvoice_core.js");
const EXT_CORE = path.join(EXT_DIR, "src", "einvoice_core.js");

// 1. Validate identical core parser bytes
assert.equal(
  fs.readFileSync(EXT_CORE, "utf8"),
  fs.readFileSync(SRC_CORE, "utf8"),
  "Extension einvoice_core.js drifted from canonical engine!"
);

// 2. Validate MV3 manifest.json strict store hygiene
const manifest = JSON.parse(fs.readFileSync(path.join(EXT_DIR, "manifest.json"), "utf8"));
assert.equal(manifest.manifest_version, 3);
assert.deepEqual(manifest.permissions, [], "Companion viewer extension must request 0 permissions");
assert.deepEqual(manifest.host_permissions, [], "Companion viewer extension must request 0 host_permissions");

for (const rel of [
  manifest.action.default_popup,
  ...Object.values(manifest.action.default_icon),
  ...Object.values(manifest.icons),
  "src/viewer.html",
  "src/viewer.js",
  "src/popup.js",
  "src/styles.css",
  "src/einvoice_core.js",
]) {
  assert.ok(fs.existsSync(path.join(EXT_DIR, rel)), `Missing referenced extension file: ${rel}`);
}

for (const htmlFile of ["src/popup.html", "src/viewer.html"]) {
  const html = fs.readFileSync(path.join(EXT_DIR, htmlFile), "utf8");
  assert.ok(!/cdn\.tailwindcss\.com/i.test(html), `CDN reference found in ${htmlFile}`);
  assert.ok(!/<script>(?![\s]*$)/i.test(html), `Inline <script> not allowed under MV3 CSP in ${htmlFile}`);
}

// 3. Verify einvoice_core.js via Python ElementTree-backed mock DOMParser
const CORE = require(EXT_CORE);

class PyDOMParser {
  parseFromString(xmlStr) {
    const py = `
import json, sys, xml.etree.ElementTree as ET
raw = sys.stdin.read().lstrip("\\ufeff").strip()
root = ET.fromstring(raw)
def to_d(el):
    loc = el.tag.rsplit("}", 1)[-1]
    return {"localName": loc, "tagName": loc, "attrib": dict(el.attrib), "text": "".join(el.itertext()).strip(), "children": [to_d(c) for c in list(el)]}
print(json.dumps(to_d(root)))
`;
    let jsonOut;
    try {
      jsonOut = execFileSync("python3", ["-c", py], { input: String(xmlStr), encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });
    } catch {
      const errNode = { localName: "parsererror", tagName: "parsererror", textContent: "XMLSyntaxError", children: [], getAttribute: () => null, getElementsByTagName: () => [] };
      return { documentElement: errNode, getElementsByTagName: () => [errNode] };
    }
    const wrap = (o) => ({
      localName: o.localName,
      tagName: o.tagName,
      textContent: o.text,
      children: o.children.map(wrap),
      getAttribute: (k) => (k in o.attrib ? o.attrib[k] : null),
      getElementsByTagName: () => [],
    });
    const root = wrap(JSON.parse(jsonOut));
    return { documentElement: root, getElementsByTagName: () => [] };
  }
}

const xrechnungXml = fs.readFileSync(
  path.resolve(EXT_DIR, "..", "..", "docs", "samples", "files", "sample-xrechnung-3.0-ubl.xml"),
  "utf8"
);
const res1 = CORE.parseXmlInvoice(xrechnungXml, "sample.xml", PyDOMParser);
assert.equal(res1.valid, true);
assert.equal(res1.id, "XR-SAMPLE-2026-1001");
assert.equal(res1.gross, 238);
assert.equal(res1.bu, "9");

// XSS & semicolon escaping check on CreditNote
const xssCn = xrechnungXml
  .replace(/<Invoice /g, "<CreditNote ")
  .replace(/<\/Invoice>/g, "</CreditNote>")
  .replace(/InvoiceLine>/g, "CreditNoteLine>")
  .replace(/InvoicedQuantity/g, "CreditedQuantity")
  .replace("NordWerk Software GmbH", "Bad; &lt;img src=x onerror=alert(1)&gt; GmbH");

const cnRes = CORE.parseXmlInvoice(xssCn, "cn.xml", PyDOMParser);
assert.equal(cnRes.isCreditNote, true);
assert.equal(cnRes.valid, true);
const exp = CORE.buildExports([cnRes]);
assert.ok(exp.datevRows[0].includes(";H;EUR;3400;70000;9;"), "CreditNote must emit DATEV H flag");
assert.ok(exp.datevRows[0].includes('"Bad; <img src=x onerror=alert(1)> GmbH (UBL_2.1)"'), "Semicolon must be quoted cleanly in DATEV CSV");
assert.ok(!CORE.escHtml(cnRes.seller).includes("<img"), "escHtml must neutralize HTML tags");

// CSV formula injection & Decimal half-up parity & fractional VAT rate checks
assert.equal(CORE.toCents("1.005"), 101);
assert.equal(CORE.toCents("-1.005"), -101);
assert.equal(CORE.num("1,50"), 0);
assert.equal(CORE.fmtRate(25.5), "25.5");
assert.equal(CORE.fmtRate(19.0), "19");
const formulaXml = xrechnungXml.replace("NordWerk Software GmbH", "=HYPERLINK(\"https://evil.test\",\"x\")");
const fRes = CORE.parseXmlInvoice(formulaXml, "formula.xml", PyDOMParser);
const fExp = CORE.buildExports([fRes]);
assert.ok(fExp.datevRows[0].includes("'=HYPERLINK("), "Formula trigger must be neutralized with leading single quote");

// Invalid XML must fail gracefully without throwing
const badRes = CORE.parseXmlInvoice("<Invoice><broken></Invoice>", "bad.xml", PyDOMParser);
assert.equal(badRes.valid, false);
assert.equal(badRes.syntax, "UNKNOWN");

console.log("PASS: Chrome Viewer Extension MV3 manifest, CSP, core sync, CreditNote H-flag, CSV quoting & XSS safety verified.");
