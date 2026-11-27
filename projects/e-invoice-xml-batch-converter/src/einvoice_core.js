(function (root) {
  "use strict";

  function toCents(raw) {
    if (typeof raw === "number") {
      if (!Number.isFinite(raw)) return 0;
      return raw >= 0 ? Math.floor(raw * 100 + 0.5000001) : -Math.floor(-raw * 100 + 0.5000001);
    }
    const s = String(raw ?? "").trim();
    const m = s.match(/^([+-]?)\s*(\d+)(?:\.(\d+))?$/);
    if (!m) return 0;
    const sign = m[1] === "-" ? -1 : 1;
    const whole = parseInt(m[2], 10);
    const frac = (m[3] || "") + "000";
    let cents = whole * 100 + parseInt(frac.slice(0, 2), 10);
    if (parseInt(frac[2], 10) >= 5) cents += 1;
    return sign * cents;
  }

  function num(v) {
    return toCents(v) / 100;
  }

  function fmtRate(r) {
    return Number(num(r).toFixed(2)).toString();
  }

  function escHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function sanitizeCsvVal(v) {
    const s = String(v ?? "");
    if (/^[=+\-@\t\r]/.test(s) && !/^-?\d+([.,]\d+)?$/.test(s)) {
      return "'" + s;
    }
    return s;
  }

  function csvCellSemi(v) {
    const s = sanitizeCsvVal(v);
    return /[;"\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function csvCellComma(v) {
    const s = sanitizeCsvVal(v);
    return /[,"\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function localName(el) {
    return (el?.localName || el?.tagName || "").split(":").pop();
  }

  function kids(parent, name) {
    return parent ? Array.from(parent.children || []).filter((c) => localName(c) === name) : [];
  }

  function kid(parent, name) {
    return kids(parent, name)[0] || null;
  }

  function pathEl(node, parts) {
    let cur = node;
    for (const p of parts) {
      cur = kid(cur, p);
      if (!cur) return null;
    }
    return cur;
  }

  function pathTxt(node, parts, defVal = "") {
    const el = parts.length ? pathEl(node, parts) : node;
    return (el?.textContent || defVal).trim();
  }

  function normDate(s) {
    const c = String(s || "").trim();
    if (/^\d{8}$/.test(c)) return c.slice(0, 4) + "-" + c.slice(4, 6) + "-" + c.slice(6, 8);
    return c.slice(0, 10);
  }

  function mapLineTax(cat, rate) {
    const c = String(cat || "S").trim().toUpperCase();
    const r = num(rate);
    if (c === "AE") {
      return {
        bu: "94",
        acct: "3123",
        xeroTax: "Reverse Charge Expenses (0%)",
        qboAcct: "3123 EU Reverse Charge (§13b)",
      };
    }
    if (c === "K") {
      if (Math.abs(r - 7) <= 0.05) {
        return {
          bu: "92",
          acct: "3420",
          xeroTax: "EC Acquisitions (7%)",
          qboAcct: "3420 Intra-EU Acquisition (7%)",
        };
      }
      return {
        bu: "91",
        acct: "3425",
        xeroTax: "EC Acquisitions (19%)",
        qboAcct: "3425 Intra-EU Acquisition (19%)",
      };
    }
    if (Math.abs(r - 19) <= 0.05) {
      return {
        bu: "9",
        acct: "3400",
        xeroTax: "INPUT (19%)",
        qboAcct: "3400 Standard Purchases (19%)",
      };
    }
    if (Math.abs(r - 7) <= 0.05) {
      return {
        bu: "8",
        acct: "3300",
        xeroTax: "INPUT (7%)",
        qboAcct: "3300 Reduced Purchases (7%)",
      };
    }
    if (r === 0 || ["E", "Z", "O", "G"].includes(c)) {
      return {
        bu: "0",
        acct: "3200",
        xeroTax: "EXEMPTINPUT (0%)",
        qboAcct: "3200 Tax-Exempt Purchases (0%)",
      };
    }
    return {
      bu: "0",
      acct: "3425",
      xeroTax: "INPUT (" + fmtRate(r) + "%)",
      qboAcct: "3425 General Purchases",
    };
  }

  function pickUblVatId(partyEl) {
    if (!partyEl) return "";
    const schemes = kids(partyEl, "PartyTaxScheme");
    let fallback = "";
    for (const sc of schemes) {
      const cid = pathTxt(sc, ["CompanyID"]);
      if (!cid) continue;
      const schemeId = pathTxt(sc, ["TaxScheme", "ID"]).toUpperCase();
      if (schemeId === "VAT") return cid;
      if (!fallback) fallback = cid;
    }
    return fallback;
  }

  function pickCiiVatId(partyEl) {
    if (!partyEl) return "";
    const regs = kids(partyEl, "SpecifiedTaxRegistration");
    let fallback = "";
    for (const reg of regs) {
      const idEl = kid(reg, "ID");
      if (!idEl) continue;
      const txt = (idEl.textContent || "").trim();
      if (!txt) continue;
      const scheme = (idEl.getAttribute?.("schemeID") || "").trim().toUpperCase();
      if (scheme === "VA") return txt;
      if (!fallback) fallback = txt;
    }
    return fallback;
  }

  function pickCurrencyAmt(parent, tagName, cur) {
    const els = kids(parent, tagName);
    if (!els.length) return 0;
    const match = els.find((el) => {
      const cid = (el.getAttribute?.("currencyID") || "").trim().toUpperCase();
      return !cid || cid === cur;
    });
    return num((match || els[0]).textContent);
  }

  function pickUblTaxTotal(root, cur) {
    const taxTotals = kids(root, "TaxTotal");
    if (!taxTotals.length) return 0;
    const match = taxTotals.find((tt) => {
      const amtEl = kid(tt, "TaxAmount");
      const cid = (amtEl?.getAttribute?.("currencyID") || "").trim().toUpperCase();
      return amtEl && (!cid || cid === cur);
    });
    return num(pathTxt(match || taxTotals[0], ["TaxAmount"]));
  }

  function hasParserError(dom, root) {
    if (!root) return true;
    const rn = localName(root).toLowerCase();
    if (rn === "parsererror" || rn === "html") return true;
    if (typeof dom?.getElementsByTagName === "function") {
      const errs = dom.getElementsByTagName("parsererror");
      if (errs && errs.length > 0) return true;
    }
    return false;
  }

  function parseXmlInvoice(xmlText, filename, DOMParserCtor) {
    const Parser = DOMParserCtor || root.DOMParser;
    const errors = [];
    let dom;
    try {
      dom = new Parser().parseFromString(String(xmlText || "").trim(), "application/xml");
    } catch (err) {
      return {
        filename: filename || "invoice.xml",
        syntax: "UNKNOWN",
        isCreditNote: false,
        id: filename || "(invalid)",
        issue: "",
        due: "",
        cur: "EUR",
        buyerRef: "",
        seller: "",
        sellerVat: "",
        iban: "",
        buyer: "",
        buyerVat: "",
        net: 0,
        vat: 0,
        gross: 0,
        lines: [],
        valid: false,
        errors: ["Invalid XML syntax: " + (err?.message || "parse failed")],
        bu: "0",
        acct: "3200",
      };
    }

    const xmlRoot = dom?.documentElement;
    if (hasParserError(dom, xmlRoot)) {
      return {
        filename: filename || "invoice.xml",
        syntax: "UNKNOWN",
        isCreditNote: false,
        id: filename || "(invalid XML)",
        issue: "",
        due: "",
        cur: "EUR",
        buyerRef: "",
        seller: "",
        sellerVat: "",
        iban: "",
        buyer: "",
        buyerVat: "",
        net: 0,
        vat: 0,
        gross: 0,
        lines: [],
        valid: false,
        errors: ["Invalid XML syntax (parsererror)."],
        bu: "0",
        acct: "3200",
      };
    }

    const rn = localName(xmlRoot);
    let syntax = "UBL_2.1";
    let isCreditNote = false;
    let id = "";
    let issue = "";
    let due = "";
    let cur = "EUR";
    let buyerRef = "";
    let seller = "";
    let sellerVat = "";
    let iban = "";
    let buyer = "";
    let buyerVat = "";
    let net = 0;
    let vat = 0;
    let gross = 0;
    const lines = [];

    if (rn === "Invoice" || rn === "CreditNote") {
      isCreditNote = rn === "CreditNote";
      id = pathTxt(xmlRoot, ["ID"]);
      issue = normDate(pathTxt(xmlRoot, ["IssueDate"]));
      due = normDate(pathTxt(xmlRoot, ["DueDate"]) || pathTxt(xmlRoot, ["PaymentMeans", "PaymentDueDate"])) || issue;
      cur = pathTxt(xmlRoot, ["DocumentCurrencyCode"], "EUR").toUpperCase() || "EUR";
      buyerRef = pathTxt(xmlRoot, ["BuyerReference"]);

      const sp = pathEl(xmlRoot, ["AccountingSupplierParty", "Party"]);
      seller = pathTxt(sp, ["PartyLegalEntity", "RegistrationName"]) || pathTxt(sp, ["PartyName", "Name"]);
      sellerVat = pickUblVatId(sp);
      iban = pathTxt(xmlRoot, ["PaymentMeans", "PayeeFinancialAccount", "ID"]);

      const cp = pathEl(xmlRoot, ["AccountingCustomerParty", "Party"]);
      buyer = pathTxt(cp, ["PartyLegalEntity", "RegistrationName"]) || pathTxt(cp, ["PartyName", "Name"]);
      buyerVat = pickUblVatId(cp);

      vat = pickUblTaxTotal(xmlRoot, cur);
      const lmt = kid(xmlRoot, "LegalMonetaryTotal");
      net = num(pathTxt(lmt, ["TaxExclusiveAmount"]));
      gross = num(pathTxt(lmt, ["PayableAmount"]) || pathTxt(lmt, ["TaxInclusiveAmount"]));

      const lineTag = isCreditNote ? "CreditNoteLine" : "InvoiceLine";
      const qtyTag = isCreditNote ? "CreditedQuantity" : "InvoicedQuantity";
      kids(xmlRoot, lineTag).forEach((li) => {
        const cat = pathEl(li, ["Item", "ClassifiedTaxCategory"]);
        const rate = num(pathTxt(cat, ["Percent"]));
        const catCode = pathTxt(cat, ["ID"], "S").toUpperCase();
        const qty = num(pathTxt(li, [qtyTag], "1"));
        const rawUnit = num(pathTxt(li, ["Price", "PriceAmount"]));
        const baseQty = num(pathTxt(li, ["Price", "BaseQuantity"], "1"));
        let unit = baseQty > 0 && baseQty !== 1 ? num(rawUnit / baseQty) : rawUnit;
        const lineNet = num(pathTxt(li, ["LineExtensionAmount"]));
        if (qty !== 0 && Math.abs(num(qty * unit) - lineNet) > 0.02) {
          unit = num(lineNet / qty);
        }
        const effRate = catCode === "AE" || catCode === "K" ? 0 : rate;
        const mapped = mapLineTax(catCode, rate);
        lines.push({
          name: pathTxt(li, ["Item", "Name"]) || pathTxt(li, ["Item", "Description"]) || "Line Item",
          qty,
          unit,
          lineNet,
          lineTax: num((lineNet * effRate) / 100),
          rate,
          cat: catCode,
          bu: mapped.bu,
          acct: mapped.acct,
          xeroTax: mapped.xeroTax,
          qboAcct: mapped.qboAcct,
        });
      });

      kids(xmlRoot, "AllowanceCharge").forEach((ac) => {
        const isCharge = pathTxt(ac, ["ChargeIndicator"], "false").toLowerCase() === "true";
        const sign = isCharge ? 1 : -1;
        const amt = num(sign * num(pathTxt(ac, ["Amount"])));
        const cat = kid(ac, "TaxCategory");
        const rate = num(pathTxt(cat, ["Percent"]));
        const catCode = pathTxt(cat, ["ID"], "S").toUpperCase();
        const effRate = catCode === "AE" || catCode === "K" ? 0 : rate;
        const mapped = mapLineTax(catCode, rate);
        const reason = pathTxt(ac, ["AllowanceChargeReason"]) || (isCharge ? "Header Charge" : "Header Allowance");
        lines.push({
          name: reason,
          qty: 1,
          unit: amt,
          lineNet: amt,
          lineTax: num((amt * effRate) / 100),
          rate,
          cat: catCode,
          bu: mapped.bu,
          acct: mapped.acct,
          xeroTax: mapped.xeroTax,
          qboAcct: mapped.qboAcct,
        });
      });
    } else if (rn === "CrossIndustryInvoice") {
      syntax = "CII_EN16931";
      const ex = kid(xmlRoot, "ExchangedDocument");
      id = pathTxt(ex, ["ID"]);
      const typeCode = pathTxt(ex, ["TypeCode"], "380");
      isCreditNote = typeCode === "381";
      issue = normDate(pathTxt(ex, ["IssueDateTime", "DateTimeString"]));

      const tx = kid(xmlRoot, "SupplyChainTradeTransaction");
      const agr = kid(tx, "ApplicableHeaderTradeAgreement");
      buyerRef = pathTxt(agr, ["BuyerReference"]);
      const sp = kid(agr, "SellerTradeParty");
      seller = pathTxt(sp, ["Name"]);
      sellerVat = pickCiiVatId(sp);

      const cp = kid(agr, "BuyerTradeParty");
      buyer = pathTxt(cp, ["Name"]);
      buyerVat = pickCiiVatId(cp);

      const setEl = kid(tx, "ApplicableHeaderTradeSettlement");
      cur = pathTxt(setEl, ["InvoiceCurrencyCode"], "EUR").toUpperCase() || "EUR";
      iban = pathTxt(setEl, ["SpecifiedTradeSettlementPaymentMeans", "PayeePartyCreditorFinancialAccount", "IBANID"]);
      due = normDate(pathTxt(setEl, ["SpecifiedTradePaymentTerms", "DueDateDateTime", "DateTimeString"])) || issue;

      const summ = kid(setEl, "SpecifiedTradeSettlementHeaderMonetarySummation");
      net = pickCurrencyAmt(summ, "TaxBasisTotalAmount", cur);
      vat = pickCurrencyAmt(summ, "TaxTotalAmount", cur);
      gross = num(pathTxt(summ, ["DuePayableAmount"]) || pathTxt(summ, ["GrandTotalAmount"]));

      kids(tx, "IncludedSupplyChainTradeLineItem").forEach((li) => {
        const ls = kid(li, "SpecifiedLineTradeSettlement");
        const rate = num(pathTxt(ls, ["ApplicableTradeTax", "RateApplicablePercent"]));
        const catCode = pathTxt(ls, ["ApplicableTradeTax", "CategoryCode"], "S").toUpperCase();
        const qty = num(pathTxt(li, ["SpecifiedLineTradeDelivery", "BilledQuantity"], "1"));
        const rawUnit = num(pathTxt(li, ["SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "ChargeAmount"]));
        const basisQty = num(pathTxt(li, ["SpecifiedLineTradeAgreement", "NetPriceProductTradePrice", "BasisQuantity"], "1"));
        let unit = basisQty > 0 && basisQty !== 1 ? num(rawUnit / basisQty) : rawUnit;
        const lineNet = num(pathTxt(ls, ["SpecifiedTradeSettlementLineMonetarySummation", "LineTotalAmount"]));
        if (qty !== 0 && Math.abs(num(qty * unit) - lineNet) > 0.02) {
          unit = num(lineNet / qty);
        }
        const effRate = catCode === "AE" || catCode === "K" ? 0 : rate;
        const mapped = mapLineTax(catCode, rate);
        lines.push({
          name: pathTxt(li, ["SpecifiedTradeProduct", "Name"]) || "Line Item",
          qty,
          unit,
          lineNet,
          lineTax: num((lineNet * effRate) / 100),
          rate,
          cat: catCode,
          bu: mapped.bu,
          acct: mapped.acct,
          xeroTax: mapped.xeroTax,
          qboAcct: mapped.qboAcct,
        });
      });

      kids(setEl, "SpecifiedTradeAllowanceCharge").forEach((ac) => {
        const indTxt = pathTxt(ac, ["ChargeIndicator", "Indicator"], "") || pathTxt(ac, ["ChargeIndicator"], "false");
        const isCharge = indTxt.toLowerCase() === "true";
        const sign = isCharge ? 1 : -1;
        const amt = num(sign * num(pathTxt(ac, ["ActualAmount"])));
        const cat = kid(ac, "CategoryTradeTax");
        const rate = num(pathTxt(cat, ["RateApplicablePercent"]));
        const catCode = pathTxt(cat, ["CategoryCode"], "S").toUpperCase();
        const effRate = catCode === "AE" || catCode === "K" ? 0 : rate;
        const mapped = mapLineTax(catCode, rate);
        const reason = pathTxt(ac, ["Reason"]) || (isCharge ? "Header Charge" : "Header Allowance");
        lines.push({
          name: reason,
          qty: 1,
          unit: amt,
          lineNet: amt,
          lineTax: num((amt * effRate) / 100),
          rate,
          cat: catCode,
          bu: mapped.bu,
          acct: mapped.acct,
          xeroTax: mapped.xeroTax,
          qboAcct: mapped.qboAcct,
        });
      });
    } else {
      return {
        filename: filename || "invoice.xml",
        syntax: "UNKNOWN",
        isCreditNote: false,
        id: filename || "(unsupported XML)",
        issue: "",
        due: "",
        cur: "EUR",
        buyerRef: "",
        seller: "",
        sellerVat: "",
        iban: "",
        buyer: "",
        buyerVat: "",
        net: 0,
        vat: 0,
        gross: 0,
        lines: [],
        valid: false,
        errors: ["Unsupported XML root <" + rn + "> (expected UBL Invoice/CreditNote or CII CrossIndustryInvoice)."],
        bu: "0",
        acct: "3200",
      };
    }

    if (!id) errors.push("BR-CO-13: Missing invoice_id");
    if (!issue) errors.push("BR-CO-13: Missing issue_date");
    if (!seller) errors.push("BR-CO-13: Missing seller_name");
    if (!buyer) errors.push("BR-CO-13: Missing buyer_name");

    const sumLines = num(lines.reduce((a, b) => a + toCents(b.lineNet), 0) / 100);
    const sumLineVat = num(lines.reduce((a, b) => a + toCents(b.lineTax), 0) / 100);
    const diffVat = num(vat - sumLineVat);

    if (lines.length > 0 && Math.abs(sumLines - net) > 0.02) {
      errors.push("BR-CO-10: Sum of line net (" + sumLines.toFixed(2) + ") != TaxExclusiveAmount (" + net.toFixed(2) + ")");
    }
    if (lines.length > 0 && Math.abs(diffVat) > 0.05) {
      errors.push("BR-CO-14: Sum of line VAT (" + sumLineVat.toFixed(2) + ") != TaxTotal (" + vat.toFixed(2) + ")");
    } else if (lines.length > 0 && diffVat !== 0) {
      const adj = [...lines].reverse().find((l) => l.lineTax !== 0) || lines[lines.length - 1];
      adj.lineTax = num(adj.lineTax + diffVat);
    }
    if (Math.abs(num(net + vat) - gross) > 0.02) {
      errors.push("BR-CO-15: Net + VAT (" + num(net + vat).toFixed(2) + ") != PayableAmount (" + gross.toFixed(2) + ")");
    }

    let bu = "0";
    let acct = "3200";
    if (lines.length) {
      const bus = [];
      const accts = [];
      lines.forEach((l) => {
        if (!bus.includes(l.bu)) bus.push(l.bu);
        if (!accts.includes(l.acct)) accts.push(l.acct);
      });
      bu = bus.join("+");
      acct = accts.join(",");
    } else if (Math.abs(net) > 0 && Math.abs(vat) > 0) {
      const inf = mapLineTax("S", (Math.abs(vat) / Math.abs(net)) * 100);
      bu = inf.bu;
      acct = inf.acct;
    }

    return {
      filename: filename || "invoice.xml",
      syntax,
      isCreditNote,
      id: id || filename || "(missing ID)",
      issue,
      due,
      cur,
      buyerRef,
      seller,
      sellerVat,
      iban,
      buyer,
      buyerVat,
      net,
      vat,
      gross,
      lines,
      valid: errors.length === 0,
      errors,
      bu,
      acct,
    };
  }

  function buildExports(parsedInvoices) {
    const datevHeader = "Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Konto;Gegenkonto;BU-Schlüssel;Belegdatum;Belegfeld 1;Buchungstext";
    const xeroHeader = "*ContactName,*InvoiceNumber,*InvoiceDate,*DueDate,*Description,*Quantity,*UnitAmount,*AccountCode,*TaxType,TaxAmount,Currency";
    const qboHeader = "BillNo,Supplier,BillDate,DueDate,Account,LineDescription,Quantity,UnitPrice,LineAmount,TaxCode,TaxAmount,Currency";

    const datevRows = [];
    const xeroRows = [];
    const qboRows = [];

    parsedInvoices.forEach((inv) => {
      if (!inv || (inv.syntax === "UNKNOWN" && inv.lines.length === 0 && inv.gross === 0)) return;
      const p = String(inv.issue || "").split("-");
      const ddmm = p.length === 3 && p[1].length === 2 && p[2].length === 2 ? p[2] + p[1] : "";
      const infRate = Math.abs(inv.net) > 0 && Math.abs(inv.vat) > 0 ? (Math.abs(inv.vat) / Math.abs(inv.net)) * 100 : 0;
      const fallbackMapped = mapLineTax("S", infRate);

      const exportLines = inv.lines.length
        ? inv.lines
        : [
            {
              name: inv.syntax + " Invoice " + inv.id,
              qty: 1,
              unit: inv.net,
              lineNet: inv.net,
              lineTax: inv.vat,
              rate: num(infRate),
              bu: inv.bu || fallbackMapped.bu,
              acct: inv.acct || fallbackMapped.acct,
              xeroTax: fallbackMapped.xeroTax,
              qboAcct: fallbackMapped.qboAcct,
            },
          ];

      const bMap = new Map();
      exportLines.forEach((ln) => {
        const bk = ln.bu + "|" + ln.acct + "|" + ln.rate.toFixed(2);
        if (!bMap.has(bk)) bMap.set(bk, { bu: ln.bu, acct: ln.acct, gross: 0 });
        bMap.get(bk).gross = num(bMap.get(bk).gross + ln.lineNet + ln.lineTax);
      });
      const buckets = Array.from(bMap.values());
      buckets.forEach((b) => {
        const isNegBucket = b.gross < 0;
        const sh = (inv.isCreditNote ? !isNegBucket : isNegBucket) ? "H" : "S";
        const text = buckets.length > 1 ? inv.seller + " (" + inv.syntax + " · BU " + b.bu + ")" : inv.seller + " (" + inv.syntax + ")";
        datevRows.push(
          [
            Math.abs(b.gross).toFixed(2).replace(".", ","),
            sh,
            inv.cur,
            b.acct,
            "70000",
            b.bu,
            ddmm,
            inv.id,
            text,
          ]
            .map(csvCellSemi)
            .join(";")
        );
      });

      const docSign = inv.isCreditNote ? -1 : 1;
      exportLines.forEach((ln) => {
        const signedUnit = num(ln.unit * docSign);
        const signedNet = num(ln.lineNet * docSign);
        const signedTax = num(ln.lineTax * docSign);
        xeroRows.push(
          [
            inv.seller,
            inv.id,
            inv.issue,
            inv.due,
            ln.name,
            ln.qty.toFixed(2),
            signedUnit.toFixed(2),
            ln.acct,
            ln.xeroTax,
            signedTax.toFixed(2),
            inv.cur,
          ]
            .map(csvCellComma)
            .join(",")
        );
        qboRows.push(
          [
            inv.id,
            inv.seller,
            inv.issue,
            inv.due,
            ln.qboAcct,
            ln.name,
            ln.qty.toFixed(2),
            signedUnit.toFixed(2),
            signedNet.toFixed(2),
            "BU " + ln.bu,
            signedTax.toFixed(2),
            inv.cur,
          ]
            .map(csvCellComma)
            .join(",")
        );
      });
    });

    return {
      datev: [datevHeader, ...datevRows].join("\n"),
      xero: [xeroHeader, ...xeroRows].join("\n"),
      qbo: [qboHeader, ...qboRows].join("\n"),
      datevRows,
      xeroRows,
      qboRows,
      headers: { datev: datevHeader, xero: xeroHeader, qbo: qboHeader },
    };
  }

  const api = {
    toCents,
    num,
    fmtRate,
    escHtml,
    sanitizeCsvVal,
    csvCellSemi,
    csvCellComma,
    normDate,
    mapLineTax,
    parseXmlInvoice,
    buildExports,
  };

  root.EInvoiceCore = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : window);
