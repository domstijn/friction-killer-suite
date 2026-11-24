#!/usr/bin/env python3
"""Generate localized /de/ landing pages, 20 error-code guides, 3 free calculators, fixtures, /partners/, and llms.txt."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Callable

SITE_BASE_URL = "https://domstijn.github.io/friction-killer-suite"
BUNDLE_URL_DEFAULT = "https://buy.stripe.com/eVq3cvfHmcKEe5idNO6sw03"

STRIPE_LINKS: dict[str, str] = {
    "e-invoice-xml-batch-converter": "https://buy.stripe.com/bJe5kD8eU8uobXa5hi6sw0c",
    "camt053-mt940-qbo-xero-converter": "https://buy.stripe.com/4gM9ATfHm5ic5yMh006sw0e",
    "eu-oss-vat-return-compiler": "https://buy.stripe.com/00w6oH52I7qk2mA6lm6sw0a",
    "lemonsqueezy-stripe-polar-migrator": "https://buy.stripe.com/3cI6oHeDibGAf9m4de6sw09",
    "woo-shopify-metafield-migrator": "https://buy.stripe.com/6oU8wPan2fWQ8KY4de6sw0d",
    "amazon-settlement-xero-qbo-splitter": "https://buy.stripe.com/bJefZh66M2601iw6lm6sw0b",
    "stripe-payout-xero-qbo-splitter": "https://buy.stripe.com/7sY9AT9iYh0U8KY39a6sw08",
}

DE_ALTERNATES: dict[str, str] = {
    "e-invoice-xml-batch-converter": f"{SITE_BASE_URL}/de/xrechnung-zugferd-konverter/",
    "camt053-mt940-qbo-xero-converter": f"{SITE_BASE_URL}/de/camt053-mt940-datev-konverter/",
    "eu-oss-vat-return-compiler": f"{SITE_BASE_URL}/de/bzst-oss-csv-konverter/",
}


def _json_ld_script(payload: dict[str, Any]) -> str:
    safe = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return f'  <script type="application/ld+json">{safe}</script>'


def _render_page_shell(
    *,
    title: str,
    description: str,
    canonical_url: str,
    lang: str,
    rel_root: str,
    main_html: str,
    analytics_slug: str,
    analytics_title: str,
    analytics_cfg: dict[str, str],
    bundle_checkout_url: str,
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None = None,
    extra_head: str = "",
    extra_script: str = "",
    include_feedback: bool = True,
) -> str:
    safe_title = html.escape(title, quote=True)
    safe_desc = html.escape(description, quote=True)
    safe_canon = html.escape(canonical_url, quote=True)
    analytics_block = (
        analytics_renderer(
            analytics_slug,
            analytics_title,
            analytics_cfg,
            include_feedback_bar=include_feedback,
        )
        if analytics_renderer
        else ""
    )
    de_label = "Alle Tools" if lang == "de" else "All Tools"
    guides_label = "Ratgeber" if lang == "de" else "Guides"
    tools_label = "Rechner (Kostenlos)" if lang == "de" else "Free Tools"
    samples_label = "Beispieldateien" if lang == "de" else "Samples"
    partners_label = "Kanzleien" if lang == "de" else "Accountants"

    return f"""<!DOCTYPE html>
<html lang="{html.escape(lang, quote=True)}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_title}</title>
  <meta name="description" content="{safe_desc}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="{safe_canon}" />
  <meta property="og:title" content="{safe_title}" />
  <meta property="og:description" content="{safe_desc}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{safe_canon}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{safe_title}" />
  <meta name="twitter:description" content="{safe_desc}" />
{extra_head}
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
  <header class="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-6 no-print">
    <a href="{html.escape(rel_root)}index.html" class="text-base font-bold tracking-tight text-white hover:text-indigo-300">Friction-Killer Suite</a>
    <nav class="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-slate-300">
      <a href="{html.escape(rel_root)}index.html" class="hover:text-white">{de_label}</a>
      <a href="{html.escape(rel_root)}tools/index.html" class="hover:text-white">{tools_label}</a>
      <a href="{html.escape(rel_root)}guides/index.html" class="hover:text-white">{guides_label}</a>
      <a href="{html.escape(rel_root)}samples/index.html" class="hover:text-white">{samples_label}</a>
      <a href="{html.escape(rel_root)}partners/index.html" class="hover:text-white">{partners_label}</a>
      <a href="{html.escape(rel_root)}de/index.html" class="rounded border border-slate-700 px-2 py-0.5 text-xs text-slate-200 hover:border-indigo-400">DE</a>
      <a href="{html.escape(bundle_checkout_url)}" data-fk-cta="pro-checkout" class="rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-400">Bundle — €49</a>
    </nav>
  </header>

  <main class="mx-auto max-w-5xl px-6 pb-14">
{main_html}
  </main>

{legal_footer_html}
  <footer class="mx-auto max-w-5xl border-t border-slate-800 px-6 py-8 text-center text-xs text-slate-500 no-print">
    Friction-Killer Suite by Stijn Dom (@domstijn) · 100% Local Browser Processing · <a href="{html.escape(rel_root)}sitemap.xml" class="underline">Sitemap</a> · <a href="{html.escape(rel_root)}llms.txt" class="underline">llms.txt</a> · <a href="mailto:dom.stijn99@gmail.com" class="underline">dom.stijn99@gmail.com</a>
  </footer>
{extra_script}
{analytics_block}
</body>
</html>
"""


DE_PAGES: list[dict[str, Any]] = [
    {
        "dir": "xrechnung-zugferd-konverter",
        "slug": "de_xrechnung_zugferd",
        "product_slug": "e-invoice-xml-batch-converter",
        "en_canonical": f"{SITE_BASE_URL}/products/e-invoice-xml-batch-converter/",
        "title": "XRechnung & ZUGFeRD XML zu A4-PDF & DATEV EXTF — EInvoiceLocal (100 % lokal)",
        "description": "XRechnung (UBL 2.1), ZUGFeRD 2.x (CII) und Peppol BIS 3.0 XML direkt im Browser nach EN 16931 prüfen, als A4-PDF drucken und mit DATEV BU-Schlüssel (EXTF CSV) exportieren. Ohne Cloud-Upload.",
        "badge": "DSGVO & GoBD · KEIN CLOUD-UPLOAD",
        "h1": "XRechnung & ZUGFeRD XML lokal prüfen, als A4-PDF drucken & zu DATEV EXTF exportieren",
        "sub": "Keine sensiblen Lieferanten-IBANs oder USt-IDs auf fremde Server hochladen: EInvoiceLocal parst OASIS UBL 2.1 und UN/CEFACT CII direkt im Chrome-Speicher (im DevTools-Netzwerk-Tab nachprüfbar) und mappt BT-118/BT-151 automatisch auf DATEV BU-Schlüssel 9, 8, 94 und 0.",
        "primary_cta": "Jetzt im Browser starten (3 XMLs kostenlos)",
        "secondary_cta": "DATEV BU-Schlüssel Rechner öffnen",
        "secondary_href": "../../tools/datev-bu-schluessel-lookup/index.html",
        "guide_href": "../../guides/xrechnung-xml-zu-pdf-und-datev-extf/index.html",
        "sample_href": "../../samples/files/sample-xrechnung-3.0-ubl.xml",
        "bullets": [
            ("Dual-Syntax (UBL 2.1 & CII)", "Verarbeitet XRechnung 3.0 UBL, Peppol BIS Billing 3.0 und ZUGFeRD / Factur-X CII in einem Batch ohne Java- oder Electron-Abstürze."),
            ("EN 16931 Summenprüfung (BR-CO-10 / BR-CO-15)", "Prüft Nettozeilensummen, MwSt-Beträge und Bruttogesamtbetrag centgenau vor dem DATEV-Export."),
            ("DATEV EXTF (;-CSV) & BU-Schlüssel", "Erzeugt direkt importierbare DATEV-Buchungsstapel mit Komma-Dezimalen, SKR03-Konten (3400/3300/3123) und BU-Schlüssel."),
        ],
        "faqs": [
            ("Verlassen meine E-Rechnungen meinen Computer?", "Nein. Browser-DOMParser verarbeitet jede XML-Datei lokal im Arbeitsspeicher. Für große Ordner oder automatisierte Kanzlei-Prozesse ist zudem eine Offline-Python-CLI (.whl) enthalten."),
            ("Erhalte ich beim Kauf eine ordentliche Rechnung?", "Ja. Über Stripe Managed Payments (€29 einmalig, kein Abo) erhalten Sie automatisch eine Umsatzsteuer-Rechnung (PDF) sowie eine 14-Tage-Geld-zurück-Garantie."),
        ],
    },
    {
        "dir": "camt053-mt940-datev-konverter",
        "slug": "de_camt053_mt940",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "en_canonical": f"{SITE_BASE_URL}/products/camt053-mt940-qbo-xero-converter/",
        "title": "CAMT.053 XML & MT940 Konverter zu DATEV CSV, QuickBooks .QBO & Xero — BankFeedBridge",
        "description": "Sparkasse, Volksbank & Deutsche Bank ISO 20022 CAMT.053 XML und SWIFT MT940 (.sta) 100 % lokal entpacken, SEPA-Sammler aufschlüsseln, Saldo centgenau prüfen und in DATEV CSV / .QBO / Xero exportieren.",
        "badge": "SPARKASSE · VOLKSBANK · ISO 20022 CAMT.053",
        "h1": "CAMT.053 XML & MT940 (.sta) lokal entpacken — für DATEV CSV, QuickBooks .QBO & Xero",
        "sub": "Schluss mit abgebrochenen SEPA-Sammlern und fehlenden MT940-Verwendungszwecken (?20..?33): BankFeedBridge flacht verschachtelte <NtryDtls><TxDtls>-Sammler ab, verifiziert OPBD/CLBD-Salden in Ganzzahl-Cent und kostet einmalig €29 statt teurer Monats-Abos.",
        "primary_cta": "CAMT.053 / MT940 im Browser testen (10 Buchungen frei)",
        "secondary_cta": "Sparkasse/Volksbank CAMT.053 Guide",
        "secondary_href": "../../guides/sparkasse-volksbank-camt053-datev-csv/index.html",
        "guide_href": "../../guides/quickbooks-error-ol-222-camt053-fix/index.html",
        "sample_href": "../../samples/files/sample-camt053-001-08-sepa-batch.xml",
        "bullets": [
            ("SEPA-Sammelbuchungen (<TxDtls>) aufschlüsseln", "Löst Einzelumsätze samt Empfänger-IBAN, EndToEndId und Remittance-Text aus CAMT.053.001.02 / .08 und MT940 :86: Unterfeldern auf."),
            ("Centgenaue OPBD → CLBD Saldo-Kontrolle", "Warnt sofort bei Abweichungen zwischen Anfangs-, Bewegungs- und Endsaldo—kein stiller Datenverlust bei Bankwechseln."),
            ("Einmalig €29 statt $180–$599/Jahr", "Ersetzt wiederkehrende SaaS-Abos wie ProperSoft durch Browser-App + Offline-Python-CLI inklusive Stripe USt-PDF-Beleg."),
        ],
        "faqs": [
            ("Funktioniert BankFeedBridge mit deutschen Banken (Sparkasse, VR-Bank, ING)?", "Ja. Sowohl ISO 20022 camt.053.001.02/.08 als auch klassische SWIFT MT940 (.sta/.940) mit ?20..?33 Subfeldern werden lokal erkannt."),
            ("Warum schlägt QuickBooks mit Fehler OL-222 bei fremden OFX-Dateien fehl?", "QuickBooks verlangt eine freigeschaltete <INTU.BID>-Bank-ID (z. B. 3000) sowie eindeutige <FITID>-Hashes. BankFeedBridge setzt beide deterministisch."),
        ],
    },
    {
        "dir": "bzst-oss-csv-konverter",
        "slug": "de_bzst_oss",
        "product_slug": "eu-oss-vat-return-compiler",
        "en_canonical": f"{SITE_BASE_URL}/products/eu-oss-vat-return-compiler/",
        "title": "BZSt OSS CSV lokal erstellen — Stripe Tax & Shopify zu Mein BOP / EU-OSS Export",
        "description": "Stripe Tax, Shopify & Lemon Squeezy CSVs lokal in Chrome zu einer prüffähigen BZSt BOP (;)-CSV für das EU One-Stop-Shop (OSS) Verfahren bündeln. Automatische GR->EL Korrektur, B2B-Abzug & EZB-FX.",
        "badge": "BZSt MEIN BOP · EU-OSS QUARTALSMELDUNG",
        "h1": "BZSt OSS CSV (Mein BOP) aus Stripe, Shopify & Lemon Squeezy lokal erstellen",
        "sub": "Keine teure Tax-Compliance-Plattform nötig: OssVatBridge führt Exporte lokal im Browser zusammen, rechnet Nicht-EUR-Umsätze über EZB-Quartalskurse um, mappt Griechenland automatisch von GR auf EL und trennt Inlandsumsätze sowie Reverse-Charge-B2B-Rechnungen sauber heraus.",
        "primary_cta": "OSS-CSV im Browser testen (15 Zeilen kostenlos)",
        "secondary_cta": "EU-27 MwSt-Sätze & GR→EL Rechner",
        "secondary_href": "../../tools/eu-oss-vat-rates-2026/index.html",
        "guide_href": "../../guides/bzst-oss-csv-gr-el-greece-error-fix/index.html",
        "sample_href": "../../samples/files/sample-eu-oss-stripe-shopify.csv",
        "bullets": [
            ("BZSt Mein BOP (;-CSV) & Ireland ROS XML", "Exportiert direkt Semikolon-getrennte BZSt-Dateien mit sauberer Trennung nach Mitgliedstaat, MwSt-Satz und Leistungsart."),
            ("Typische BOP-Fehler abgefangen (GR → EL)", "Korrigiert ISO-Code GR automatisch auf das vom BZSt/EU-Schema geforderte EL und zieht Gutschriften/Erstattungen (Refunds) korrekt ab."),
            ("DSGVO-sicher ohne Kundendaten-Upload", "Kundennamen, E-Mails und USt-IDs verlassen niemals Ihren Rechner. Einmalig €29 inkl. Stripe PDF-Rechnung."),
        ],
        "faqs": [
            ("Kann ich mehrere Shops und Stripe-Konten zusammenfassen?", "Ja. Sie können mehrere CSV-Dateien von Stripe Tax, Shopify Tax Reports und Lemon Squeezy gleichzeitig auswählen und zu einem konsolidierten EU-27 OSS-Bericht verschmelzen."),
            ("Was kostet die Pro-Lizenz?", "€29 einmalig (oder €49 im All-Access-Bundle für alle 13 Werkzeuge inklusive EInvoiceLocal und BankFeedBridge) — ohne Abo."),
        ],
    },
]

GUIDES: list[dict[str, Any]] = [
    {
        "slug": "quickbooks-error-ol-222-camt053-fix",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "product_name": "BankFeedBridge",
        "lang": "en",
        "sample_file": "sample-camt053-001-08-sepa-batch.xml",
        "title": "Fix QuickBooks Error OL-222 When Importing CAMT.053 / MT940 (.QBO) — Complete Reference",
        "h1": "How to Fix QuickBooks Error OL-222 for CAMT.053 & MT940 Bank Files",
        "meta_desc": "Why QuickBooks Desktop rejects converted bank files with Error OL-222 / OL-221: missing <INTU.BID>, invalid <CURDEF>, unescaped XML & duplicate <FITID>. Fix locally in Chrome.",
        "symptom": "QuickBooks Desktop shows 'QuickBooks is unable to verify the Financial Institution Information for this download (OL-222)' right after importing a .QBO Web Connect file converted from European CAMT.053 XML or SWIFT MT940.",
        "root_cause": "QuickBooks Web Connect refuses standard SGML/XML OFX files unless they contain a whitelisted <INTU.BID> financial institution code (e.g. 3000), valid OFX v1 header block, clean ASCII/escaped entities (&amp;), and deterministic <FITID> transaction IDs without SEPA batch collapse.",
        "headers": ["QuickBooks Rejection Cause", "Broken Tag / Input", "Required .QBO Fix"],
        "rows": [
            ["Unrecognized Financial Institution", "Missing or custom <INTU.BID>", "Set whitelisted Intuit BID (3000 Universal / EU Bank)"],
            ["SEPA Batch Truncation", "Only <Ntry> read, <TxDtls> skipped", "Flatten every <TxDtls> line and assert OPBD-CLBD = 0 cents"],
            ["Duplicate or Colliding Re-imports", "Empty or row-index <FITID>", "Hash IBAN + BookgDt + TxDtls index + EndToEndId + cents"],
            ["Unescaped Remittance Ampersands", "RmtInf contains 'AT&T & Co'", "Escape '&', '<', '>' cleanly in <NAME> and <MEMO>"],
        ],
        "snippet": "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\n<BANKMSGSRSV1>\n  <STMTTRNRS><STMTRS>\n    <CURDEF>EUR</CURDEF>\n    <BANKACCTFROM><BANKID>3000</BANKID><ACCTID>DE89370400440532013000</ACCTID><ACCTTYPE>CHECKING</ACCTTYPE></BANKACCTFROM>\n    <INTU.BID>3000</INTU.BID>\n  </STMTRS></BANKMSGSRSV1>",
        "steps": [
            "Open BankFeedBridge locally in Chrome (zero server upload) and drop your bank's .xml (CAMT.053) or .sta (MT940) file.",
            "Confirm opening-to-closing balance variance shows €0.00 OK across unwrapped <NtryDtls><TxDtls> SEPA batches.",
            "Keep QuickBooks <INTU.BID> set to 3000 (Universal / EU & International Bank) and download the generated .qbo Web Connect file.",
        ],
        "faqs": [
            ("Is INTU.BID 3000 safe for European & UK bank accounts in QuickBooks?", "Yes. Intuit BID 3000 maps to a generic whitelisted checking bank profile so QuickBooks imports EUR, GBP, or USD Web Connect transactions cleanly without Direct Connect credentials."),
            ("Will re-importing overlapping date ranges create duplicate transactions?", "No, because BankFeedBridge computes deterministic <FITID> hashes per transaction from IBAN, booking date, batch index, EndToEndId, and integer-cent amount."),
        ],
    },
    {
        "slug": "camt053-to-quickbooks-qbo-converter",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "product_name": "BankFeedBridge",
        "lang": "en",
        "sample_file": "sample-camt053-001-08-sepa-batch.xml",
        "title": "Convert ISO 20022 CAMT.053 XML to QuickBooks (.QBO Web Connect) Without SaaS Subscriptions",
        "h1": "Convert ISO 20022 CAMT.053.001.02 / .08 XML to QuickBooks .QBO Locally",
        "meta_desc": "Step-by-step guide to converting EU ISO 20022 CAMT.053 bank statements into QuickBooks Web Connect (.qbo) in Chrome with zero bank file uploads.",
        "symptom": "European banks export ISO 20022 CAMT.053 XML statements instead of QuickBooks .QBO Web Connect files, forcing firms toward $180-$599/yr third-party SaaS converters.",
        "root_cause": "QuickBooks Desktop and several legacy ledgers require OFX 1.02 SGML wrapped as .qbo with explicit debit/credit signage (<TRNAMT>), <DTPOSTED> YYYYMMDD timestamps, and valid Intuit headers.",
        "headers": ["CAMT.053 XPath Node", "QuickBooks .QBO Element", "Transformation Rule"],
        "rows": [
            ["Stmt/Acct/Id/IBAN", "<ACCTID>", "Preserves IBAN digits (fallback <Othr><Id>)"],
            ["Ntry/Amt + CdtDbtInd", "<TRNAMT> & <TRNTYPE>", "DBIT negates to negative cents + DEBIT; CRDT stays positive + CREDIT"],
            ["Ntry/BookgDt/Dt", "<DTPOSTED>", "Strips hyphens YYYY-MM-DD -> YYYYMMDD"],
            ["TxDtls/RltdPties + RmtInf/Ustrd", "<NAME> + <MEMO>", "Extracts counterparty name (32 chars) & full reference"],
        ],
        "snippet": "<Ntry>\n  <Amt Ccy=\"EUR\">2500.00</Amt><CdtDbtInd>CRDT</CdtDbtInd>\n  <NtryDtls><TxDtls>\n    <AmtDtls><TxAmt><Amt Ccy=\"EUR\">1500.00</Amt></TxAmt></AmtDtls>\n    <RltdPties><Dbtr><Nm>Acme GmbH</Nm></Dbtr></RltdPties>\n    <RmtInf><Ustrd>Invoice 2026-101</Ustrd></RmtInf>\n  </TxDtls></NtryDtls>\n</Ntry>",
        "steps": [
            "Export your statement in CAMT.053 (.xml) format from your online banking portal.",
            "Load it into BankFeedBridge (or run `camt053-mt940-qbo-xero-converter` CLI locally on a folder of XMLs).",
            "Download the verified .qbo file and import via File -> Utilities -> Import -> Web Connect Files in QuickBooks.",
        ],
        "faqs": [
            ("Does BankFeedBridge work for both camt.053.001.02 and camt.053.001.08?", "Yes. The browser DOMParser reads namespace-agnostic local element names across all standard SEPA CAMT.053 revisions."),
            ("Do my company bank balances touch your servers?", "Never. Processing occurs 100% inside Chrome JavaScript memory."),
        ],
    },
    {
        "slug": "mt940-sta-to-xero-ofx-csv",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "product_name": "BankFeedBridge",
        "lang": "en",
        "sample_file": "sample-swift-mt940-statement.sta",
        "title": "Convert SWIFT MT940 (.STA / .940) Bank Statements to Xero OFX & CSV Locally",
        "h1": "Convert SWIFT MT940 (.sta / .940) Files into Clean Xero OFX & CSV Statements",
        "meta_desc": "Parse SWIFT MT940 :60F:, :61:, :86: structured subfields (?20..?33), RD/RC reversals, and :62F: closing balances into clean Xero OFX and CSV files locally.",
        "symptom": "Uploading raw SWIFT MT940 (.sta) files fails or lumps cryptic '?20' / 'EREF+' strings into a single unsearchable Xero Payee field.",
        "root_cause": "MT940 encodes statement lines across fixed 6-digit YYMMDD dates in :61: (including reverse-debit 'RD' and reverse-credit 'RC' indicators) paired with multiline :86: subfields (?00, ?20-?29, ?32 counterparty name, ?38 IBAN).",
        "headers": ["MT940 Field / Tag", "Example", "Parsed Output"],
        "rows": [
            [":60F: / :62F:", "C261101EUR5000,00", "Opening/closing signed integer cents balance audit"],
            [":61: Indicator", "2611031103DR450,25NTRFNONREF", "Parses C/D/RC/RD debit-credit reversal signs cleanly"],
            [":86: ?32 / ?38", "?32Vendor Ltd?38NL91ABNA...", "Splits clean Payee Name & IBAN instead of raw codes"],
            [":86: /TAG/ format", "/NAME/Acme/REMI/Inv 9", "Supports Dutch/European slash-delimited MT940 tags"],
        ],
        "snippet": ":20:STMT202611\n:25:NL91ABNA0417164300\n:28C:001/001\n:60F:C261101EUR5000,00\n:61:2611031103CR1250,00NTRFINV101\n:86:051?20Payment Inv 101?32Kunden GmbH?38DE44500105175407324931\n:62F:C261103EUR6250,00",
        "steps": [
            "Open BankFeedBridge and click Sample MT940 or drop your bank's .sta / .mt940 export.",
            "Inspect the integer-cent balance variance badge (should read €0.00 OK).",
            "Download Xero OFX or Xero Bank CSV and import directly into your Xero bank account.",
        ],
        "faqs": [
            ("How are reversed entries (RD / RC) in :61: handled?", "BankFeedBridge handles C (credit), D (debit), RC (reversal credit / negative credit), and RD (reversal debit / positive credit) automatically."),
            ("What if my bank uses Dutch slash tags (/NAME/, /REMI/) instead of ?32?", "Both German ?XX SEPA subfield codes and slash-delimited /TAG/ MT940 structures are supported."),
        ],
    },
    {
        "slug": "ing-rabobank-abn-amro-camt053-xero-qbo",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "product_name": "BankFeedBridge",
        "lang": "en",
        "sample_file": "sample-camt053-001-08-sepa-batch.xml",
        "title": "ING, Rabobank & ABN AMRO CAMT.053 / MT940 to Xero & QuickBooks Converter",
        "h1": "Convert Dutch Bank CAMT.053 & MT940 (ING, Rabobank, ABN AMRO) to Xero & QuickBooks",
        "meta_desc": "Handle ING, Rabobank, bunq, and ABN AMRO CAMT.053 XML or MT940 statements in Xero and QuickBooks Desktop/Online without losing SEPA batch details.",
        "symptom": "Dutch banks export CAMT.053.001.02/.08 or slash-tag MT940 files that QuickBooks rejects and Xero leaves with missing supplier names on batch payments.",
        "root_cause": "ING and Rabobank wrap iDEAL payouts and salary/supplier SEPA batches in nested <NtryDtls><TxDtls> entries sharing one parent <AcctSvcrRef>.",
        "headers": ["Dutch Bank Export", "Common Issue", "BankFeedBridge Resolution"],
        "rows": [
            ["Rabobank / ING CAMT.053", "Batch SEPA totals mask child invoices", "Flattens each <TxDtls> child with Debtor/Creditor IBAN"],
            ["ABN AMRO MT940", "/TRTP/ & /NAME/ strings broken across lines", "Unwraps 65-char :86: continuations & extracts /NAME/, /IBAN/, /REMI/"],
            ["Multi-currency / EUR accounts", "Decimal comma vs dot issues", "Outputs clean ISO dot decimals for Xero/QBO & comma for DATEV"],
        ],
        "snippet": "<Ntry><NtryDtls><TxDtls><RltdPties><Cdtr><Nm>Rabobank Vendor BV</Nm></Cdtr><CdtrAcct><Id><IBAN>NL91ABNA0417164300</IBAN></Id></CdtrAcct></RltdPties></TxDtls></NtryDtls></Ntry>",
        "steps": [
            "Download CAMT.053 XML or MT940 from Mijn ING Zakelijk, Rabo Business Banking, or ABN AMRO Internet Banking.",
            "Drop the file directly into BankFeedBridge (runs locally in Chrome, 0 data transmitted).",
            "Export Xero CSV / .ofx or QuickBooks .qbo in one click.",
        ],
        "faqs": [
            ("Can Dutch boekhouders run this on client folders?", "Yes. The €29 Pro license (or €49 Suite) unlocks unlimited rows and the local Python CLI (`camt053-mt940-qbo-xero-converter --input ./exports/`)."),
            ("Is INTU.BID 3000 accepted for EUR accounts in QuickBooks?", "Yes—combined with `<CURDEF>EUR</CURDEF>`, QuickBooks Web Connect imports EUR checking feeds cleanly."),
        ],
    },
    {
        "slug": "sparkasse-volksbank-camt053-datev-csv",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "product_name": "BankFeedBridge",
        "lang": "de",
        "sample_file": "sample-camt053-001-08-sepa-batch.xml",
        "title": "Sparkasse & Volksbank CAMT.053 XML in DATEV Bank-CSV umwandeln (ohne Cloud-Upload)",
        "h1": "Sparkasse & Volksbank CAMT.053 / MT940 lokal nach DATEV CSV & Xero konvertieren",
        "meta_desc": "ISO 20022 CAMT.053.001.02/.08 und MT940 von Sparkasse, VR-Bank, Deutsche Bank & Commerzbank lokal im Browser in saubere DATEV-CSV, .QBO oder Xero OFX umwandeln.",
        "symptom": "Nach der Banken-Umstellung von MT940 auf ISO 20022 CAMT.053 XML liefern Skripte leere Empfänger oder falsche Sammelbuchungs-Summen für DATEV, Lexware oder QuickBooks.",
        "root_cause": "Sparkassen- und Fiducia/Atruvia-Dateien nutzen verschachtelte <NtryDtls><TxDtls>-Knoten für SEPA-Sammler sowie strukturierte DTA-Subfelder (?20..?33) in MT940.",
        "headers": ["Bank-Feld (DE)", "Fehlerquelle", "Lösung in BankFeedBridge"],
        "rows": [
            ["<NtryDtls><TxDtls>", "Sammler nur als Gesamtbetrag erfasst", "Entpackt jede Einzeltransaktion inkl. Gegenkonto-IBAN"],
            ["MT940 :86: ?20-?33", "Zerstückelter Verwendungszweck", "Rekonstruiert Zahlungsempfänger (?32) und Text sauber"],
            ["OPBD vs. CLBD Saldo", "Rundungs- oder Datumsfehler", "Mathematischer Abgleich auf 0 Cent Differenz vor Export"],
        ],
        "snippet": "Buchungstag;Valutadatum;Auftraggeber/Empfänger;IBAN;Verwendungszweck;Betrag;Währung;Ref\n2026-11-10;2026-11-10;NordWerk GmbH;DE44500105175407324931;Rechnung RE-1042;1500,00;EUR;REF-2026-001-1",
        "steps": [
            "Laden Sie Ihre CAMT.053-XML- oder MT940-Datei aus dem Sparkassen-/VR-Onlinebanking herunter.",
            "Ziehen Sie die Datei lokal in BankFeedBridge (DSGVO-konform, null Server-Kontakt).",
            "Prüfen Sie den 0,00-€-Saldocheck und exportieren Sie DATEV CSV, .QBO oder Xero.",
        ],
        "faqs": [
            ("Funktioniert der Konverter DSGVO-konform ohne Auftragsverarbeitung (AVV)?", "Ja, da keine Kontoauszüge an einen Server übertragen werden. Alles läuft im lokalen Browser-Tab bzw. der Offline-Python-CLI."),
            ("Gibt es auch deutsche Unterstützung für E-Rechnungen nach DATEV?", "Ja: EInvoiceLocal konvertiert XRechnung und ZUGFeRD XML lokal in DATEV EXTF-Buchungsstapel mit BU-Schlüssel."),
        ],
    },
    {
        "slug": "propersoft-bank2qbo-alternative-local",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "product_name": "BankFeedBridge",
        "lang": "en",
        "sample_file": "sample-camt053-001-08-sepa-batch.xml",
        "title": "Zero-Subscription Alternative to ProperSoft Bank2QBO for CAMT.053 & MT940 (€29 Once)",
        "h1": "Zero-Subscription Alternative to ProperSoft Bank2QBO (€29 Once vs. $19.99–$49/mo)",
        "meta_desc": "Why firms switch from recurring ProperSoft / MoneyThumb subscriptions to a €29 one-time browser-local CAMT.053 & MT940 to QBO/OFX/Xero/DATEV converter.",
        "symptom": "Paying $239–$599 every year just to convert monthly CAMT.053 XML or SWIFT MT940 bank statements into QuickBooks .QBO or Xero .OFX.",
        "root_cause": "Legacy desktop converters moved to recurring monthly plans, while bank-statement XML/MT940 conversion is a stateless deterministic transformation.",
        "headers": ["Capability", "Typical SaaS / Subscription Converter", "BankFeedBridge (€29 Once)"],
        "rows": [
            ["Pricing Model", "$19.99–$49.98/mo ($239–$599/yr)", "€29 one-time lifetime license (+ €49 full suite)"],
            ["ISO 20022 CAMT.053 Batches", "Often requires manual mapping profiles", "Automatic <NtryDtls><TxDtls> SEPA flattening"],
            ["Balance Math Audit", "Rarely halts on missing rows", "Integer-cent OPBD -> CLBD reconciliation check"],
            ["Execution Environment", "Installed binary / cloud portal", "Zero-install Chrome Web App + Offline Python .whl CLI"],
        ],
        "snippet": "pip install ./camt053_mt940_qbo_xero_converter-0.1.0-py3-none-any.whl\ncamt053-mt940-qbo-xero-converter convert ./bank_exports/ --format qbo --intu-bid 3000",
        "steps": [
            "Test BankFeedBridge right now in your browser using the built-in CAMT.053 & MT940 samples (up to 10 transactions free).",
            "Drop your own statement to verify <INTU.BID>, payee parsing, and zero balance variance.",
            "Unlock unlimited files across all team machines for €29 once via Stripe Managed Payments.",
        ],
        "faqs": [
            ("Do I also get QuickBooks, Xero, AND DATEV exports in one license?", "Yes. One €29 Pro license covers QuickBooks .qbo, Xero .ofx, Xero CSV, and DATEV bank CSV."),
            ("Is an offline CLI included for bookkeepers with dozens of folders?", "Yes, every Pro purchase includes the zero-dependency Python .whl CLI."),
        ],
    },
    {
        "slug": "sepa-batch-ntrydtls-txdtls-reconciliation",
        "product_slug": "camt053-mt940-qbo-xero-converter",
        "product_name": "BankFeedBridge",
        "lang": "en",
        "sample_file": "sample-camt053-001-08-sepa-batch.xml",
        "title": "CAMT.053 SEPA Batch Unwrapping: Fixing <NtryDtls><TxDtls> Parent/Child Drift",
        "h1": "How to Unwrap Nested CAMT.053 <NtryDtls><TxDtls> Batches Without Cent Drift",
        "meta_desc": "Technical guide to flattening ISO 20022 CAMT.053 SEPA batch entries (<NtryDtls>/<TxDtls>) while asserting OPBD + delta = CLBD in exact integer cents.",
        "symptom": "Custom XML-to-CSV scripts either import a single lump-sum batch total without supplier details, or double-count both <Ntry/Amt> and child <TxDtls> lines.",
        "root_cause": "In ISO 20022 CAMT.053, an <Ntry> represents a collective bank booking while zero, one, or N <TxDtls> elements represent underlying SEPA transfers whose amounts only fall back to <Ntry> when <AmtDtls> is omitted.",
        "headers": ["XML Structure Case", "Child Amount Lookup Order", "Duplicate Prevention Key"],
        "rows": [
            ["0 or 1 <TxDtls>", "Prefer TxAmt, fallback to Ntry/Amt + CdtDbtInd", "AcctSvcrRef + BookgDt + index 0"],
            ["Multi-<TxDtls> SEPA Batch", "Iterate every TxDtls; do NOT emit parent Ntry row", "Hash(IBAN, BookgDt, idx, EndToEndId, cents)"],
            ["Credit vs Debit Mixed Sign", "Read TxDtls/CdtDbtInd before Ntry/CdtDbtInd", "Multiply signed cents and sum against OPBD/CLBD"],
        ],
        "snippet": "// Integer-cent invariant checked before export:\nconst expectedClosingCents = openingCents + sum(txList.map(t => t.cents));\nconst varianceCents = closingCents - expectedClosingCents; // Must equal 0",
        "steps": [
            "Never represent financial amounts as IEEE-754 floats—parse string decimals directly to integer cents.",
            "Emit child <TxDtls> rows strictly in place of parent <Ntry> totals when child nodes exist.",
            "Run BankFeedBridge on your statement to see instant child flattening and exact variance diagnostics.",
        ],
        "faqs": [
            ("Why do many naive converters drift by €0.01?", "Floating-point addition like 19.99 + 0.01 introduces binary rounding noise; integer-cent arithmetic prevents drift permanently."),
            ("Can I download a valid SEPA batch CAMT.053 test file?", "Yes—grab sample-camt053-001-08-sepa-batch.xml on our Samples page."),
        ],
    },
    {
        "slug": "xrechnung-xml-zu-pdf-und-datev-extf",
        "product_slug": "e-invoice-xml-batch-converter",
        "product_name": "EInvoiceLocal",
        "lang": "de",
        "sample_file": "sample-xrechnung-3.0-ubl.xml",
        "title": "XRechnung XML sichtbar machen: A4-PDF drucken & DATEV EXTF CSV erstellen (DE)",
        "h1": "XRechnung XML einfach lesen, als A4-PDF drucken & DATEV EXTF exportieren",
        "meta_desc": "Reine XRechnung-XML-Dateien (ohne PDF-Hülle) lokal in Chrome als saubere A4-Rechnung drucken, EN 16931 Summen prüfen und als DATEV EXTF Buchungsstapel exportieren.",
        "symptom": "Lieferanten senden reine XRechnung-.xml-Dateien (UBL 2.1 oder CII) ohne eingebettetes PDF. In Excel öffnen sich hunderte kryptische Tags—und manche Desktop-Viewer stürzen ab.",
        "root_cause": "Im Gegensatz zu ZUGFeRD besitzt reine XRechnung kein PDF-Dokument, sondern besteht ausschließlich aus strukturiertem EN-16931-XML.",
        "headers": ["EN 16931 / UBL / CII Feld", "Bedeutung auf Rechnung", "Ziel in DATEV EXTF / A4 PDF"],
        "rows": [
            ["BT-1 / ID", "Rechnungsnummer", "Belegfeld 1 & PDF-Kopfbereich"],
            ["BT-10 / BuyerReference", "Leitweg-ID / Bestellreferenz", "Kopfzeile & Buchungstext"],
            ["BT-118 / CategoryCode", "Steuerkategorie (S, AE, E, Z)", "Steuert BU-Schlüssel (9, 8, 94, 0)"],
            ["BT-112 / PayableAmount", "Bruttobetrag", "Umsatz in DATEV (Komma-Format)"],
        ],
        "snippet": "<cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>\n<cbc:ID>XR-2026-1001</cbc:ID>\n<cbc:BuyerReference>991-12345-67</cbc:BuyerReference>",
        "steps": [
            "Laden Sie eine oder mehrere XML-Rechnungen in EInvoiceLocal (bis 3 Dateien pro Stapel kostenlos).",
            "Klicken Sie auf eine Zeile im Batch, um rechts die druckfertige A4-Ansicht per Strg+P / Drucken als PDF zu speichern.",
            "Exportieren Sie mit Pro (€29 einmalig) komplette Ordner direkt als DATEV EXTF, Xero oder QBO CSV.",
        ],
        "faqs": [
            ("Funktioniert EInvoiceLocal auch für Peppol- und ZUGFeRD-XMLs?", "Ja, UBL 2.1 (XRechnung & Peppol BIS 3.0) sowie UN/CEFACT CII (ZUGFeRD) werden automatisch erkannt."),
            ("Bleibt das gedruckte PDF GoBD-prüfbar?", "Das gedruckte A4-PDF dient der schnellen visuellen Freigabe; für die GoBD-Archivierung bewahren Sie die ursprüngliche XML-Datei auf."),
        ],
    },
    {
        "slug": "en16931-br-co-10-br-co-15-validation-errors",
        "product_slug": "e-invoice-xml-batch-converter",
        "product_name": "EInvoiceLocal",
        "lang": "en",
        "sample_file": "sample-xrechnung-3.0-ubl.xml",
        "title": "Fix EN 16931 BR-CO-10 & BR-CO-15 Invoice XML Validation Errors (XRechnung / Peppol)",
        "h1": "Debugging EN 16931 BR-CO-10 & BR-CO-15 Tax Calculation Errors in XRechnung & Peppol XML",
        "meta_desc": "Understand and verify EN 16931 math rules BR-CO-10 (LineNetTotal vs LegalMonetaryTotal) and BR-CO-15 (Net + VAT = Gross) across UBL 2.1 and CII XML.",
        "symptom": "KoSIT Validator or Peppol Access Points reject incoming XRechnung/Factur-X invoices with [BR-CO-10] or [BR-CO-15] fatal calculation errors.",
        "root_cause": "BR-CO-10 checks that Sum(InvoiceLine/LineExtensionAmount) equals LineExtensionAmount (adjusted by document charges/allowances); BR-CO-15 asserts TaxExclusiveAmount + TaxAmount = TaxInclusiveAmount.",
        "headers": ["EN 16931 Rule", "Formula Checked", "Typical Cause of Rejection"],
        "rows": [
            ["BR-CO-10", "Sum(BT-131 Line Net) == BT-106", "Per-line rounding mismatch vs header net total"],
            ["BR-CO-14", "Sum(TaxSubtotal/TaxAmount) == BT-110", "Mixed 19% / 7% VAT buckets rounded per line instead of per category"],
            ["BR-CO-15", "BT-109 + BT-110 == BT-112", "TaxExclusiveAmount + TaxTotal does not equal Gross Payable"],
        ],
        "snippet": "<cac:LegalMonetaryTotal>\n  <cbc:LineExtensionAmount currencyID=\"EUR\">200.00</cbc:LineExtensionAmount>\n  <cbc:TaxExclusiveAmount currencyID=\"EUR\">200.00</cbc:TaxExclusiveAmount>\n  <cbc:TaxInclusiveAmount currencyID=\"EUR\">238.00</cbc:TaxInclusiveAmount>\n  <cbc:PayableAmount currencyID=\"EUR\">238.00</cbc:PayableAmount>\n</cac:LegalMonetaryTotal>",
        "steps": [
            "Drop your failing XML files into EInvoiceLocal to inspect computed line sums vs header totals immediately without Java setup.",
            "Click any row marked ERR vs PASS to compare line quantities, unit rates, and VAT buckets.",
            "Use our valid sample-xrechnung-3.0-ubl.xml fixture to benchmark your ERP's XML output.",
        ],
        "faqs": [
            ("Do I need Java 17 or KoSIT binaries installed to run quick checks?", "No—EInvoiceLocal checks BR-CO-10 and BR-CO-15 math plus line totals right in Chrome."),
            ("What tolerance does EInvoiceLocal use?", "2 decimal places (±0.02 EUR tolerance matching EU EN 16931 practical rounding diagnostics)."),
        ],
    },
    {
        "slug": "zugferd-xml-datev-bu-schluessel-mapping",
        "product_slug": "e-invoice-xml-batch-converter",
        "product_name": "EInvoiceLocal",
        "lang": "de",
        "sample_file": "sample-zugferd-cii-en16931.xml",
        "title": "ZUGFeRD & XRechnung zu DATEV EXTF: BU-Schlüssel & SKR03 Konten richtig mappen",
        "h1": "DATEV BU-Schlüssel & SKR03-Konten aus ZUGFeRD & XRechnung XML bestimmen",
        "meta_desc": "Wie BT-118 / BT-151 Umsatzsteuer-Kategorien (S, AE, Z, E) aus ZUGFeRD CII und XRechnung UBL deterministisch auf DATEV BU-Schlüssel 9, 8, 94 und 0 gemappt werden.",
        "symptom": "OCR-Belegleser raten Vorsteuer-Prozentsätze aus PDF-Text und setzen § 13b Reverse-Charge-Rechnungen fälschlicherweise mit BU 9 statt BU 94 an.",
        "root_cause": "Im XML stehen eindeutige EN-16931-Kategoriecodes (BT-118 / BT-151): 'S' (Standard), 'AE' (Reverse Charge), 'E' (Steuerfrei), 'Z' (Nullsatz).",
        "headers": ["XML Kategorie (BT-151)", "Steuersatz", "DATEV BU-Schlüssel", "SKR03 Aufwand (Standard)"],
        "rows": [
            ["S (Standard Rate)", "19 %", "9 (19 % VSt)", "3400"],
            ["S (Reduced Rate)", "7 %", "8 (7 % VSt)", "3300"],
            ["AE (Reverse Charge § 13b)", "0 %", "94 (Reverse Charge)", "3123"],
            ["E / O / Z (Steuerfrei)", "0 %", "0 (Steuerfrei)", "3425 / 3200"],
        ],
        "snippet": "<ram:ApplicableTradeTax>\n  <ram:TypeCode>VAT</ram:TypeCode>\n  <ram:CategoryCode>S</ram:CategoryCode>\n  <ram:RateApplicablePercent>7</ram:RateApplicablePercent>\n</ram:ApplicableTradeTax>",
        "steps": [
            "Prüfen Sie Ihre Kategorien kostenlos in unserem interaktiven DATEV BU-Schlüssel Lookup-Tool.",
            "Laden Sie Ihre ZUGFeRD-CII- oder XRechnung-XMLs in EInvoiceLocal, um die EXTF-Vorschau live zu testen.",
            "Exportieren Sie den fertigen Buchungsstapel (; CSV mit Komma-Beträgen) direkt für DATEV Unternehmen online.",
        ],
        "faqs": [
            ("Ersetzt EInvoiceLocal das DATEV XML Interface?", "Für kleine und mittlere Betriebe oder Kanzleien ohne kostenpflichtiges DATEV-E-Rechnungsmodul liefert EInvoiceLocal sofort fertige EXTF-Stapel für einmalig €29."),
            ("Kann ich DATEV-Stapel vorab mit Testdaten ausprobieren?", "Ja, sowohl mit der integrierten 4-XML-Sample-Batch als auch über unseren kostenlosen Downloads-Bereich."),
        ],
    },
    {
        "slug": "peppol-bis-3-xml-to-pdf-xero-csv",
        "product_slug": "e-invoice-xml-batch-converter",
        "product_name": "EInvoiceLocal",
        "lang": "en",
        "sample_file": "sample-peppol-bis3-invoice.xml",
        "title": "Convert Peppol BIS Billing 3.0 XML Invoices to A4 PDF, Xero Bills & QBO CSV Locally",
        "h1": "Convert Peppol BIS 3.0 UBL XML Files into Readable PDFs & Xero/QuickBooks Bills CSV",
        "meta_desc": "Read incoming Belgian, German, and EU Peppol BIS Billing 3.0 XML invoices locally in Chrome, print A4 copies, and export Xero Bills or QuickBooks Bills CSV.",
        "symptom": "Suppliers over Peppol deliver raw UBL 2.1 XML files that bookkeepers cannot easily read or bulk-import into Xero / QuickBooks as itemized bills.",
        "root_cause": "Peppol BIS 3.0 enforces EN 16931 UBL tags (`InvoiceLine`, `TaxCategory`, `AccountingSupplierParty`) designed for machine-to-machine ERP ingestion rather than human inspection.",
        "headers": ["Peppol BIS 3.0 UBL Node", "A4 PDF View", "Xero Bills CSV Column"],
        "rows": [
            ["cac:AccountingSupplierParty", "Supplier Name & VAT Header", "*ContactName"],
            ["cbc:ID / cbc:IssueDate / DueDate", "Invoice Header & Dates", "*InvoiceNumber, *InvoiceDate, *DueDate"],
            ["cac:InvoiceLine / Item / Name", "Line Item Table", "*Description, *Quantity, *UnitAmount"],
            ["cac:ClassifiedTaxCategory", "Line VAT % + Pass/Fail Pill", "*TaxType (Tax on Purchases / Tax Exempt)"],
        ],
        "snippet": "<cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>\n<cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>",
        "steps": [
            "Open EInvoiceLocal and drop incoming Peppol BIS 3.0 .xml invoices into Chrome.",
            "Inspect rendered line items, click Print / Save A4 PDF for approvals, or switch to the Xero Bills / QBO Bills tabs.",
            "Unlock Pro (€29 once) when importing folders beyond 3 XMLs per batch.",
        ],
        "faqs": [
            ("Does this work for Belgian 2026 mandatory B2B Peppol invoices too?", "Yes—Peppol BIS Billing 3.0 is standard UBL 2.1 EN 16931 and parses identically."),
            ("Are supplier VAT numbers and bank IBANs kept confidential?", "Yes, 100% browser-local execution with zero uploads."),
        ],
    },
    {
        "slug": "quba-viewer-alternative-browser-einvoice",
        "product_slug": "e-invoice-xml-batch-converter",
        "product_name": "EInvoiceLocal",
        "lang": "en",
        "sample_file": "sample-xrechnung-3.0-ubl.xml",
        "title": "Zero-Install Browser Alternative to Quba Viewer for XRechnung & ZUGFeRD (No Java/Electron Crashes)",
        "h1": "Zero-Install Browser Alternative When Quba Viewer Crashes (libjcef / LC_ALL / Locale Bugs)",
        "meta_desc": "Avoid JCEF locale SIGSEGV crashes and heavy desktop installers: view, validate EN 16931, print A4 PDFs, and export DATEV EXTF right inside Chrome.",
        "symptom": "Desktop XRechnung viewers like Quba Viewer throw Java/JCEF `std::__facet_shims` SIGSEGV crashes on macOS/Linux locales or require IT admin installation rights.",
        "root_cause": "Electron/JCEF C++ bindings clash with regional OS locale settings (`de_DE` / `en_US`), and corporate locked-down laptops often restrict unsigned desktop downloads.",
        "headers": ["Aspect", "Desktop XRechnung Viewer", "EInvoiceLocal (Browser-Local)"],
        "rows": [
            ["Install Footprint", "150+ MB Electron / Java / JCEF", "0 MB install — runs in Chrome tab (also CLI .whl)"],
            ["Locale Crashes (libjcef)", "Can crash without LC_ALL=C", "Uses native browser XML DOMParser"],
            ["Batch Export to Accounting", "1 file view at a time", "Batch table + DATEV EXTF, Xero & QBO Bills CSV"],
        ],
        "snippet": "// Runs directly inside Chrome DOMParser with zero network egress:\nconst doc = new DOMParser().parseFromString(xmlText, \"application/xml\");",
        "steps": [
            "Open EInvoiceLocal in any modern Chrome, Edge, Firefox, or Safari tab without admin permissions.",
            "Validate and print up to 3 XML invoices immediately for €0.",
            "Use the €29 Pro CLI or Web App for multi-invoice DATEV/Xero/QBO batches.",
        ],
        "faqs": [
            ("Can I disconnect Wi-Fi after opening the page to verify privacy?", "Yes—once the HTML page is loaded, parsing and A4 printing work completely offline."),
            ("Does it render both UBL 2.1 and CII XMLs?", "Yes, side by side in the same batch table."),
        ],
    },
    {
        "slug": "bzst-oss-csv-gr-el-greece-error-fix",
        "product_slug": "eu-oss-vat-return-compiler",
        "product_name": "OssVatBridge",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "Fix BZSt Mein BOP OSS CSV Rejections: Greece Code 'GR' Must Be 'EL' & Refund Netting",
        "h1": "How to Fix BZSt Mein BOP OSS CSV Import Errors ('GR' vs 'EL', Semicolon Delimiter & Refunds)",
        "meta_desc": "Solve German BZSt Mein BOP EU-OSS CSV upload rejections caused by ISO country code GR (Greece -> EL), comma vs semicolon delimiters, B2B rows, and refunds.",
        "symptom": "Uploading a Stripe or Shopify VAT export directly into Germany's BZSt Mein BOP portal fails with invalid Member State codes ('GR') or rejected row syntax.",
        "root_cause": "Stripe and Shopify output ISO 3166 country code `GR` for Greece, whereas EU VAT OSS schemas (BZSt BOP & Ireland ROS) require `EL`; BOP also requires semicolon (`;`) rows stripped of domestic, non-EU, and B2B reverse-charge sales.",
        "headers": ["Platform Export Value", "Why BZSt BOP Rejects It", "OssVatBridge Auto-Fix"],
        "rows": [
            ["Country = GR (Greece)", "EU VAT prefix for Greece is EL", "Rewrites GR -> EL cleanly in BOP & ROS outputs"],
            ["Country == Home State (e.g. DE)", "Domestic sales stay on domestic UStVA, not OSS", "Auto-excludes seller's domestic EU country"],
            ["Customer VAT ID Present (B2B)", "OSS covers B2C only, never reverse-charge B2B", "Flags and excludes B2B reverse-charge rows"],
            ["Refunds / Credit Notes", "Positive vs negative netting ambiguity", "Subtracts refund net & VAT amounts per country/rate bucket"],
        ],
        "snippet": "Satzart;Mitgliedstaat des Verbrauchs;Umsatzsteuersatz;Steuerbetrag;Bemessungsgrundlage\n1;EL;24,00;24,00;100,00\n1;FR;20,00;19,90;99,50",
        "steps": [
            "Open our free EU-27 OSS VAT Rates 2026 lookup tool to verify Member-State codes (`EL` for Greece) and standard rates.",
            "Upload your raw Stripe Tax, Shopify, or Lemon Squeezy CSVs into OssVatBridge locally in Chrome.",
            "Verify the excluded counts (Domestic / B2B / Non-EU) and export BZSt BOP (;-CSV) or Ireland ROS XML.",
        ],
        "faqs": [
            ("How does OssVatBridge handle non-EUR currencies like SEK, PLN, or DKK?", "It normalizes amounts to EUR using quarterly ECB reference FX rates inside Chrome before summing each Member-State bucket."),
            ("Can I test 15 rows free before buying Pro?", "Yes, up to 15 CSV rows compile and preview live in the browser for €0."),
        ],
    },
    {
        "slug": "stripe-tax-shopify-eu-oss-vat-return",
        "product_slug": "eu-oss-vat-return-compiler",
        "product_name": "OssVatBridge",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "Merge Stripe Tax + Shopify + Lemon Squeezy CSVs Into Quarterly EU OSS VAT Returns",
        "h1": "Combine Stripe Tax, Shopify & Lemon Squeezy Sales into One Quarterly EU OSS Return",
        "meta_desc": "Stop maintaining fragile VLOOKUP Excel sheets every quarter: merge multi-platform EU B2C CSV exports locally into BZSt BOP CSV & Ireland ROS XML.",
        "symptom": "Founders selling via both Shopify and Stripe Tax (plus legacy Lemon Squeezy orders) spend hours merging mismatched CSV headers each EU OSS quarter.",
        "root_cause": "Each platform uses different column names, country codes (`GR` vs `EL`), currency denominations, and negative refund representations.",
        "headers": ["Source Platform", "Key Tax Columns Mapped", "Merged Into OSS Bucket"],
        "rows": [
            ["Stripe Tax / Invoices CSV", "Customer address country, currency, tax_amount", "Net EUR, VAT EUR, Rate %, Services vs Goods"],
            ["Shopify Tax / Orders CSV", "Shipping Country Code, Taxes, Subtotal", "Excludes domestic & non-EU; nets refunds cleanly"],
            ["Lemon Squeezy Export", "Country, Tax, Subtotal, Status (refunded)", "Consolidates alongside Stripe after migration"],
        ],
        "snippet": "pip install eu-oss-vat-return-compiler\neu-oss-vat-return-compiler --home-country DE --format bzst ./q4_exports/*.csv",
        "steps": [
            "Download your quarterly tax CSVs from Stripe, Shopify, or Lemon Squeezy.",
            "Select all CSVs at once inside OssVatBridge and pick your EU Home Member State.",
            "Download the unified BZSt BOP ;-CSV, Ireland ROS XML, or EU-27 audit CSV.",
        ],
        "faqs": [
            ("Do I pay €29 per quarter or €29 once?", "Once—you keep both the browser Pro unlock and the `eu-oss-vat-return-compiler` PyPI/CLI tool permanently."),
            ("Is there an EU OSS tax rate reference chart?", "Yes, use our free EU-27 VAT Rates 2026 & GR->EL lookup calculator."),
        ],
    },
    {
        "slug": "ireland-ros-eu-oss-xml-generator",
        "product_slug": "eu-oss-vat-return-compiler",
        "product_name": "OssVatBridge",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "Generate Ireland Revenue ROS EU VAT OSS XML Locally From Stripe & Shopify CSVs",
        "h1": "How to Generate Validated Ireland ROS EU VAT OSS XML Without Manual Portal Entry",
        "meta_desc": "Compile multi-country Stripe Tax & Shopify sales CSVs into structured EU VAT OSS member-state buckets and ROS XML locally in Chrome.",
        "symptom": "Entering 20+ EU Member-State net & VAT buckets by hand inside Revenue Online Service (ROS) risks fat-finger errors every quarter.",
        "root_cause": "Stripe and Shopify do not directly generate EU portal-ready ROS XML files tailored to your Member State of Identification (IE).",
        "headers": ["ROS XML Section", "Aggregated Data", "Compliance Safeguard"],
        "rows": [
            ["UnionOSS / MemberStates", "Grouped by Consumption Country & Rate", "Converts GR -> EL and separates Services vs Goods"],
            ["FxNormalization", "ECB Reference Currency Conversion", "Normalizes GBP/USD/PLN/SEK into EUR cleanly"],
            ["Exclusions Audit Log", "Domestic (IE) + B2B + Non-EU totals", "Transparent reconciliation against Stripe Gross Volume"],
        ],
        "snippet": "<OSSReturn xmlns=\"urn:eu:oss:v1\">\n  <MemberStateOfConsumption>FR</MemberStateOfConsumption>\n  <VATRatePercent>20.00</VATRatePercent>\n  <TaxableAmountEUR>99.50</TaxableAmountEUR>\n  <VATAmountEUR>19.90</VATAmountEUR>\n</OSSReturn>",
        "steps": [
            "Set your Home Country selector to IE in OssVatBridge.",
            "Upload your Stripe / Shopify CSVs (domestic IE B2C and B2B VAT-ID rows are excluded automatically).",
            "Export the ROS XML tab or use `eu-oss-vat-return-compiler --home-country IE` via pip.",
        ],
        "faqs": [
            ("Can I audit excluded domestic IE rows separately?", "Yes, OssVatBridge shows exact row counts and totals excluded for Domestic, B2B, and Non-EU sales."),
            ("Can I also install the CLI via pip?", "Yes: `pip install eu-oss-vat-return-compiler` (live on PyPI)."),
        ],
    },
    {
        "slug": "lemon-squeezy-shutdown-paypal-stripe-migration",
        "product_slug": "lemonsqueezy-stripe-polar-migrator",
        "product_name": "LemonExitBridge",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "Lemon Squeezy Shutdown (March 31, 2027): Split PayPal vs Card MRR & Preserve Stripe trial_end",
        "h1": "Migrating Off Lemon Squeezy Before March 31, 2027: PayPal Cohort Split & Stripe trial_end Unix",
        "meta_desc": "Why Lemon Squeezy PayPal subscriptions cannot auto-migrate to Stripe/Polar without buyer re-auth—and how to audit MRR-at-risk and compute exact trial_end Unix timestamps.",
        "symptom": "Founders exporting Lemon Squeezy subscribers face two silent disasters: missing PayPal billing-agreement non-portability and double-charging Card users due to ISO-date vs Unix-epoch `trial_end` formatting.",
        "root_cause": "Card tokens migrate via Stripe billing transfers, whereas PayPal recurring agreements belong to Lemon Squeezy as Merchant of Record and die unless subscribers click a fresh checkout link.",
        "headers": ["Lemon Squeezy Cohort", "Migration Reality", "LemonExitBridge Output"],
        "rows": [
            ["payment_method = card", "Portable to Stripe Billing via renews_at", "Generates Stripe Import CSV with exact Unix `trial_end`"],
            ["payment_method = paypal", "Non-portable MoR billing agreement", "Isolates PayPal Prorated Re-Auth CSV + credit days left"],
            ["status = cancelled / expired", "Must exclude active double-bill risk", "Filters cleanly & builds Legacy License Key map"],
        ],
        "snippet": "// Exact Unix trial_end timestamp prevents double-billing during mid-cycle cutover:\nconst trialEndUnix = Math.floor(new Date(row.renews_at).getTime() / 1000);",
        "steps": [
            "Measure your PayPal MRR at risk immediately with our free interactive Lemon Squeezy Shutdown Calculator.",
            "Upload your Lemon Squeezy Subscriptions + License Keys CSVs into LemonExitBridge locally (zero customer email uploads).",
            "Download the Stripe/Polar Subscription CSV, PayPal Prorated Re-Auth cohort, and legacy-keys.json.",
        ],
        "faqs": [
            ("Why do customer emails and license keys stay 100% safe?", "LemonExitBridge runs completely client-side in Chrome (and locally via `pip install lemonsqueezy-stripe-polar-migrator`)."),
            ("What if subscribers still have remaining paid days when PayPal stops?", "The PayPal Re-Auth Cohort CSV calculates exact remaining prorated credit days and creates a clean cutover schedule."),
        ],
    },
    {
        "slug": "lemon-squeezy-to-polar-legacy-license-keys",
        "product_slug": "lemonsqueezy-stripe-polar-migrator",
        "product_name": "LemonExitBridge",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "Preserve Legacy Lemon Squeezy License Keys When Moving to Stripe or Polar.sh",
        "h1": "How to Keep Existing Lemon Squeezy License Keys Working After Migrating to Stripe / Polar",
        "meta_desc": "Stop breaking existing paid users' desktop apps and CLI licenses during your Lemon Squeezy migration: export a deterministic legacy-keys.json lookup map.",
        "symptom": "Existing lifetime/annual users lose app activation the moment Lemon Squeezy's `/v1/licenses/validate` endpoint is turned off.",
        "root_cause": "Apps hardcoded against Lemon Squeezy license keys need an offline signed JSON map or local fallback validator preserving `key`, `status`, `customer_email`, and `activation_limit`.",
        "headers": ["Lemon Squeezy Key Field", "Migration Action", "Exported Key Map Field"],
        "rows": [
            ["key (UUID)", "Preserve exact customer string", "legacyKeys[uuid].key"],
            ["status (active / inactive)", "Snapshot validity before shutdown", "legacyKeys[uuid].valid = true/false"],
            ["activation_limit / count", "Retain machine cap parity", "legacyKeys[uuid].max_activations"],
        ],
        "snippet": "{\n  \"A1B2C3D4-E5F6-4789-ABCD-1234567890EF\": {\n    \"valid\": true,\n    \"email_hash\": \"sha256:...\",\n    \"plan\": \"pro_lifetime\",\n    \"max_activations\": 3\n  }\n}",
        "steps": [
            "Export your License Keys CSV from the Lemon Squeezy Dashboard.",
            "Load it into LemonExitBridge locally in Chrome or run `lemonsqueezy-stripe-polar-migrator`.",
            "Embed `legacy-keys.json` in a tiny Cloudflare Worker or offline verifier before March 31, 2027.",
        ],
        "faqs": [
            ("Can I run this alongside my Stripe subscription cutover CSV?", "Yes—LemonExitBridge generates both the Stripe/Polar migration CSVs and the `legacy-keys.json` bundle in one run."),
            ("Is there a recurring SaaS fee?", "No, €29 once (and the CLI is live on PyPI)."),
        ],
    },
    {
        "slug": "woocommerce-to-shopify-metafields-matrixify-csv",
        "product_slug": "woo-shopify-metafield-migrator",
        "product_name": "ShopMetaShift",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "WooCommerce to Shopify Migration: Fix >3 Attributes, Orphan Variants, Metafields & 301 Redirects",
        "h1": "Migrate WooCommerce CSVs to Shopify / Matrixify Without Orphaning Variants or Dropping Attributes 4+",
        "meta_desc": "Native Shopify CSV breaks on WooCommerce variable children, >3 product attributes, Yoast SEO metadata, GTINs, and old URLs. Convert locally in Chrome.",
        "symptom": "Uploading a standard WooCommerce Product Export CSV directly to Shopify drops Attribute 4+, disconnects variations (`id:101` vs SKU), ignores Yoast SEO titles, and breaks Google rankings without 301 redirects.",
        "root_cause": "Shopify enforces a hard 3-option limit on native variants and expects Matrixify `Metafield:` / `Variant Metafield:` headers plus strict Handle continuation rows with parent-only fields blanked.",
        "headers": ["WooCommerce CSV Pain Point", "Native Shopify Import Failure", "ShopMetaShift Automated Fix"],
        "rows": [
            ["`variable` + `variation` rows", "Variations become standalone broken products", "Stitches by `id:<ID>` or parent SKU & clears rows 2..N"],
            ["4+ Product Attributes", "Attributes 4+ silently discarded", "Promotes Attr 4+ to typed `Variant Metafield: custom.* [type]`"],
            ["Yoast / RankMath / COGS / GTIN", "Ignored in native CSV", "Maps to SEO Title, Description Tag, Cost per item & Variant Barcode"],
            ["`/product/<slug>/` SEO links", "404 errors after DNS cutover", "Outputs Shopify `/products/<handle>` 301 Redirects CSV"],
        ],
        "snippet": "Handle,Title,Option1 Name,Option1 Value,Option2 Name,Option2 Value,Option3 Name,Option3 Value,Variant Metafield: custom.wattage [number_integer],Variant SKU\nacme-lamp,Acme Lamp,Color,Black,Size,L,Material,Brass,60,ACME-BLK-L",
        "steps": [
            "Export Products from WooCommerce -> Products -> Export (include custom meta).",
            "Drop the CSV into ShopMetaShift locally in Chrome (up to 15 parent products free).",
            "Download Matrixify MERGE CSV + Shopify 301 Redirects CSV—zero Cart2Cart Admin API keys required.",
        ],
        "faqs": [
            ("Why use ShopMetaShift instead of connecting a €200 migration app to live admin APIs?", "Zero admin API credentials leave your store, no monthly recurring Matrixify fee needed for a one-time cutover, and you inspect every column before import."),
            ("Are internal WordPress `_edit_lock` keys filtered out?", "Yes, ShopMetaShift strips noisy WordPress internal meta keys automatically."),
        ],
    },
    {
        "slug": "amazon-settlement-report-v2-xero-quickbooks",
        "product_slug": "amazon-settlement-xero-qbo-splitter",
        "product_name": "AmzSettlementBridge",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "Split Amazon Seller Settlement Reports V2 Into Balanced Xero & QuickBooks Journals Locally",
        "h1": "Split Amazon Settlement Report V2 (.TSV/.TXT) Into Xero & QuickBooks Deposit Journals",
        "meta_desc": "Why recording raw Amazon bank deposits distorts P&L revenue and VAT: unpack Gross Sales, FBA Fees, Refunds, Promos & Reserves into balanced zero-diff journals locally.",
        "symptom": "QuickBooks and Xero treat each bi-weekly Amazon payout as net sales, understating gross turnover, hiding FBA/referral fees, and breaking VAT reconciliation.",
        "root_cause": "Each Amazon bank deposit is a net sum of dozens of Settlement Report V2 transaction types (`Principal`, `Commission`, `FBAPerUnitFulfillmentFee`, `Reserve`).",
        "headers": ["Amazon V2 Transaction Type", "Ledger Direction", "Account Bucket Mapped"],
        "rows": [
            ["Principal / Product Charges", "Credit (+)", "Amazon Gross Sales Revenue"],
            ["Commission / FBA / Storage Fees", "Debit (-)", "Marketplace Selling & Fulfillment Fees"],
            ["Tax / MarketplaceFacilitatorVAT", "Separate Tax Line", "Sales Tax / VAT Clearing"],
            ["Previous/Current Reserve Amount", "Balance Sheet Asset", "Amazon Seller Reserve Clearing (Net Sum = Deposit)"],
        ],
        "snippet": "pip install amazon-settlement-xero-qbo-splitter\namazon-settlement-xero-qbo-splitter --input ./settlements/ --format xero",
        "steps": [
            "Download Settlement Report V2 (Flat File V2) from Amazon Seller Central -> Payments -> All Statements.",
            "Load the TSV/TXT locally in AmzSettlementBridge to verify `Gross - Fees - Reserves == Bank Deposit`.",
            "Export balanced Xero Manual Journals or QuickBooks IIF/CSV—no A2X per-order monthly tax.",
        ],
        "faqs": [
            ("Do my Seller Central MWS / SP-API keys stay offline?", "Completely offline—AmzSettlementBridge requires zero Amazon API OAuth tokens."),
            ("Does the math verify exact deposit parity?", "Yes, journal debits and credits balance cleanly to match the exact bank clearing deposit."),
        ],
    },
    {
        "slug": "stripe-payout-reconciliation-xero-quickbooks",
        "product_slug": "stripe-payout-xero-qbo-splitter",
        "product_name": "StripePayoutBridge",
        "lang": "en",
        "sample_file": "sample-eu-oss-stripe-shopify.csv",
        "title": "Reconcile Stripe Payouts, Processing Fees & Refunds in Xero & QuickBooks Without Synder/A2X",
        "h1": "Split Net Stripe Bank Deposits Back into Gross Revenue, Fees & Refunds Locally",
        "meta_desc": "Stop letting Stripe Payouts lump net deposits into bank feeds: split Stripe Balance History CSVs into Gross Sales, Stripe Fees, Refunds & Disputes for Xero/QBO.",
        "symptom": "Stripe deposits €968.20 into your bank account while invoices total €1,000.00—leaving bookkeepers chasing exact €31.80 fee and dispute differences.",
        "root_cause": "Bank feeds show only net `payout` amounts, whereas Stripe's Balance Transactions CSV breaks down `charge`, `refund`, `adjustment`, and `fee` components per payout ID.",
        "headers": ["Stripe Balance CSV Row", "Accounting Entry", "Target Account"],
        "rows": [
            ["type = charge (Gross)", "Credit Sales Clearing", "Stripe Sales Clearing / Gross Revenue"],
            ["fee column (Processing)", "Debit Fee Expense", "Stripe Processing Fees Expense"],
            ["type = refund / dispute", "Debit Contra-Revenue", "Refunds & Chargebacks"],
            ["Payout Net Total", "Zero-Variance Match", "Matches Exact Bank Feed Deposit"],
        ],
        "snippet": "*JournalNumber,*Date,*Description,*AccountCode,*TaxRate,*Debit,*Credit\nSTR-PO-01,2026-11-15,Stripe Gross Sales,200,Tax Exempt,,1000.00\nSTR-PO-01,2026-11-15,Stripe Processing Fees,404,Tax Exempt,31.80,",
        "steps": [
            "Export Balance History / Payouts CSV from your Stripe Dashboard -> Balances -> Transactions.",
            "Drop the CSV into StripePayoutBridge right in Chrome (0 Stripe API keys or OAuth needed).",
            "Export Xero Journal CSV or QuickBooks Journal/CSV in seconds for a single €29 payment.",
        ],
        "faqs": [
            ("Can I try it without granting Synder or A2X read-access to my Stripe account?", "Yes, drop a CSV file locally with zero Stripe OAuth permissions."),
            ("Are multi-currency conversion fees handled?", "Yes, Stripe Balance Transactions export exact settlement-currency net and fee columns cleanly."),
        ],
    },
]


EU_VAT_RATES_2026: list[dict[str, Any]] = [
    {"iso": "AT", "bzst": "AT", "name": "Austria (Österreich)", "std": 20.0, "red": "10 / 13", "note": ""},
    {"iso": "BE", "bzst": "BE", "name": "Belgium (België/Belgique)", "std": 21.0, "red": "6 / 12", "note": ""},
    {"iso": "BG", "bzst": "BG", "name": "Bulgaria (България)", "std": 20.0, "red": "9", "note": ""},
    {"iso": "CY", "bzst": "CY", "name": "Cyprus (Κύπρος)", "std": 19.0, "red": "5 / 9", "note": ""},
    {"iso": "CZ", "bzst": "CZ", "name": "Czechia (Česko)", "std": 21.0, "red": "12", "note": ""},
    {"iso": "DE", "bzst": "DE", "name": "Germany (Deutschland)", "std": 19.0, "red": "7", "note": ""},
    {"iso": "DK", "bzst": "DK", "name": "Denmark (Danmark)", "std": 25.0, "red": "-", "note": ""},
    {"iso": "EE", "bzst": "EE", "name": "Estonia (Eesti)", "std": 24.0, "red": "9 / 13", "note": "24% standard rate (from July 2025+)"},
    {"iso": "GR", "bzst": "EL", "name": "Greece (Ελλάδα)", "std": 24.0, "red": "6 / 13", "note": "CRITICAL: Stripe/Shopify 'GR' MUST become 'EL' in BZSt/ROS!"},
    {"iso": "ES", "bzst": "ES", "name": "Spain (España)", "std": 21.0, "red": "4 / 10", "note": "Canary Islands (IC), Ceuta, Melilla outside EU VAT"},
    {"iso": "FI", "bzst": "FI", "name": "Finland (Suomi)", "std": 25.5, "red": "10 / 14", "note": "25.5% standard rate"},
    {"iso": "FR", "bzst": "FR", "name": "France", "std": 20.0, "red": "2.1 / 5.5 / 10", "note": "Monaco included as FR for EU OSS"},
    {"iso": "HR", "bzst": "HR", "name": "Croatia (Hrvatska)", "std": 25.0, "red": "5 / 13", "note": ""},
    {"iso": "HU", "bzst": "HU", "name": "Hungary (Magyarország)", "std": 27.0, "red": "5 / 18", "note": "Highest standard VAT in EU (27%)"},
    {"iso": "IE", "bzst": "IE", "name": "Ireland", "std": 23.0, "red": "9 / 13.5", "note": ""},
    {"iso": "IT", "bzst": "IT", "name": "Italy (Italia)", "std": 22.0, "red": "4 / 5 / 10", "note": ""},
    {"iso": "LT", "bzst": "LT", "name": "Lithuania (Lietuva)", "std": 21.0, "red": "5 / 9", "note": ""},
    {"iso": "LU", "bzst": "LU", "name": "Luxembourg", "std": 17.0, "red": "3 / 8 / 14", "note": "Lowest standard VAT in EU (17%)"},
    {"iso": "LV", "bzst": "LV", "name": "Latvia (Latvija)", "std": 21.0, "red": "5 / 12", "note": ""},
    {"iso": "MT", "bzst": "MT", "name": "Malta", "std": 18.0, "red": "5 / 7 / 12", "note": ""},
    {"iso": "NL", "bzst": "NL", "name": "Netherlands (Nederland)", "std": 21.0, "red": "9", "note": ""},
    {"iso": "PL", "bzst": "PL", "name": "Poland (Polska)", "std": 23.0, "red": "5 / 8", "note": ""},
    {"iso": "PT", "bzst": "PT", "name": "Portugal", "std": 23.0, "red": "6 / 13", "note": ""},
    {"iso": "RO", "bzst": "RO", "name": "Romania (România)", "std": 19.0, "red": "5 / 9", "note": ""},
    {"iso": "SE", "bzst": "SE", "name": "Sweden (Sverige)", "std": 25.0, "red": "6 / 12", "note": ""},
    {"iso": "SI", "bzst": "SI", "name": "Slovenia (Slovenija)", "std": 22.0, "red": "5 / 9.5", "note": ""},
    {"iso": "SK", "bzst": "SK", "name": "Slovakia (Slovensko)", "std": 23.0, "red": "5 / 19", "note": "23% standard rate"},
]


def _render_de_hub(
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    cards = "\n".join(
        f"""      <article class="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 flex flex-col justify-between">
        <div>
          <span class="rounded-full bg-indigo-500/15 border border-indigo-500/30 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-300">{html.escape(p["badge"])}</span>
          <h2 class="mt-3 text-lg font-bold text-white">{html.escape(p["h1"])}</h2>
          <p class="mt-2 text-sm text-slate-300">{html.escape(p["sub"])}</p>
        </div>
        <div class="mt-5 flex flex-wrap gap-3 pt-4 border-t border-slate-800">
          <a href="./{html.escape(p["dir"])}/index.html" class="rounded-lg bg-indigo-500 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-400">Deutsche Seite &amp; Details</a>
          <a href="../products/{html.escape(p["product_slug"])}/index.html?ref=src.de-hub#live-app" class="rounded-lg border border-slate-700 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800">Live-Tool öffnen &rarr;</a>
        </div>
      </article>"""
        for p in DE_PAGES
    )
    main_html = f"""    <section class="py-8 text-center">
      <span class="inline-block rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">DSGVO &amp; GoBD · 100 % LOKAL IM BROWSER</span>
      <h1 class="mt-4 text-3xl sm:text-4xl font-extrabold text-white">Deutsche Steuer-, E-Rechnungs- &amp; Bank-Tools — ohne Abo &amp; ohne Cloud</h1>
      <p class="mx-auto mt-3 max-w-2xl text-sm text-slate-300">
        XRechnung/ZUGFeRD nach DATEV EXTF, Sparkasse/VR CAMT.053 nach DATEV/QuickBooks/Xero und BZSt EU-OSS CSV — komplett lokal im Chrome-Speicher. Einmalig €29 pro Tool oder €49 für alle 13 Werkzeuge inklusive Stripe USt-Rechnung.
      </p>
      <div class="mt-6 flex flex-wrap justify-center gap-3">
        <a href="../tools/datev-bu-schluessel-lookup/index.html" class="rounded-xl bg-white px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-slate-200">Kostenloser BU-Schlüssel Rechner</a>
        <a href="../tools/eu-oss-vat-rates-2026/index.html" class="rounded-xl border border-slate-700 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800">EU-27 OSS MwSt-Sätze (inkl. GR→EL)</a>
      </div>
    </section>
    <section class="grid gap-6 md:grid-cols-3">
{cards}
    </section>"""
    extra_head = f"""  <link rel="alternate" hreflang="en" href="{SITE_BASE_URL}/" />
  <link rel="alternate" hreflang="de" href="{SITE_BASE_URL}/de/" />"""
    return _render_page_shell(
        title="Deutsche E-Rechnungs-, CAMT.053 & BZSt-OSS Tools ohne Abo — Friction-Killer Suite",
        description="XRechnung/ZUGFeRD zu DATEV EXTF, CAMT.053/MT940 zu DATEV/.QBO/Xero und BZSt OSS CSV lokal in Chrome erstellen. Null Server-Uploads.",
        canonical_url=f"{SITE_BASE_URL}/de/",
        lang="de",
        rel_root="../",
        main_html=main_html,
        analytics_slug="de_hub",
        analytics_title="Friction-Killer Suite DE",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
        extra_head=extra_head,
    )


def _render_de_product_page(
    spec: dict[str, Any],
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    checkout_url = STRIPE_LINKS.get(spec["product_slug"], bundle_checkout_url)
    bullets_html = "\n".join(
        f"""      <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 class="text-base font-bold text-white">{html.escape(t)}</h2>
        <p class="mt-2 text-sm text-slate-300">{html.escape(b)}</p>
      </div>"""
        for t, b in spec["bullets"]
    )
    faq_html = "\n".join(
        f"""      <div class="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
        <h3 class="font-semibold text-white">{html.escape(q)}</h3>
        <p class="mt-1 text-sm text-slate-300">{html.escape(a)}</p>
      </div>"""
        for q, a in spec["faqs"]
    )
    ld_faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in spec["faqs"]
        ],
    }
    de_url = f"{SITE_BASE_URL}/de/{spec['dir']}/"
    extra_head = "\n".join(
        [
            f'  <link rel="alternate" hreflang="de" href="{html.escape(de_url, quote=True)}" />',
            f'  <link rel="alternate" hreflang="en" href="{html.escape(spec["en_canonical"], quote=True)}" />',
            _json_ld_script(ld_faq),
        ]
    )
    main_html = f"""    <section class="py-8">
      <div class="flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <a href="../index.html" class="hover:text-white">Deutsch</a> / <span>{html.escape(spec["dir"])}</span>
      </div>
      <span class="mt-4 inline-block rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">{html.escape(spec["badge"])}</span>
      <h1 class="mt-4 text-3xl sm:text-4xl font-extrabold text-white">{html.escape(spec["h1"])}</h1>
      <p class="mt-4 max-w-3xl text-base leading-relaxed text-slate-300">{html.escape(spec["sub"])}</p>
      <div class="mt-6 flex flex-wrap gap-3">
        <a href="../../products/{html.escape(spec["product_slug"])}/index.html?ref=src.de-{html.escape(spec["dir"])}#live-app" class="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-slate-200">{html.escape(spec["primary_cta"])} &rarr;</a>
        <a href="{html.escape(checkout_url)}" data-fk-cta="pro-checkout" class="rounded-xl bg-indigo-500 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-400">Pro-Lizenz kaufen — €29 einmalig</a>
        <a href="{html.escape(spec["secondary_href"])}" class="rounded-xl border border-slate-700 px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-slate-800">{html.escape(spec["secondary_cta"])}</a>
      </div>
      <p class="mt-3 text-xs text-emerald-300">✓ Automatische Stripe USt-Rechnung (PDF) · ✓ 14 Tage Geld-zurück-Garantie · ✓ 0 Server-Uploads (im Chrome Netzwerk-Tab verifizierbar)</p>
    </section>

    <section class="grid gap-5 md:grid-cols-3 py-4">
{bullets_html}
    </section>

    <section class="my-8 rounded-2xl border border-indigo-500/30 bg-slate-900/70 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <div class="text-xs font-semibold uppercase tracking-wider text-indigo-300">Direkt testen ohne eigene Datei</div>
        <div class="mt-1 text-sm text-slate-200">Beispieldatei herunterladen oder Schritt-für-Schritt-Technikguide lesen.</div>
      </div>
      <div class="flex flex-wrap gap-3 shrink-0">
        <a href="{html.escape(spec["sample_href"])}" download class="rounded-lg border border-slate-700 px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-800">Testdatei laden</a>
        <a href="{html.escape(spec["guide_href"])}" class="rounded-lg bg-slate-800 px-3.5 py-2 text-xs font-semibold text-indigo-300 hover:bg-slate-700">Technischer Ratgeber &rarr;</a>
      </div>
    </section>

    <section class="py-6 space-y-4">
      <h2 class="text-2xl font-bold text-white">Häufige Fragen (DE / EU)</h2>
{faq_html}
    </section>"""
    return _render_page_shell(
        title=spec["title"],
        description=spec["description"],
        canonical_url=de_url,
        lang="de",
        rel_root="../../",
        main_html=main_html,
        analytics_slug=spec["slug"],
        analytics_title=spec["h1"],
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
        extra_head=extra_head,
    )


def _render_guides_index(
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    cards = "\n".join(
        f"""      <article class="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between gap-2 text-[11px]">
            <span class="rounded bg-indigo-500/15 px-2 py-0.5 font-semibold text-indigo-300">{html.escape(g["product_name"])}</span>
            <span class="uppercase text-slate-400">{html.escape(g["lang"])}</span>
          </div>
          <h2 class="mt-3 text-base font-bold text-white"><a href="./{html.escape(g["slug"])}/index.html" class="hover:text-indigo-300">{html.escape(g["h1"])}</a></h2>
          <p class="mt-2 text-xs text-slate-400">{html.escape(g["meta_desc"])}</p>
        </div>
        <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
          <a href="./{html.escape(g["slug"])}/index.html" class="font-semibold text-indigo-300 hover:text-white">Read Guide &rarr;</a>
          <a href="../products/{html.escape(g["product_slug"])}/index.html?ref=src.guides-hub#live-app" class="text-emerald-300 hover:underline">Open Web App</a>
        </div>
      </article>"""
        for g in GUIDES
    )
    main_html = f"""    <section class="py-8 text-center">
      <span class="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300">20 TECHNICAL TROUBLESHOOTING GUIDES</span>
      <h1 class="mt-4 text-3xl sm:text-4xl font-extrabold text-white">Error-Code, Bank-Feed &amp; E-Invoicing Fix Library</h1>
      <p class="mx-auto mt-3 max-w-2xl text-sm text-slate-300">Concrete tag mappings, schema checks, and zero-upload local workflows for QuickBooks OL-222, ISO 20022 CAMT.053, MT940, XRechnung EN 16931, DATEV BU-Schlüssel, BZSt GR→EL, Lemon Squeezy shutdown migrations, and Shopify CSVs.</p>
    </section>
    <section class="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
{cards}
    </section>"""
    return _render_page_shell(
        title="20 Technical Troubleshooting Guides — CAMT.053, XRechnung, BZSt OSS & Shopify | Friction-Killer Suite",
        description="Error-code guides and XML/CSV format references for QuickBooks OL-222, CAMT.053, MT940, XRechnung BR-CO-10/15, DATEV BU-Schlüssel, BZSt GR->EL, and Lemon Squeezy migration.",
        canonical_url=f"{SITE_BASE_URL}/guides/",
        lang="en",
        rel_root="../",
        main_html=main_html,
        analytics_slug="guides_index",
        analytics_title="Troubleshooting Guides Index",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
    )


def _render_single_guide(
    g: dict[str, Any],
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    checkout_url = STRIPE_LINKS.get(g["product_slug"], bundle_checkout_url)
    th_html = "".join(f'<th class="px-3 py-2 text-left">{html.escape(h)}</th>' for h in g["headers"])
    tr_html = "\n".join(
        "          <tr class='border-t border-slate-800'>"
        + "".join(f"<td class='px-3 py-2 text-slate-300'>{html.escape(cell)}</td>" for cell in row)
        + "</tr>"
        for row in g["rows"]
    )
    steps_html = "\n".join(
        f'        <li class="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-200"><strong class="text-indigo-300">Step {i}:</strong> {html.escape(st)}</li>'
        for i, st in enumerate(g["steps"], 1)
    )
    faq_html = "\n".join(
        f"""        <div class="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
          <h3 class="text-sm font-semibold text-white">{html.escape(q)}</h3>
          <p class="mt-1 text-xs text-slate-300">{html.escape(a)}</p>
        </div>"""
        for q, a in g["faqs"]
    )
    howto_ld = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": g["h1"],
        "description": g["meta_desc"],
        "step": [{"@type": "HowToStep", "position": i, "text": st} for i, st in enumerate(g["steps"], 1)],
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in g["faqs"]
        ],
    }
    de_alt = DE_ALTERNATES.get(g["product_slug"])
    alt_link = f'  <link rel="alternate" hreflang="de" href="{html.escape(de_alt, quote=True)}" />\n' if de_alt else ""
    extra_head = alt_link + _json_ld_script(howto_ld) + "\n" + _json_ld_script(faq_ld)
    cta_url = f"../../products/{g['product_slug']}/index.html?ref=guide.{g['slug']}#live-app"
    analytics_slug = f"guide_{g['slug'].replace('-', '_')}"[:64]

    main_html = f"""    <div class="text-xs text-slate-400"><a href="../index.html" class="text-indigo-300 hover:underline">&larr; All 20 Guides</a> · <span>{html.escape(g["product_name"])}</span></div>
    <article class="mt-4 space-y-8">
      <header class="space-y-4">
        <span class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">ZERO-UPLOAD LOCAL FIX · {html.escape(g["product_name"]).upper()}</span>
        <h1 class="text-3xl sm:text-4xl font-extrabold text-white">{html.escape(g["h1"])}</h1>
        <p class="text-base text-slate-300">{html.escape(g["meta_desc"])}</p>
        <div class="flex flex-wrap gap-3 pt-1">
          <a href="{html.escape(cta_url)}" class="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-slate-200">Launch {html.escape(g["product_name"])} Live in Browser &rarr;</a>
          <a href="{html.escape(checkout_url)}" data-fk-cta="pro-checkout" class="rounded-xl bg-indigo-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-400">Unlock Unlimited Pro — €29 once</a>
          <a href="../../samples/files/{html.escape(g["sample_file"])}" download class="rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-800">Download Sample File</a>
        </div>
      </header>

      <section class="grid gap-4 md:grid-cols-2">
        <div class="rounded-2xl border border-rose-500/30 bg-slate-900/60 p-5">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-rose-300">Exact Symptom</h2>
          <p class="mt-2 text-sm text-slate-200">{html.escape(g["symptom"])}</p>
        </div>
        <div class="rounded-2xl border border-indigo-500/30 bg-slate-900/60 p-5">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-indigo-300">Technical Root Cause</h2>
          <p class="mt-2 text-sm text-slate-200">{html.escape(g["root_cause"])}</p>
        </div>
      </section>

      <section class="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
        <table class="w-full text-xs sm:text-sm">
          <thead class="bg-slate-900 text-slate-400 uppercase text-[11px]"><tr>{th_html}</tr></thead>
          <tbody>
{tr_html}
          </tbody>
        </table>
      </section>

      <section class="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
        <h2 class="text-sm font-bold text-white">Verified Format / Code Snippet</h2>
        <pre class="mt-3 overflow-x-auto rounded-xl bg-slate-950 p-4 font-mono text-xs text-emerald-300">{html.escape(g["snippet"])}</pre>
      </section>

      <section class="space-y-3">
        <h2 class="text-xl font-bold text-white">Step-by-Step Local Resolution</h2>
        <ol class="space-y-2">
{steps_html}
        </ol>
      </section>

      <section class="space-y-3">
        <h2 class="text-xl font-bold text-white">Technical FAQ</h2>
        <div class="space-y-3">
{faq_html}
        </div>
      </section>
    </article>"""
    return _render_page_shell(
        title=f"{g['title']} | Friction-Killer Suite",
        description=g["meta_desc"],
        canonical_url=f"{SITE_BASE_URL}/guides/{g['slug']}/",
        lang=g["lang"],
        rel_root="../../",
        main_html=main_html,
        analytics_slug=analytics_slug,
        analytics_title=g["product_name"],
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
        extra_head=extra_head,
    )


def _render_tools_index(
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    tools = [
        ("eu-oss-vat-rates-2026", "2026 EU-27 OSS VAT Rates & BZSt GR→EL Checker", "Instant filterable Member-State VAT table, net/VAT/gross calculator, €10,000 threshold reminder, and Greece GR→EL warning.", "OssVatBridge"),
        ("lemon-squeezy-shutdown-calculator", "Lemon Squeezy March 31, 2027 Shutdown & PayPal MRR Calculator", "Compute exact PayPal revenue at churn risk, live shutdown countdown, and Stripe/Polar migration checklist.", "LemonExitBridge"),
        ("datev-bu-schluessel-lookup", "DATEV BU-Schlüssel & EN 16931 VAT Code Lookup (DE/EN)", "Interactive SKR03/SKR04 mapping between EN 16931 BT-118/BT-151 tax codes (S, AE, E, Z) and DATEV BU-Schlüssel (9, 8, 94, 0).", "EInvoiceLocal"),
    ]
    cards = "\n".join(
        f"""      <article class="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 flex flex-col justify-between">
        <div>
          <span class="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300">100% FREE · NO PAYWALL</span>
          <h2 class="mt-3 text-lg font-bold text-white">{html.escape(t)}</h2>
          <p class="mt-2 text-sm text-slate-300">{html.escape(d)}</p>
        </div>
        <div class="mt-5 pt-4 border-t border-slate-800 flex items-center justify-between text-xs">
          <a href="./{html.escape(slug)}/index.html" class="rounded-lg bg-white px-3.5 py-2 font-semibold text-slate-950 hover:bg-slate-200">Open Free Tool &rarr;</a>
          <span class="text-slate-400">Pairs with {html.escape(pair)}</span>
        </div>
      </article>"""
        for slug, t, d, pair in tools
    )
    main_html = f"""    <section class="py-8 text-center">
      <span class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">FREE DIAGNOSTIC TOOLS &amp; CALCULATORS</span>
      <h1 class="mt-4 text-3xl sm:text-4xl font-extrabold text-white">Free EU VAT, DATEV BU-Schlüssel &amp; SaaS Migration Calculators</h1>
      <p class="mx-auto mt-3 max-w-2xl text-sm text-slate-300">Bookmark-grade reference utilities running 100% in your browser—built for European founders, bookkeepers, and Steuerkanzleien.</p>
    </section>
    <section class="grid gap-6 md:grid-cols-3">
{cards}
    </section>"""
    return _render_page_shell(
        title="Free EU VAT OSS, DATEV BU-Schlüssel & Lemon Squeezy Shutdown Calculators | Friction-Killer Suite",
        description="Free browser-local interactive calculators: 2026 EU-27 VAT rates with BZSt GR->EL checker, Lemon Squeezy PayPal MRR risk calculator, and DATEV BU-Schlüssel lookup.",
        canonical_url=f"{SITE_BASE_URL}/tools/",
        lang="en",
        rel_root="../",
        main_html=main_html,
        analytics_slug="tools_index",
        analytics_title="Free Calculators Index",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
    )


def _render_tool_eu_oss_rates(
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    rates_json = json.dumps(EU_VAT_RATES_2026, ensure_ascii=False).replace("</", "<\\/")
    main_html = """    <div class="text-xs text-slate-400"><a href="../index.html" class="text-indigo-300 hover:underline">&larr; All Free Calculators</a></div>
    <section class="mt-4 space-y-6">
      <div>
        <span class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">FREE EU OSS REFERENCE · 27 MEMBER STATES</span>
        <h1 class="mt-3 text-3xl font-extrabold text-white">2026 EU-27 OSS VAT Rates, BZSt Portal Codes (<code>GR &rarr; EL</code>) &amp; Gross/Net Calculator</h1>
        <p class="mt-2 text-sm text-slate-300">Instantly verify EU One-Stop-Shop rates, avoid the classic Greece <code>GR</code> &rarr; <code>EL</code> BZSt rejection, or check whether cross-border B2C sales exceed the €10,000 Union threshold.</p>
      </div>

      <div class="grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 md:grid-cols-4">
        <div>
          <label for="vat-country" class="block text-xs font-semibold text-slate-300">Customer EU Country</label>
          <select id="vat-country" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"></select>
        </div>
        <div>
          <label for="vat-net" class="block text-xs font-semibold text-slate-300">Net Price (EUR)</label>
          <input id="vat-net" type="number" step="0.01" value="100.00" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
        </div>
        <div>
          <label for="eu-cross-total" class="block text-xs font-semibold text-slate-300">Annual EU Cross-Border B2C (EUR)</label>
          <input id="eu-cross-total" type="number" step="100" value="12500" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
        </div>
        <div class="flex items-end">
          <button id="app-run-btn" type="button" class="w-full rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-400">Calculate VAT &amp; OSS</button>
        </div>
      </div>

      <div id="vat-calc-result" class="grid gap-4 sm:grid-cols-3">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">BZSt / ROS Country Code</div>
          <div id="out-bzst-code" class="mt-1 text-2xl font-extrabold text-indigo-300">DE</div>
          <div id="out-code-note" class="mt-1 text-xs text-slate-400">Standard rate: 19%</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">VAT + Payable Gross (EUR)</div>
          <div id="out-gross" class="mt-1 text-2xl font-extrabold text-white">€119.00</div>
          <div id="out-vat" class="mt-1 text-xs text-emerald-300">VAT: €19.00</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">€10,000 EU OSS Threshold Status</div>
          <div id="out-thresh" class="mt-1 text-lg font-bold text-amber-300">EU OSS REQUIRED</div>
          <div class="mt-1 text-xs text-slate-400">Threshold is total cross-border EU B2C combined</div>
        </div>
      </div>

      <div class="rounded-2xl border border-indigo-500/40 bg-indigo-950/30 p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="text-sm text-slate-200">Need to turn quarterly <strong>Stripe Tax, Shopify, or Lemon Squeezy CSVs</strong> into a validated <strong>BZSt BOP (;-CSV)</strong> or <strong>Ireland ROS XML</strong> without Excel errors?</div>
        <a href="../../products/eu-oss-vat-return-compiler/index.html?ref=src.tool-oss-rates#live-app" class="shrink-0 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-slate-950 hover:bg-slate-200">Compile CSVs in OssVatBridge &rarr;</a>
      </div>

      <div class="space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-lg font-bold text-white">Complete EU-27 Reference Table</h2>
          <input id="vat-filter" type="text" placeholder="Filter country or code (e.g. Greece, EL, Germany)..." class="w-full sm:w-72 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-white" />
        </div>
        <div class="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
          <table class="w-full text-xs">
            <thead class="bg-slate-900 text-slate-400 uppercase text-[11px]">
              <tr><th class="px-3 py-2 text-left">ISO2</th><th class="px-3 py-2 text-left">BZSt / ROS</th><th class="px-3 py-2 text-left">Member State</th><th class="px-3 py-2 text-right">Standard</th><th class="px-3 py-2 text-left">Reduced</th><th class="px-3 py-2 text-left">Notes</th></tr>
            </thead>
            <tbody id="vat-table-body"></tbody>
          </table>
        </div>
      </div>
    </section>"""
    extra_script = f"""  <script>
    (function () {{
      const RATES = {rates_json};
      const sel = document.getElementById("vat-country");
      const netEl = document.getElementById("vat-net");
      const crossEl = document.getElementById("eu-cross-total");
      const filterEl = document.getElementById("vat-filter");
      const tbody = document.getElementById("vat-table-body");

      RATES.forEach((r) => {{
        const opt = document.createElement("option");
        opt.value = r.iso;
        opt.textContent = r.name + " (" + r.std + "%)";
        if (r.iso === "GR") opt.selected = true;
        sel.appendChild(opt);
      }});

      function updateCalc() {{
        const row = RATES.find((r) => r.iso === sel.value) || RATES[0];
        const net = Number(netEl.value || 0);
        const cross = Number(crossEl.value || 0);
        const vat = +(net * (row.std / 100)).toFixed(2);
        const gross = +(net + vat).toFixed(2);
        document.getElementById("out-bzst-code").textContent = row.iso === row.bzst ? row.bzst : row.iso + " -> " + row.bzst;
        document.getElementById("out-code-note").textContent = row.note || ("Standard rate: " + row.std + "% · Reduced: " + row.red + "%");
        document.getElementById("out-gross").textContent = "€" + gross.toFixed(2);
        document.getElementById("out-vat").textContent = "VAT (" + row.std + "%): €" + vat.toFixed(2);
        const thEl = document.getElementById("out-thresh");
        thEl.textContent = cross > 10000 ? "EU OSS REQUIRED (> €10,000)" : "Below €10,000 threshold (optional)";
        thEl.className = cross > 10000 ? "mt-1 text-lg font-bold text-amber-300" : "mt-1 text-lg font-bold text-emerald-300";
      }}

      function renderTable(q) {{
        const term = String(q || "").trim().toLowerCase();
        tbody.innerHTML = RATES.filter((r) =>
          !term || r.name.toLowerCase().includes(term) || r.iso.toLowerCase().includes(term) || r.bzst.toLowerCase().includes(term)
        ).map((r) =>
          "<tr class='border-t border-slate-800'>" +
          "<td class='px-3 py-2 font-mono text-slate-300'>" + r.iso + "</td>" +
          "<td class='px-3 py-2 font-mono font-bold " + (r.iso !== r.bzst ? "text-amber-300" : "text-indigo-300") + "'>" + r.bzst + "</td>" +
          "<td class='px-3 py-2 text-white'>" + r.name + "</td>" +
          "<td class='px-3 py-2 text-right font-mono text-emerald-300'>" + r.std + "%</td>" +
          "<td class='px-3 py-2 text-slate-300'>" + r.red + "</td>" +
          "<td class='px-3 py-2 text-slate-400'>" + (r.note || "—") + "</td>" +
          "</tr>"
        ).join("");
      }}

      document.getElementById("app-run-btn")?.addEventListener("click", updateCalc);
      sel?.addEventListener("change", updateCalc);
      filterEl?.addEventListener("input", () => renderTable(filterEl.value));
      updateCalc();
      renderTable("");
    }})();
  </script>"""
    return _render_page_shell(
        title="2026 EU-27 OSS VAT Rates & BZSt GR->EL Code Checker | Friction-Killer Suite",
        description="Free interactive EU-27 VAT rates reference (2026), BZSt portal country code checker highlighting GR->EL, net/VAT/gross calculator, and €10,000 OSS threshold helper.",
        canonical_url=f"{SITE_BASE_URL}/tools/eu-oss-vat-rates-2026/",
        lang="en",
        rel_root="../../",
        main_html=main_html,
        analytics_slug="tool_eu_oss_vat_rates_2026",
        analytics_title="EU OSS VAT Rates Calculator",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
        extra_script=extra_script,
    )


def _render_tool_lemon_calc(
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    main_html = """    <div class="text-xs text-slate-400"><a href="../index.html" class="text-indigo-300 hover:underline">&larr; All Free Calculators</a></div>
    <section class="mt-4 space-y-6">
      <div>
        <span class="rounded-full border border-rose-500/30 bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-300">LEMON SQUEEZY SHUTDOWN AUDIT · MARCH 31, 2027</span>
        <h1 class="mt-3 text-3xl font-extrabold text-white">Lemon Squeezy PayPal MRR Risk &amp; Shutdown Migration Calculator</h1>
        <p class="mt-2 text-sm text-slate-300">Estimate how much recurring revenue is trapped inside non-portable PayPal billing agreements before Lemon Squeezy winds down, and calculate your exact pre-cutover runway.</p>
      </div>

      <div class="grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 md:grid-cols-4">
        <div>
          <label for="ls-mrr" class="block text-xs font-semibold text-slate-300">Total Monthly MRR (€ or $)</label>
          <input id="ls-mrr" type="number" step="50" value="4000" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
        </div>
        <div>
          <label for="ls-paypal-pct" class="block text-xs font-semibold text-slate-300">PayPal Subscriber Share (%)</label>
          <input id="ls-paypal-pct" type="number" min="0" max="100" value="28" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
        </div>
        <div>
          <label for="ls-keys" class="block text-xs font-semibold text-slate-300">Active Legacy License Keys</label>
          <input id="ls-keys" type="number" min="0" value="350" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white" />
        </div>
        <div class="flex items-end">
          <button id="app-run-btn" type="button" class="w-full rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-400">Audit Exposure</button>
        </div>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">Days Until March 31, 2027 Shutdown</div>
          <div id="ls-days" class="mt-1 text-2xl font-extrabold text-amber-300">—</div>
          <div class="mt-1 text-xs text-slate-400">Recommended cutover: at least 60 days prior</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">Non-Portable PayPal MRR At Risk</div>
          <div id="ls-risk-mrr" class="mt-1 text-2xl font-extrabold text-rose-400">—</div>
          <div id="ls-annual-risk" class="mt-1 text-xs text-slate-400">12-month ARR at risk: —</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">Portable Card MRR (trial_end CSV)</div>
          <div id="ls-card-mrr" class="mt-1 text-2xl font-extrabold text-emerald-300">—</div>
          <div id="ls-key-note" class="mt-1 text-xs text-slate-400">Legacy keys needing JSON map: —</div>
        </div>
      </div>

      <div class="rounded-2xl border border-indigo-500/40 bg-indigo-950/30 p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="text-sm text-slate-200">Ready to split your real Lemon Squeezy Subscriptions CSV into <strong>Stripe/Polar Card CSV (with Unix <code>trial_end</code>)</strong> + <strong>PayPal Prorated Re-Auth Cohort</strong> + <code>legacy-keys.json</code> locally?</div>
        <a href="../../products/lemonsqueezy-stripe-polar-migrator/index.html?ref=src.tool-lemon-calc#live-app" class="shrink-0 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-slate-950 hover:bg-slate-200">Audit CSV in LemonExitBridge &rarr;</a>
      </div>
    </section>"""
    extra_script = """  <script>
    (function () {
      function calc() {
        const mrr = Number(document.getElementById("ls-mrr").value || 0);
        const pp = Math.min(100, Math.max(0, Number(document.getElementById("ls-paypal-pct").value || 0)));
        const keys = Number(document.getElementById("ls-keys").value || 0);
        const ppMrr = +(mrr * (pp / 100)).toFixed(2);
        const cardMrr = +(mrr - ppMrr).toFixed(2);
        const shutdownMs = new Date("2027-03-31T00:00:00Z").getTime();
        const days = Math.max(0, Math.ceil((shutdownMs - Date.now()) / 86400000));
        document.getElementById("ls-days").textContent = days + " days";
        document.getElementById("ls-risk-mrr").textContent = ppMrr.toLocaleString("en-US", { minimumFractionDigits: 2 }) + "/mo";
        document.getElementById("ls-annual-risk").textContent = "12-month ARR needing re-auth: " + (ppMrr * 12).toLocaleString("en-US", { minimumFractionDigits: 2 }) + "/yr";
        document.getElementById("ls-card-mrr").textContent = cardMrr.toLocaleString("en-US", { minimumFractionDigits: 2 }) + "/mo";
        document.getElementById("ls-key-note").textContent = keys + " active keys need deterministic legacy-keys.json export";
      }
      document.getElementById("app-run-btn")?.addEventListener("click", calc);
      ["ls-mrr", "ls-paypal-pct", "ls-keys"].forEach((id) => document.getElementById(id)?.addEventListener("input", calc));
      calc();
    })();
  </script>"""
    return _render_page_shell(
        title="Lemon Squeezy Shutdown Calculator (PayPal MRR Churn Risk & Countdown) | Friction-Killer Suite",
        description="Calculate exact PayPal subscription MRR at risk before Lemon Squeezy winds down on March 31, 2027, plus portable Card MRR and legacy key export scope.",
        canonical_url=f"{SITE_BASE_URL}/tools/lemon-squeezy-shutdown-calculator/",
        lang="en",
        rel_root="../../",
        main_html=main_html,
        analytics_slug="tool_lemon_squeezy_calc",
        analytics_title="Lemon Squeezy Shutdown Calculator",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
        extra_script=extra_script,
    )


def _render_tool_datev_bu_lookup(
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    main_html = """    <div class="text-xs text-slate-400"><a href="../index.html" class="text-indigo-300 hover:underline">&larr; All Free Calculators</a></div>
    <section class="mt-4 space-y-6">
      <div>
        <span class="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300">DE / EN · EN 16931 &rarr; DATEV EXTF</span>
        <h1 class="mt-3 text-3xl font-extrabold text-white">DATEV BU-Schlüssel &amp; EN 16931 (<code>BT-118</code> / <code>BT-151</code>) Steuer-Lookup</h1>
        <p class="mt-2 text-sm text-slate-300">Ermitteln Sie sofort den passenden DATEV-Steuerschlüssel (BU-Schlüssel) und das SKR03/SKR04-Konto aus XRechnung- und ZUGFeRD-XML-Kategorien.</p>
      </div>

      <div class="grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 md:grid-cols-3">
        <div>
          <label for="bu-scenario" class="block text-xs font-semibold text-slate-300">Rechnungsszenario / EN 16931 Code</label>
          <select id="bu-scenario" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
            <option value="S19">Inland Eingangsrechnung 19 % (Code S, 19%)</option>
            <option value="S7">Inland Eingangsrechnung 7 % (Code S, 7%)</option>
            <option value="AE">EU / § 13b Reverse Charge (Code AE, 0%)</option>
            <option value="E0">Steuerfrei / Kleinunternehmer § 19 UStG (Code E / O / Z)</option>
            <option value="K0">Innergemeinschaftlicher Erwerb (Code K, 19% fällig)</option>
          </select>
        </div>
        <div>
          <label for="bu-chart" class="block text-xs font-semibold text-slate-300">Kontenrahmen</label>
          <select id="bu-chart" class="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
            <option value="SKR03">SKR03 (Standard Gewerbe)</option>
            <option value="SKR04">SKR04 (Abschlussgliederung)</option>
          </select>
        </div>
        <div class="flex items-end">
          <button id="app-run-btn" type="button" class="w-full rounded-xl bg-indigo-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-400">BU-Schlüssel anzeigen</button>
        </div>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">DATEV BU-Schlüssel</div>
          <div id="bu-out-key" class="mt-1 text-3xl font-extrabold text-indigo-300">9</div>
          <div id="bu-out-label" class="mt-1 text-xs text-slate-300">19 % Vorsteuer</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">Standard-Aufwandskonto</div>
          <div id="bu-out-acct" class="mt-1 text-3xl font-extrabold text-white">3400</div>
          <div id="bu-out-chart" class="mt-1 text-xs text-slate-400">SKR03 Standard</div>
        </div>
        <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div class="text-xs text-slate-400">EN 16931 XML Tag (BT-151)</div>
          <div id="bu-out-xml" class="mt-1 text-xl font-bold font-mono text-emerald-300">CategoryCode: S (19%)</div>
          <div class="mt-1 text-xs text-slate-400">Gültig für UBL 2.1 &amp; ZUGFeRD CII</div>
        </div>
      </div>

      <div class="rounded-2xl border border-indigo-500/40 bg-indigo-950/30 p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="text-sm text-slate-200">Automatisch Dutzende <strong>XRechnung-, ZUGFeRD- &amp; Peppol-XMLs</strong> lokal mit diesem BU-Schlüssel in <strong>DATEV EXTF CSV</strong> umwandeln?</div>
        <a href="../../products/e-invoice-xml-batch-converter/index.html?ref=src.tool-bu-lookup#live-app" class="shrink-0 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-slate-950 hover:bg-slate-200">EInvoiceLocal starten &rarr;</a>
      </div>
    </section>"""
    extra_script = """  <script>
    (function () {
      const MAP = {
        S19: { key: "9", label: "19 % abziehbare Vorsteuer", SKR03: "3400", SKR04: "5400", xml: "CategoryCode: S (19%)" },
        S7:  { key: "8", label: "7 % abziehbare Vorsteuer", SKR03: "3300", SKR04: "5300", xml: "CategoryCode: S (7%)" },
        AE:  { key: "94", label: "§ 13b UStG Reverse Charge (19 % VSt + USt)", SKR03: "3123", SKR04: "5923", xml: "CategoryCode: AE (0%)" },
        E0:  { key: "0", label: "Steuerfrei / Kein Vorsteuerabzug", SKR03: "3425", SKR04: "5200", xml: "CategoryCode: E / O / Z" },
        K0:  { key: "19", label: "Innergemeinschaftlicher Erwerb (Standard 19 %)", SKR03: "3425", SKR04: "5425", xml: "CategoryCode: K (0%/19%)" }
      };
      function update() {
        const s = MAP[document.getElementById("bu-scenario").value] || MAP.S19;
        const chart = document.getElementById("bu-chart").value || "SKR03";
        document.getElementById("bu-out-key").textContent = s.key;
        document.getElementById("bu-out-label").textContent = s.label;
        document.getElementById("bu-out-acct").textContent = s[chart];
        document.getElementById("bu-out-chart").textContent = chart + " Kontenvorschlag";
        document.getElementById("bu-out-xml").textContent = s.xml;
      }
      document.getElementById("app-run-btn")?.addEventListener("click", update);
      document.getElementById("bu-scenario")?.addEventListener("change", update);
      document.getElementById("bu-chart")?.addEventListener("change", update);
      update();
    })();
  </script>"""
    return _render_page_shell(
        title="DATEV BU-Schlüssel & EN 16931 (BT-151) Lookup | Friction-Killer Suite",
        description="Free interactive DE/EN lookup mapping XRechnung & ZUGFeRD EN 16931 VAT categories (S, AE, E, Z, K) to DATEV BU-Schlüssel (9, 8, 94, 0) and SKR03/SKR04 accounts.",
        canonical_url=f"{SITE_BASE_URL}/tools/datev-bu-schluessel-lookup/",
        lang="de",
        rel_root="../../",
        main_html=main_html,
        analytics_slug="tool_datev_bu_lookup",
        analytics_title="DATEV BU-Schlüssel Lookup",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
        extra_script=extra_script,
    )


def _write_sample_fixtures(samples_files_dir: Path) -> list[dict[str, str]]:
    samples_files_dir.mkdir(parents=True, exist_ok=True)
    fixtures = [
        {
            "filename": "sample-xrechnung-3.0-ubl.xml",
            "title": "XRechnung 3.0 OASIS UBL 2.1 Invoice (Balanced 19% VAT)",
            "product_slug": "e-invoice-xml-batch-converter",
            "product_name": "EInvoiceLocal",
            "content": """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>
  <cbc:ID>XR-SAMPLE-2026-1001</cbc:ID>
  <cbc:IssueDate>2026-11-18</cbc:IssueDate>
  <cbc:DueDate>2026-12-02</cbc:DueDate>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>991-12345-67</cbc:BuyerReference>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyName><cbc:Name>NordWerk Software GmbH</cbc:Name></cac:PartyName><cac:PartyTaxScheme><cbc:CompanyID>DE298765432</cbc:CompanyID></cac:PartyTaxScheme></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyName><cbc:Name>Muster Handel GmbH</cbc:Name></cac:PartyName><cac:PartyTaxScheme><cbc:CompanyID>DE123456789</cbc:CompanyID></cac:PartyTaxScheme></cac:Party></cac:AccountingCustomerParty>
  <cac:PaymentMeans><cac:PayeeFinancialAccount><cbc:ID>DE89370400440532013000</cbc:ID></cac:PayeeFinancialAccount></cac:PaymentMeans>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">38.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="EUR">200.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="EUR">200.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="EUR">238.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="EUR">238.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="HUR">2.00</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="EUR">200.00</cbc:LineExtensionAmount>
    <cac:Item><cbc:Name>ERP Schnittstellenberatung</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="EUR">100.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
</Invoice>
""",
        },
        {
            "filename": "sample-zugferd-cii-en16931.xml",
            "title": "ZUGFeRD 2.x UN/CEFACT CII XML Invoice (Balanced 7% VAT)",
            "product_slug": "e-invoice-xml-batch-converter",
            "product_name": "EInvoiceLocal",
            "content": """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocument><ram:ID>ZF-SAMPLE-2026-2002</ram:ID><ram:IssueDateTime><udt:DateTimeString format="102">20261119</udt:DateTimeString></ram:IssueDateTime></rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:SpecifiedLineTradeProduct><ram:Name>Fachbuch E-Rechnung &amp; DATEV</ram:Name></ram:SpecifiedLineTradeProduct>
      <ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="C62">1.00</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement><ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>7</ram:RateApplicablePercent></ram:ApplicableTradeTax><ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty><ram:Name>Alpen Fachverlag GmbH</ram:Name><ram:SpecifiedTaxRegistration><ram:ID>DE811223344</ram:ID></ram:SpecifiedTaxRegistration></ram:SellerTradeParty>
      <ram:BuyerTradeParty><ram:Name>Muster Handel GmbH</ram:Name><ram:SpecifiedTaxRegistration><ram:ID>DE123456789</ram:ID></ram:SpecifiedTaxRegistration></ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:LineTotalAmount>100.00</ram:LineTotalAmount>
        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">7.00</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>107.00</ram:GrandTotalAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
""",
        },
        {
            "filename": "sample-peppol-bis3-invoice.xml",
            "title": "Peppol BIS Billing 3.0 XML Invoice (Reverse Charge AE)",
            "product_slug": "e-invoice-xml-batch-converter",
            "product_name": "EInvoiceLocal",
            "content": """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0</cbc:CustomizationID>
  <cbc:ID>PEP-SAMPLE-2026-3003</cbc:ID>
  <cbc:IssueDate>2026-11-20</cbc:IssueDate>
  <cbc:DueDate>2026-12-20</cbc:DueDate>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cbc:BuyerReference>PO-BE-2026-09</cbc:BuyerReference>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyName><cbc:Name>Brussels Cloud BV</cbc:Name></cac:PartyName><cac:PartyTaxScheme><cbc:CompanyID>BE0999888777</cbc:CompanyID></cac:PartyTaxScheme></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyName><cbc:Name>Muster Handel GmbH</cbc:Name></cac:PartyName><cac:PartyTaxScheme><cbc:CompanyID>DE123456789</cbc:CompanyID></cac:PartyTaxScheme></cac:Party></cac:AccountingCustomerParty>
  <cac:PaymentMeans><cac:PayeeFinancialAccount><cbc:ID>BE68539007547034</cbc:ID></cac:PayeeFinancialAccount></cac:PaymentMeans>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">0.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="EUR">450.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="EUR">450.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="EUR">450.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="EUR">450.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">1.00</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="EUR">450.00</cbc:LineExtensionAmount>
    <cac:Item><cbc:Name>Cross-border EU SaaS Consulting (Reverse Charge §13b)</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>AE</cbc:ID><cbc:Percent>0</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="EUR">450.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
</Invoice>
""",
        },
        {
            "filename": "sample-camt053-001-08-sepa-batch.xml",
            "title": "ISO 20022 CAMT.053.001.08 Statement (Multi-<TxDtls> SEPA Batch + Balance Check)",
            "product_slug": "camt053-mt940-qbo-xero-converter",
            "product_name": "BankFeedBridge",
            "content": """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
  <BkToCstmrStmt>
    <Stmt>
      <Id>STMT-SAMPLE-2026-11</Id>
      <Acct><Id><IBAN>DE89370400440532013000</IBAN></Id><Ccy>EUR</Ccy></Acct>
      <Bal><Tp><CdOrPrtry><Cd>OPBD</Cd></CdOrPrtry></Tp><Amt Ccy="EUR">10000.00</Amt><CdtDbtInd>CRDT</CdtDbtInd><Dt><Dt>2026-11-01</Dt></Dt></Bal>
      <Bal><Tp><CdOrPrtry><Cd>CLBD</Cd></CdOrPrtry></Tp><Amt Ccy="EUR">11845.50</Amt><CdtDbtInd>CRDT</CdtDbtInd><Dt><Dt>2026-11-12</Dt></Dt></Bal>
      <Ntry>
        <Amt Ccy="EUR">2500.00</Amt><CdtDbtInd>CRDT</CdtDbtInd><BookgDt><Dt>2026-11-10</Dt></BookgDt><AcctSvcrRef>REF-SAMPLE-001</AcctSvcrRef>
        <NtryDtls>
          <TxDtls><Refs><EndToEndId>E2E-101</EndToEndId></Refs><AmtDtls><TxAmt><Amt Ccy="EUR">1500.00</Amt></TxAmt></AmtDtls><RltdPties><Dbtr><Nm>Acme GmbH</Nm></Dbtr></RltdPties><RmtInf><Ustrd>Invoice 2026-101</Ustrd></RmtInf></TxDtls>
          <TxDtls><Refs><EndToEndId>E2E-102</EndToEndId></Refs><AmtDtls><TxAmt><Amt Ccy="EUR">1000.00</Amt></TxAmt></AmtDtls><RltdPties><Dbtr><Nm>Globex BV</Nm></Dbtr></RltdPties><RmtInf><Ustrd>Invoice 2026-102</Ustrd></RmtInf></TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">654.50</Amt><CdtDbtInd>DBIT</CdtDbtInd><BookgDt><Dt>2026-11-11</Dt></BookgDt><AcctSvcrRef>REF-SAMPLE-002</AcctSvcrRef>
        <NtryDtls><TxDtls><Refs><EndToEndId>E2E-99</EndToEndId></Refs><RltdPties><Cdtr><Nm>Hetzner Online GmbH</Nm></Cdtr></RltdPties><RmtInf><Ustrd>Server Hosting Nov</Ustrd></RmtInf></TxDtls></NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
""",
        },
        {
            "filename": "sample-swift-mt940-statement.sta",
            "title": "SWIFT MT940 Statement (.STA with :86: ?20..?38 Structured Subfields)",
            "product_slug": "camt053-mt940-qbo-xero-converter",
            "product_name": "BankFeedBridge",
            "content": """:20:SAMPLE202611
:25:NL91ABNA0417164300
:28C:00001/001
:60F:C261101EUR5000,00
:61:2611031103CR1250,00NTRFINV101
:86:051?20Payment Invoice 101?32NordWerk GmbH?38DE44500105175407324931
:61:2611051105DR265,25NTRFFEES99
:86:166?20Cloud SaaS Fee?32Linear Software Inc?38US000000000001
:62F:C261105EUR5984,75
-
""",
        },
        {
            "filename": "sample-eu-oss-stripe-shopify.csv",
            "title": "Multi-Country EU OSS Sample CSV (Includes DE Domestic, GR Greece & Refund)",
            "product_slug": "eu-oss-vat-return-compiler",
            "product_name": "OssVatBridge",
            "content": """source,order_id,customer_country,currency,net_amount,tax_amount,tax_rate,tx_type,supply_type,customer_vat_id
stripe_tax,st_sample_01,FR,EUR,100.00,20.00,20.0,sale,SERVICES,
stripe_tax,st_sample_02,GR,EUR,100.00,24.00,24.0,sale,SERVICES,
stripe_tax,st_sample_03,FR,EUR,25.00,5.00,20.0,refund,SERVICES,
shopify,sh_sample_04,NL,EUR,50.00,10.50,21.0,sale,GOODS,
shopify,sh_sample_05,DE,EUR,80.00,15.20,19.0,sale,GOODS,
stripe_tax,st_sample_06,IT,EUR,200.00,0.00,0.0,sale,SERVICES,IT12345678901
""",
        },
    ]
    for fx in fixtures:
        (samples_files_dir / fx["filename"]).write_text(fx["content"], encoding="utf-8")
    return fixtures


def _render_samples_index(
    fixtures: list[dict[str, str]],
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    cards = "\n".join(
        f"""      <article class="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 flex flex-col justify-between">
        <div>
          <span class="rounded-full bg-indigo-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-300">{html.escape(fx["product_name"])}</span>
          <h2 class="mt-3 text-base font-bold text-white">{html.escape(fx["title"])}</h2>
          <p class="mt-2 font-mono text-xs text-slate-400">{html.escape(fx["filename"])}</p>
        </div>
        <div class="mt-5 pt-4 border-t border-slate-800 flex flex-wrap gap-2.5 text-xs">
          <a href="./files/{html.escape(fx["filename"])}" download class="rounded-lg bg-white px-3.5 py-2 font-semibold text-slate-950 hover:bg-slate-200">Download File</a>
          <a href="../products/{html.escape(fx["product_slug"])}/index.html?ref=src.samples#live-app" class="rounded-lg border border-slate-700 px-3.5 py-2 font-semibold text-slate-200 hover:bg-slate-800">Test Live &rarr;</a>
        </div>
      </article>"""
        for fx in fixtures
    )
    main_html = f"""    <section class="py-8 text-center">
      <span class="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300">OPEN SAMPLE TEST FIXTURES</span>
      <h1 class="mt-4 text-3xl sm:text-4xl font-extrabold text-white">Validated XRechnung, ZUGFeRD, Peppol, CAMT.053 &amp; MT940 Sample Files</h1>
      <p class="mx-auto mt-3 max-w-2xl text-sm text-slate-300">Clean, anonymized, mathematically balanced sample fixtures for developers, QA engineers, and bookkeepers testing ERP imports or local browser converters.</p>
    </section>
    <section class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
{cards}
    </section>"""
    return _render_page_shell(
        title="Free Sample XRechnung, ZUGFeRD, CAMT.053, MT940 & EU OSS Test Files | Friction-Killer Suite",
        description="Download valid, balanced test fixtures for XRechnung 3.0 UBL, ZUGFeRD CII, Peppol BIS 3.0, ISO 20022 CAMT.053 SEPA batch XML, SWIFT MT940 .sta, and EU OSS CSV.",
        canonical_url=f"{SITE_BASE_URL}/samples/",
        lang="en",
        rel_root="../",
        main_html=main_html,
        analytics_slug="samples_index",
        analytics_title="Open Sample Fixtures",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
    )


def _render_partners_page(
    bundle_checkout_url: str,
    analytics_cfg: dict[str, str],
    legal_footer_html: str,
    analytics_renderer: Callable[..., str] | None,
) -> str:
    main_html = f"""    <section class="py-8">
      <span class="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">FOR STEUERKANZLEIEN, XERO/QBO ADVISORS &amp; SHOPIFY AGENCIES</span>
      <h1 class="mt-4 text-3xl sm:text-4xl font-extrabold text-white">Process Unlimited Client Bank Statements, E-Invoices &amp; Migrations with Zero Cloud Exposure</h1>
      <p class="mt-3 max-w-3xl text-base text-slate-300">
        Accounting practices and migration agencies waste hours fighting broken SaaS connectors and GDPR data-processing hurdles. Equip your team with deterministic browser-local utilities and offline Python CLIs—for a one-time €49 Practice Suite fee.
      </p>
      <div class="mt-6 flex flex-wrap gap-3">
        <a href="{html.escape(bundle_checkout_url)}" data-fk-cta="pro-checkout" class="rounded-xl bg-indigo-500 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-400">Unlock All 13 Tools for Your Practice — €49 once</a>
        <a href="mailto:dom.stijn99@gmail.com?subject=Partner%20%2F%20Practice%20Inquiry%20-%20Friction-Killer%20Suite" data-fk-cta="feedback" class="rounded-xl border border-slate-700 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800">Request Custom Bank / Format Support &rarr;</a>
      </div>
    </section>

    <section class="grid gap-6 md:grid-cols-3 py-4">
      <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 class="text-lg font-bold text-white">1. DACH Steuerberater &amp; Buchhalter</h2>
        <p class="mt-2 text-sm text-slate-300">Batch-convert incoming client XRechnung / ZUGFeRD XMLs to DATEV EXTF (with automatic BU-Schlüssel 9/8/94/0) and unwrap Sparkasse/VR CAMT.053 SEPA batches with zero client IBAN uploads.</p>
      </div>
      <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 class="text-lg font-bold text-white">2. Xero &amp; QuickBooks Advisors</h2>
        <p class="mt-2 text-sm text-slate-300">Replace $20–$50/mo bank converters &amp; settlement apps with BankFeedBridge (`.qbo` / Xero `.ofx`), AmzSettlementBridge, StripePayoutBridge, and OssVatBridge across every client file.</p>
      </div>
      <div class="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 class="text-lg font-bold text-white">3. Shopify &amp; Webflow Agencies</h2>
        <p class="mt-2 text-sm text-slate-300">Use ShopMetaShift (WooCommerce &rarr; Matrixify Metafield CSV + 301 Redirects) and WebflowAssetZip (100% CMS ZIP backup) before store handovers without giving third parties live admin tokens.</p>
      </div>
    </section>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <h2 class="text-lg font-bold text-white">Zero-DPA Privacy Proof (Audit in 10 Seconds)</h2>
      <p class="mt-2 text-sm text-slate-300">Every conversion runs locally in Chrome DevTools memory (`DOMParser` + vanilla JS) or air-gapped inside Python (`pip install`). Open DevTools &rarr; Network tab while dropping a client XML or CSV file: <strong>0 upload requests leave your workstation.</strong></p>
    </section>"""
    return _render_page_shell(
        title="Partners & Accounting Practices (Steuerberater, Bookkeepers, Agencies) | Friction-Killer Suite",
        description="GDPR/DSGVO zero-upload browser tools and offline Python CLIs for Steuerkanzleien, Xero/QuickBooks bookkeepers, and Shopify migration agencies.",
        canonical_url=f"{SITE_BASE_URL}/partners/",
        lang="en",
        rel_root="../",
        main_html=main_html,
        analytics_slug="partners_page",
        analytics_title="Accountant & Agency Partners",
        analytics_cfg=analytics_cfg,
        bundle_checkout_url=bundle_checkout_url,
        legal_footer_html=legal_footer_html,
        analytics_renderer=analytics_renderer,
    )


def _write_llms_files(
    products: list[dict[str, Any]],
    docs_dir: Path,
    bundle_checkout_url: str,
) -> None:
    prod_lines = "\n".join(
        f"- [{p['short_title']}]({SITE_BASE_URL}/products/{p['slug']}/) ({p['price']}): {p['summary']}"
        for p in products
    )
    de_lines = "\n".join(
        f"- [{p['h1']}]({SITE_BASE_URL}/de/{p['dir']}/)"
        for p in DE_PAGES
    )
    guide_lines = "\n".join(
        f"- [{g['h1']}]({SITE_BASE_URL}/guides/{g['slug']}/): {g['meta_desc']}"
        for g in GUIDES
    )
    llms_txt = f"""# Friction-Killer Suite

> 13 zero-subscription, 100% local-first Web Apps & offline Python CLIs for European/B2B finance, e-invoicing, bank-feed conversion, e-commerce migration, and developer workflows. All data runs locally in browser memory or offline CLI with zero server uploads.

## Key Links
- [Storefront Hub ({len(products)} Tools)]({SITE_BASE_URL}/)
- [All-Access Bundle (€49 once)]({bundle_checkout_url})
- [Deutsch / DACH Tools](/de/): {SITE_BASE_URL}/de/
- [Free Interactive Calculators (EU VAT OSS, Lemon Squeezy Shutdown, DATEV BU-Schlüssel)]({SITE_BASE_URL}/tools/)
- [20 Error-Code & Format Guides]({SITE_BASE_URL}/guides/)
- [Free Test Fixtures (XRechnung, ZUGFeRD, Peppol, CAMT.053, MT940)]({SITE_BASE_URL}/samples/)
- [Accountant & Agency Partners]({SITE_BASE_URL}/partners/)

## Active Products
{prod_lines}

## Free Diagnostic Calculators
- [2026 EU-27 OSS VAT Rates & BZSt GR->EL Checker]({SITE_BASE_URL}/tools/eu-oss-vat-rates-2026/)
- [Lemon Squeezy Shutdown PayPal MRR Risk Calculator]({SITE_BASE_URL}/tools/lemon-squeezy-shutdown-calculator/)
- [DATEV BU-Schlüssel & EN 16931 BT-151 Lookup]({SITE_BASE_URL}/tools/datev-bu-schluessel-lookup/)

## Full Context
- [llms-full.txt]({SITE_BASE_URL}/llms-full.txt)
"""
    llms_full = f"""{llms_txt}

## German / DACH Localized Pages
{de_lines}

## 20 Technical Troubleshooting & Format Conversion Guides
{guide_lines}

## Privacy & Verification Architecture
- Browser Web Apps use native `DOMParser` and JavaScript `File.text()` inside the browser tab with zero uploaded XML/CSV payloads.
- Air-gapped `.whl` Python CLIs run locally offline (`camt053-mt940-qbo-xero-converter`, `e-invoice-xml-batch-converter`, `eu-oss-vat-return-compiler`, `lemonsqueezy-stripe-polar-migrator`, `amazon-settlement-xero-qbo-splitter`, `stripe-payout-xero-qbo-splitter`, `woo-shopify-metafield-migrator`, `notion-clean-md-exporter`, `claude-profile-switch`).
- Contact: dom.stijn99@gmail.com | Source: https://github.com/domstijn/friction-killer-suite
"""
    (docs_dir / "llms.txt").write_text(llms_txt, encoding="utf-8")
    (docs_dir / "llms-full.txt").write_text(llms_full, encoding="utf-8")


def build_growth_assets(
    products: list[dict[str, Any]],
    docs_dir: Path,
    analytics_cfg: dict[str, str],
    bundle_checkout_url: str = BUNDLE_URL_DEFAULT,
    *,
    legal_footer_html: str = "",
    analytics_renderer: Callable[..., str] | None = None,
) -> list[tuple[str, str]]:
    """Build /de/, /guides/, /tools/, /samples/, /partners/, and llms*.txt into docs/ and return sitemap entries."""
    sitemap_entries: list[tuple[str, str]] = []

    # 1. German /de/ hub & 3 DACH pages
    de_dir = docs_dir / "de"
    de_dir.mkdir(parents=True, exist_ok=True)
    (de_dir / "index.html").write_text(
        _render_de_hub(bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
        encoding="utf-8",
    )
    sitemap_entries.append((f"{SITE_BASE_URL}/de/", "0.9"))
    for spec in DE_PAGES:
        pdir = de_dir / spec["dir"]
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "index.html").write_text(
            _render_de_product_page(spec, bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
            encoding="utf-8",
        )
        sitemap_entries.append((f"{SITE_BASE_URL}/de/{spec['dir']}/", "0.9"))

    # 2. 20 High-intent guides
    guides_dir = docs_dir / "guides"
    guides_dir.mkdir(parents=True, exist_ok=True)
    (guides_dir / "index.html").write_text(
        _render_guides_index(bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
        encoding="utf-8",
    )
    sitemap_entries.append((f"{SITE_BASE_URL}/guides/", "0.8"))
    for g in GUIDES:
        gdir = guides_dir / g["slug"]
        gdir.mkdir(parents=True, exist_ok=True)
        (gdir / "index.html").write_text(
            _render_single_guide(g, bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
            encoding="utf-8",
        )
        sitemap_entries.append((f"{SITE_BASE_URL}/guides/{g['slug']}/", "0.8"))

    # 3. 3 Free calculators (/tools/)
    tools_dir = docs_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "index.html").write_text(
        _render_tools_index(bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
        encoding="utf-8",
    )
    sitemap_entries.append((f"{SITE_BASE_URL}/tools/", "0.9"))
    tool_builders = [
        ("eu-oss-vat-rates-2026", _render_tool_eu_oss_rates),
        ("lemon-squeezy-shutdown-calculator", _render_tool_lemon_calc),
        ("datev-bu-schluessel-lookup", _render_tool_datev_bu_lookup),
    ]
    for tslug, builder in tool_builders:
        tdir = tools_dir / tslug
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "index.html").write_text(
            builder(bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
            encoding="utf-8",
        )
        sitemap_entries.append((f"{SITE_BASE_URL}/tools/{tslug}/", "0.9"))

    # 4. Open-source fixtures pack (/samples/)
    samples_dir = docs_dir / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    fixtures = _write_sample_fixtures(samples_dir / "files")
    (samples_dir / "index.html").write_text(
        _render_samples_index(fixtures, bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
        encoding="utf-8",
    )
    sitemap_entries.append((f"{SITE_BASE_URL}/samples/", "0.8"))

    # 5. B2B Accountant & Agency Partners page (/partners/)
    partners_dir = docs_dir / "partners"
    partners_dir.mkdir(parents=True, exist_ok=True)
    (partners_dir / "index.html").write_text(
        _render_partners_page(bundle_checkout_url, analytics_cfg, legal_footer_html, analytics_renderer),
        encoding="utf-8",
    )
    sitemap_entries.append((f"{SITE_BASE_URL}/partners/", "0.8"))

    # 6. GEO / AI-Search Index (llms.txt + llms-full.txt)
    _write_llms_files(products, docs_dir, bundle_checkout_url)

    return sitemap_entries
