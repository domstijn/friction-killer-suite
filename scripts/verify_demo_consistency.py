#!/usr/bin/env python3
"""Deterministic cross-tab, sample-fixture & UI consistency verifier for all Friction-Killer demos."""

from __future__ import annotations

import csv
import html as html_lib
import io
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


class _DomExtractor(HTMLParser):
    """Extract initial element IDs, text content, values, checked flags, and inline scripts."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: dict[str, dict[str, Any]] = {}
        self.scripts: list[str] = []
        self._stack: list[tuple[str, str | None]] = []
        self._in_script = False
        self._script_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: ("" if v is None else html_lib.unescape(v)) for k, v in attrs}
        el_id = attr_map.get("id")
        if el_id:
            self.elements[el_id] = {
                "tag": tag.lower(),
                "value": attr_map.get("value", ""),
                "checked": "checked" in attr_map,
                "textContent": "",
                "innerHTML": "",
                "attrs": attr_map,
            }
        self._stack.append((tag.lower(), el_id))
        if tag.lower() == "script" and "src" not in attr_map and attr_map.get("type", "").lower() != "application/ld+json":
            self._in_script = True
            self._script_buf = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "script" and self._in_script:
            self._in_script = False
            self.scripts.append("".join(self._script_buf))
            self._script_buf = []
        for idx in range(len(self._stack) - 1, -1, -1):
            if self._stack[idx][0] == t:
                del self._stack[idx:]
                break

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._script_buf.append(data)
            return
        for _tag, el_id in reversed(self._stack):
            if el_id and el_id in self.elements:
                if self.elements[el_id]["tag"] == "textarea":
                    self.elements[el_id]["value"] += html_lib.unescape(data)
                else:
                    self.elements[el_id]["textContent"] += html_lib.unescape(data)
                break


def _run_page_js(html_path: Path, actions_js: str, *, pro_storage: tuple[str, str] | None = None) -> dict[str, Any]:
    raw_html = html_path.read_text(encoding="utf-8")
    parser = _DomExtractor()
    parser.feed(raw_html)

    # Filter out telemetry/analytics scripts; keep app logic script(s)
    app_scripts = [
        s for s in parser.scripts
        if "fk-funnel-beacon" not in s and "fk_ignore_telemetry" not in s
    ]
    if not app_scripts:
        raise AssertionError(f"No app script found in {html_path}")

    # Collect class-based elements referenced (e.g. .einv-tab, .amz-tab, .oss-tab, .pg-tab, .bf-tab, .sm-tab)
    class_els: list[dict[str, Any]] = []
    for m in re.finditer(r"<button\b([^>]*)>", raw_html):
        attrs_str = m.group(1)
        cls_m = re.search(r'class="([^"]+)"', attrs_str)
        attrs_dict = {
            k: html_lib.unescape(v)
            for k, v in re.findall(r'([a-zA-Z0-9_-]+)="([^"]*)"', attrs_str)
        }
        if cls_m and any(k.startswith("data-") and k.endswith("-tab") for k in attrs_dict):
            class_els.append({"tag": "button", "className": cls_m.group(1), "attrs": attrs_dict})

    seed_storage = {}
    if pro_storage:
        seed_storage[pro_storage[0]] = json.dumps({"valid": True, "key": pro_storage[1], "verifiedAt": 1795544000000})

    harness = f"""
const vm = require("vm");
const {{ execFileSync }} = require("child_process");

const initialEls = {json.dumps(parser.elements)};
const tabBtnDefs = {json.dumps(class_els)};
const storageMap = new Map(Object.entries({json.dumps(seed_storage)}));
const allElements = [];

function makeNode(id, def) {{
  const listeners = {{}};
  const clsSet = new Set(String(def.className || def.attrs?.class || "").split(/\\s+/).filter(Boolean));
  const node = {{
    id: id || "",
    tagName: (def.tag || "div").toUpperCase(),
    value: def.value || "",
    checked: Boolean(def.checked),
    disabled: false,
    scrollTop: 0,
    style: {{}},
    children: [],
    _textContent: def.textContent || "",
    _innerHTML: def.innerHTML || "",
    attrs: Object.assign({{}}, def.attrs || {{}}),
    classList: {{
      add: (...xs) => xs.forEach((x) => clsSet.add(x)),
      remove: (...xs) => xs.forEach((x) => clsSet.delete(x)),
      toggle: (x, force) => {{
        const on = force === undefined ? !clsSet.has(x) : Boolean(force);
        if (on) clsSet.add(x); else clsSet.delete(x);
      }},
      contains: (x) => clsSet.has(x),
    }},
    get className() {{ return Array.from(clsSet).join(" "); }},
    set className(v) {{ clsSet.clear(); String(v || "").split(/\\s+/).filter(Boolean).forEach((x) => clsSet.add(x)); }},
    get textContent() {{ return this._textContent; }},
    set textContent(v) {{ this._textContent = String(v ?? ""); }},
    get innerHTML() {{ return this._innerHTML; }},
    set innerHTML(v) {{
      this._innerHTML = String(v ?? "");
      if (this._innerHTML === "") this.children = [];
      else {{
        // Synthesize lightweight child wrappers for click / option / row queries
        const trMatches = this._innerHTML.match(/<tr\\b[^>]*data-iso='([^']+)'/g) || [];
        if (trMatches.length) {{
          this.children = trMatches.map((m) => {{
            const iso = m.match(/data-iso='([^']+)'/)[1];
            return makeNode("", {{ tag: "tr", attrs: {{ "data-iso": iso }} }});
          }});
        }}
      }}
    }},
    appendChild(child) {{
      this.children.push(child);
      if (this.tagName === "SELECT" && (child.selected || (!this.value && this.children.length === 1))) {{
        this.value = child.value;
      }}
      return child;
    }},
    remove() {{}},
    click() {{ this.dispatchEvent({{ type: "click", target: this }}); }},
    getAttribute(k) {{ return k in this.attrs ? this.attrs[k] : null; }},
    setAttribute(k, v) {{ this.attrs[k] = String(v); }},
    addEventListener(ev, fn) {{ (listeners[ev] = listeners[ev] || []).push(fn); }},
    dispatchEvent(evObj) {{
      const list = listeners[evObj.type] || [];
      list.forEach((fn) => fn.call(this, evObj));
    }},
    querySelector(sel) {{ return this.querySelectorAll(sel)[0] || null; }},
    querySelectorAll(sel) {{
      if (sel.startsWith("option[value=")) {{
        const v = sel.match(/value="([^"]+)"/)?.[1];
        return this.children.filter((c) => c.value === v);
      }}
      if (sel.startsWith("tr[data-iso]")) {{
        return this.children.filter((c) => c.attrs && "data-iso" in c.attrs);
      }}
      if (sel.startsWith(".")) {{
        const c = sel.slice(1);
        return this.children.filter((ch) => ch.classList.contains(c));
      }}
      return [];
    }},
  }};
  allElements.push(node);
  return node;
}}

const elsById = {{}};
for (const [id, def] of Object.entries(initialEls)) {{
  elsById[id] = makeNode(id, def);
}}
const extraTabEls = tabBtnDefs.map((d) => makeNode("", d));

function parseXmlViaPy(xmlStr) {{
  const pyScript = `
import json, sys, xml.etree.ElementTree as ET
raw = sys.stdin.read().lstrip("\\\\ufeff").strip()
root = ET.fromstring(raw)
def node_to_dict(el):
    local = el.tag.rsplit("}}", 1)[-1]
    return {{
        "localName": local,
        "tagName": local,
        "attrib": dict(el.attrib),
        "text": "".join(el.itertext()).strip(),
        "ownText": (el.text or "").strip(),
        "children": [node_to_dict(c) for c in list(el)],
    }}
print(json.dumps(node_to_dict(root)))
`;
  const jsonOut = execFileSync("python3", ["-c", pyScript], {{ input: xmlStr, encoding: "utf-8" }});
  const wrap = (obj) => {{
    const wrappedChildren = obj.children.map(wrap);
    const node = {{
      localName: obj.localName,
      tagName: obj.tagName,
      textContent: obj.text,
      children: wrappedChildren,
      getAttribute: (k) => (k in obj.attrib ? obj.attrib[k] : null),
      getElementsByTagName(name) {{
        const out = [];
        const walk = (n) => {{
          for (const ch of n.children) {{
            if (name === "*" || ch.localName === name) out.push(ch);
            walk(ch);
          }}
        }};
        walk(this);
        return out;
      }},
    }};
    return node;
  }};
  const root = wrap(JSON.parse(jsonOut));
  return {{
    documentElement: root,
    getElementsByTagName: (name) => root.getElementsByTagName(name),
  }};
}}

const documentObj = {{
  body: makeNode("body", {{ tag: "body" }}),
  getElementById: (id) => elsById[id] || null,
  createElement: (tag) => makeNode("", {{ tag }}),
  querySelectorAll: (sel) => {{
    if (sel.startsWith("[data-") && sel.endsWith("]")) {{
      const attr = sel.slice(1, -1);
      return [...extraTabEls, ...allElements].filter((el) => el.attrs && attr in el.attrs);
    }}
    if (sel.startsWith(".")) {{
      const cls = sel.slice(1);
      return [...extraTabEls, ...allElements].filter((el) => el.classList && el.classList.contains(cls));
    }}
    return [];
  }},
}};

let fetchCalled = false;
const ctx = {{
  document: documentObj,
  window: {{ dispatchEvent() {{}} }},
  location: {{ hostname: "domstijn.github.io", protocol: "https:", search: "" }},
  navigator: {{}},
  localStorage: {{
    getItem: (k) => storageMap.has(k) ? storageMap.get(k) : null,
    setItem: (k, v) => storageMap.set(k, String(v)),
  }},
  DOMParser: function () {{ return {{ parseFromString: (txt) => parseXmlViaPy(txt) }}; }},
  Blob: function () {{}},
  URL: {{ createObjectURL: () => "blob:mock", revokeObjectURL: () => {{}} }},
  CustomEvent: function (t, d) {{ this.type = t; this.detail = d; }},
  fetch: async () => {{ fetchCalled = true; throw new Error("unexpected network fetch"); }},
  print: () => {{}},
  console,
  Math, Number, String, Boolean, Array, Object, Set, Map, JSON, Date, RegExp, Error,
  parseFloat, parseInt, isFinite, encodeURIComponent, decodeURIComponent,
}};
ctx.globalThis = ctx;

vm.createContext(ctx);
for (const code of {json.dumps(app_scripts)}) {{
  vm.runInContext(code, ctx);
}}

const result = (() => {{
  {actions_js}
}})();

console.log(JSON.stringify({{ fetchCalled, result }}));
"""
    proc = subprocess.run(
        ["node", "-"],
        input=harness,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Node harness failed on {html_path}:\n{proc.stderr}\n{proc.stdout}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def verify_all() -> None:
    print("1. Checking static hygiene across docs/...")
    docs_html = sorted(DOCS_DIR.rglob("*.html"))
    for p in docs_html:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        rel = str(p.relative_to(DOCS_DIR))
        assert "Score " not in txt or rel.startswith("guides/"), f"Leaked Score in {rel}"
        assert "Zero PRDs, source code" not in txt, f"Leaked PRD boilerplate in {rel}"
        if re.search(r"€-\d", txt):
            raise AssertionError(f"Negative sign after € bug in {rel}")
        # localhost:4242 only permitted inside an explicit isLocalHost guard
        if "http://localhost:4242" in txt:
            assert "isLocalHost" in txt or "location.hostname" in txt, f"Unguarded localhost fetch in {rel}"

    idx_txt = (DOCS_DIR / "index.html").read_text(encoding="utf-8")
    assert "Score " not in idx_txt, "Score leaked on docs/index.html"
    assert "all 9 Friction" not in str(list(DOCS_DIR.rglob("*.html"))), "Stale 'all 9' count found"
    for p in DOCS_DIR.glob("products/*/index.html"):
        ptxt = p.read_text(encoding="utf-8")
        assert "all 9 " not in ptxt and "all 10 " not in ptxt and "all 11 " not in ptxt, f"Stale tool count in {p}"
        if p.parent.name in {
            "e-invoice-xml-batch-converter",
            "camt053-mt940-qbo-xero-converter",
            "eu-oss-vat-return-compiler",
            "amazon-settlement-xero-qbo-splitter",
            "stripe-payout-xero-qbo-splitter",
            "lemonsqueezy-stripe-polar-migrator",
            "woo-shopify-metafield-migrator",
            "webflow-cms-asset-migrator",
        }:
            # On docs/index.html no .zip/.whl link should point directly at these 8 paid web apps
            for ext in (f"{p.parent.name}-v0.1.0.zip", f"{p.parent.name.replace('-', '_')}-0.1.0-py3-none-any.whl"):
                assert ext not in idx_txt, f"Free source archive {ext} exposed on docs/index.html"

    # German /de/ and BU-Lookup pages must have German policy/feedback footers
    for de_file in [DOCS_DIR / "de" / "index.html", DOCS_DIR / "tools" / "datev-bu-schluessel-lookup" / "index.html"]:
        dt = de_file.read_text(encoding="utf-8")
        assert "Support &amp; Kontakt" in dt and "Fehlt ein Format" in dt, f"Missing German footer/feedback in {de_file}"
        assert "Missing a bank" not in dt and "14-Day Refund Policy" not in dt, f"English boilerplate leaked into {de_file}"

    print("2. Verifying EInvoiceLocal cross-tab parity (Free & Pro)...")
    einv_page = DOCS_DIR / "products" / "e-invoice-xml-batch-converter" / "index.html"
    for mode, key, expected_gross, expected_rows in [
        ("free", None, Decimal("585.00"), 3),
        ("pro", ("fk_einvoice_pro_state", "cs_live_ValidEInvoiceProKey123456"), Decimal("918.00"), 4),
    ]:
        out = _run_page_js(
            einv_page,
            """
            documentObj.getElementById("app-sample-btn").click();
            const getTab = (name) => {
              const btn = documentObj.querySelectorAll("[data-einv-tab]").find((b) => b.getAttribute("data-einv-tab") === name);
              btn.click();
              return documentObj.getElementById("app-output").textContent;
            };
            const datev = getTab("datev");
            const xero = getTab("xero");
            const qbo = getTab("qbo");
            return {
              net: documentObj.getElementById("stat-net").textContent,
              vat: documentObj.getElementById("stat-vat").textContent,
              gross: documentObj.getElementById("stat-gross").textContent,
              valid: documentObj.getElementById("stat-valid").textContent,
              tableHtml: documentObj.getElementById("app-table-body").children.map((c) => c._innerHTML),
              datev, xero, qbo
            };
            """,
            pro_storage=key,
        )["result"]
        assert Decimal(out["gross"].replace("€", "")) == expected_gross, f"EInvoice {mode} gross={out['gross']}"
        d_rows = list(csv.DictReader(io.StringIO(out["datev"]), delimiter=";"))
        x_rows = list(csv.DictReader(io.StringIO(out["xero"])))
        q_rows = list(csv.DictReader(io.StringIO(out["qbo"])))
        d_sum = sum(Decimal(r["Umsatz (ohne Soll/Haben-Kz)"].replace(",", ".")) for r in d_rows)
        x_sum = sum(Decimal(r["*Quantity"]) * Decimal(r["*UnitAmount"]) + Decimal(r["TaxAmount"]) for r in x_rows)
        q_sum = sum(Decimal(r["LineAmount"]) + Decimal(r["TaxAmount"]) for r in q_rows)
        assert d_sum == x_sum == q_sum == expected_gross, f"EInvoice cross-tab drift: D={d_sum}, X={x_sum}, Q={q_sum}"
        assert "400" not in {r["*AccountCode"] for r in x_rows}, "Hardcoded Xero AccountCode 400 still present!"
        assert len({r["*InvoiceNumber"] for r in x_rows}) == expected_rows
        assert "PEP-2026-3003" in out["xero"] and "Antwerp Logistics Systems BV" in out["xero"]

    print("3. Verifying StripePayoutBridge, AmzSettlementBridge, OssVatBridge, LemonExitBridge, BankFeedBridge...")
    sp_out = _run_page_js(
        DOCS_DIR / "products" / "stripe-payout-xero-qbo-splitter" / "index.html",
        """
        documentObj.getElementById("app-sample-btn").click();
        const xero = documentObj.getElementById("app-output").textContent;
        const fmtEl = documentObj.getElementById("app-format");
        fmtEl.value = "qbo";
        fmtEl.dispatchEvent({ type: "change" });
        const qbo = documentObj.getElementById("app-output").textContent;
        fmtEl.value = "datev";
        fmtEl.dispatchEvent({ type: "change" });
        const datev = documentObj.getElementById("app-output").textContent;
        return {
          debits: documentObj.getElementById("stat-debits").textContent,
          net: documentObj.getElementById("stat-net").textContent,
          status: documentObj.getElementById("app-status").textContent,
          xero, qbo, datev
        };
        """,
    )["result"]
    assert sp_out["debits"] == "€352.50" and sp_out["net"] == "€235.25", sp_out
    x_sp = list(csv.DictReader(io.StringIO(sp_out["xero"])))
    assert all(r["*TaxType"] == "NONE" for r in x_sp), "StripePayout Xero *TaxType must be NONE"
    assert sum(Decimal(r["*Amount"]) for r in x_sp) == Decimal("0.00"), "StripePayout Xero unbalanced"
    assert "Debits" in sp_out["qbo"] and "Soll/Haben" in sp_out["datev"]

    amz_out = _run_page_js(
        DOCS_DIR / "products" / "amazon-settlement-xero-qbo-splitter" / "index.html",
        """
        documentObj.getElementById("app-sample-btn").click();
        return {
          fees: documentObj.getElementById("stat-fees").textContent,
          deposit: documentObj.getElementById("stat-deposit").textContent,
          drift: documentObj.getElementById("stat-drift").textContent,
          xero: documentObj.getElementById("app-output").textContent,
        };
        """,
    )["result"]
    assert amz_out["fees"] == "-€93.70" and amz_out["deposit"] == "€264.10", amz_out
    assert "Drift €0.00" in amz_out["drift"]
    x_amz = list(csv.DictReader(io.StringIO(amz_out["xero"])))
    assert all(r["*TaxRate"] == "NONE" for r in x_amz), "Amz Xero *TaxRate must be NONE"
    assert sum(Decimal(r["*Amount"]) for r in x_amz) == Decimal("0.00")

    oss_out = _run_page_js(
        DOCS_DIR / "products" / "eu-oss-vat-return-compiler" / "index.html",
        """
        documentObj.getElementById("app-sample-btn").click();
        return { bzst: documentObj.getElementById("app-output").textContent };
        """,
    )["result"]
    assert "Umsatzart;" in oss_out["bzst"] and "BOP_OSS_V1;EL;SERVICES;STANDARD;24,00;" in oss_out["bzst"]
    assert "BOP_OSS_V1;AT;GOODS;REDUCED;10,00;" in oss_out["bzst"]

    lm_out = _run_page_js(
        DOCS_DIR / "products" / "lemonsqueezy-stripe-polar-migrator" / "index.html",
        """
        documentObj.getElementById("app-sample-btn").click();
        return {
          card: documentObj.getElementById("stat-card-mrr").textContent,
          pp: documentObj.getElementById("stat-pp-mrr").textContent,
          keys: documentObj.getElementById("stat-keys").textContent,
          out: documentObj.getElementById("app-output").textContent,
        };
        """,
    )["result"]
    assert "acme.io" not in lm_out["out"], "Old user1@acme.io sample still present"
    csv_block = "\n".join(ln for ln in lm_out["out"].splitlines() if ln and not ln.startswith("#"))
    lm_rows = list(csv.DictReader(io.StringIO(csv_block)))
    assert len(lm_rows) == 15
    active_st = {"active", "on_trial", "past_due", "paused"}
    card_sum = sum(Decimal(r["mrr"]) for r in lm_rows if r["status"] in active_st and "paypal" not in r["payment_method"])
    pp_sum = sum(Decimal(r["mrr"]) for r in lm_rows if r["status"] in active_st and "paypal" in r["payment_method"])
    assert f"${card_sum:.2f}" == lm_out["card"] and f"${pp_sum:.2f}" == lm_out["pp"], (card_sum, pp_sum, lm_out)

    print("4. Verifying Homepage Playgrounds & Calculators...")
    hub_out = _run_page_js(
        DOCS_DIR / "index.html",
        """
        return {
          wf: documentObj.getElementById("pg-wf-output").textContent,
          pb: documentObj.getElementById("pg-pb-output").textContent,
          oss: documentObj.getElementById("pg-ossvat-output").textContent,
          amz: documentObj.getElementById("pg-amz-output").textContent,
          einv: documentObj.getElementById("pg-einv-output").textContent,
          bf: documentObj.getElementById("pg-bankfeed-output").textContent,
        };
        """,
    )["result"]
    assert "Debits €352.50 == Credits €352.50" in hub_out["pb"], hub_out["pb"]
    assert "BOP_OSS_V1;EL;SERVICES;STANDARD;" in hub_out["oss"], hub_out["oss"]
    assert "NONE," in hub_out["amz"], hub_out["amz"]
    assert "-420.00,CloudHost BV" in hub_out["bf"] and "-234.50,Stripe Processing Fee" in hub_out["bf"], hub_out["bf"]

    bu_out = _run_page_js(
        DOCS_DIR / "tools" / "datev-bu-schluessel-lookup" / "index.html",
        """
        const sc = documentObj.getElementById("bu-scenario");
        sc.value = "K0";
        sc.dispatchEvent({ type: "change" });
        const k19 = { key: documentObj.getElementById("bu-out-key").textContent, acct: documentObj.getElementById("bu-out-acct").textContent };
        sc.value = "K7";
        sc.dispatchEvent({ type: "change" });
        const k7 = { key: documentObj.getElementById("bu-out-key").textContent, acct: documentObj.getElementById("bu-out-acct").textContent };
        return { k19, k7 };
        """,
    )["result"]
    assert bu_out["k19"] == {"key": "91", "acct": "3425"}, bu_out
    assert bu_out["k7"] == {"key": "92", "acct": "3420"}, bu_out

    oss_calc = _run_page_js(
        DOCS_DIR / "tools" / "eu-oss-vat-rates-2026" / "index.html",
        """
        const initGross = documentObj.getElementById("out-gross").textContent;
        const initCode = documentObj.getElementById("out-bzst-code").textContent;
        documentObj.getElementById("vat-mode").value = "gross_to_net";
        documentObj.getElementById("vat-net").value = "124.00";
        documentObj.getElementById("vat-mode").dispatchEvent({ type: "change" });
        const revNet = documentObj.getElementById("out-gross").textContent;
        return { initGross, initCode, revNet };
        """,
    )["result"]
    assert oss_calc == {"initGross": "€124.00", "initCode": "GR -> EL", "revNet": "€100.00"}, oss_calc

    print("ALL DEMO CONSISTENCY & CROSS-TAB PARITY CHECKS PASSED!")


if __name__ == "__main__":
    verify_all()
