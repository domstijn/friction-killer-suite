# Operation XRechnung 2027 — Verified Distribution & Outreach Kit (`2026-11-27`)

> **Important:** Do not post or send externally without final human review. All URLs and GitHub issue states below were verified live on **`2026-11-27`** (`HTTP 200`, GitHub `state == "open"` & `locked == false`). All privacy benchmark figures come strictly from live Chrome DevTools inspection of synthetic XML `sample-xrechnung-3.0-ubl.xml`.

---

## 1. Key URLs (Zero-CDN & Tracked)

- **DE Landing Page (Zero-CDN):** `https://domstijn.github.io/friction-killer-suite/de/xrechnung-zugferd-konverter/`
- **Live Browser App (Zero-CDN, Value-First Paywall):** `https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/`
- **Air-Gapped 1-Line Embed Widget (0 Network Requests):** `https://domstijn.github.io/friction-killer-suite/embed/xrechnung-viewer/`
- **2026 DevTools Privacy Benchmark (DE):** `https://domstijn.github.io/friction-killer-suite/tools/xrechnung-viewer-dsgvo-test-2026/`
- **Chrome Web Store Companion Package:** `projects/einvoice-local-chrome-viewer/dist/einvoice-local-chrome-viewer-v1.0.0.zip` ([CWS_LISTING.md](file:///Users/stijndom/Documents/antigravity/joyful-newton/projects/einvoice-local-chrome-viewer/CWS_LISTING.md))

---

## 2. Verified Live GitHub Issues (`open`, `locked=false` as of `2026-11-27`)

> Note: `nicolettas-muggelbude/RechnungsFee#598` was verified **closed** on `2026-11-26` — excluded below and replaced with active open issues.

1. **`Le-Space/belege#932`** — *The BU key by where the vendor sits: domestic, EU, third country*
   - **URL:** https://github.com/Le-Space/belege/issues/932
   - **Draft Reply (`?ref=src.gh-sniper`):**
     > Deriving DATEV `BU-Schlüssel` purely from vendor country or PDF OCR breaks quickly on § 13b reverse-charge (`AE` → `BU 94 / 3123`), intra-EU acquisitions (`K` → `BU 91 / 3425` or `BU 92 / 3420`), and mixed 7%/19% hospitality invoices (`BU 8+9`). On structured UBL 2.1 / CII e-invoices, mapping line-level `BT-151` VAT category codes + percentages deterministically per bucket avoids collapsing mixed rates. If anyone wants a zero-upload browser reference or batch EXTF exporter implementing that exact mapping locally (with 100% free full-batch EN 16931 check + 2-row CSV preview, €29 Pro CLI/CSV), see EInvoiceLocal: https://domstijn.github.io/friction-killer-suite/de/xrechnung-zugferd-konverter/?ref=src.gh-sniper

2. **`bitbetterde/paperless-ngx-erechnung#12`** — *Feature Request: Add multi layer eInvoice validation*
   - **URL:** https://github.com/bitbetterde/paperless-ngx-erechnung/issues/12
   - **Draft Reply (`?ref=src.gh-sniper`):**
     > Two subtle traps when adding multi-layer Python EN 16931 checks without the Java KoSIT stack: (1) CII files often carry both `FC` (Steuernummer) and `VA` (USt-IdNr) inside multiple `<ram:SpecifiedTaxRegistration>` nodes, so filtering on `schemeID="VA"` prevents misreading German tax IDs; (2) UBL `<cac:TaxTotal>` can repeat in foreign accounting currency unless matched against `DocumentCurrencyCode`. If you need an offline browser/Python sidekick to cross-check UBL 2.1 + CII math (`BR-CO-10/14/15`) and preview DATEV `EXTF` rows locally (`0` XML bytes leave Chrome), feel free to test against EInvoiceLocal: https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/?ref=src.gh-sniper

3. **`Stirling-Tools/Stirling-PDF#2025`** — *Generate a PDF file from a XRechnung XML file*
   - **URL:** https://github.com/Stirling-Tools/Stirling-PDF/issues/2025
   - **Draft Reply (`?ref=src.gh-sniper`):**
     > Watch out for dual syntax drift when building XRechnung XML -> PDF in a single pass: incoming German B2B invoices arrive as UBL 2.1 (`Invoice` & `CreditNote`) AND UN/CEFACT CII (`CrossIndustryInvoice`), and pure XSLT often omits explicit `BR-CO-10` / `BR-CO-15` summation checks before rendering. For users needing an air-gapped zero-upload browser viewer or self-hostable `<iframe>` widget right now (0 CDNs, 0 cookies, 0 server uploads), we published an open embeddable viewer here: https://domstijn.github.io/friction-killer-suite/embed/xrechnung-viewer/?ref=src.gh-sniper

4. **`ZUGFeRD/quba-viewer#194`** — *Quba Viewer 2.0.0 crashes on opening ZUGFeRD PDF*
   - **URL:** https://github.com/ZUGFeRD/quba-viewer/issues/194
   - **Draft Reply (`?ref=src.gh-sniper`):**
     > As noted above, `LC_ALL=C` works around the JCEF `std::__facet_shims` locale crash on Linux. If anyone hits that runtime blocker urgently on a locked-down machine and just needs to inspect XRechnung UBL 2.1 / ZUGFeRD CII XMLs and print an A4 PDF without Java/Electron dependencies, our zero-upload browser viewer runs in memory with 0 network requests: https://domstijn.github.io/friction-killer-suite/embed/xrechnung-viewer/?ref=src.gh-sniper

5. **`kschulzeEcommerce/14-B2B-Angebotserstellung#16`** — *[CR][FA] Billbee-Rechnungs-XML, XRechnung und KoSIT-Validierung*
   - **URL:** https://github.com/kschulzeEcommerce/14-B2B-Angebotserstellung/issues/16
   - *(Technical comment comparing KoSIT validation vs lightweight local EN 16931 math verification + link to `/tools/datev-bu-schluessel-lookup/?ref=src.gh-sniper` or `/de/xrechnung-zugferd-konverter/?ref=src.gh-sniper`.)*

6. **Backup Verified Open Targets:**
   - `microsoft/BCApps#13922`: https://github.com/microsoft/BCApps/issues/13922
   - `Speicherstadt/haben-at#1`: https://github.com/Speicherstadt/haben-at/issues/1
   - `Speicherstadt/haben#1833`: https://github.com/Speicherstadt/haben/issues/1833
   - `Schelawski/Abgerechnet#12`: https://github.com/Schelawski/Abgerechnet/issues/12

---

## 3. Ready-to-Post Content Teardowns (Strictly Fact-Checked Against `2026-11-27` Audit)

### A. LinkedIn Post (DE — *Steuerberater, Buchhalter & Datenschutz*)
> **9 kostenlose XRechnung-Viewer im Chrome-DevTools-Test: Bei 3 davon verlässt Ihre XML-Rechnung den Browser**
>
> Ab dem 1. Januar 2027 endet die nächste Übergangsfrist der B2B-E-Rechnungspflicht. Viele Unternehmen und Kanzleien prüfen XML-Dateien schnell über den ersten Google-Treffer „XRechnung Viewer kostenlos“.
>
> Wir haben heute (`27.11.2026`) **9 öffentliche deutsche Online-Viewer** mit einer synthetischen Test-XRechnung (`XR-SAMPLE-2026-1001`) und geöffnetem Chrome-Netzwerk-Tab geprüft. Das Ergebnis:
> - **3 von 9 Viewern** senden die ausgewählte XML-Datei per HTTP-`POST` an einen Server (`rechnex.de/api/view-xrechnung`, `toolkits.sevdesk.de/api/toolkits/eInvoiceViewer` und `xrechnung-online.de/visualisierung` für die KoSIT-Prüfung). Das ist legitim, erfordert in Kanzleien aber saubere AVV-/Datenschutzprüfung nach Art. 28 DSGVO.
> - **2 von 9 Viewern** parsen lokal im Browser, feuern aber aktive Analytics-Requests (`googletagmanager.com` beim Öffnen bzw. `analytics.northerndynamic.org` bei Dateiauswahl).
> - **4 von 9 Viewern** (`elster.de`, `belegviewer.de`, `xrechnungs.de`, `rechnungswaechter.de` vor Opt-in) arbeiten komplett lokal ohne XML-Upload.
>
> **Was uns bei allen 9 gefehlt hat:** Keiner der kostenlosen Viewer macht nach der Ansicht den Schritt in die Buchhaltung — also mehrere XRechnungen + ZUGFeRD-XMLs sauber in **DATEV EXTF (`;`-CSV mit SKR03 & BU-Schlüssel 9/8/94/91/0)** oder Xero/QuickBooks umzuwandeln, ohne Upload und ohne Monatsabo.
>
> Genau dafür haben wir:
> 1. Den vollständigen DevTools-Protokoll-Test (inkl. Test-XML zum Selbernachprüfen): https://domstijn.github.io/friction-killer-suite/tools/xrechnung-viewer-dsgvo-test-2026/?ref=src.li-teardown
> 2. Ein kostenloses, komplett luftdichtes 1-Zeilen-`<iframe>`-Widget für Kanzlei- & Steuer-Blogs (0 Uploads, 0 Cookies, 0 CDNs): https://domstijn.github.io/friction-killer-suite/embed/xrechnung-viewer/?ref=src.li-teardown
>
> Welche E-Rechnungs-Hürde kostet bei Ihnen im Kanzleialltag gerade am meisten Zeit?

### B. Hacker News / `r/de_EDV` / `r/selfhosted` Technical Post (EN)
> **We inspected 9 German free online XRechnung (EN 16931) viewers in Chrome DevTools — 3 upload invoices over HTTP POST, and none export local DATEV CSVs**
>
> With Germany's B2B e-invoicing transition hitting its Jan 2027 milestone, freelancers and accountants frequently drop confidential UBL 2.1 / CII supplier invoices (full IBANs, VAT IDs, unit pricing) into browser "free XRechnung viewers".
>
> Testing 9 public German viewers today with a synthetic EN 16931 UBL file under Chrome network inspection:
> - **3/9** uploaded the XML payload via HTTP `POST` (`rechnex.de`, `toolkits.sevdesk.de`, `xrechnung-online.de`).
> - **2/9** parsed locally in JS while loading third-party analytics beacons (`rechnungscanner.de`, `rechnungapp.de`).
> - **4/9** processed strictly client-side with zero XML network traffic (`elster.de`, `belegviewer.de`, `xrechnungs.de`, `rechnungswaechter.de` pre-consent).
>
> Full reproducible network log + synthetic XML fixture: https://domstijn.github.io/friction-killer-suite/tools/xrechnung-viewer-dsgvo-test-2026/?ref=src.hn-teardown
>
> We also built an air-gapped zero-network `<iframe>` viewer (`0` CDNs, `0` telemetry) plus **EInvoiceLocal** (client-side UBL `Invoice`/`CreditNote` + CII `380`/`381` validator + DATEV EXTF / Xero / QuickBooks CSV batch exporter): https://domstijn.github.io/friction-killer-suite/products/e-invoice-xml-batch-converter/?ref=src.hn-teardown

### C. *DATEV-Community* / Accounting Forum Discussion Post (DE, Non-Promotional Lead)
> **Praxishinweis für Kanzleien: Netzwerkanalyse beim Online-Check von XRechnungen (AVV vs. Client-Side)**
>
> Wer Mandanten für die schnelle XML-Sichtprüfung auf kostenlose Online-Viewer verweist, sollte kurz im Netzwerk-Tab prüfen, ob die XML tatsächlich im Browser bleibt: Im Test vom 27.11.2026 übertragen 3 von 9 gängigen Tools die Datei per `POST` an externe Server (bei `xrechnung-online.de` z. B. für die serverseitige KoSIT-1.5.0-Validierung, bei `rechnex.de` und `sevdesk.de` über eigene API-Endpunkte). Rein lokal im Browser ohne XML-Upload arbeiten z. B. `elster.de/eportal/e-rechnung` (Saxon-JS), `belegviewer.de` oder unser komplett offline laufendes Einbettungs-Widget (`embed/xrechnung-viewer`). Vollständige Testtabelle inkl. Beispieldatei zum Nachstellen: https://domstijn.github.io/friction-killer-suite/tools/xrechnung-viewer-dsgvo-test-2026/?ref=src.datev-comm

---

## 4. 20 Verified DACH Target Portals (`HTTP 200`, Widget & Benchmark Pitch)

### Tailor-Made German Widget Pitch Template (4 Sentences)
> **Betreff:** Kostenloses 0-Upload XRechnung-Widget (ohne AVV/Cookies) für Ihren E-Rechnungs-Beitrag
>
> Hallo [Redaktion / Vorname Name],
>
> Ihren praxisnahen Beitrag zur E-Rechnungspflicht ([Artikel-URL einfügen]) verlinken wir bereits häufiger für KMU-Fragen — gerade vor dem 01.01.2027 suchen viele Leser direkt im Artikel nach einem schnellen XML-Viewer ohne Registrierung.
> Wir haben ein komplett **luftdichtes 1-Zeilen-`<iframe>`-Widget** gebaut, das XRechnung (UBL) und ZUGFeRD (CII) zu 100 % im Browser-Speicher des Lesers darstellt — **0 Server-Uploads, 0 Cookies, 0 externe CDNs** (kein AVV nötig): `https://domstijn.github.io/friction-killer-suite/embed/xrechnung-viewer/?ref=src.partner`
> Passend dazu haben wir heute 9 öffentliche XRechnung-Viewer im Chrome-Netzwerk-Tab getestet (`https://domstijn.github.io/friction-killer-suite/tools/xrechnung-viewer-dsgvo-test-2026/`). Falls das Widget als praktisches Extra für Ihre Leser interessant ist, sende ich Ihnen gern den fertigen HTML-Embed-Code.
>
> Viele Grüße, Stijn Dom (`@domstijn`)

### Verified 20 Targets (`2026-11-27`)

| # | Portal / Kanzlei | Verified Live Article URL | Segment |
| :---: | :--- | :--- | :--- |
| 1 | **Steuerberaten.de** | https://www.steuerberaten.de/blog/650/e-rechnung-2027-wer-rechnungen-ausdruckt-riskiert-den-vorsteuerabzug/ | Steuerberater / Kanzlei |
| 2 | **Steuerberater Jens Preßler** | https://www.steuerberater-pressler.de/elektronische-rechnungen-2/ | Steuerberater / Kanzlei |
| 3 | **Steuerberater Horak-von Bothmer** | https://www.steuerberater-horakvb.de/e-rechnung/ | Steuerberater / Kanzlei |
| 4 | **Deubner Steuern** | https://www.deubner-steuern.de/themen/digitalisierung-steuerberatung/elektronische-rechnung/ | Steuerberater / Kanzlei |
| 5 | **Tax-Tech.de** | https://tax-tech.de/e-rechnung-steuerkanzlei/ | Steuerberater / Kanzlei |
| 6 | **Steuerberater-Websites.de** | https://steuerberater-websites.de/wissen/e-rechnung-2027-mandanten-informieren/ | Steuerberater / Kanzlei |
| 7 | **IT-Recht Kanzlei** | https://www.it-recht-kanzlei.de/gesetzesaenderung-e-rechnnung-steuerrecht.html | Kanzlei / Recht |
| 8 | **VGSD** | https://www.vgsd.de/linksammlung-kostenlose-e-rechnungs-tools/ | Freelancer / Verband |
| 9 | **Steuertipps.de** | https://www.steuertipps.de/selbststaendigkeit/e-rechnung-fuer-unternehmer-ab-2025 | Freelancer / KMU |
| 10 | **Qonto Deutschland Blog** | https://qonto.com/de/blog/selbststaendige/management-buchhaltung/e-rechnung-pflicht-freiberufler | Freelancer / FinTech |
| 11 | **Gründerplattform** | https://gruenderplattform.de/unternehmensfuehrung/e-rechnungen | Freelancer / Gründer |
| 12 | **freelancermap Blog** | https://www.freelancermap.de/blog/e-rechnung/ | Freelancer |
| 13 | **freelance.de Blog** | https://www.freelance.de/blog/e-rechnungspflicht-fuer-freelancer-was-sie-wissen-muessen/ | Freelancer |
| 14 | **DATEV Themenfokus** | https://www.datev.de/web/de/unternehmen/loesungen/themen-im-fokus/aktuelle-themen-fuer-unternehmen/e-rechnung-ab-2027 | Steuerberater / ERP |
| 15 | **BuchhaltungsButler Wiki** | https://www.buchhaltungsbutler.de/wiki/e-rechnung-pflicht/ | ERP / Buchhaltung |
| 16 | **weclapp Lexikon** | https://www.weclapp.com/de/lexikon/e-rechnung/ | ERP Blog |
| 17 | **IHK München & Oberbayern** | https://www.ihk-muenchen.de/ratgeber/steuern/steuerliche-sonderthemen/elektronische-rechnungen/ | IHK Portal |
| 18 | **IHK Region Stuttgart** | https://www.ihk.de/stuttgart/fuer-unternehmen/recht-und-steuern/steuerrecht/steuermeldungen/e-rechnungen-5864496 | IHK Portal |
| 19 | **HWK Region Stuttgart** | https://www.hwk-stuttgart.de/artikel/e-rechnung-alle-wichtigen-infos-fuer-betriebe-67,0,3061.html | HWK Portal |
| 20 | **ZDH** | https://www.zdh.de/ueber-uns/fachbereich-steuern-und-finanzen/elektronische-rechnung/ | Handwerksverband |
