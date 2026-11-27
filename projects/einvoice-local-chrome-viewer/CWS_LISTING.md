# Chrome Web Store Listing — EInvoiceLocal Local Viewer

## Store Metadata
- **Title (EN):** `EInvoiceLocal — XRechnung & ZUGFeRD Local Viewer (0 Uploads)`
- **Title (DE):** `EInvoiceLocal — XRechnung & ZUGFeRD XML lokal anzeigen (0 Uploads)`
- **Summary (132 chars max):** `View & validate XRechnung (UBL 2.1), ZUGFeRD (CII-XML) & Peppol XML invoices offline in Chrome with DATEV BU & A4 PDF.`
- **Category:** Productivity / Business Tools
- **Language:** German, English
- **Permissions Requested:** **None (`permissions: []`, `host_permissions: []`)**

## Description (DE / EN)
Prüfen und drucken Sie elektronische B2B-Rechnungen (**XRechnung 3.0 UBL**, **ZUGFeRD 2.x CII-XML**, **Peppol BIS 3.0 XML**) direkt im Chrome-Tab — **zu 100 % offline im lokalen Arbeitsspeicher ohne Server-Upload**.

- **DSGVO & GoBD ohne AVV-Hürde:** Lieferanten-IBANs, USt-IDs und Positionspreise verlassen niemals Ihren Computer.
- **EN 16931 Summenprüfung:** Erkennt `BR-CO-10`, `BR-CO-14` und `BR-CO-15` Rechenfehler sofort.
- **Automatische DATEV-Vorschau:** Zeigt den passenden `BU-Schlüssel` (`9`, `8`, `94`, `91`, `92`, `0`) und das SKR03-Konto direkt am Beleg.
- **Sauberer A4-PDF-Druck:** Verwandelt unlesbare XML-Tags in eine prüffähige A4-Rechnungsansicht.

Für komplette Sammel-Exporte nach **DATEV EXTF (`;`-CSV)**, **Xero Bills** und **QuickBooks Bills CSV** verlinkt der Viewer optional auf die Browser-Web-App **EInvoiceLocal Pro** (€29 einmalig, kein Abo).

## Privacy Practice Disclosures (Chrome Web Store Dashboard)
- **Single Purpose:** Local parsing, EN 16931 validation, and printable A4 rendering of XRechnung / ZUGFeRD / Peppol XML invoice files in browser memory.
- **Permission Justification:** Requests zero Chrome API permissions (`[]`) and zero host permissions (`[]`).
- **Data Usage:** Does **NOT** collect, read, store remotely, or transmit any personal, financial, or XML document data. Zero analytics, zero cookies, zero external CDNs.

## Packaging Command
```bash
node projects/einvoice-local-chrome-viewer/tests/test_extension.mjs
# Zip archive ready at:
# projects/einvoice-local-chrome-viewer/dist/einvoice-local-chrome-viewer-v1.0.0.zip
```
