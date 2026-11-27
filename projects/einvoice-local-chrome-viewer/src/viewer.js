(function () {
  "use strict";
  const CORE = window.EInvoiceCore;
  const esc = CORE.escHtml;

  const SAMPLE_DOCS = [
    {
      name: "xrechnung-ubl-1001.xml",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ID>XR-2026-1001</cbc:ID><cbc:IssueDate>2026-11-18</cbc:IssueDate><cbc:DueDate>2026-12-18</cbc:DueDate><cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode><cbc:BuyerReference>991-12345-67</cbc:BuyerReference>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyTaxScheme><cbc:CompanyID>DE298765432</cbc:CompanyID></cac:PartyTaxScheme><cac:PartyLegalEntity><cbc:RegistrationName>Nordic Cloud Infrastructure GmbH</cbc:RegistrationName></cac:PartyLegalEntity></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyTaxScheme><cbc:CompanyID>DE112233445</cbc:CompanyID></cac:PartyTaxScheme><cac:PartyLegalEntity><cbc:RegistrationName>Mittelstand Ops GmbH</cbc:RegistrationName></cac:PartyLegalEntity></cac:Party></cac:AccountingCustomerParty>
  <cac:PaymentMeans><cac:PayeeFinancialAccount><cbc:ID>DE89370400440532013000</cbc:ID></cac:PayeeFinancialAccount></cac:PaymentMeans>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">38.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal><cbc:TaxExclusiveAmount currencyID="EUR">200.00</cbc:TaxExclusiveAmount><cbc:PayableAmount currencyID="EUR">238.00</cbc:PayableAmount></cac:LegalMonetaryTotal>
  <cac:InvoiceLine><cbc:ID>1</cbc:ID><cbc:InvoicedQuantity>2</cbc:InvoicedQuantity><cbc:LineExtensionAmount>150.00</cbc:LineExtensionAmount><cac:Item><cbc:Name>Dedicated PostgreSQL Nodes</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item><cac:Price><cbc:PriceAmount>75.00</cbc:PriceAmount></cac:Price></cac:InvoiceLine>
  <cac:InvoiceLine><cbc:ID>2</cbc:ID><cbc:InvoicedQuantity>1</cbc:InvoicedQuantity><cbc:LineExtensionAmount>50.00</cbc:LineExtensionAmount><cac:Item><cbc:Name>Daily Encrypted Snapshots</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item><cac:Price><cbc:PriceAmount>50.00</cbc:PriceAmount></cac:Price></cac:InvoiceLine>
</Invoice>`,
    },
    {
      name: "zugferd-cii-2002.xml",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocument><ram:ID>ZF-2026-2002</ram:ID><ram:IssueDateTime><udt:DateTimeString format="102">20261119</udt:DateTimeString></ram:IssueDateTime></rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem><ram:SpecifiedTradeProduct><ram:Name>Technical Compliance Handbook (Print Edition)</ram:Name></ram:SpecifiedTradeProduct><ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement><ram:SpecifiedLineTradeDelivery><ram:BilledQuantity>1</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery><ram:SpecifiedLineTradeSettlement><ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>7.00</ram:RateApplicablePercent></ram:ApplicableTradeTax><ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement></ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeAgreement><ram:BuyerReference>LEITWEG-04011000-12345-01</ram:BuyerReference><ram:SellerTradeParty><ram:Name>Fachverlag Berlin KG</ram:Name><ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE812345678</ram:ID></ram:SpecifiedTaxRegistration></ram:SellerTradeParty><ram:BuyerTradeParty><ram:Name>Mittelstand Ops GmbH</ram:Name><ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE112233445</ram:ID></ram:SpecifiedTaxRegistration></ram:BuyerTradeParty></ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode><ram:SpecifiedTradeSettlementPaymentMeans><ram:PayeePartyCreditorFinancialAccount><ram:IBANID>DE44500105175407324931</ram:IBANID></ram:PayeePartyCreditorFinancialAccount></ram:SpecifiedTradeSettlementPaymentMeans><ram:SpecifiedTradePaymentTerms><ram:DueDateDateTime><udt:DateTimeString format="102">20261205</udt:DateTimeString></ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms><ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount><ram:TaxTotalAmount>7.00</ram:TaxTotalAmount><ram:DuePayableAmount>107.00</ram:DuePayableAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation></ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>`,
    },
    {
      name: "peppol-bis3-3003.xml",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ID>PEP-2026-3003</cbc:ID><cbc:IssueDate>2026-11-20</cbc:IssueDate><cbc:DueDate>2026-12-20</cbc:DueDate><cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode><cbc:BuyerReference>PO-2026-BE-44</cbc:BuyerReference>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyTaxScheme><cbc:CompanyID>BE0897234567</cbc:CompanyID></cac:PartyTaxScheme><cac:PartyLegalEntity><cbc:RegistrationName>Antwerp Logistics Systems BV</cbc:RegistrationName></cac:PartyLegalEntity></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyTaxScheme><cbc:CompanyID>DE112233445</cbc:CompanyID></cac:PartyTaxScheme><cac:PartyLegalEntity><cbc:RegistrationName>Mittelstand Ops GmbH</cbc:RegistrationName></cac:PartyLegalEntity></cac:Party></cac:AccountingCustomerParty>
  <cac:PaymentMeans><cac:PayeeFinancialAccount><cbc:ID>BE68539007547034</cbc:ID></cac:PayeeFinancialAccount></cac:PaymentMeans>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">0.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal><cbc:TaxExclusiveAmount currencyID="EUR">240.00</cbc:TaxExclusiveAmount><cbc:PayableAmount currencyID="EUR">240.00</cbc:PayableAmount></cac:LegalMonetaryTotal>
  <cac:InvoiceLine><cbc:ID>1</cbc:ID><cbc:InvoicedQuantity>1</cbc:InvoicedQuantity><cbc:LineExtensionAmount>180.00</cbc:LineExtensionAmount><cac:Item><cbc:Name>EU Peppol Access Point Gateway</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>AE</cbc:ID><cbc:Percent>0.00</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item><cac:Price><cbc:PriceAmount>180.00</cbc:PriceAmount></cac:Price></cac:InvoiceLine>
  <cac:InvoiceLine><cbc:ID>2</cbc:ID><cbc:InvoicedQuantity>3</cbc:InvoicedQuantity><cbc:LineExtensionAmount>60.00</cbc:LineExtensionAmount><cac:Item><cbc:Name>AS4 Message Routing Tier</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>AE</cbc:ID><cbc:Percent>0.00</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item><cac:Price><cbc:PriceAmount>20.00</cbc:PriceAmount></cac:Price></cac:InvoiceLine>
</Invoice>`,
    },
    {
      name: "zugferd-mixed-4004.xml",
      text: `<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocument><ram:ID>ZF-2026-4004</ram:ID><ram:IssueDateTime><udt:DateTimeString format="102">20261121</udt:DateTimeString></ram:IssueDateTime></rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem><ram:SpecifiedTradeProduct><ram:Name>Business Accommodation (2 Nights)</ram:Name></ram:SpecifiedTradeProduct><ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement><ram:SpecifiedLineTradeDelivery><ram:BilledQuantity>2</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery><ram:SpecifiedLineTradeSettlement><ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>7.00</ram:RateApplicablePercent></ram:ApplicableTradeTax><ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>200.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement></ram:IncludedSupplyChainTradeLineItem>
    <ram:IncludedSupplyChainTradeLineItem><ram:SpecifiedTradeProduct><ram:Name>Conference Room &amp; Catering Package</ram:Name></ram:SpecifiedTradeProduct><ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement><ram:SpecifiedLineTradeDelivery><ram:BilledQuantity>1</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery><ram:SpecifiedLineTradeSettlement><ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>19.00</ram:RateApplicablePercent></ram:ApplicableTradeTax><ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement></ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeAgreement><ram:BuyerReference>CONF-MUC-2026</ram:BuyerReference><ram:SellerTradeParty><ram:Name>Tagungshotel München GmbH</ram:Name><ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE276543219</ram:ID></ram:SpecifiedTaxRegistration></ram:SellerTradeParty><ram:BuyerTradeParty><ram:Name>Mittelstand Ops GmbH</ram:Name><ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE112233445</ram:ID></ram:SpecifiedTaxRegistration></ram:BuyerTradeParty></ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode><ram:SpecifiedTradeSettlementPaymentMeans><ram:PayeePartyCreditorFinancialAccount><ram:IBANID>DE12700202700015984000</ram:IBANID></ram:PayeePartyCreditorFinancialAccount></ram:SpecifiedTradeSettlementPaymentMeans><ram:SpecifiedTradePaymentTerms><ram:DueDateDateTime><udt:DateTimeString format="102">20261206</udt:DateTimeString></ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms><ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:TaxBasisTotalAmount>300.00</ram:TaxBasisTotalAmount><ram:TaxTotalAmount>33.00</ram:TaxTotalAmount><ram:DuePayableAmount>333.00</ram:DuePayableAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation></ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>`,
    },
  ];

  function renderA4(inv) {
    if (!inv) return;
    document.getElementById("a4-syntax").textContent = inv.syntax + " · EN 16931 ANSICHT";
    document.getElementById("a4-id").textContent = (inv.isCreditNote ? "Gutschrift " : "Rechnung ") + inv.id;
    document.getElementById("a4-dates").textContent =
      "Datum: " + (inv.issue || "—") + " · Fällig: " + (inv.due || "—") + (inv.buyerRef ? " · Ref: " + inv.buyerRef : "");
    document.getElementById("a4-seller").textContent = inv.seller || "—";
    document.getElementById("a4-seller-vat").textContent = "USt-IdNr: " + (inv.sellerVat || "—");
    document.getElementById("a4-iban").textContent = "IBAN: " + (inv.iban || "—");
    document.getElementById("a4-buyer").textContent = inv.buyer || "—";
    document.getElementById("a4-buyer-vat").textContent = inv.buyerVat || "—";

    const pill = document.getElementById("a4-pill");
    if (inv.valid) {
      pill.textContent = "EN 16931 PASS · BU " + inv.bu;
      pill.style.background = "#dcfce7";
      pill.style.color = "#166534";
    } else {
      pill.textContent = "FEHLER / WARNUNG";
      pill.style.background = "#ffe4e6";
      pill.style.color = "#9f1239";
    }

    document.getElementById("a4-lines").innerHTML = inv.lines.length
      ? inv.lines
          .map(
            (l) =>
              "<tr><td>" +
              esc(l.name) +
              "</td><td class='right'>" +
              l.qty.toFixed(2) +
              "</td><td class='right'>" +
              l.unit.toFixed(2) +
              "</td><td class='right'>" +
              CORE.fmtRate(l.rate) +
              "%</td><td class='right mono'>" +
              l.lineNet.toFixed(2) +
              " " +
              esc(inv.cur) +
              "</td></tr>"
          )
          .join("")
      : "<tr><td colspan='5' class='err'>" + esc((inv.errors || []).join("; ") || "Keine Positionen gefunden.") + "</td></tr>";

    document.getElementById("a4-net").textContent = inv.net.toFixed(2) + " " + inv.cur;
    document.getElementById("a4-vat").textContent = inv.vat.toFixed(2) + " " + inv.cur;
    document.getElementById("a4-gross").textContent = inv.gross.toFixed(2) + " " + inv.cur;

    document.getElementById("a4-stamp").textContent =
      "EN 16931 geprüft · DATEV BU " +
      inv.bu +
      " / SKR03 " +
      inv.acct +
      " · 100 % lokal in Chrome ohne Cloud-Upload — EInvoiceLocal (domstijn.github.io/friction-killer-suite/de/xrechnung-zugferd-konverter/)";
  }

  function renderDocs(docs) {
    const parsed = docs.map((d) => CORE.parseXmlInvoice(d.text, d.name, DOMParser));
    const tbody = document.getElementById("batch-body");
    tbody.innerHTML = "";
    let validCnt = 0;
    let netCents = 0;
    let vatCents = 0;
    let grossCents = 0;
    const curs = new Set();

    parsed.forEach((inv, idx) => {
      if (inv.valid) validCnt += 1;
      const sign = inv.isCreditNote ? -1 : 1;
      netCents += CORE.toCents(inv.net) * sign;
      vatCents += CORE.toCents(inv.vat) * sign;
      grossCents += CORE.toCents(inv.gross) * sign;
      if (inv.cur && inv.syntax !== "UNKNOWN") curs.add(inv.cur);

      const tr = document.createElement("tr");
      tr.className = "row-item" + (idx === 0 ? " active" : "");
      const grossDisplay = (inv.isCreditNote ? "-" : "") + inv.gross.toFixed(2) + " " + inv.cur;
      tr.innerHTML =
        '<td class="mono">' +
        esc(inv.id) +
        (inv.isCreditNote ? " <small>(CN)</small>" : "") +
        "</td><td>" +
        esc(inv.syntax) +
        "</td><td>" +
        esc(inv.seller || "—") +
        '</td><td class="mono">BU ' +
        esc(inv.bu) +
        " / " +
        esc(inv.acct) +
        '</td><td class="right mono">' +
        esc(grossDisplay) +
        '</td><td class="center">' +
        (inv.valid ? '<span class="pass">PASS</span>' : '<span class="err">ERR</span>') +
        "</td>";
      tr.addEventListener("click", () => {
        tbody.querySelectorAll(".row-item").forEach((r) => r.classList.remove("active"));
        tr.classList.add("active");
        renderA4(inv);
      });
      tbody.appendChild(tr);
    });

    const curList = Array.from(curs);
    const fmtSum = (c) => {
      const val = Math.abs(c) / 100;
      const pref = c < 0 ? "-" : "";
      if (curList.length > 1) return pref + val.toFixed(2) + " (" + curList.join("/") + ")";
      if (curList.length === 1 && curList[0] !== "EUR") return pref + val.toFixed(2) + " " + curList[0];
      return pref + "€" + val.toFixed(2);
    };

    document.getElementById("stat-valid").textContent = validCnt + " / " + parsed.length;
    document.getElementById("stat-net").textContent = fmtSum(netCents);
    document.getElementById("stat-vat").textContent = fmtSum(vatCents);
    document.getElementById("stat-gross").textContent = fmtSum(grossCents);
    if (parsed[0]) renderA4(parsed[0]);
  }

  document.getElementById("sample-btn")?.addEventListener("click", () => renderDocs(SAMPLE_DOCS));
  document.getElementById("print-btn")?.addEventListener("click", () => window.print());
  document.getElementById("xml-files")?.addEventListener("change", async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    try {
      const docs = await Promise.all(files.map(async (f) => ({ name: f.name, text: await f.text() })));
      renderDocs(docs);
    } catch {
      document.getElementById("batch-body").innerHTML = '<tr><td colspan="6" class="err">Fehler beim Lesen der Datei.</td></tr>';
    }
  });
})();
