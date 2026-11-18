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
    "notion-linear-prd-sync": "$29 once",
    "notion-clean-md-exporter": "$24 once",
    "vscode-workspace-profile-config": "$19 once",
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
          <p class="mt-1">All tools run locally in your browser, CLI, or editor. Zero PRDs, source code, or API keys are transmitted to third-party servers. Payments and license delivery are processed securely by Lemon Squeezy.</p>
        </div>
      </div>
    </div>
  </section>"""


def detect_price(proj_dir: Path, slug: str) -> str:
    landing = proj_dir / "launch" / "landing.html"
    if landing.is_file():
        text = landing.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(\$\d+\s+once)", text)
        if m:
            return m.group(1)
    return DEFAULT_PRICES.get(slug, "$29 once")


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
                "landing_rel": f"../projects/{slug}/launch/landing.html",
                "kit_rel": f"../projects/{slug}/launch/LAUNCH_KIT.md",
                "zip_rel": f"../projects/{slug}/dist/{slug}-v0.1.0.zip",
                "site_page_rel": f"./products/{slug}/index.html",
                "site_zip_rel": f"./downloads/{slug}-v0.1.0.zip",
                "zip_exists": zip_path.is_file(),
            }
        )
    return items


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
        zip_badge = (
            f'<a href="{html.escape(zip_href)}" download data-fk-cta="free-install" class="text-xs text-indigo-300 hover:text-indigo-200 underline">Download .zip</a>'
            if p["zip_exists"]
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
  <script src="https://assets.lemonsqueezy.com/lemon.js" defer></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
  <header class="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
    <div class="text-lg font-bold tracking-tight text-white">Friction-Killer Suite</div>
    <nav class="flex items-center gap-6 text-sm text-slate-300">
      <a href="#bundle" class="hover:text-white">Bundle</a>
      <a href="#policies" class="hover:text-white">Support &amp; Policies</a>
      <a href="#bundle" class="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400">
        All-Access Bundle — $49
      </a>
    </nav>
  </header>

  <main class="mx-auto max-w-6xl px-6 pb-12">
    <section class="py-12 text-center">
      <span class="inline-block rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
        Zero-Subscription · Local-First · Instant Lemon Squeezy Keys
      </span>
      <h1 class="mt-5 text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
        Eliminate Notion, Linear &amp; VS Code friction<br />
        <span class="text-indigo-400">without paying monthly SaaS taxes.</span>
      </h1>
      <p class="mx-auto mt-4 max-w-2xl text-base text-slate-300">
        Three purpose-built utilities that automate PRD-to-Linear epics, clean Notion Markdown Git exports, and declarative VS Code workspace profiles.
      </p>
    </section>

    <section class="grid gap-6 md:grid-cols-3">
{cards_html}
    </section>

    <section id="bundle" class="mt-14 rounded-3xl border border-indigo-500/50 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/60 p-8 sm:p-10">
      <div class="flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
        <div>
          <span class="rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-300">BEST VALUE · SAVE 32%</span>
          <h2 class="mt-3 text-3xl font-extrabold text-white">All-Access Friction-Killer Bundle</h2>
          <p class="mt-2 max-w-xl text-sm text-slate-300">
            Unlock Pro licenses for all {len(products)} tools (LinearBridge + NotionGitExport + ExtProfileLock) with one single purchase ($72 combined value).
          </p>
        </div>
        <div class="w-full shrink-0 rounded-2xl border border-slate-700 bg-slate-950/70 p-6 text-center md:w-72">
          <div class="text-xs text-slate-400 line-through">$72 combined</div>
          <div class="mt-1 text-4xl font-extrabold text-white">$49 <span class="text-sm font-normal text-slate-400">once</span></div>
          <a href="{html.escape(bundle_checkout_url)}" data-fk-cta="pro-checkout" class="lemonsqueezy-button mt-5 block rounded-xl bg-indigo-500 py-3 text-sm font-semibold text-white hover:bg-indigo-400">
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


def render_playbook_md(products: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        f"| **{p['short_title']}** (`{p['slug']}`) | {p['ecosystem']} | {p['price']} | "
        f"`projects/{p['slug']}/dist/{p['slug']}-v0.1.0.zip` | [Sales Page]({p['landing_rel']}) / [Kit]({p['kit_rel']}) |"
        for p in products
    )
    cmds = "\n".join(
        f"python3 scripts/configure_checkout.py --slug {p['slug']} --checkout-url \"https://YOUR_STORE.lemonsqueezy.com/buy/...\" --product-id \"PRODUCT_ID\""
        for p in products
    )
    return f"""# Master Launch Playbook (15-Minute Go-Live Checklist)

## Portfolio Summary ({len(products)} Shipped Products)

| Product | Ecosystem | Pro Price | Distributable Bundle | Launch Assets |
| :--- | :--- | :---: | :--- | :--- |
{rows}
| **All-Access Bundle** | Multi-Product | **\\$49 once** (Save 32%) | All 3 Pro Keys | [Storefront](index.html) |

---

## Step 1: Create Lemon Squeezy Products (~5 mins)
1. Create 3 single products in Lemon Squeezy with **License Keys enabled** (3 device activations):
   - **LinearBridge Pro** — \\$29 one-time
   - **NotionGitExport Pro** — \\$24 one-time
   - **ExtProfileLock Pro** — \\$19 one-time
2. Create 1 **All-Access Bundle** product at **\\$49 one-time** and pass `--bundle-url` to `configure_checkout.py`.

## Step 2: Wire Live Checkout URLs & Rebuild Site/Zips (~2 mins)
```bash
{cmds}
python3 scripts/configure_checkout.py --bundle-url "https://YOUR_STORE.lemonsqueezy.com/buy/BUNDLE_LINK"
```

## Step 3: Publish & Distribute (~8 mins)
1. **GitHub Pages Storefront (`docs/`)**: Push `main` so `https://domstijn.github.io/friction-killer-suite/` serves live checkout buttons and direct `.zip` downloads.
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
