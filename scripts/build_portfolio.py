#!/usr/bin/env python3
"""Generate unified Portfolio Storefront (launch_hub/ + GitHub Pages docs/) and Master Launch Playbook."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = REPO_ROOT / "pipeline" / "state.json"
DEFAULT_HUB_DIR = REPO_ROOT / "launch_hub"
DEFAULT_DOCS_DIR = REPO_ROOT / "docs"
DEFAULT_BUNDLE_CONFIG = DEFAULT_HUB_DIR / "bundle_config.json"

DEFAULT_PRICES = {
    "notion-linear-prd-sync": "€29 once",
    "notion-clean-md-exporter": "€24 once",
    "vscode-workspace-profile-config": "€19 once",
}

LEGAL_FOOTER_HTML = """  <section id="policies" class="mx-auto max-w-5xl px-6 pb-10">
    <div class="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 text-xs leading-relaxed text-slate-400">
      <div class="grid gap-6 md:grid-cols-3">
        <div>
          <h3 class="font-semibold text-slate-200">Support &amp; Contact</h3>
          <p class="mt-1">Operated by Stijn Dom (@domstijn).</p>
          <p class="mt-1">Email: <a href="mailto:dom.stijn99@gmail.com" class="text-indigo-300 underline">dom.stijn99@gmail.com</a></p>
          <p class="mt-1">Issues: <a href="https://github.com/domstijn/friction-killer-suite/issues" class="text-indigo-300 underline">GitHub Support Tracker</a></p>
        </div>
        <div>
          <h3 class="font-semibold text-slate-200">14-Day Refund Policy</h3>
          <p class="mt-1">All Pro licenses include a 14-day no-questions-asked refund guarantee. Email <a href="mailto:dom.stijn99@gmail.com" class="text-indigo-300 underline">dom.stijn99@gmail.com</a> with your order ID for a full refund.</p>
        </div>
        <div>
          <h3 class="font-semibold text-slate-200">Terms &amp; Privacy</h3>
          <p class="mt-1">All tools run locally in your browser, CLI, or editor. Zero PRDs, source code, or API keys are transmitted to third-party servers. Payments are processed securely by Stripe.</p>
        </div>
      </div>
    </div>
  </section>"""


def detect_price(proj_dir: Path, slug: str) -> str:
    landing = proj_dir / "launch" / "landing.html"
    if landing.is_file():
        text = landing.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"([€$]\d+\s+once)", text)
        if m:
            return m.group(1)
    return DEFAULT_PRICES.get(slug, "€29 once")


def detect_summary(proj_dir: Path, opp: dict[str, Any] | None) -> str:
    if opp and opp.get("solution"):
        return str(opp["solution"])
    spec = proj_dir / "SPEC.md"
    if spec.is_file():
        for line in spec.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip().startswith("- **10x Relief**:"):
                return line.split(":", 2)[-1].strip()
    return "Zero-backend friction-killer tool built for high-leverage daily workflows."


def collect_products(state: dict[str, Any], projects_dir: Path) -> list[dict[str, Any]]:
    opps_by_id = {o["id"]: o for o in state.get("opportunities", []) if "id" in o}
    items: list[dict[str, Any]] = []
    for slug, proj in state.get("projects", {}).items():
        proj_dir = projects_dir / slug
        if not proj_dir.is_dir():
            continue
        opp = opps_by_id.get(slug, {})
        zip_path = proj_dir / "dist" / f"{slug}-v0.1.0.zip"
        vsix_path = proj_dir / "dist" / f"{slug}-0.1.0.vsix"
        whl_name = f"{re.sub(r'[-_.]+', '_', slug)}-0.1.0-py3-none-any.whl"
        whl_path = proj_dir / "dist" / whl_name
        items.append(
            {
                "slug": slug,
                "title": proj.get("title") or opp.get("title") or slug,
                "short_title": str(proj.get("title") or slug).split(":")[0].strip(),
                "ecosystem": proj.get("ecosystem") or opp.get("ecosystem") or "tool",
                "target_software": proj.get("target_software") or opp.get("target_software") or "Software",
                "status": proj.get("status") or "STAGE_4_LAUNCH",
                "score": opp.get("score", "-"),
                "price": detect_price(proj_dir, slug),
                "summary": detect_summary(proj_dir, opp),
                "proj_dir": proj_dir,
                "zip_path": zip_path,
                "vsix_path": vsix_path,
                "whl_path": whl_path,
                "whl_name": whl_name,
                "landing_rel": f"../projects/{slug}/launch/landing.html",
                "kit_rel": f"../projects/{slug}/launch/LAUNCH_KIT.md",
                "zip_rel": f"../projects/{slug}/dist/{slug}-v0.1.0.zip",
                "vsix_rel": f"../projects/{slug}/dist/{slug}-0.1.0.vsix",
                "whl_rel": f"../projects/{slug}/dist/{whl_name}",
                "site_page_rel": f"./products/{slug}/index.html",
                "site_zip_rel": f"./downloads/{slug}-v0.1.0.zip",
                "site_vsix_rel": f"./downloads/{slug}-0.1.0.vsix",
                "site_whl_rel": f"./downloads/{whl_name}",
                "zip_exists": zip_path.is_file(),
                "vsix_exists": vsix_path.is_file(),
                "whl_exists": whl_path.is_file(),
            }
        )
    return items


PLAYGROUND_SECTION = r"""    <section id="playground" class="mt-14 rounded-3xl border border-slate-800 bg-slate-900/70 p-6 sm:p-8">
      <div class="flex flex-col justify-between gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-center">
        <div>
          <span class="rounded-full bg-indigo-500/20 px-2.5 py-0.5 text-xs font-semibold text-indigo-300">ZERO-INSTALL INTERACTIVE DEMO</span>
          <h2 class="mt-2 text-2xl font-bold text-white">Try All 3 Tools Live in Your Browser</h2>
          <p class="mt-1 text-xs text-slate-400">Runs 100% locally in JavaScript — nothing leaves your browser.</p>
        </div>
        <div class="flex flex-wrap gap-2" role="tablist">
          <button type="button" data-pg-tab="linear" class="pg-tab rounded-lg bg-indigo-500 px-3.5 py-2 text-xs font-semibold text-white">1. LinearBridge</button>
          <button type="button" data-pg-tab="notion" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">2. NotionGitExport</button>
          <button type="button" data-pg-tab="vscode" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">3. ExtProfileLock</button>
        </div>
      </div>

      <!-- Tab 1: LinearBridge -->
      <div id="pg-panel-linear" class="pg-panel mt-6 grid gap-6 md:grid-cols-2">
        <div>
          <label class="text-xs font-semibold text-slate-300" for="pg-linear-input">Paste Notion PRD Markdown</label>
          <textarea id="pg-linear-input" rows="10" class="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"># Mobile Billing V2
Streamline checkout retries and receipt exports.

## API Layer
- [ ] Implement webhook signature guard
- [ ] Add idempotency keys [ENG-10]
- [x] Already shipped item

## Frontend
* [ ] Build retry banner
- [ ] Export CSV receipts</textarea>
        </div>
        <div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-emerald-300">Linear Parent Epic + GraphQL Mutations Preview</span>
            <span id="pg-linear-stats" class="text-xs text-slate-400"></span>
          </div>
          <pre id="pg-linear-output" class="mt-2 h-60 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 2: NotionGitExport -->
      <div id="pg-panel-notion" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-notion-file">Messy Notion Filename</label>
            <input id="pg-notion-file" value="Engineering Docs a1b2c3d4e5f60123456789abcdef0123/Product Spec 0123456789abcdef0123456789abcdef.md" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-200 focus:border-indigo-500 focus:outline-none" />
          </div>
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-notion-md">Messy Notion Export Markdown</label>
            <textarea id="pg-notion-md" rows="8" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"># API Guide

Status: Ready
Tags: docs, api

See [Overview](Overview%200123456789abcdef0123456789abcdef.md) and [External](https://example.com).</textarea>
          </div>
        </div>
        <div>
          <div class="flex items-center justify-between gap-2">
            <span class="text-xs font-semibold text-emerald-300">Clean Path: <code id="pg-notion-cleanfile" class="text-indigo-300"></code></span>
            <button id="pg-notion-copy" type="button" class="rounded-lg bg-slate-800 px-2.5 py-1 text-xs font-semibold text-white hover:bg-slate-700">Copy Clean MD</button>
          </div>
          <pre id="pg-notion-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 3: ExtProfileLock -->
      <div id="pg-panel-vscode" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-vs-lock">workspace-lock.json + Installed (comma-sep)</label>
            <textarea id="pg-vs-lock" rows="4" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">{"required":["esbenp.prettier-vscode","dbaeumer.vscode-eslint"],"disabled":["tabnine.tabnine-vscode"]}</textarea>
            <input id="pg-vs-installed" value="dbaeumer.vscode-eslint, tabnine.tabnine-vscode" class="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200" />
          </div>
          <div class="grid gap-2 sm:grid-cols-2">
            <textarea id="pg-vs-env" rows="3" class="w-full rounded-xl border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-200">SDK_ROOT="/Users/dev/sdk"
API_URL="https://staging.api"</textarea>
            <textarea id="pg-vs-ws" rows="3" class="w-full rounded-xl border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-200">{"folders":[{"path":"${env:SDK_ROOT}/core"}],"settings":{"api":"${env:API_URL}"}}</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">CLI Toggle Commands + Interpolated .code-workspace</span>
          <pre id="pg-vs-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>
    </section>"""


PLAYGROUND_SCRIPT = r"""  <script>
    (function () {
      const tabs = document.querySelectorAll(".pg-tab");
      const panels = {
        linear: document.getElementById("pg-panel-linear"),
        notion: document.getElementById("pg-panel-notion"),
        vscode: document.getElementById("pg-panel-vscode"),
      };
      tabs.forEach((btn) => {
        btn.addEventListener("click", () => {
          const target = btn.getAttribute("data-pg-tab");
          tabs.forEach((b) => {
            const active = b.getAttribute("data-pg-tab") === target;
            b.className = active
              ? "pg-tab rounded-lg bg-indigo-500 px-3.5 py-2 text-xs font-semibold text-white"
              : "pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700";
          });
          Object.entries(panels).forEach(([k, el]) => {
            if (!el) return;
            el.classList.toggle("hidden", k !== target);
          });
        });
      });

      // 1. LinearBridge live parser
      const lIn = document.getElementById("pg-linear-input");
      const lOut = document.getElementById("pg-linear-output");
      const lStats = document.getElementById("pg-linear-stats");
      function runLinear() {
        if (!lIn || !lOut) return;
        let title = "Untitled PRD", section = "General", skipped = 0;
        const tasks = [];
        for (const raw of lIn.value.split(/\r?\n/)) {
          const line = raw.trim();
          const hm = line.match(/^(#{1,3})\s+(.+)$/);
          if (hm) {
            if (hm[1].length === 1 && title === "Untitled PRD") title = hm[2].trim();
            else section = hm[2].trim();
            continue;
          }
          const cm = line.match(/^(?:[-*]\s*)?\[([ xX]?)\]\s+(.+)$/);
          if (cm) {
            const done = cm[1].toLowerCase() === "x";
            const body = cm[2].trim();
            const keyMatch = body.match(/\[([A-Z][A-Z0-9]+-\d+)(?::[^\]]+)?\]/);
            if (done || keyMatch) { skipped += 1; continue; }
            tasks.push({ title: body, section, parentTitle: "[PRD] " + title });
          }
        }
        if (lStats) lStats.textContent = tasks.length + " to create · " + skipped + " skipped";
        lOut.textContent = JSON.stringify({
          parentEpic: { title: "[PRD] " + title },
          subIssues: tasks.map((t) => ({ title: t.title, description: "**Section:** " + t.section, parentId: "<PARENT_EPIC_ID>" }))
        }, null, 2);
      }
      lIn?.addEventListener("input", runLinear);
      runLinear();

      // 2. NotionGitExport live cleaner
      const nFile = document.getElementById("pg-notion-file");
      const nMd = document.getElementById("pg-notion-md");
      const nCleanFile = document.getElementById("pg-notion-cleanfile");
      const nOut = document.getElementById("pg-notion-output");
      function cleanSegment(seg) {
        return seg.replace(/(?:\s+|%20)[0-9a-fA-F]{32}$/, "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "untitled";
      }
      function stripUuidPath(p) {
        const parts = decodeURIComponent(p.trim()).split("/").filter(Boolean);
        return parts.map((part, idx) => {
          if (idx === parts.length - 1 && part.includes(".")) {
            const i = part.lastIndexOf(".");
            return cleanSegment(part.slice(0, i)) + "." + part.slice(i + 1).toLowerCase();
          }
          return cleanSegment(part);
        }).join("/");
      }
      function runNotion() {
        if (!nFile || !nMd || !nOut) return;
        if (nCleanFile) nCleanFile.textContent = stripUuidPath(nFile.value);
        const lines = nMd.value.split(/\r?\n/);
        let idx = 0, title = null, meta = {};
        while (idx < lines.length && !lines[idx].trim()) idx++;
        if (idx < lines.length && lines[idx].startsWith("# ")) {
          title = lines[idx].slice(2).trim(); idx++;
          while (idx < lines.length && !lines[idx].trim()) idx++;
          while (idx < lines.length) {
            const m = lines[idx].trim().match(/^([A-Za-z][A-Za-z0-9 _-]{0,30}):\s+(.+)$/);
            if (!m) break;
            meta[m[1].toLowerCase().replace(/[^a-z0-9]+/g, "_")] = m[2].trim();
            idx++;
          }
        }
        const body = (title ? lines.slice(idx).join("\n") : nMd.value)
          .replace(/(!?\[[^\]]*\])\(([^)]+)\)/g, (full, lbl, target) => {
            if (/^(https?:|mailto:|#)/i.test(target)) return full;
            return lbl + "(" + stripUuidPath(target) + ")";
          }).trim();
        let fm = "";
        if (title) {
          const fmLines = ["---", 'title: "' + title + '"'];
          for (const [k, v] of Object.entries(meta)) {
            fmLines.push(k === "tags" && v.includes(",") ? k + ": [" + v.split(",").map((s) => '"' + s.trim() + '"').join(", ") + "]" : k + ': "' + v + '"');
          }
          fm = fmLines.join("\n") + "\n---\n\n";
        }
        nOut.textContent = fm + body;
      }
      nFile?.addEventListener("input", runNotion);
      nMd?.addEventListener("input", runNotion);
      document.getElementById("pg-notion-copy")?.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(nOut?.textContent || ""); } catch {}
      });
      runNotion();

      // 3. ExtProfileLock live interpolator
      const vLock = document.getElementById("pg-vs-lock");
      const vInst = document.getElementById("pg-vs-installed");
      const vEnv = document.getElementById("pg-vs-env");
      const vWs = document.getElementById("pg-vs-ws");
      const vOut = document.getElementById("pg-vs-output");
      function runVscode() {
        if (!vLock || !vOut) return;
        try {
          const lock = JSON.parse(vLock.value || "{}");
          const installed = new Set((vInst?.value || "").split(",").map((s) => s.trim().toLowerCase()).filter(Boolean));
          const cmds = [];
          for (const req of (lock.required || [])) {
            if (!installed.has(req.toLowerCase())) cmds.push("code --install-extension " + req);
          }
          for (const dis of (lock.disabled || [])) {
            if (installed.has(dis.toLowerCase())) cmds.push("code --disable-extension " + dis);
          }
          const envMap = {};
          for (const raw of (vEnv?.value || "").split(/\r?\n/)) {
            const line = raw.trim().replace(/^export\s+/, "");
            const eq = line.indexOf("=");
            if (eq > 0) envMap[line.slice(0, eq).trim()] = line.slice(eq + 1).trim().replace(/^["']|["']$/g, "");
          }
          const ws = (vWs?.value || "{}").replace(/\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}/g, (f, k) => envMap[k] ?? f);
          vOut.textContent = "# Generated CLI Batch:\n" + (cmds.length ? cmds.join("\n") : "# Workspace compliant") + "\n\n# Interpolated .code-workspace:\n" + ws;
        } catch (err) {
          vOut.textContent = "JSON parse error: " + err.message;
        }
      }
      [vLock, vInst, vEnv, vWs].forEach((el) => el?.addEventListener("input", runVscode));
      runVscode();
    })();
  </script>"""


def render_hub_html(
    products: list[dict[str, Any]],
    *,
    for_pages: bool = False,
    bundle_checkout_url: str = "#BUNDLE_CHECKOUT_URL_HERE",
) -> str:
    cards: list[str] = []
    for p in products:
        page_href = p["site_page_rel"] if for_pages else p["landing_rel"]
        zip_href = p["site_zip_rel"] if for_pages else p["zip_rel"]
        vsix_href = p["site_vsix_rel"] if for_pages else p["vsix_rel"]
        whl_href = p["site_whl_rel"] if for_pages else p["whl_rel"]
        dl_links = []
        if p["zip_exists"]:
            dl_links.append(
                f'<a href="{html.escape(zip_href)}" download data-fk-cta="free-install" class="text-xs text-indigo-300 hover:text-indigo-200 underline">.zip</a>'
            )
        if p["vsix_exists"]:
            dl_links.append(
                f'<a href="{html.escape(vsix_href)}" download data-fk-cta="free-install" class="text-xs text-emerald-300 hover:text-emerald-200 underline">.vsix</a>'
            )
        if p["whl_exists"]:
            dl_links.append(
                f'<a href="{html.escape(whl_href)}" download data-fk-cta="free-install" class="text-xs text-emerald-300 hover:text-emerald-200 underline">.whl (pip)</a>'
            )
        zip_badge = (
            '<div class="flex items-center gap-2.5">' + " ".join(dl_links) + "</div>"
            if dl_links
            else '<span class="text-xs text-slate-500">Unpackaged</span>'
        )
        cards.append(
            f"""      <article class="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <div>
          <div class="flex items-center justify-between gap-2">
            <span class="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-xs font-medium text-indigo-300">{html.escape(p["ecosystem"])}</span>
            <span class="text-sm font-bold text-emerald-400">{html.escape(p["price"])}</span>
          </div>
          <h3 class="mt-4 text-xl font-bold text-white">{html.escape(p["short_title"])}</h3>
          <p class="mt-1 text-xs uppercase tracking-wider text-slate-400">For {html.escape(p["target_software"])} · Score {html.escape(str(p["score"]))}</p>
          <p class="mt-3 text-sm leading-relaxed text-slate-300">{html.escape(p["summary"])}</p>
        </div>
        <div class="mt-6 flex items-center justify-between border-t border-slate-800 pt-4">
          <a href="{html.escape(page_href)}" class="rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-700">Open Product Page</a>
          {zip_badge}
        </div>
      </article>"""
        )

    cards_html = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Friction-Killer Suite — All-Access Developer &amp; PM Tools</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
  <header class="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
    <div class="text-lg font-bold tracking-tight text-white">Friction-Killer Suite</div>
    <nav class="flex items-center gap-6 text-sm text-slate-300">
      <a href="#playground" class="hover:text-white">Live Playground</a>
      <a href="#bundle" class="hover:text-white">Bundle</a>
      <a href="#policies" class="hover:text-white">Support &amp; Policies</a>
      <a href="#bundle" class="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400">
        All-Access Bundle — €49
      </a>
    </nav>
  </header>

  <main class="mx-auto max-w-6xl px-6 pb-12">
    <section class="py-12 text-center">
      <span class="inline-block rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
        Zero-Subscription · Local-First · Powered by Stripe Managed Payments
      </span>
      <h1 class="mt-5 text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
        Eliminate Notion, Linear &amp; VS Code friction<br />
        <span class="text-indigo-400">without paying monthly SaaS taxes.</span>
      </h1>
      <p class="mx-auto mt-4 max-w-2xl text-base text-slate-300">
        Three purpose-built utilities that automate PRD-to-Linear epics, clean Notion Markdown Git exports, and declarative VS Code workspace profiles.
      </p>
      <div class="mt-7 flex flex-wrap justify-center gap-3">
        <a href="#playground" class="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-slate-200">Try Live in Browser</a>
        <a href="#bundle" class="rounded-xl border border-slate-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-800">Get All-Access Bundle — €49</a>
      </div>
    </section>

    <section class="grid gap-6 md:grid-cols-3">
{cards_html}
    </section>

{PLAYGROUND_SECTION}

    <section id="bundle" class="mt-14 rounded-3xl border border-indigo-500/50 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/60 p-8 sm:p-10">
      <div class="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
        <div>
          <span class="rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-300">BEST VALUE · SAVE 32%</span>
          <h2 class="mt-3 text-3xl font-extrabold text-white">All-Access Friction-Killer Bundle</h2>
          <p class="mt-2 max-w-xl text-sm text-slate-300">
            Unlock Pro licenses for all {len(products)} tools (LinearBridge + NotionGitExport + ExtProfileLock) with one single purchase (€72 combined value).
          </p>
        </div>
        <div class="w-full shrink-0 rounded-2xl border border-slate-700 bg-slate-950/70 p-6 text-center md:w-72">
          <div class="text-xs text-slate-400 line-through">€72 combined</div>
          <div class="mt-1 text-4xl font-extrabold text-white">€49 <span class="text-sm font-normal text-slate-400">once</span></div>
          <a href="{html.escape(bundle_checkout_url)}" data-fk-cta="pro-checkout" class="stripe-checkout-button mt-5 block rounded-xl bg-indigo-500 py-3 text-sm font-semibold text-white hover:bg-indigo-400">
            Get All-Access Bundle
          </a>
        </div>
      </div>
    </section>
  </main>

{LEGAL_FOOTER_HTML}

  <footer class="mx-auto max-w-6xl border-t border-slate-800 px-6 py-8 text-center text-xs text-slate-500">
    Friction-Killer Suite by Stijn Dom (@domstijn) · <a href="https://github.com/domstijn/friction-killer-suite" class="text-slate-400 underline">GitHub</a> · <a href="mailto:dom.stijn99@gmail.com" class="text-slate-400 underline">dom.stijn99@gmail.com</a>
  </footer>

  <script>
    document.querySelectorAll("[data-fk-cta]").forEach((el) => {{
      el.addEventListener("click", () => {{
        const cta = el.getAttribute("data-fk-cta");
        try {{
          const key = "fk_cta_telemetry";
          const data = JSON.parse(localStorage.getItem(key) || "{{}}");
          data[cta] = (Number(data[cta]) || 0) + 1;
          localStorage.setItem(key, JSON.stringify(data));
          window.dispatchEvent(new CustomEvent("fk:cta", {{ detail: {{ cta, counts: data }} }}));
        }} catch {{}}
      }});
    }});
  </script>
{PLAYGROUND_SCRIPT}
</body>
</html>
"""


def render_product_page_for_docs(product: dict[str, Any]) -> str:
    landing_path = product["proj_dir"] / "launch" / "landing.html"
    page_html = landing_path.read_text(encoding="utf-8")
    slug = product["slug"]
    zip_href = f"../../downloads/{slug}-v0.1.0.zip"

    # Rewrite #install action links to direct downloadable .zip artifact
    page_html = page_html.replace('href="#install"', f'href="{zip_href}" download')

    # Inject suite navigation back-link inside header <nav>
    page_html = page_html.replace(
        '<nav class="flex items-center gap-6 text-sm text-slate-300">',
        '<nav class="flex items-center gap-6 text-sm text-slate-300">\n      <a href="../../index.html" class="text-indigo-300 hover:text-white">&larr; All Suite Tools</a>',
        1,
    )

    # Replace basic footer with Lemon Squeezy verification-compliant support/refund footer
    compliant_footer = (
        f"{LEGAL_FOOTER_HTML}\n"
        f'  <footer class="mx-auto max-w-5xl border-t border-slate-800 px-6 py-8 text-center text-xs text-slate-500">\n'
        f'    {html.escape(product["short_title"])} (<code>{html.escape(slug)}</code>) — Friction-Killer Suite by Stijn Dom (@domstijn) · '
        f'<a href="https://github.com/domstijn/friction-killer-suite/issues" class="underline">Support</a> · '
        f'<a href="mailto:dom.stijn99@gmail.com" class="underline">dom.stijn99@gmail.com</a> · 14-day refund policy\n'
        f"  </footer>"
    )
    page_html = re.sub(r"<footer[\s\S]*?</footer>", compliant_footer, page_html, count=1)
    return page_html


def publish_docs_site(
    products: list[dict[str, Any]],
    docs_dir: Path,
    bundle_checkout_url: str,
) -> None:
    downloads_dir = docs_dir / "downloads"
    products_dir = docs_dir / "products"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    products_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / ".nojekyll").write_text("", encoding="utf-8")

    for p in products:
        if p["zip_exists"]:
            shutil.copy2(p["zip_path"], downloads_dir / f"{p['slug']}-v0.1.0.zip")
        if p["vsix_exists"]:
            shutil.copy2(p["vsix_path"], downloads_dir / f"{p['slug']}-0.1.0.vsix")
        if p["whl_exists"]:
            shutil.copy2(p["whl_path"], downloads_dir / p["whl_name"])
        landing = p["proj_dir"] / "launch" / "landing.html"
        if landing.is_file():
            prod_out = products_dir / p["slug"]
            prod_out.mkdir(parents=True, exist_ok=True)
            (prod_out / "index.html").write_text(
                render_product_page_for_docs(p), encoding="utf-8"
            )

    (docs_dir / "index.html").write_text(
        render_hub_html(products, for_pages=True, bundle_checkout_url=bundle_checkout_url),
        encoding="utf-8",
    )
    (docs_dir / "success.html").write_text(
        render_success_html(products, for_pages=True), encoding="utf-8"
    )
    (docs_dir / "cancel.html").write_text(render_cancel_html(), encoding="utf-8")


def render_success_html(products: list[dict[str, Any]], *, for_pages: bool = True) -> str:
    dl_items = []
    for p in products:
        zip_href = p["site_zip_rel"] if for_pages else p["zip_rel"]
        dl_items.append(
            f'<a href="{html.escape(zip_href)}" download class="rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-semibold text-indigo-300 hover:border-indigo-400 hover:text-white">Download {html.escape(p["short_title"])} (.zip)</a>'
        )
    downloads_html = "\n        ".join(dl_items)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Thanks for purchasing! — Friction-Killer Suite</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased">
  <main class="mx-auto max-w-2xl px-6 py-16">
    <a href="./index.html" class="text-xs font-medium text-indigo-300 hover:text-white">&larr; Back to Friction-Killer Suite</a>
    <div class="mt-6 rounded-3xl border border-emerald-500/40 bg-slate-900/80 p-8">
      <span class="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-300">PAYMENT CONFIRMED</span>
      <h1 class="mt-4 text-3xl font-extrabold text-white">Thanks for purchasing!</h1>
      <p class="mt-2 text-sm text-slate-300">
        Your Stripe Checkout Session ID below acts as your Pro License Key for LinearBridge, NotionGitExport, and ExtProfileLock.
      </p>

      <div class="mt-6 rounded-2xl border border-slate-700 bg-slate-950 p-5">
        <div class="text-xs font-semibold uppercase tracking-wider text-slate-400">Your Pro License Key</div>
        <div class="mt-2 flex items-center justify-between gap-3">
          <code id="license-key" class="truncate font-mono text-sm text-emerald-300">Check URL ?session_id=...</code>
          <button id="copy-btn" type="button" class="shrink-0 rounded-lg bg-indigo-500 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-400">
            Copy License Key
          </button>
        </div>
        <p id="copy-status" class="mt-2 text-xs text-slate-400"></p>
      </div>

      <div class="mt-6 space-y-2 text-xs text-slate-300">
        <p class="font-semibold text-white">How to activate:</p>
        <p>• <strong>LinearBridge</strong>: Open extension popup &rarr; paste key &rarr; click <em>Activate</em>.</p>
        <p>• <strong>NotionGitExport</strong>: Run <code>python3 src/cli.py --activate YOUR_KEY</code>.</p>
        <p>• <strong>ExtProfileLock</strong>: Call <code>activate("YOUR_KEY")</code> in your workspace profile config.</p>
      </div>

      <div class="mt-6 flex flex-wrap gap-2">
        {downloads_html}
      </div>

      <p class="mt-6 border-t border-slate-800 pt-4 text-xs text-slate-400">
        Questions about your order? Email <a href="mailto:dom.stijn99@gmail.com" class="text-indigo-300 underline">dom.stijn99@gmail.com</a>.
      </p>
    </div>
  </main>
  <script>
    const params = new URLSearchParams(window.location.search);
    const sid = params.get("session_id");
    const keyEl = document.getElementById("license-key");
    const statusEl = document.getElementById("copy-status");
    if (sid) {{
      keyEl.textContent = sid;
    }} else {{
      keyEl.textContent = "No session_id found in URL";
      statusEl.textContent = "Return here directly from Stripe Checkout to display your license key.";
    }}
    document.getElementById("copy-btn")?.addEventListener("click", async () => {{
      if (!sid) return;
      try {{
        await navigator.clipboard.writeText(sid);
        statusEl.textContent = "Copied license key to clipboard!";
      }} catch {{
        statusEl.textContent = "Select and copy the key above.";
      }}
    }});
  </script>
</body>
</html>
"""


def render_cancel_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Checkout canceled — Friction-Killer Suite</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased">
  <main class="mx-auto max-w-xl px-6 py-24 text-center">
    <div class="rounded-3xl border border-slate-800 bg-slate-900/70 p-10">
      <h1 class="text-2xl font-bold text-white">Checkout canceled</h1>
      <p class="mt-3 text-sm text-slate-300">
        Not ready to purchase yet? No problem, we'll be here when you are! You can still download and use the Free Tier of every tool below.
      </p>
      <a href="./index.html" class="mt-6 inline-block rounded-xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-400">
        Return to Friction-Killer Suite
      </a>
    </div>
  </main>
</body>
</html>
"""


def render_playbook_md(products: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| **{p['short_title']}** (`{p['slug']}`) | {p['ecosystem']} | {p['price']} | "
        f"`projects/{p['slug']}/dist/{p['slug']}-v0.1.0.zip` | [Sales Page]({p['landing_rel']}) / [Kit]({p['kit_rel']}) |"
        for p in products
    )
    return f"""# Master Launch Playbook (Stripe Managed Payments)

## Portfolio Summary ({len(products)} Shipped Products)

| Product | Ecosystem | Pro Price | Distributable Bundle | Launch Assets |
| :--- | :--- | :---: | :--- | :--- |
{rows}
| **All-Access Bundle** | Multi-Product | **€49 once** (Save 32%) | All 3 Pro Keys | [Storefront](index.html) |

---

## Step 1: Provision Stripe Catalog & Payment Links (~1 min)
1. Enable Managed Payments in your Stripe Dashboard (`https://dashboard.stripe.com/settings/managed-payments`).
2. Create/sync all 4 EUR products, prices (`txcd_10103000`, `tax_behavior: inclusive`), and hosted Payment Links (`Stripe-Version: 2025-03-31.basil`):
```bash
python3 scripts/stripe_managed_payments.py provision --wire-checkout
```

## Step 2: Run Checkout, License Verify & Webhook Server (~1 min)
```bash
python3 scripts/stripe_managed_payments.py serve --port 4242
# Test redirect to Stripe Checkout:
curl -X POST -is "http://localhost:4242/create-checkout-session" -d ""
```

## Step 3: Publish & Distribute
1. **GitHub Pages Storefront (`docs/`)**: Push `main` so `https://domstijn.github.io/friction-killer-suite/` serves live product pages, `success.html` (auto-displays `?session_id=` Pro key), `cancel.html`, and direct `.zip` downloads.
2. **Marketplace Submissions**:
   - Upload `projects/notion-linear-prd-sync/dist/notion-linear-prd-sync-v0.1.0.zip` to the Chrome Web Store Developer Dashboard.
   - Package `projects/vscode-workspace-profile-config` for the VS Code Marketplace (`vsce package`).
3. **High-Intent Sniper Replies**:
   - Follow each product's `LAUNCH_KIT.md` to post helpful, non-spammy replies on the exact discovered GitHub issues and HN threads.
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build launch_hub portfolio storefront, GitHub Pages docs/, and playbook."
    )
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_PATH), help="Path to pipeline/state.json")
    parser.add_argument("--hub-dir", default=str(DEFAULT_HUB_DIR), help="Output launch_hub directory")
    parser.add_argument("--docs-dir", default=str(DEFAULT_DOCS_DIR), help="Output GitHub Pages docs directory")
    parser.add_argument("--projects-dir", default=str(REPO_ROOT / "projects"), help="Projects directory")
    parser.add_argument("--bundle-url", help="Optional live Lemon Squeezy All-Access Bundle checkout URL")
    args = parser.parse_args()

    state_path = Path(args.state_file)
    if not state_path.is_file():
        print(f"Error: State file not found: {state_path}", file=sys.stderr)
        return 1

    hub_dir = Path(args.hub_dir)
    hub_dir.mkdir(parents=True, exist_ok=True)
    bundle_cfg_path = hub_dir / "bundle_config.json"

    bundle_checkout_url = "#BUNDLE_CHECKOUT_URL_HERE"
    if args.bundle_url:
        bundle_checkout_url = args.bundle_url
        bundle_cfg_path.write_text(
            json.dumps({"bundle_checkout_url": bundle_checkout_url}, indent=2) + "\n",
            encoding="utf-8",
        )
    elif bundle_cfg_path.is_file():
        saved_cfg = json.loads(bundle_cfg_path.read_text(encoding="utf-8"))
        bundle_checkout_url = saved_cfg.get("bundle_checkout_url") or bundle_checkout_url

    state = json.loads(state_path.read_text(encoding="utf-8"))
    products = collect_products(state, Path(args.projects_dir))

    html_path = hub_dir / "index.html"
    md_path = hub_dir / "MASTER_LAUNCH_PLAYBOOK.md"
    html_path.write_text(
        render_hub_html(products, for_pages=False, bundle_checkout_url=bundle_checkout_url),
        encoding="utf-8",
    )
    (hub_dir / "success.html").write_text(
        render_success_html(products, for_pages=False), encoding="utf-8"
    )
    (hub_dir / "cancel.html").write_text(render_cancel_html(), encoding="utf-8")
    md_path.write_text(render_playbook_md(products), encoding="utf-8")

    docs_dir = Path(args.docs_dir)
    publish_docs_site(products, docs_dir, bundle_checkout_url)

    print(
        f"Built portfolio hub & GitHub Pages site for {len(products)} product(s) "
        f"-> {html_path}, {md_path}, & {docs_dir / 'index.html'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
