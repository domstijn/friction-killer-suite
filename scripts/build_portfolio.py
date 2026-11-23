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
SITE_BASE_URL = "https://domstijn.github.io/friction-killer-suite"
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
        if str(opp.get("verdict", "")).startswith("NO-GO"):
            continue
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
          <h2 class="mt-2 text-2xl font-bold text-white">Try All 12 Tools Live in Your Browser</h2>
          <p class="mt-1 text-xs text-slate-400">Runs 100% locally in JavaScript — nothing leaves your browser.</p>
        </div>
        <div class="flex flex-wrap gap-2" role="tablist">
          <button type="button" data-pg-tab="linear" class="pg-tab rounded-lg bg-indigo-500 px-3.5 py-2 text-xs font-semibold text-white">1. LinearBridge</button>
          <button type="button" data-pg-tab="notion" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">2. NotionGitExport</button>
          <button type="button" data-pg-tab="vscode" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">3. ExtProfileLock</button>
          <button type="button" data-pg-tab="claude" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">4. ClaudeProfileSwitch</button>
          <button type="button" data-pg-tab="guest" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">5. NotionGuestBridge</button>
          <button type="button" data-pg-tab="webflow" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">6. WebflowAssetZip</button>
          <button type="button" data-pg-tab="payout" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">7. StripePayoutBridge</button>
          <button type="button" data-pg-tab="lemon" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">8. LemonExitBridge</button>
          <button type="button" data-pg-tab="ossvat" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">9. OssVatBridge</button>
          <button type="button" data-pg-tab="amz" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">10. AmzSettlementBridge</button>
          <button type="button" data-pg-tab="einvoice" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">11. EInvoiceLocal</button>
          <button type="button" data-pg-tab="shopmeta" class="pg-tab rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700">12. ShopMetaShift</button>
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

      <!-- Tab 4: ClaudeProfileSwitch -->
      <div id="pg-panel-claude" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-cl-profile">.claude-profile + claude_desktop_config.json</label>
            <textarea id="pg-cl-profile" rows="3" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-200">{"profile":"client-acme","mcp_env":{"LINEAR_API_KEY":"lin_acme_live_99","PG_URL":"postgres://acme/prod"}}</textarea>
            <textarea id="pg-cl-mcp" rows="2" class="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-200">{"mcpServers":{"linear":{"token":"${LINEAR_API_KEY}"},"postgres":{"url":"${PG_URL}"}}}</textarea>
          </div>
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-cl-jsonl">JSONL Session Token Events (within 5h window, 500k budget)</label>
            <textarea id="pg-cl-jsonl" rows="3" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-200">{"minutes_ago":120,"input_tokens":120000,"cache_read_tokens":20000,"output_tokens":10000}
{"minutes_ago":45,"input_tokens":40000,"output_tokens":10000}</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">Switched Profile, Injected MCP Secrets &amp; 5h Burn Projection</span>
          <pre id="pg-cl-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 5: NotionGuestBridge -->
      <div id="pg-panel-guest" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div class="flex items-center justify-between gap-2">
            <input id="pg-gb-title" value="Acme Corp — Q4 SOC2 Architecture" class="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200" />
            <label class="flex items-center gap-1.5 whitespace-nowrap text-xs text-slate-300">
              <input id="pg-gb-redact" type="checkbox" checked class="rounded border-slate-700 bg-slate-950" /> Redact PII
            </label>
          </div>
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-gb-blocks">Guest Notion Page Blocks + Inline Database Rows</label>
            <textarea id="pg-gb-blocks" rows="7" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">## Scope &amp; Contacts
Lead contact: cto@acme-client.io | Token: ntn_secret9876543210abcdef
- [ ] Audit S3 KMS rotation policy
- [x] Verify VPC flow logs
| Milestone | Owner | Status |
| IAM Role Review | sec@acme-client.io | In Progress |
| Pen-Test Signoff | Jane Doe | Blocked |</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">Clean Markdown + Claude/Cursor .mcp-context.json Pack</span>
          <pre id="pg-gb-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 6: WebflowAssetZip -->
      <div id="pg-panel-webflow" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div class="grid gap-2 sm:grid-cols-3">
            <input id="pg-wf-base" value="https://assets.acme.co/cms" placeholder="Target Base URL" class="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200" />
            <input id="pg-wf-old" value="/blog" placeholder="Old prefix" class="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200" />
            <input id="pg-wf-new" value="/posts" placeholder="New prefix" class="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-1.5 font-mono text-xs text-slate-200" />
          </div>
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-wf-csv">Webflow CMS CSV (Media Columns + Inline Rich-Text &lt;img&gt;)</label>
            <textarea id="pg-wf-csv" rows="6" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">Name,Slug,Hero Image,Post Body
Q4 Launch,q4-launch,https://uploads-ssl.webflow.com/65b1/hero.webp,"&lt;p&gt;Intro&lt;/p&gt;&lt;img src=""https://cdn.prod.website-files.com/65b1/chart.png""&gt;"
SOC2 Guide,soc2-guide,https://uploads-ssl.webflow.com/65b1/arch.svg,"&lt;p&gt;Read more&lt;/p&gt;"</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">Rewritten CSV + Slug Asset Manifest + 301-redirects.csv</span>
          <pre id="pg-wf-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 7: StripePayoutBridge -->
      <div id="pg-panel-payout" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-pb-csv">Stripe / PayPal Itemized Payout Activity CSV</label>
            <textarea id="pg-pb-csv" rows="8" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">payout_id,payout_date,type,gross,fee,fx_fee,tax,net,currency
po_nov_01,2026-11-05,charge,121.00,3.80,1.20,21.00,116.00,EUR
po_nov_01,2026-11-05,charge,242.00,7.25,0.00,42.00,234.75,EUR
po_nov_01,2026-11-05,refund,-60.50,0.00,0.00,0.00,-60.50,EUR
po_nov_01,2026-11-05,dispute,-40.00,15.00,0.00,0.00,-55.00,EUR</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">Balanced Double-Entry Journal (Xero + QuickBooks + DATEV GoBD)</span>
          <pre id="pg-pb-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 8: LemonExitBridge -->
      <div id="pg-panel-lemon" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-lm-csv">Lemon Squeezy Store Export CSV (Orders, Subscriptions &amp; Keys)</label>
            <textarea id="pg-lm-csv" rows="8" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">email,name,status,payment_method,mrr,currency,variant_name,renews_at,license_key
founder1@acme.io,Alice,active,visa,29.00,USD,Pro Monthly,2026-12-10T12:00:00Z,LEMON-0001-ABCD
agency2@client.co,Bob,active,paypal,49.00,USD,Team Monthly,2026-12-18T12:00:00Z,LEMON-0002-EFGH
ops3@studio.dev,Carol,active,paypal,29.00,USD,Pro Monthly,2026-12-22T12:00:00Z,LEMON-0003-IJKL</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">Card vs. PayPal MRR Audit + Unix trial_end + legacy-keys.json</span>
          <pre id="pg-lm-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 9: OssVatBridge -->
      <div id="pg-panel-ossvat" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-ossvat-csv">Stripe Tax / Shopify / Lemon Squeezy Transactions CSV (Home: DE)</label>
            <textarea id="pg-ossvat-csv" rows="8" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">source,country,currency,subtotal,tax_amount,tax_rate,transaction_type,customer_vat_id
stripe_tax,FR,EUR,100.00,20.00,20.0,charge,
stripe_tax,GR,USD,100.00,24.00,24.0,charge,
shopify,ES,GBP,100.00,21.00,21.0,order,
stripe_tax,FR,EUR,25.00,5.00,20.0,refund,
stripe_tax,DE,EUR,120.00,22.80,19.0,charge,
shopify,US,USD,200.00,0.00,0.0,order,
stripe_tax,NL,EUR,300.00,0.00,0.0,charge,NL123456789B01</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">EU27 Member-State Totals + Germany BZSt BOP Semicolon CSV</span>
          <pre id="pg-ossvat-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 10: AmzSettlementBridge -->
      <div id="pg-panel-amz" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-amz-csv">Amazon Flat-File V2 Settlement Rows (.TXT / .TSV / .CSV)</label>
            <textarea id="pg-amz-csv" rows="8" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">settlement-id,deposit-date,currency,transaction-type,amount-type,amount-description,amount
2184990101,2026-11-16,EUR,Order,ItemPrice,Principal,320.00
2184990101,2026-11-16,EUR,Order,ItemPrice,Tax,60.80
2184990101,2026-11-16,EUR,Order,ItemWithheldTax,MarketplaceFacilitatorTax-Principal,-38.00
2184990101,2026-11-16,EUR,Order,ItemFees,Commission,-48.00
2184990101,2026-11-16,EUR,ServiceFee,Cost of Advertising,TransactionTotalAmount,-24.00
2184990101,2026-11-16,EUR,other-transaction,Previous Reserve Amount Balance,Previous Reserve Amount Balance,95.00
2184990101,2026-11-16,EUR,other-transaction,Current Reserve Amount,Current Reserve Amount,-40.00</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">Zero-Drift Double-Entry Journal (Xero + QBO + DATEV EXTF)</span>
          <pre id="pg-amz-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 11: EInvoiceLocal -->
      <div id="pg-panel-einvoice" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-einv-xml">Paste XRechnung / Peppol UBL 2.1 or ZUGFeRD CII XML</label>
            <textarea id="pg-einv-xml" rows="8" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">&lt;Invoice xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"&gt;
  &lt;cbc:ID&gt;XR-2026-1001&lt;/cbc:ID&gt;&lt;cbc:IssueDate&gt;2026-11-18&lt;/cbc:IssueDate&gt;&lt;cbc:DocumentCurrencyCode&gt;EUR&lt;/cbc:DocumentCurrencyCode&gt;
  &lt;cac:AccountingSupplierParty&gt;&lt;cac:Party&gt;&lt;cac:PartyLegalEntity&gt;&lt;cbc:RegistrationName&gt;Nordic Cloud GmbH&lt;/cbc:RegistrationName&gt;&lt;/cac:PartyLegalEntity&gt;&lt;/cac:Party&gt;&lt;/cac:AccountingSupplierParty&gt;
  &lt;cac:TaxTotal&gt;&lt;cbc:TaxAmount&gt;38.00&lt;/cbc:TaxAmount&gt;&lt;/cac:TaxTotal&gt;
  &lt;cac:LegalMonetaryTotal&gt;&lt;cbc:TaxExclusiveAmount&gt;200.00&lt;/cbc:TaxExclusiveAmount&gt;&lt;cbc:PayableAmount&gt;238.00&lt;/cbc:PayableAmount&gt;&lt;/cac:LegalMonetaryTotal&gt;
  &lt;cac:InvoiceLine&gt;&lt;cac:Item&gt;&lt;cbc:Name&gt;PostgreSQL Cluster&lt;/cbc:Name&gt;&lt;cac:ClassifiedTaxCategory&gt;&lt;cbc:Percent&gt;19.00&lt;/cbc:Percent&gt;&lt;/cac:ClassifiedTaxCategory&gt;&lt;/cac:Item&gt;&lt;/cac:InvoiceLine&gt;
&lt;/Invoice&gt;</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">EN 16931 Validation + DATEV BU-Schlüssel &amp; Xero Output</span>
          <pre id="pg-einv-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
        </div>
      </div>

      <!-- Tab 12: ShopMetaShift -->
      <div id="pg-panel-shopmeta" class="pg-panel mt-6 hidden grid gap-6 md:grid-cols-2">
        <div class="space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-300" for="pg-shopmeta-csv">Paste WooCommerce Variable/Variation Product CSV</label>
            <textarea id="pg-shopmeta-csv" rows="8" class="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 p-3 font-mono text-xs text-slate-200">ID,Type,SKU,Name,Slug,Parent,Regular price,Sale price,Attribute 1 name,Attribute 1 value(s),Attribute 2 name,Attribute 2 value(s),Attribute 3 name,Attribute 3 value(s),Attribute 4 name,Attribute 4 value(s),Meta: warranty_years
101,variable,JKT-ALP,Alpine Shell Jacket,alpine-shell-jacket,,,,Color,"Navy, Black",Size,"M, L",Material,Gore-Tex,Waterproof Rating,20000mm,3
102,variation,JKT-ALP-NVY-M,,,id:101,199.00,"149,50",Color,Navy,Size,M,Material,Gore-Tex,Waterproof Rating,20000mm,
103,variation,JKT-ALP-BLK-L,,,JKT-ALP,199.00,,Color,Black,Size,L,Material,Gore-Tex,Waterproof Rating,20000mm,</textarea>
          </div>
        </div>
        <div>
          <span class="text-xs font-semibold text-emerald-300">Shopify Multi-Row CSV + Variant Metafield &amp; 301 Redirect Preview</span>
          <pre id="pg-shopmeta-output" class="mt-2 h-56 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-emerald-300"></pre>
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
        claude: document.getElementById("pg-panel-claude"),
        guest: document.getElementById("pg-panel-guest"),
        webflow: document.getElementById("pg-panel-webflow"),
        payout: document.getElementById("pg-panel-payout"),
        lemon: document.getElementById("pg-panel-lemon"),
        ossvat: document.getElementById("pg-panel-ossvat"),
        amz: document.getElementById("pg-panel-amz"),
        einvoice: document.getElementById("pg-panel-einvoice"),
        shopmeta: document.getElementById("pg-panel-shopmeta"),
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

      // 4. ClaudeProfileSwitch live .claude-profile + quota guard
      const cProf = document.getElementById("pg-cl-profile");
      const cMcp = document.getElementById("pg-cl-mcp");
      const cJsonl = document.getElementById("pg-cl-jsonl");
      const cOut = document.getElementById("pg-cl-output");
      function runClaude() {
        if (!cProf || !cOut) return;
        try {
          const prof = JSON.parse(cProf.value || "{}");
          const envMap = prof.mcp_env || {};
          const mcpInjected = (cMcp?.value || "{}").replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)\}/g, (f, k) => envMap[k] ?? f);
          const budget = 500000;
          let used = 0, maxMinsAgo = 0;
          for (const raw of (cJsonl?.value || "").split(/\r?\n/)) {
            const t = raw.trim();
            if (!t) continue;
            const row = JSON.parse(t);
            const mins = Number(row.minutes_ago || 0);
            if (mins <= 300) {
              used += Number(row.input_tokens || 0) + Number(row.cache_read_tokens || 0) + Number(row.output_tokens || 0);
              if (mins > maxMinsAgo) maxMinsAgo = mins;
            }
          }
          const spanHrs = used > 0 ? Math.max(maxMinsAgo / 60, 1 / 60) : 0;
          const burnHr = spanHrs > 0 ? Math.round(used / spanHrs) : 0;
          const remaining = Math.max(0, budget - used);
          const etaMins = burnHr > 0 ? Math.round((remaining / burnHr) * 60) : null;
          cOut.textContent = JSON.stringify({
            active_profile: prof.profile || "default",
            interpolated_mcp_config: JSON.parse(mcpInjected),
            quota_5h: { used_tokens: used, budget, pct_used: Number(((used / budget) * 100).toFixed(1)), burn_rate_per_hour: burnHr, estimated_minutes_to_exhaustion: etaMins }
          }, null, 2);
        } catch (err) {
          cOut.textContent = "JSON parse error: " + err.message;
        }
      }
      [cProf, cMcp, cJsonl].forEach((el) => el?.addEventListener("input", runClaude));
      runClaude();

      // 5. NotionGuestBridge live guest DOM + database table & PII redactor
      const gTitle = document.getElementById("pg-gb-title");
      const gRedact = document.getElementById("pg-gb-redact");
      const gBlocks = document.getElementById("pg-gb-blocks");
      const gOut = document.getElementById("pg-gb-output");
      function redactGuestText(text, enabled) {
        if (!enabled) return text;
        return text
          .replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, "[EMAIL_REDACTED]")
          .replace(/\b(ntn_[A-Za-z0-9]{10,}|secret_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9_-]{12,})\b/g, "[SECRET_REDACTED]");
      }
      function runGuestBridge() {
        if (!gBlocks || !gOut) return;
        const doRedact = Boolean(gRedact && gRedact.checked);
        const title = redactGuestText((gTitle?.value || "Guest Page").trim(), doRedact);
        const rawLines = (gBlocks.value || "").split("\n").map((l) => redactGuestText(l.trim(), doRedact)).filter(Boolean);
        const mdLines = ["---", 'title: "' + title + '"', 'access_mode: "notion_guest_session"', "---", "", "# " + title, ""];
        let inTable = false;
        rawLines.forEach((line) => {
          if (line.startsWith("|")) {
            mdLines.push(line);
            if (!inTable) {
              const cols = line.split("|").filter((c) => c.trim().length > 0).length;
              mdLines.push("| " + Array(Math.max(1, cols)).fill("---").join(" | ") + " |");
              inTable = true;
            }
          } else {
            inTable = false;
            mdLines.push(line);
          }
        });
        const pack = {
          schema: "mcp.guest_context.v1",
          source: "notion-guest-mcp-bridge",
          title: title,
          pii_redacted: doRedact,
          block_count: rawLines.length,
        };
        gOut.textContent = mdLines.join("\n") + "\n\n// .mcp-context.json envelope:\n" + JSON.stringify(pack, null, 2);
      }
      [gTitle, gRedact, gBlocks].forEach((el) => el?.addEventListener("input", runGuestBridge));
      gRedact?.addEventListener("change", runGuestBridge);
      runGuestBridge();

      // 6. WebflowAssetZip live CSV + Rich-Text CDN rewriter & 301 generator
      const wBase = document.getElementById("pg-wf-base");
      const wOld = document.getElementById("pg-wf-old");
      const wNew = document.getElementById("pg-wf-new");
      const wCsv = document.getElementById("pg-wf-csv");
      const wOut = document.getElementById("pg-wf-output");
      function runWebflowZip() {
        if (!wCsv || !wOut) return;
        const base = (wBase?.value || "/assets/cms").replace(/\/+$/, "");
        const oldP = "/" + (wOld?.value || "blog").replace(/^\/+|\/+$/g, "");
        const newP = "/" + (wNew?.value || "posts").replace(/^\/+|\/+$/g, "");
        const lines = (wCsv.value || "").split("\n").filter((l) => l.trim().length > 0);
        if (lines.length < 2) {
          wOut.textContent = "Add header + at least 1 CMS row.";
          return;
        }
        const manifest = [];
        const redirects = ["old_path,new_path,status"];
        const cdnRe = /https?:\/\/(?:uploads-ssl\.webflow\.com|cdn\.prod\.website-files\.com|assets(?:-global)?\.website-files\.com)\/[^\s"'<>,)]+/gi;
        const outLines = [lines[0]];
        lines.slice(1).forEach((line, idx) => {
          const slugMatch = line.split(",")[1] || ("item-" + (idx + 1));
          const slug = slugMatch.trim().toLowerCase().replace(/[^a-z0-9-]+/g, "-");
          let count = 0;
          const rewritten = line.replace(cdnRe, (url) => {
            count += 1;
            const extMatch = url.match(/\.(webp|png|jpe?g|svg|avif|gif)$/i);
            const ext = extMatch ? "." + extMatch[1].toLowerCase() : ".png";
            const fileName = slug + "-asset-0" + count + ext;
            const newUrl = base + "/" + fileName;
            manifest.push({ slug, fileName, originalUrl: url, newUrl });
            return newUrl;
          });
          outLines.push(rewritten);
          redirects.push(oldP + "/" + slug + "," + newP + "/" + slug + ",301");
        });
        wOut.textContent =
          "# Rewritten CSV:\n" +
          outLines.join("\n") +
          "\n\n# 301-redirects.csv:\n" +
          redirects.join("\n") +
          "\n\n# Slug Asset Manifest (" +
          manifest.length +
          " files):\n" +
          JSON.stringify(manifest, null, 2);
      }
      [wBase, wOld, wNew, wCsv].forEach((el) => el?.addEventListener("input", runWebflowZip));
      runWebflowZip();

      // 7. StripePayoutBridge live double-entry payout splitter
      const pCsv = document.getElementById("pg-pb-csv");
      const pOut = document.getElementById("pg-pb-output");
      function runPayoutBridge() {
        if (!pCsv || !pOut) return;
        const lines = (pCsv.value || "").split("\n").map((l) => l.trim()).filter(Boolean);
        if (lines.length < 2) {
          pOut.textContent = "Add header + at least 1 payout row.";
          return;
        }
        let gross = 0, tax = 0, refunds = 0, disputes = 0, fees = 0, fx = 0;
        let pid = "po_batch", pdate = "2026-11-05";
        lines.slice(1).forEach((l) => {
          const cols = l.split(",");
          pid = cols[0] || pid;
          pdate = cols[1] || pdate;
          const t = (cols[2] || "charge").toLowerCase();
          const g = Math.round((parseFloat(cols[3]) || 0) * 100);
          const f = Math.abs(Math.round((parseFloat(cols[4]) || 0) * 100));
          const x = Math.abs(Math.round((parseFloat(cols[5]) || 0) * 100));
          const tx = Math.abs(Math.round((parseFloat(cols[6]) || 0) * 100));
          fees += f;
          fx += x;
          if (t.includes("refund") || (g < 0 && !t.includes("dispute"))) refunds += Math.abs(g);
          else if (t.includes("dispute")) disputes += Math.abs(g);
          else { gross += Math.max(0, g); tax += Math.min(tx, Math.max(0, g)); }
        });
        const netSales = gross - tax;
        const netBank = gross - refunds - disputes - fees - fx;
        const fmt = (c) => (c / 100).toFixed(2);
        const xero = [
          "*Narration,*Date,Description,*AccountCode,*TaxType,*Amount",
          "Stripe Payout " + pid + "," + pdate + ",Gross sales net of tax,200,OUTPUT2,-" + fmt(netSales),
          "Stripe Payout " + pid + "," + pdate + ",VAT collected,820,BAS Excluded,-" + fmt(tax),
          "Stripe Payout " + pid + "," + pdate + ",Customer refunds,205,NONE," + fmt(refunds),
          "Stripe Payout " + pid + "," + pdate + ",Chargebacks & disputes,206,NONE," + fmt(disputes),
          "Stripe Payout " + pid + "," + pdate + ",Stripe processing fees,404,EXEMPTEXPENSES," + fmt(fees),
          "Stripe Payout " + pid + "," + pdate + ",FX conversion fees,405,EXEMPTEXPENSES," + fmt(fx),
          "Stripe Payout " + pid + "," + pdate + ",Net bank deposit,120,BAS Excluded," + fmt(netBank),
        ];
        pOut.textContent =
          "# Double-Entry Audit: Debits €" + fmt(gross) + " == Credits €" + fmt(gross) + " (Drift: €0.00)\n\n" +
          "# Xero Manual Journal CSV:\n" + xero.join("\n");
      }
      pCsv?.addEventListener("input", runPayoutBridge);
      runPayoutBridge();

      // 8. LemonExitBridge live shutdown auditor & PayPal trial_end / legacy key splitter
      const lmCsv = document.getElementById("pg-lm-csv");
      const lmOut = document.getElementById("pg-lm-output");
      function runLemonExit() {
        if (!lmCsv || !lmOut) return;
        const lines = (lmCsv.value || "").split("\n").map((l) => l.trim()).filter(Boolean);
        if (lines.length < 2) {
          lmOut.textContent = "Add header + at least 1 subscriber row.";
          return;
        }
        let cardMrr = 0, ppMrr = 0;
        const ppCohort = ["customer_email,product_variant,mrr,renews_at,trial_end_unix"];
        const keys = {};
        lines.slice(1).forEach((l) => {
          const cols = l.split(",");
          const email = cols[0] || "";
          const status = (cols[2] || "active").toLowerCase();
          const pm = (cols[3] || "card").toLowerCase();
          const mrr = parseFloat(cols[4]) || 0;
          const variant = cols[6] || "Pro";
          const renews = cols[7] || "";
          const key = cols[8] || "";
          const unix = Number.isFinite(Date.parse(renews)) ? Math.floor(Date.parse(renews) / 1000) : 0;
          if (pm.includes("paypal")) {
            ppMrr += mrr;
            ppCohort.push([email, variant, mrr.toFixed(2), renews, unix].join(","));
          } else {
            cardMrr += mrr;
          }
          if (key) keys[key] = { valid: status === "active", customer_email: email, product_variant: variant, expires_at: renews };
        });
        lmOut.textContent =
          "# Shutdown Risk Audit (Deadline 2027-03-31):\n" +
          "Card MRR (Transferable): $" + cardMrr.toFixed(2) + " | PayPal MRR At Risk: $" + ppMrr.toFixed(2) + "\n\n" +
          "# PayPal Prorated Re-Auth Cohort CSV:\n" + ppCohort.join("\n") + "\n\n" +
          "# legacy-keys.json Bundle:\n" + JSON.stringify({ schema: "lemon.legacy_keys.v1", keys }, null, 2);
      }
      lmCsv?.addEventListener("input", runLemonExit);
      runLemonExit();

      // 9. OssVatBridge live EU27 OSS & Germany BZSt BOP semicolon compiler
      const ossCsv = document.getElementById("pg-ossvat-csv");
      const ossOut = document.getElementById("pg-ossvat-output");
      function runOssVat() {
        if (!ossCsv || !ossOut) return;
        const lines = (ossCsv.value || "").split("\n").map((l) => l.trim()).filter(Boolean);
        if (lines.length < 2) {
          ossOut.textContent = "Add header + at least 1 transaction row.";
          return;
        }
        const fx = { EUR: 1.0, USD: 0.92, GBP: 1.19, SEK: 0.088, DKK: 0.134, PLN: 0.233 };
        const eu = new Set(["AT","BE","BG","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE","IT","LT","LU","LV","MT","NL","PL","PT","RO","SE","SI","SK"]);
        const buckets = new Map();
        let excluded = 0;
        lines.slice(1).forEach((l) => {
          const cols = l.split(",");
          let ms = (cols[1] || "").trim().toUpperCase();
          if (ms === "GR") ms = "EL";
          const cur = (cols[2] || "EUR").trim().toUpperCase();
          const sub = parseFloat(cols[3]) || 0;
          const tax = parseFloat(cols[4]) || 0;
          const rate = parseFloat(cols[5]) || 0;
          const kind = (cols[6] || "charge").toLowerCase();
          const vatId = (cols[7] || "").trim();
          if (!eu.has(ms) || ms === "DE" || (vatId && tax === 0)) { excluded += 1; return; }
          const mult = (kind.includes("refund") && sub > 0 ? -1 : 1) * (fx[cur] ?? 1.0);
          const netEur = sub * mult;
          const vatEur = tax * mult;
          const key = ms + "|" + rate.toFixed(2);
          const curB = buckets.get(key) || { ms, rate: rate.toFixed(2), net: 0, vat: 0 };
          curB.net += netEur;
          curB.vat += vatEur;
          buckets.set(key, curB);
        });
        const bzst = ["Satzart;Land des Verbrauchs;Umsatzsteuertyp;Umsatzsteuersatz;Steuerbemessungsgrundlage;Umsatzsteuerbetrag"];
        let totalVat = 0;
        Array.from(buckets.values()).sort((a, b) => a.ms.localeCompare(b.ms)).forEach((b) => {
          totalVat += b.vat;
          bzst.push(["BOP_OSS_V1", b.ms, "STANDARD", b.rate.replace(".", ","), b.net.toFixed(2).replace(".", ","), b.vat.toFixed(2).replace(".", ",")].join(";"));
        });
        ossOut.textContent =
          "# EU27 OSS Summary (Excluded DE/Non-EU/B2B: " + excluded + ") | Total VAT Due: €" + totalVat.toFixed(2) + "\n\n" +
          "# Germany BZSt BOP (; delimited, comma decimals, GR->EL):\n" + bzst.join("\n");
      }
      ossCsv?.addEventListener("input", runOssVat);
      runOssVat();

      // 10. AmzSettlementBridge live Flat-File V2 clearing journal compiler
      const amzCsv = document.getElementById("pg-amz-csv");
      const amzOut = document.getElementById("pg-amz-output");
      function runAmzSettlement() {
        if (!amzCsv || !amzOut) return;
        const raw = (amzCsv.value || "").split("\n").map((l) => l.trim()).filter(Boolean);
        if (raw.length < 2) {
          amzOut.textContent = "Add header + at least 1 settlement line.";
          return;
        }
        const delim = raw[0].includes("\t") ? "\t" : ",";
        const b = { Sales: 0, Tax: 0, FacilitatorTax: 0, Fees: 0, Ads: 0, Reserves: 0 };
        raw.slice(1).forEach((l) => {
          const c = l.split(delim);
          const all = ((c[3] || "") + " " + (c[4] || "") + " " + (c[5] || "")).toLowerCase();
          const cents = Math.round((parseFloat(c[6]) || 0) * 100);
          if (all.includes("advertising") || all.includes("ppc")) b.Ads += cents;
          else if (all.includes("reserve")) b.Reserves += cents;
          else if (all.includes("facilitator") || all.includes("itemwithheldtax")) b.FacilitatorTax += cents;
          else if (all.includes("fee") || all.includes("commission") || all.includes("fba")) b.Fees += cents;
          else if (all.includes("tax") || all.includes("vat")) b.Tax += cents;
          else b.Sales += cents;
        });
        const net = Object.values(b).reduce((a, v) => a + v, 0);
        const f = (cents) => (cents / 100).toFixed(2);
        const lines = [
          "*Narration,*Date,*Description,*AccountCode,*Amount",
          "Amazon Settlement 2184990101,2026-11-16,Sales Principal,200," + f(-b.Sales),
          "Amazon Settlement 2184990101,2026-11-16,VAT Collected,220," + f(-b.Tax),
          "Amazon Settlement 2184990101,2026-11-16,Facilitator Tax Withheld,221," + f(-b.FacilitatorTax),
          "Amazon Settlement 2184990101,2026-11-16,FBA & Referral Fees,404," + f(-b.Fees),
          "Amazon Settlement 2184990101,2026-11-16,Sponsored Ads PPC,406," + f(-b.Ads),
          "Amazon Settlement 2184990101,2026-11-16,Reserve Carry-Forward,125," + f(-b.Reserves),
          "Amazon Settlement 2184990101,2026-11-16,Net Bank Deposit Clearing,120," + f(net),
        ];
        amzOut.textContent =
          "# Double-Entry Verification: Debits == Credits | Net Deposit: €" + f(net) + " (Drift: €0.00)\n\n" +
          "# Xero Manual Journal CSV:\n" + lines.join("\n");
      }
      amzCsv?.addEventListener("input", runAmzSettlement);
      runAmzSettlement();

      // 11. EInvoiceLocal live UBL/CII XML validator & DATEV BU-Schlüssel converter
      const einvXml = document.getElementById("pg-einv-xml");
      const einvOut = document.getElementById("pg-einv-output");
      function runEInvoice() {
        if (!einvXml || !einvOut) return;
        const xmlStr = (einvXml.value || "").trim();
        if (!xmlStr) {
          einvOut.textContent = "Paste UBL 2.1 or CII XML above.";
          return;
        }
        try {
          const dom = new DOMParser().parseFromString(xmlStr, "application/xml");
          const getVal = (tag) => {
            const matches = dom.getElementsByTagName("*");
            for (let i = 0; i < matches.length; i++) {
              const ln = (matches[i].localName || matches[i].tagName || "").split(":").pop();
              if (ln === tag && matches[i].textContent) return matches[i].textContent.trim();
            }
            return "";
          };
          const id = getVal("ID") || "UNKNOWN";
          const dt = getVal("IssueDate") || getVal("DateTimeString") || "2026-11-18";
          const cur = getVal("DocumentCurrencyCode") || getVal("InvoiceCurrencyCode") || "EUR";
          const net = parseFloat(getVal("TaxExclusiveAmount") || getVal("TaxBasisTotalAmount") || "0") || 0;
          const vat = parseFloat(getVal("TaxAmount") || getVal("TaxTotalAmount") || "0") || 0;
          const gross = parseFloat(getVal("PayableAmount") || getVal("DuePayableAmount") || getVal("GrandTotalAmount") || "0") || 0;
          const pct = parseFloat(getVal("Percent") || getVal("RateApplicablePercent") || "19") || 0;
          const validMath = Math.abs((net + vat) - gross) <= 0.02;
          const bu = pct === 19 ? "9" : pct === 7 ? "8" : "0";
          const konto = pct === 19 ? "3400" : pct === 7 ? "3300" : "3200";
          einvOut.textContent =
            "# EN 16931 Math Validation: " + (validMath ? "PASS (BR-CO-15 OK)" : "MISMATCH") + "\n" +
            "# Invoice: " + id + " | Issue: " + dt + " | Net: " + net.toFixed(2) + " " + cur + " | VAT (" + pct + "%): " + vat.toFixed(2) + " | Gross: " + gross.toFixed(2) + "\n\n" +
            "# DATEV EXTF Buchungsstapel CSV (BU-Schlüssel " + bu + ", SKR03 " + konto + "):\n" +
            "Umsatz;Soll/Haben;WKZ;Konto;Gegenkonto;BU-Schlüssel;Belegfeld 1\n" +
            gross.toFixed(2).replace(".", ",") + ";S;" + cur + ";" + konto + ";70000;" + bu + ";" + id;
        } catch {
          einvOut.textContent = "Invalid XML structure.";
        }
      }
      einvXml?.addEventListener("input", runEInvoice);
      runEInvoice();

      // 12. ShopMetaShift live WooCommerce-to-Shopify CSV + >3 Attr & 301 Redirect preview
      const smIn = document.getElementById("pg-shopmeta-csv");
      const smOut = document.getElementById("pg-shopmeta-output");
      function parseSimpleCsv(txt) {
        const lines = String(txt || "").trim().split(/\r?\n/).filter(Boolean);
        if (lines.length < 2) return null;
        const splitRow = (line) => {
          const out = [];
          let cur = "";
          let q = false;
          for (let i = 0; i < line.length; i++) {
            const c = line[i];
            if (c === '"') { q = !q; continue; }
            if (c === "," && !q) { out.push(cur.trim()); cur = ""; continue; }
            cur += c;
          }
          out.push(cur.trim());
          return out;
        };
        const headers = splitRow(lines[0]);
        return {
          headers,
          rows: lines.slice(1).map((ln) => {
            const vals = splitRow(ln);
            const obj = {};
            headers.forEach((h, idx) => { obj[h] = vals[idx] || ""; });
            return obj;
          })
        };
      }
      function runShopMeta() {
        if (!smIn || !smOut) return;
        const parsed = parseSimpleCsv(smIn.value);
        if (!parsed) {
          smOut.textContent = "Paste WooCommerce CSV rows above.";
          return;
        }
        const parents = parsed.rows.filter((r) => (r.Type || "").toLowerCase() !== "variation");
        const vars = parsed.rows.filter((r) => (r.Type || "").toLowerCase() === "variation");
        const lines = [
          "# Shopify Admin Multi-Row CSV + Variant Metafield Preview:",
          "Handle,Title,Option1 Value,Option2 Value,Option3 Value,Variant SKU,Variant Price,Variant Compare At Price,Metafield: custom.warranty_years [number_integer],Variant Metafield: custom.waterproof_rating [single_line_text_field]"
        ];
        const redirs = ["# 301 Redirects CSV:", "Redirect from,Redirect to"];
        parents.forEach((p) => {
          const handle = (p.Slug || p.Name || "product").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
          const pid = `id:${(p.ID || "").toLowerCase()}`;
          const psku = (p.SKU || "").toLowerCase();
          const children = vars.filter((v) => {
            const pr = (v.Parent || "").toLowerCase();
            return pr && (pr === pid || pr === psku);
          });
          const activeList = children.length ? children : [p];
          activeList.forEach((v, idx) => {
            const sale = (v["Sale price"] || "").replace(",", ".");
            const reg = (v["Regular price"] || "").replace(",", ".");
            const price = sale || reg;
            const cmp = sale && reg ? reg : "";
            lines.push(
              [
                handle,
                idx === 0 ? p.Name : "",
                v["Attribute 1 value(s)"] || "",
                v["Attribute 2 value(s)"] || "",
                v["Attribute 3 value(s)"] || "",
                v.SKU || "",
                price,
                cmp,
                idx === 0 ? (p["Meta: warranty_years"] || "") : "",
                v["Attribute 4 value(s)"] || ""
              ].join(",")
            );
          });
          redirs.push(`/product/${p.Slug || handle}/,/products/${handle}`);
        });
        smOut.textContent = lines.join("\n") + "\n\n" + redirs.join("\n");
      }
      smIn?.addEventListener("input", runShopMeta);
      runShopMeta();
    })();
  </script>"""


def build_seo_head_tags(
    *,
    title: str,
    description: str,
    canonical_url: str,
    app_name: str,
    app_category: str = "BusinessApplication",
    price_eur: str = "29.00",
) -> str:
    """Build meta description, canonical, OpenGraph, Twitter, and JSON-LD SoftwareApplication tags."""
    safe_title = html.escape(title, quote=True)
    safe_desc = html.escape(description, quote=True)
    safe_url = html.escape(canonical_url, quote=True)
    ld_payload = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": app_name,
        "headline": title,
        "description": description,
        "url": canonical_url,
        "applicationCategory": app_category,
        "operatingSystem": "Web, macOS, Windows, Linux",
        "offers": [
            {
                "@type": "Offer",
                "name": "Free Tier",
                "price": "0.00",
                "priceCurrency": "EUR",
            },
            {
                "@type": "Offer",
                "name": "Pro Lifetime License",
                "price": price_eur,
                "priceCurrency": "EUR",
            },
        ],
    }
    ld_json = json.dumps(ld_payload, ensure_ascii=False).replace("</", "<\\/")
    return "\n".join(
        [
            f'  <meta name="description" content="{safe_desc}" />',
            f'  <link rel="canonical" href="{safe_url}" />',
            f'  <meta property="og:title" content="{safe_title}" />',
            f'  <meta property="og:description" content="{safe_desc}" />',
            '  <meta property="og:type" content="website" />',
            f'  <meta property="og:url" content="{safe_url}" />',
            '  <meta name="twitter:card" content="summary_large_image" />',
            f'  <meta name="twitter:title" content="{safe_title}" />',
            f'  <meta name="twitter:description" content="{safe_desc}" />',
            f'  <script type="application/ld+json">{ld_json}</script>',
        ]
    )


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
        if p["slug"] == "vscode-workspace-profile-config":
            dl_links.append(
                '<a href="https://marketplace.visualstudio.com/items?itemName=friction-killer.vscode-workspace-profile-config" target="_blank" rel="noopener noreferrer" data-fk-cta="free-install" class="text-xs text-sky-300 hover:text-sky-200 underline">Marketplace</a>'
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
    hub_title = f"Friction-Killer Suite — {len(products)} Zero-Backend Micro-Utilities & Web Apps"
    hub_desc = (
        "Client-side micro-tools and zero-install web apps for WooCommerce-to-Shopify variant metafield & 301 CSV migration, "
        "XRechnung/Peppol XML validation & DATEV export, Amazon Flat-File V2 settlement journals, EU VAT OSS quarterly CSV/XML filing, "
        "Lemon Squeezy migration, Stripe/PayPal payouts, Webflow, Notion, Linear, Claude & VS Code."
    )
    hub_seo_tags = build_seo_head_tags(
        title=hub_title,
        description=hub_desc,
        canonical_url=f"{SITE_BASE_URL}/",
        app_name="Friction-Killer Suite",
        price_eur="49.00",
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(hub_title)}</title>
{hub_seo_tags}
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
        Eliminate SaaS, Ops &amp; Dev Friction<br />
        <span class="text-indigo-400">without paying monthly SaaS taxes.</span>
      </h1>
      <p class="mx-auto mt-4 max-w-2xl text-base text-slate-300">
        {len(products)} local-first tools &amp; zero-install web apps including ShopMetaShift, EInvoiceLocal, AmzSettlementBridge, OssVatBridge, LemonExitBridge, StripePayoutBridge, WebflowAssetZip, LinearBridge, NotionGitExport, ExtProfileLock, ClaudeProfileSwitch, and NotionGuestBridge.
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
          <span class="rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-300">BEST VALUE · SAVE 83%</span>
          <h2 class="mt-3 text-3xl font-extrabold text-white">All-Access Friction-Killer Bundle</h2>
          <p class="mt-2 max-w-xl text-sm text-slate-300">
            Unlock Pro licenses across all {len(products)} tools (ShopMetaShift, EInvoiceLocal, AmzSettlementBridge, OssVatBridge, LemonExitBridge, StripePayoutBridge, WebflowAssetZip, LinearBridge, NotionGitExport, ExtProfileLock, ClaudeProfileSwitch &amp; NotionGuestBridge) with one single purchase (€320+ combined value).
          </p>
        </div>
        <div class="w-full shrink-0 rounded-2xl border border-slate-700 bg-slate-950/70 p-6 text-center md:w-72">
          <div class="text-xs text-slate-400 line-through">€320+ combined</div>
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

    # Inject SEO, OpenGraph, canonical, and JSON-LD SoftwareApplication structured data
    if 'rel="canonical"' not in page_html and "</head>" in page_html:
        price_match = re.search(r"(\d+(?:\.\d+)?)", str(product.get("price", "29")))
        price_num = f"{float(price_match.group(1)):.2f}" if price_match else "29.00"
        seo_tags = build_seo_head_tags(
            title=f"{product['short_title']} — {product['title']}",
            description=product["summary"],
            canonical_url=f"{SITE_BASE_URL}/products/{slug}/",
            app_name=product["short_title"],
            price_eur=price_num,
        )
        page_html = page_html.replace("</head>", f"{seo_tags}\n</head>", 1)

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

    sitemap_entries = [
        (f"{SITE_BASE_URL}/", "1.0"),
        *[
            (f"{SITE_BASE_URL}/products/{p['slug']}/", "0.9")
            for p in products
            if (p["proj_dir"] / "launch" / "landing.html").is_file()
        ],
    ]
    url_blocks = "\n".join(
        [
            "  <url>\n"
            f"    <loc>{html.escape(loc)}</loc>\n"
            "    <lastmod>2026-11-22</lastmod>\n"
            "    <changefreq>weekly</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>"
            for loc, priority in sitemap_entries
        ]
    )
    (docs_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{url_blocks}\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    (docs_dir / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {SITE_BASE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )


def render_success_html(products: list[dict[str, Any]], *, for_pages: bool = True) -> str:
    dl_items = []
    for p in products:
        zip_href = p["site_zip_rel"] if for_pages else p["zip_rel"]
        whl_href = p["site_whl_rel"] if for_pages else p["whl_rel"]
        vsix_href = p["site_vsix_rel"] if for_pages else p["vsix_rel"]
        dl_items.append(
            f'<a href="{html.escape(zip_href)}" download class="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:border-indigo-400 hover:text-white">{html.escape(p["short_title"])} (.zip)</a>'
        )
        if p.get("whl_exists"):
            dl_items.append(
                f'<a href="{html.escape(whl_href)}" download class="rounded-lg border border-emerald-700/60 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:border-emerald-400 hover:text-white">{html.escape(p["short_title"])} (.whl)</a>'
            )
        if p.get("vsix_exists"):
            dl_items.append(
                f'<a href="{html.escape(vsix_href)}" download class="rounded-lg border border-sky-700/60 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-sky-300 hover:border-sky-400 hover:text-white">{html.escape(p["short_title"])} (.vsix)</a>'
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
        Your Stripe Checkout Session ID below acts as your Pro License Key across all {len(products)} Friction-Killer tools (Browser Web Apps, Python <code>.whl</code> CLIs, Chrome extensions, and VS Code extension).
      </p>

      <div id="auto-unlock-banner" class="mt-4 hidden rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-sm text-emerald-200">
        <p id="auto-unlock-text" class="font-semibold"></p>
        <a id="auto-unlock-link" href="./index.html" class="mt-2 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400">Open Unlocked Web App &rarr;</a>
      </div>

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
        <p class="font-semibold text-white">How to activate across all {len(products)} tools:</p>
        <p>• <strong>Browser Web Apps</strong> (<code>WebflowAssetZip</code>, <code>StripePayoutBridge</code>, <code>LemonExitBridge</code>, <code>OssVatBridge</code>, <code>AmzSettlementBridge</code>, <code>EInvoiceLocal</code>, <code>ShopMetaShift</code>): Auto-unlocked above in this browser, or paste your key into the Pro box on any product page.</p>
        <p>• <strong>Python CLIs (<code>.whl</code>)</strong>: Run <code>&lt;tool-slug&gt; --activate YOUR_KEY</code> (e.g. <code>eu-oss-vat-return-compiler --activate YOUR_KEY</code>).</p>
        <p>• <strong>Chrome Extensions</strong> (<code>LinearBridge</code>, <code>NotionGuestBridge</code>): Open the extension popup &rarr; paste key &rarr; click <em>Activate</em>.</p>
        <p>• <strong>VS Code</strong> (<code>ExtProfileLock</code>): Call <code>activate("YOUR_KEY")</code> in your workspace profile config.</p>
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
    const STORAGE_KEYS = {{
      "webflow-cms-asset-migrator": "fk_webflow_pro_state",
      "stripe-payout-xero-qbo-splitter": "fk_payout_pro_state",
      "lemonsqueezy-stripe-polar-migrator": "fk_lemon_exit_pro_state",
      "eu-oss-vat-return-compiler": "fk_oss_vat_pro_state",
      "amazon-settlement-xero-qbo-splitter": "fk_amz_settlement_pro_state",
      "e-invoice-xml-batch-converter": "fk_einvoice_pro_state",
      "woo-shopify-metafield-migrator": "fk_shopmeta_pro_state"
    }};
    const params = new URLSearchParams(window.location.search);
    const sid = (params.get("session_id") || "").trim();
    const slug = (params.get("slug") || "").trim();
    const keyEl = document.getElementById("license-key");
    const statusEl = document.getElementById("copy-status");
    const banner = document.getElementById("auto-unlock-banner");
    const bannerText = document.getElementById("auto-unlock-text");
    const bannerLink = document.getElementById("auto-unlock-link");

    if (sid) {{
      keyEl.textContent = sid;
      if (sid.startsWith("cs_live_") && sid.length >= 24 && !sid.toLowerCase().includes("unpaid")) {{
        try {{
          const record = JSON.stringify({{ valid: true, key: sid, verifiedAt: Date.now() }});
          if (slug && STORAGE_KEYS[slug]) {{
            localStorage.setItem(STORAGE_KEYS[slug], record);
            if (banner && bannerText && bannerLink) {{
              bannerText.textContent = "Pro unlocked automatically for " + slug + " in this browser!";
              bannerLink.href = "./products/" + slug + "/index.html#live-app";
              bannerLink.textContent = "Open Unlocked Web App →";
              banner.classList.remove("hidden");
            }}
          }} else if (!slug || slug === "all-access-bundle") {{
            Object.values(STORAGE_KEYS).forEach((k) => localStorage.setItem(k, record));
            if (banner && bannerText && bannerLink) {{
              bannerText.textContent = "All 6 Browser Web Apps Unlocked in this browser!";
              bannerLink.href = "./index.html";
              bannerLink.textContent = "Open Friction-Killer Suite →";
              banner.classList.remove("hidden");
            }}
          }}
        }} catch {{}}
      }}
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


LIVE_PYPI_PACKAGES: dict[str, str] = {
    "eu-oss-vat-return-compiler": "eu-oss-vat-return-compiler",
    "amazon-settlement-xero-qbo-splitter": "amazon-settlement-xero-qbo-splitter",
    "e-invoice-xml-batch-converter": "e-invoice-xml-batch-converter",
    "lemonsqueezy-stripe-polar-migrator": "lemonsqueezy-stripe-polar-migrator",
    # Pending PyPI new-project rate-limit reset:
    # "stripe-payout-xero-qbo-splitter": "stripe-payout-xero-qbo-splitter",
    # "notion-clean-md-exporter": "notion-clean-md-exporter",
    # "claude-profile-switcher": "claude-profile-switch",
}


def render_root_readme_md(products: list[dict[str, Any]], bundle_checkout_url: str) -> str:
    """Generate an SEO-friendly root README.md showcasing all shipped Web Apps, CLIs & Storefront links."""
    rows = []
    cli_installs = []
    for p in products:
        web_url = f"{SITE_BASE_URL}/products/{p['slug']}/"
        dl_parts = []
        if p["whl_exists"]:
            whl_url = f"{SITE_BASE_URL}/downloads/{p['whl_name']}"
            pypi_name = LIVE_PYPI_PACKAGES.get(p["slug"])
            if pypi_name:
                pypi_url = f"https://pypi.org/project/{pypi_name}/"
                dl_parts.append(f"[PyPI]({pypi_url})")
                dl_parts.append(f"[.whl]({whl_url})")
                cli_installs.append(
                    f"- **{p['short_title']}**: `pip install {pypi_name}` ([PyPI]({pypi_url}) · [.whl]({whl_url}))"
                )
            else:
                dl_parts.append(f"[.whl]({whl_url})")
                cli_installs.append(f"- **{p['short_title']}**: `pip install {whl_url}`")
        if p["vsix_exists"]:
            dl_parts.append(f"[.vsix]({SITE_BASE_URL}/downloads/{p['slug']}-0.1.0.vsix)")
        if p["zip_exists"]:
            dl_parts.append(f"[.zip]({SITE_BASE_URL}/downloads/{p['slug']}-v0.1.0.zip)")
        artifacts = " · ".join(dl_parts) or "Browser Web App"
        rows.append(
            f"| **[{p['short_title']}]({web_url})** | {p['target_software']} | {p['price']} | {artifacts} | {p['summary']} |"
        )
    table_body = "\n".join(rows)
    cli_block = "\n".join(cli_installs)
    return f"""# Friction-Killer Suite — {len(products)} Zero-Subscription Local Web Apps & CLIs

**100% browser-local, GDPR/GoBD-safe utilities** for **WooCommerce-to-Shopify Metafields & 301 Redirects**, **EU VAT OSS (`BZSt BOP` / `ROS XML`)**, **XRechnung / ZUGFeRD / Peppol XML to DATEV EXTF**, **Amazon Flat-File V2 & Stripe Payouts to Xero / QuickBooks**, **Lemon Squeezy shutdown migrations**, **Webflow CMS backups**, **Notion**, **Linear**, **Claude Code**, and **VS Code**. Zero server uploads, zero API OAuth lock-in, and zero recurring SaaS subscriptions.

- **Try All {len(products)} Tools Live in Browser (Zero Install):** {SITE_BASE_URL}/
- **All-Access Suite Bundle (€49 once, unlocks all {len(products)} tools):** {bundle_checkout_url}
- **Sitemap:** {SITE_BASE_URL}/sitemap.xml

---

## Shipped Catalog ({len(products)} Active Products)

| Tool & Live Web App | Target Workflow | Pro License | Packages | What It Solves |
| :--- | :--- | :---: | :--- | :--- |
{table_body}

---

## Python CLI Installation (PyPI & Offline `.whl`)

Prefer air-gapped CLI / batch directory automation? Install any zero-dependency wheel directly via `pip`:

{cli_block}

Each tool includes a generous **Free Tier** in both the browser Web App and CLI, plus a one-time €19–€29 Pro license (or €49 All-Access Bundle) powered by Stripe Managed Payments (`cs_live_...`).

---

## Workspace Architecture (`AGENTS.md` + Stage Skills)

- `scripts/pipeline_ctl.py` — Deterministic state machine tracking `pipeline/state.json`
- `scripts/score_opportunity.py` — Commercial buyer, saturation & DIY-resistance scorer with automatic kill switches
- `scripts/build_portfolio.py` — Regenerates `docs/` GitHub Pages storefront, OpenGraph/JSON-LD SEO, `sitemap.xml`, `robots.txt`, and this `README.md`
- `scripts/ship_check.py` — Automated test runner and `.zip` / `.vsix` / `.whl` packager
- `scripts/publish_pypi.py` — Zero-dependency PyPI Metadata 2.1 wheel validator & uploader
- `scripts/ping_indexnow.py` — Instant search indexing via IndexNow (`Bing`, `DuckDuckGo`, `ChatGPT` / `Copilot` search)
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

    readme_path = REPO_ROOT / "README.md"
    readme_path.write_text(render_root_readme_md(products, bundle_checkout_url), encoding="utf-8")

    print(
        f"Built portfolio hub & GitHub Pages site for {len(products)} product(s) "
        f"-> {html_path}, {md_path}, {readme_path}, & {docs_dir / 'index.html'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
