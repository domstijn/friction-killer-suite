"""OssVatBridge core EU VAT One-Stop-Shop (OSS) compiler and portal exporter (pure stdlib)."""

from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from xml.sax.saxutils import escape as xml_escape

FREE_ROW_LIMIT = 15
CENT = Decimal("0.01")

# EU27 Standard VAT rates (%) using EU OSS country codes ('EL' for Greece per EU directive).
EU27_STANDARD_RATES: dict[str, Decimal] = {
    "AT": Decimal("20.00"),
    "BE": Decimal("21.00"),
    "BG": Decimal("20.00"),
    "CY": Decimal("19.00"),
    "CZ": Decimal("21.00"),
    "DE": Decimal("19.00"),
    "DK": Decimal("25.00"),
    "EE": Decimal("24.00"),
    "EL": Decimal("24.00"),
    "ES": Decimal("21.00"),
    "FI": Decimal("25.50"),
    "FR": Decimal("20.00"),
    "HR": Decimal("25.00"),
    "HU": Decimal("27.00"),
    "IE": Decimal("23.00"),
    "IT": Decimal("22.00"),
    "LT": Decimal("21.00"),
    "LU": Decimal("17.00"),
    "LV": Decimal("21.00"),
    "MT": Decimal("18.00"),
    "NL": Decimal("21.00"),
    "PL": Decimal("23.00"),
    "PT": Decimal("23.00"),
    "RO": Decimal("19.00"),
    "SE": Decimal("25.00"),
    "SI": Decimal("22.00"),
    "SK": Decimal("23.00"),
}

DEFAULT_ECB_FX_TO_EUR: dict[str, Decimal] = {
    "EUR": Decimal("1.0000"),
    "USD": Decimal("0.9200"),
    "GBP": Decimal("1.1900"),
    "SEK": Decimal("0.0880"),
    "DKK": Decimal("0.1340"),
    "PLN": Decimal("0.2330"),
    "CZK": Decimal("0.0400"),
    "HUF": Decimal("0.00245"),
    "RON": Decimal("0.2010"),
    "BGN": Decimal("0.5113"),
    "CHF": Decimal("1.0600"),
    "CAD": Decimal("0.6600"),
    "AUD": Decimal("0.6000"),
}

SAMPLE_MULTI_PLATFORM_CSV = """source,order_id,country,currency,subtotal,tax_amount,tax_rate,transaction_type,supply_type,customer_vat_id
stripe_tax,st_1001,FR,EUR,100.00,20.00,20.0,charge,SERVICES,
stripe_tax,st_1002,GR,USD,100.00,24.00,0.24,charge,SERVICES,
shopify,sh_2001,NL,EUR,50.00,10.50,21%,order,GOODS,
shopify,sh_2002,ES,GBP,100.00,21.00,21.0,order,GOODS,
lemon_squeezy,ls_3001,IT,EUR,80.00,17.60,22.0,order,SERVICES,
stripe_tax,st_1003,FR,EUR,25.00,5.00,20.0,refund,SERVICES,
stripe_tax,st_1004,DE,EUR,120.00,22.80,19.0,charge,SERVICES,
shopify,sh_2003,US,USD,200.00,0.00,0.0,order,GOODS,
stripe_tax,st_1005,NL,EUR,300.00,0.00,0.0,charge,SERVICES,NL123456789B01
shopify,sh_2004,AT,EUR,40.00,4.00,10.0,order,GOODS,
lemon_squeezy,ls_3002,BE,EUR,60.00,12.60,21.0,order,SERVICES,
stripe_tax,st_1006,SE,SEK,1000.00,250.00,25.0,charge,SERVICES,
shopify,sh_2005,PL,PLN,200.00,46.00,23.0,order,GOODS,
lemon_squeezy,ls_3003,IE,EUR,90.00,20.70,23.0,order,SERVICES,
stripe_tax,st_1007,PT,EUR,70.00,16.10,23.0,charge,SERVICES,
shopify,sh_2006,FI,EUR,50.00,12.75,25.5,order,SERVICES,
lemon_squeezy,ls_3004,DK,DKK,500.00,125.00,25.0,order,SERVICES,
stripe_tax,st_1008,CZ,CZK,1000.00,210.00,21.0,charge,SERVICES,
shopify,sh_2007,GB,GBP,75.00,0.00,0.0,order,GOODS,
stripe_tax,st_1009,LU,EUR,110.00,18.70,17.0,charge,SERVICES,
"""


def _norm_country(code: str) -> str:
    clean = re.sub(r"[^A-Za-z]", "", str(code or "")).upper()[:2]
    return "EL" if clean == "GR" else clean


def _parse_decimal(raw: Any, default: str = "0") -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text:
        return Decimal(default)
    cleaned = re.sub(r"[€$£\s%]", "", text)
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal(default)


def _parse_rate_percent(raw: Any) -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text:
        return Decimal("0")
    has_pct = "%" in text
    val = _parse_decimal(text, "0")
    if not has_pct and Decimal("0") < abs(val) < Decimal("1"):
        val *= Decimal("100")
    return val.quantize(CENT, rounding=ROUND_HALF_UP)


def _q2(val: Decimal) -> Decimal:
    return val.quantize(CENT, rounding=ROUND_HALF_UP)


def _pick(lowered: dict[str, str], keys: tuple[str, ...], default: str = "") -> str:
    for key in keys:
        if key in lowered and lowered[key] != "":
            return lowered[key]
    return default


def _detect_delimiter(csv_text: str) -> str:
    first_line = next((ln for ln in csv_text.splitlines() if ln.strip()), "")
    if "\t" in first_line and first_line.count("\t") >= first_line.count(","):
        return "\t"
    if ";" in first_line and first_line.count(";") >= first_line.count(","):
        return ";"
    return ","


def parse_transactions_csv(csv_text: str, source_hint: str = "auto") -> list[dict[str, Any]]:
    """Parse Stripe Tax, Shopify Tax, Lemon Squeezy, or generic CSV into normalized rows."""
    cleaned = str(csv_text or "").strip()
    if not cleaned:
        return []

    delimiter = _detect_delimiter(cleaned)
    reader = csv.DictReader(io.StringIO(cleaned), delimiter=delimiter)
    rows: list[dict[str, Any]] = []

    for idx, raw_row in enumerate(reader, start=1):
        if not any(str(v or "").strip() for v in raw_row.values()):
            continue
        lowered = {
            str(k).strip().lower(): str(v).strip()
            for k, v in raw_row.items()
            if k is not None
        }
        detected_source = (
            _pick(lowered, ("source", "platform"), "")
            or (
                "stripe_tax"
                if ("tax_country" in lowered or "taxable_amount" in lowered)
                else "shopify"
                if ("shipping_country" in lowered or "net_sales" in lowered or "taxes" in lowered)
                else "lemon_squeezy"
                if ("subtotal" in lowered and "tax" in lowered)
                else "csv"
            )
            if source_hint == "auto"
            else source_hint
        )
        country = _pick(
            lowered,
            (
                "tax_country",
                "customer_tax_country",
                "customer_country",
                "shipping_country",
                "country_code",
                "country",
                "billing_country",
            ),
        )
        currency = (_pick(lowered, ("currency", "presentment_currency", "order_currency"), "EUR") or "EUR").upper()
        tax_amount = _parse_decimal(
            _pick(lowered, ("tax_amount", "vat_amount", "total_tax", "taxes", "tax"), "0")
        )
        raw_subtotal = _pick(
            lowered,
            ("taxable_amount", "subtotal", "net_sales", "net_amount", "amount_excluding_tax"),
            "",
        )
        if raw_subtotal != "":
            taxable_amount = _parse_decimal(raw_subtotal)
        else:
            gross_amount = _parse_decimal(_pick(lowered, ("gross_sales", "total", "amount"), "0"))
            taxable_amount = gross_amount - tax_amount

        tax_rate = _parse_rate_percent(_pick(lowered, ("tax_rate", "vat_rate", "tax_percentage", "rate"), "0"))
        tx_type = _pick(lowered, ("transaction_type", "tx_type", "type", "kind", "status"), "charge").lower()
        supply_raw = _pick(lowered, ("supply_type", "product_type", "tax_code_type"), "SERVICES").upper()
        supply_type = "GOODS" if "GOOD" in supply_raw or "PHYS" in supply_raw else "SERVICES"
        customer_vat_id = _pick(
            lowered,
            ("customer_vat_id", "vat_id", "tax_id", "customer_tax_id", "buyer_vat_number"),
            "",
        )
        rate_type_override = _pick(lowered, ("rate_type", "vat_rate_type"), "").upper()

        rows.append(
            {
                "row_num": idx,
                "source": detected_source,
                "country": country,
                "currency": currency,
                "taxable_amount": taxable_amount,
                "tax_amount": tax_amount,
                "tax_rate": tax_rate,
                "transaction_type": tx_type,
                "supply_type": supply_type,
                "customer_vat_id": customer_vat_id,
                "rate_type": rate_type_override if rate_type_override in {"STANDARD", "REDUCED"} else "",
            }
        )
    return rows


def _to_decimal_fx(fx_rates: dict[str, Any] | None) -> dict[str, Decimal]:
    merged = dict(DEFAULT_ECB_FX_TO_EUR)
    if fx_rates:
        for cur, rate in fx_rates.items():
            merged[str(cur).strip().upper()] = _parse_decimal(rate, "1")
    return merged


def compile_oss_return(
    rows: list[dict[str, Any]],
    *,
    home_country: str = "DE",
    quarter: str = "2026-Q4",
    fx_rates: dict[str, Any] | None = None,
    pro_unlocked: bool = False,
) -> dict[str, Any]:
    """Compile normalized transaction rows into an EU27 OSS summary, buckets, exclusions, and warnings."""
    total_input_rows = len(rows)
    truncated_free_tier = (not pro_unlocked) and (total_input_rows > FREE_ROW_LIMIT)
    selected = rows if pro_unlocked else rows[:FREE_ROW_LIMIT]
    truncated_rows = max(0, total_input_rows - len(selected))

    home_ms = _norm_country(home_country)
    fx_map = _to_decimal_fx(fx_rates)
    excluded = {"NON_EU": 0, "DOMESTIC_HOME_STATE": 0, "B2B_REVERSE_CHARGE": 0}
    warnings: list[str] = []
    buckets_map: dict[tuple[str, str, str, Decimal], dict[str, Any]] = {}

    for row in selected:
        mscon = _norm_country(str(row.get("country", "")))
        if mscon not in EU27_STANDARD_RATES:
            excluded["NON_EU"] += 1
            continue
        if mscon == home_ms:
            excluded["DOMESTIC_HOME_STATE"] += 1
            continue

        vat_id = str(row.get("customer_vat_id") or "").strip()
        tax_amt = _parse_decimal(row.get("tax_amount", 0))
        if vat_id and tax_amt == Decimal("0"):
            excluded["B2B_REVERSE_CHARGE"] += 1
            continue

        taxable_amt = _parse_decimal(row.get("taxable_amount", 0))
        tx_type = str(row.get("transaction_type") or "charge").lower()
        is_refund = any(tok in tx_type for tok in ("refund", "credit", "chargeback"))
        if is_refund:
            if taxable_amt > Decimal("0"):
                taxable_amt = -taxable_amt
            if tax_amt > Decimal("0"):
                tax_amt = -tax_amt

        currency = str(row.get("currency") or "EUR").strip().upper()
        if currency not in fx_map:
            warnings.append(f"Row {row.get('row_num', '?')}: Unknown currency {currency}; defaulted FX rate to 1.00.")
        fx_mult = fx_map.get(currency, Decimal("1.0"))
        taxable_eur = _q2(taxable_amt * fx_mult)
        vat_eur = _q2(tax_amt * fx_mult)

        vat_rate = _parse_rate_percent(row.get("tax_rate", 0))
        if vat_rate == Decimal("0"):
            if taxable_eur != Decimal("0") and vat_eur != Decimal("0"):
                vat_rate = _q2((vat_eur / taxable_eur) * Decimal("100"))
            else:
                vat_rate = EU27_STANDARD_RATES[mscon]

        expected_vat = _q2((taxable_eur * vat_rate) / Decimal("100"))
        if abs(vat_eur - expected_vat) > Decimal("0.05"):
            warnings.append(
                f"Row {row.get('row_num', '?')} ({mscon}): VAT EUR {vat_eur:.2f} differs from "
                f"{taxable_eur:.2f} * {vat_rate}% = {expected_vat:.2f}."
            )

        std_rate = EU27_STANDARD_RATES[mscon]
        rate_type = str(row.get("rate_type") or "").upper()
        if rate_type not in {"STANDARD", "REDUCED"}:
            rate_type = "REDUCED" if vat_rate < (std_rate - Decimal("2.50")) else "STANDARD"

        supply_type = "GOODS" if str(row.get("supply_type") or "").upper() == "GOODS" else "SERVICES"
        key = (mscon, supply_type, rate_type, vat_rate)
        if key not in buckets_map:
            buckets_map[key] = {
                "mscon": mscon,
                "supply_type": supply_type,
                "rate_type": rate_type,
                "vat_rate": vat_rate,
                "tx_count": 0,
                "net_taxable_eur": Decimal("0.00"),
                "net_vat_eur": Decimal("0.00"),
            }
        bucket = buckets_map[key]
        bucket["tx_count"] += 1
        bucket["net_taxable_eur"] = _q2(bucket["net_taxable_eur"] + taxable_eur)
        bucket["net_vat_eur"] = _q2(bucket["net_vat_eur"] + vat_eur)

    sorted_keys = sorted(buckets_map.keys())
    buckets: list[dict[str, Any]] = []
    total_taxable_eur = Decimal("0.00")
    total_vat_due_eur = Decimal("0.00")
    active_states: set[str] = set()

    for key in sorted_keys:
        b = buckets_map[key]
        if b["net_taxable_eur"] < Decimal("0.00") or b["net_vat_eur"] < Decimal("0.00"):
            warnings.append(
                f"{b['mscon']} ({b['supply_type']} {b['vat_rate']}%): Negative net period balance "
                f"({b['net_taxable_eur']:.2f} EUR) requires an OSS correction entry on BZSt/ROS."
            )
        total_taxable_eur = _q2(total_taxable_eur + b["net_taxable_eur"])
        total_vat_due_eur = _q2(total_vat_due_eur + b["net_vat_eur"])
        active_states.add(b["mscon"])
        buckets.append(
            {
                "mscon": b["mscon"],
                "supply_type": b["supply_type"],
                "rate_type": b["rate_type"],
                "vat_rate": f"{b['vat_rate']:.2f}",
                "tx_count": b["tx_count"],
                "net_taxable_eur": f"{b['net_taxable_eur']:.2f}",
                "net_vat_eur": f"{b['net_vat_eur']:.2f}",
            }
        )

    if len(buckets) > 1000:
        warnings.append(
            f"Bucket count ({len(buckets)}) exceeds Germany BZSt BOP's 1,000-row CSV upload cap; split across batches."
        )

    return {
        "ok": True,
        "pro_unlocked": pro_unlocked,
        "truncated_free_tier": truncated_free_tier,
        "total_input_rows": total_input_rows,
        "processed_rows": len(selected),
        "truncated_rows": truncated_rows,
        "home_country": home_ms,
        "quarter": quarter,
        "summary": {
            "total_taxable_eur": f"{total_taxable_eur:.2f}",
            "total_vat_due_eur": f"{total_vat_due_eur:.2f}",
            "active_member_states": len(active_states),
            "bucket_count": len(buckets),
        },
        "buckets": buckets,
        "excluded": excluded,
        "warnings": warnings,
    }


def _require_pro_report(report: dict[str, Any]) -> None:
    if not report.get("pro_unlocked"):
        raise PermissionError("Pro license required to export portal-ready EU OSS files.")


def _de_decimal(val: Any) -> str:
    return f"{Decimal(str(val)):.2f}".replace(".", ",")


def render_bzst_bop_csv(report: dict[str, Any]) -> str:
    """Render Germany BZSt/BOP OSS upload CSV (semicolon delimiter, comma decimals)."""
    _require_pro_report(report)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\n")
    writer.writerow(
        [
            "Satzart",
            "Land des Verbrauchs",
            "Umsatzart",
            "Umsatzsteuertyp",
            "Umsatzsteuersatz",
            "Steuerbemessungsgrundlage",
            "Umsatzsteuerbetrag",
        ]
    )
    for b in report.get("buckets", []):
        writer.writerow(
            [
                "BOP_OSS_V1",
                b["mscon"],
                b["supply_type"],
                b["rate_type"],
                _de_decimal(b["vat_rate"]),
                _de_decimal(b["net_taxable_eur"]),
                _de_decimal(b["net_vat_eur"]),
            ]
        )
    return buf.getvalue().rstrip("\n")


def render_ros_xml(report: dict[str, Any], *, seller_vat_id: str = "DE123456789") -> str:
    """Render well-formed UTF-8 EU OSS XML return (Ireland ROS style)."""
    _require_pro_report(report)
    supplies_xml: list[str] = []
    for b in report.get("buckets", []):
        supplies_xml.append(
            "    <Supply>\n"
            f"      <MSCON>{xml_escape(str(b['mscon']))}</MSCON>\n"
            f"      <SupplyType>{xml_escape(str(b['supply_type']))}</SupplyType>\n"
            f"      <RateType>{xml_escape(str(b['rate_type']))}</RateType>\n"
            f"      <VATRate>{xml_escape(str(b['vat_rate']))}</VATRate>\n"
            f"      <TaxableAmountEUR>{xml_escape(str(b['net_taxable_eur']))}</TaxableAmountEUR>\n"
            f"      <VATAmountEUR>{xml_escape(str(b['net_vat_eur']))}</VATAmountEUR>\n"
            f"      <TransactionCount>{int(b['tx_count'])}</TransactionCount>\n"
            "    </Supply>"
        )
    summary = report.get("summary", {})
    xml_text = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<OSSReturn version="1.0">\n'
        f"  <Period>{xml_escape(str(report.get('quarter', '2026-Q4')))}</Period>\n"
        f"  <MemberStateOfIdentification>{xml_escape(str(report.get('home_country', 'DE')))}</MemberStateOfIdentification>\n"
        f"  <SellerVATID>{xml_escape(str(seller_vat_id))}</SellerVATID>\n"
        f"  <TotalTaxableEUR>{xml_escape(str(summary.get('total_taxable_eur', '0.00')))}</TotalTaxableEUR>\n"
        f"  <TotalVATDueEUR>{xml_escape(str(summary.get('total_vat_due_eur', '0.00')))}</TotalVATDueEUR>\n"
        "  <Supplies>\n"
        + ("\n".join(supplies_xml) + "\n" if supplies_xml else "")
        + "  </Supplies>\n"
        "</OSSReturn>"
    )
    ET.fromstring(xml_text)
    return xml_text


def render_eu27_audit_csv(report: dict[str, Any]) -> str:
    """Render standard EU27 accountant audit reconciliation CSV."""
    _require_pro_report(report)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=",", lineterminator="\n")
    writer.writerow(
        [
            "Member State",
            "Supply Type",
            "Rate Type",
            "VAT Rate %",
            "Tx Count",
            "Net Taxable EUR",
            "Net VAT EUR",
        ]
    )
    for b in report.get("buckets", []):
        writer.writerow(
            [
                b["mscon"],
                b["supply_type"],
                b["rate_type"],
                b["vat_rate"],
                b["tx_count"],
                b["net_taxable_eur"],
                b["net_vat_eur"],
            ]
        )
    return buf.getvalue().rstrip("\n")
