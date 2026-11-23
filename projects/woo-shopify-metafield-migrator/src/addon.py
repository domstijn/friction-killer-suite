"""ShopMetaShift core compiler: 100% stdlib WooCommerce-to-Shopify CSV, metafield & 301 engine."""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

try:
    from .license_client import require_pro_feature, verify_license
except ImportError:
    from license_client import require_pro_feature, verify_license

APP_SLUG = "woo-shopify-metafield-migrator"
PROVIDER = "stripe"
DEFAULT_PRODUCT_ID = "prod_VgOLfg5TiKHhLU,prod_VeW6IYwGyYJkPv"
FREE_PRODUCT_LIMIT = 15

INTERNAL_WP_META_KEYS = frozenset(
    {
        "_edit_lock",
        "_edit_last",
        "_wp_old_slug",
        "_thumbnail_id",
        "_product_attributes",
        "_default_attributes",
        "_stock_status",
        "_wc_average_rating",
        "_wc_review_count",
        "_downloadable_files",
        "total_sales",
        "_wp_page_template",
        "_wp_attachment_metadata",
    }
)

SEO_TITLE_KEYS = frozenset({"_yoast_wpseo_title", "rank_math_title", "_aioseo_title"})
SEO_DESC_KEYS = frozenset({"_yoast_wpseo_metadesc", "rank_math_description", "_aioseo_description"})
COST_META_KEYS = frozenset({"_wc_cog_cost", "_cost", "_alg_wc_cog_cost"})
GTIN_META_KEYS = frozenset({"_gtin", "_ean", "_upc", "hwp_var_gtin", "gtin", "ean", "upc"})

ATTR_NAME_RE = re.compile(r"^attribute\s+(\d+)\s+name$", re.IGNORECASE)
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)
INT_RE = re.compile(r"^-?\d+$")
DECIMAL_RE = re.compile(r"^-?\d+\.\d+$")

SAMPLE_WOO_CSV = """ID,Type,SKU,Name,Slug,Published,Description,Categories,Tags,Brands,Images,Weight (kg),Regular price,Sale price,In stock?,Stock,Parent,Attribute 1 name,Attribute 1 value(s),Attribute 2 name,Attribute 2 value(s),Attribute 3 name,Attribute 3 value(s),Attribute 4 name,Attribute 4 value(s),Meta: _yoast_wpseo_title,Meta: _yoast_wpseo_metadesc,Meta: _wc_cog_cost,Meta: _gtin,Meta: care_instructions,Meta: release_date,Meta: spec_sheet_url,Meta: is_limited_edition,Meta: warranty_years,Meta: fill_weight_g,Meta: specs_json,Meta: fabric_oz_yd,Meta: _edit_lock
101,variable,JKT-ALP,Alpine Shell Jacket,alpine-shell-jacket,1,"<p>3-layer storm shell built for alpine traverses.</p>","Apparel > Outerwear, Winter Gear","jacket, waterproof",NordPeak,"https://cdn.example.com/woo/alpine-main.jpg, https://cdn.example.com/woo/alpine-back.jpg",,,,1,,,Color,"Navy, Black, Olive",Size,"M, L, XL",Material,"Gore-Tex, Recycled Nylon",Waterproof Rating,"20000mm, 15000mm",Alpine Shell Jacket | NordPeak,Technical 3-layer waterproof mountain shell with taped seams.,,,"Machine wash 30C.\nHang dry only.",2026-10-01,https://cdn.example.com/specs/alpine-shell.pdf,true,3,,,5.25,1700000001:1
102,variation,JKT-ALP-NVY-M,Alpine Shell Jacket - Navy M,,1,,,,NordPeak,https://cdn.example.com/woo/alpine-navy.jpg,0.85,199.00,"149,50",1,14,id:101,Color,Navy,Size,M,Material,Gore-Tex,Waterproof Rating,20000mm,,,42.50,4006381333931,,,,,,180,"{""breathability"":""15000g"",""seams"":""taped""}",,
103,variation,JKT-ALP-BLK-L,Alpine Shell Jacket - Black L,,1,,,,NordPeak,https://cdn.example.com/woo/alpine-black.jpg,0.92,199.00,,1,9,JKT-ALP,Color,Black,Size,L,Material,Gore-Tex,Waterproof Rating,20000mm,,,42.50,4006381333932,,,,,,195,"{""breathability"":""15000g"",""seams"":""taped""}",,
104,variation,JKT-ALP-OLV-XL,Alpine Shell Jacket - Olive XL,,1,,,,NordPeak,https://cdn.example.com/woo/alpine-olive.jpg,0.98,209.00,179.00,1,6,id:101,Color,Olive,Size,XL,Material,Recycled Nylon,Waterproof Rating,15000mm,,,44.00,4006381333933,,,,,,210,"{""breathability"":""12000g"",""seams"":""taped""}",,
201,simple,BAG-24L,Daypack 24L,daypack-24l,1,"<p>Weather-sealed commuter backpack.</p>",Accessories > Bags,"pack, travel",NordPeak,"https://cdn.example.com/woo/daypack-front.jpg, https://cdn.example.com/woo/daypack-inside.jpg",0.65,89.00,,1,25,,,,,,,,,,,,21.00,4006381333999,"Spot clean cold.\nDo not tumble dry.",2026-09-15,https://cdn.example.com/specs/daypack-24l.pdf,false,5,,,4.10,1700000002:1
"""

SHOPIFY_BASE_HEADERS = [
    "Handle",
    "Title",
    "Body (HTML)",
    "Vendor",
    "Product Category",
    "Type",
    "Tags",
    "Published",
    "Option1 Name",
    "Option1 Value",
    "Option2 Name",
    "Option2 Value",
    "Option3 Name",
    "Option3 Value",
    "Variant SKU",
    "Variant Grams",
    "Variant Inventory Tracker",
    "Variant Inventory Qty",
    "Variant Inventory Policy",
    "Variant Fulfillment Service",
    "Variant Price",
    "Variant Compare At Price",
    "Variant Requires Shipping",
    "Variant Taxable",
    "Variant Barcode",
    "Image Src",
    "Image Position",
    "Image Alt Text",
    "Variant Image",
    "Variant Weight Unit",
    "Cost per item",
    "Status",
    "SEO Title",
    "SEO Description",
]

MATRIXIFY_BASE_HEADERS = [
    "Handle",
    "Command",
    "Title",
    "Body HTML",
    "Vendor",
    "Type",
    "Tags",
    "Published",
    "Status",
    "Option1 Name",
    "Option1 Value",
    "Option2 Name",
    "Option2 Value",
    "Option3 Name",
    "Option3 Value",
    "Variant Command",
    "Variant SKU",
    "Variant Price",
    "Variant Compare At Price",
    "Variant Cost",
    "Variant Barcode",
    "Variant Weight",
    "Variant Weight Unit",
    "Variant Grams",
    "Variant Inventory Tracker",
    "Variant Inventory Qty",
    "Image Src",
    "Image Position",
    "Image Command",
    "Variant Image",
    "Metafield: seo.title_tag [single_line_text_field]",
    "Metafield: seo.description_tag [single_line_text_field]",
]


def slugify_handle(text: str) -> str:
    """Fold Unicode to ASCII and convert text into a clean Shopify URL handle."""
    normalized = unicodedata.normalize("NFKD", str(text or ""))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug or "product"


def _snake_key(raw: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(raw or ""))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    key = re.sub(r"[^a-z0-9]+", "_", ascii_only).strip("_")
    return key or "custom_field"


def _normalize_decimal_token(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    s = re.sub(r"[€$£\s\u00a0]", "", s)
    if not s:
        return ""
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return s


def parse_decimal_str(raw: str) -> str:
    """Normalize EU/US currency strings (e.g. '149,50', '€1.299,00') to dot-decimal '0.00'."""
    token = _normalize_decimal_token(raw)
    if not token:
        return ""
    try:
        val = Decimal(token)
        return str(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except InvalidOperation:
        return ""


def weight_to_grams(raw: str, unit: str = "kg") -> int:
    """Convert product weight string in kg/g/lb/oz into rounded integer grams."""
    token = _normalize_decimal_token(raw)
    if not token:
        return 0
    try:
        val = Decimal(token)
    except InvalidOperation:
        return 0
    multipliers = {
        "kg": Decimal("1000"),
        "g": Decimal("1"),
        "lb": Decimal("453.59237"),
        "lbs": Decimal("453.59237"),
        "oz": Decimal("28.349523125"),
    }
    factor = multipliers.get(unit.strip().lower(), Decimal("1000"))
    return max(0, int((val * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))


def infer_metafield_type(values: list[str]) -> str:
    """Infer Shopify metafield definition type from observed non-empty values."""
    clean = [str(v).strip() for v in values if str(v or "").strip()]
    if not clean:
        return "single_line_text_field"
    if all(INT_RE.match(v) for v in clean):
        return "number_integer"
    if all(INT_RE.match(v) or DECIMAL_RE.match(v) for v in clean) and any(DECIMAL_RE.match(v) for v in clean):
        return "number_decimal"
    if all(v.lower() in {"true", "false", "yes", "no"} for v in clean):
        return "boolean"
    if all(ISO_DATE_RE.match(v) for v in clean):
        return "date"
    if all(URL_RE.match(v) for v in clean):
        return "url"
    if all((v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")) for v in clean):
        try:
            for v in clean:
                json.loads(v)
            return "json"
        except json.JSONDecodeError:
            pass
    if any("\n" in v or "\r" in v or len(v) > 160 for v in clean):
        return "multi_line_text_field"
    return "single_line_text_field"


def _detect_delimiter(sample: str) -> str:
    header_line = sample.splitlines()[0] if sample.splitlines() else ""
    if header_line.count(";") > header_line.count(","):
        return ";"
    return ","


def _is_truthy(val: str, default: bool = False) -> bool:
    s = str(val or "").strip().lower()
    if not s:
        return default
    return s in {"1", "true", "yes", "visible", "publish", "published"}


def _split_images(raw: str) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in str(raw).split(",") if part.strip()]


def _extract_attributes(row: dict[str, str], col_lookup: dict[str, str]) -> list[tuple[str, str]]:
    indices: set[int] = set()
    for col in row.keys():
        if not col:
            continue
        m = ATTR_NAME_RE.match(col.strip())
        if m:
            indices.add(int(m.group(1)))
    attrs: list[tuple[str, str]] = []
    for idx in sorted(indices):
        name_col = col_lookup.get(f"attribute {idx} name")
        val_col = col_lookup.get(f"attribute {idx} value(s)") or col_lookup.get(f"attribute {idx} value")
        name = (row.get(name_col or "", "") or "").strip()
        val = (row.get(val_col or "", "") or "").strip()
        if name or val:
            attrs.append((name or f"Attribute {idx}", val))
    return attrs


def _detect_weight_unit(headers: list[str], default_unit: str) -> str:
    for h in headers:
        hl = h.strip().lower()
        if hl.startswith("weight (") and hl.endswith(")"):
            inner = hl[len("weight (") : -1].strip()
            if inner in {"kg", "g", "lb", "lbs", "oz"}:
                return inner
    return default_unit


def _first_non_empty(row: dict[str, str], col_lookup: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        col = col_lookup.get(alias.lower())
        if col and (row.get(col) or "").strip():
            return row[col].strip()
    return ""


def _resolve_sale_and_compare_prices(regular_raw: str, sale_raw: str) -> tuple[str, str]:
    reg = parse_decimal_str(regular_raw)
    sale = parse_decimal_str(sale_raw)
    if sale:
        if reg:
            try:
                if Decimal(reg) > Decimal(sale):
                    return sale, reg
            except InvalidOperation:
                pass
        return sale, ""
    return reg, ""


def _normalize_meta_value(raw: str, mf_type: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    if mf_type == "boolean":
        return "true" if s.lower() in {"true", "yes", "1"} else "false"
    return s


def compile_woo_to_shopify(
    csv_text: str,
    *,
    weight_unit: str = "kg",
    overflow_mode: str = "metafield",
    include_category_redirects: bool = True,
    skip_internal_meta: bool = True,
    pro_unlocked: bool = False,
) -> dict[str, Any]:
    """Parse WooCommerce product CSV and compile Shopify Admin, Matrixify, and 301 Redirect outputs."""
    clean_csv = (csv_text or "").lstrip("\ufeff").strip()
    if not clean_csv:
        return {"ok": False, "errors": ["Empty CSV input."], "warnings": []}

    delim = _detect_delimiter(clean_csv)
    reader = csv.DictReader(io.StringIO(clean_csv), delimiter=delim)
    raw_headers = [h for h in (reader.fieldnames or []) if h is not None]
    if not raw_headers:
        return {"ok": False, "errors": ["CSV header row missing."], "warnings": []}

    col_lookup = {h.strip().lower(): h for h in raw_headers}
    eff_weight_unit = weight_unit or _detect_weight_unit(raw_headers, "kg")
    eff_overflow = overflow_mode if overflow_mode in {"metafield", "compound"} else "metafield"

    rows = [r for r in reader if any((v or "").strip() for v in r.values())]
    if not rows:
        return {"ok": False, "errors": ["CSV contains headers only and no product rows."], "warnings": []}

    warnings: list[str] = []
    errors: list[str] = []

    top_products: list[dict[str, Any]] = []
    index_by_id: dict[str, dict[str, Any]] = {}
    index_by_sku: dict[str, dict[str, Any]] = {}
    variation_rows: list[dict[str, str]] = []

    for row in rows:
        rtype = _first_non_empty(row, col_lookup, "type").lower() or "simple"
        if rtype == "variation":
            variation_rows.append(row)
            continue
        rid = _first_non_empty(row, col_lookup, "id")
        rsku = _first_non_empty(row, col_lookup, "sku")
        entry = {"parent": row, "variations": [], "id": rid, "sku": rsku}
        top_products.append(entry)
        if rid:
            index_by_id[f"id:{rid.lower()}"] = entry
            index_by_id[rid.lower()] = entry
        if rsku:
            index_by_sku[rsku.lower()] = entry

    for vrow in variation_rows:
        parent_ref = _first_non_empty(vrow, col_lookup, "parent")
        target = None
        if parent_ref:
            key = parent_ref.lower()
            target = index_by_id.get(key) or index_by_sku.get(key)
        if target is not None:
            target["variations"].append(vrow)
        else:
            vsku = _first_non_empty(vrow, col_lookup, "sku", "name") or "unknown-variation"
            warnings.append(
                f"Orphan variation '{vsku}' (Parent='{parent_ref}') could not match a parent product; emitted as standalone fallback."
            )
            top_products.append({"parent": vrow, "variations": [], "id": "", "sku": vsku, "orphan": True})

    total_products_found = len(top_products)
    truncated_by_free_tier = (not pro_unlocked) and total_products_found > FREE_PRODUCT_LIMIT
    active_products = top_products if pro_unlocked else top_products[:FREE_PRODUCT_LIMIT]
    if truncated_by_free_tier:
        warnings.append(
            f"Free tier preview capped output at {FREE_PRODUCT_LIMIT} of {total_products_found} products. Activate Pro for unlimited SKUs."
        )

    # Identify all custom Meta: columns & overflow attributes across active products
    raw_meta_cols: list[tuple[str, str, str]] = []
    for h in raw_headers:
        stripped = h.strip()
        if stripped.lower().startswith("meta:"):
            raw_key = stripped[5:].strip()
            low_key = raw_key.lower()
            if low_key in SEO_TITLE_KEYS | SEO_DESC_KEYS | COST_META_KEYS | GTIN_META_KEYS:
                continue
            if skip_internal_meta and low_key in INTERNAL_WP_META_KEYS:
                continue
            raw_meta_cols.append((h, raw_key, _snake_key(raw_key)))

    meta_parent_vals: dict[str, list[str]] = {orig: [] for orig, _, _ in raw_meta_cols}
    meta_variant_vals: dict[str, list[str]] = {orig: [] for orig, _, _ in raw_meta_cols}
    overflow_attr_specs: dict[str, dict[str, Any]] = {}

    for grp in active_products:
        parent = grp["parent"]
        variations = grp["variations"]
        for orig, _, _ in raw_meta_cols:
            pv = (parent.get(orig) or "").strip()
            if pv:
                meta_parent_vals[orig].append(pv)
            for v in variations:
                vv = (v.get(orig) or "").strip()
                if vv:
                    meta_variant_vals[orig].append(vv)

        all_attr_sources = variations if variations else [parent]
        for src_row in all_attr_sources:
            attrs = _extract_attributes(src_row, col_lookup)
            if eff_overflow == "metafield" and len(attrs) > 3:
                for aname, aval in attrs[3:]:
                    skey = _snake_key(aname)
                    spec = overflow_attr_specs.setdefault(
                        skey,
                        {"name": aname, "key": skey, "values": [], "has_variants": False},
                    )
                    if aval:
                        spec["values"].append(aval)
                    if variations:
                        spec["has_variants"] = True

    product_meta_defs: list[dict[str, str]] = []
    variant_meta_defs: list[dict[str, str]] = []
    metafield_schema: list[dict[str, Any]] = []

    for orig, raw_key, skey in raw_meta_cols:
        pvals = meta_parent_vals[orig]
        vvals = meta_variant_vals[orig]
        if vvals:
            mtype = infer_metafield_type(vvals + pvals)
            header = f"Variant Metafield: custom.{skey} [{mtype}]"
            variant_meta_defs.append({"col": orig, "raw_key": raw_key, "key": skey, "type": mtype, "header": header, "source": "meta"})
            metafield_schema.append({"scope": "variant", "key": f"custom.{skey}", "type": mtype, "header": header, "samples": len(vvals)})
        elif pvals:
            mtype = infer_metafield_type(pvals)
            header = f"Metafield: custom.{skey} [{mtype}]"
            product_meta_defs.append({"col": orig, "raw_key": raw_key, "key": skey, "type": mtype, "header": header, "source": "meta"})
            metafield_schema.append({"scope": "product", "key": f"custom.{skey}", "type": mtype, "header": header, "samples": len(pvals)})

    for skey, spec in overflow_attr_specs.items():
        mtype = infer_metafield_type(spec["values"])
        scope_prefix = "Variant Metafield" if spec["has_variants"] else "Metafield"
        header = f"{scope_prefix}: custom.{skey} [{mtype}]"
        entry = {"col": "", "raw_key": spec["name"], "key": skey, "type": mtype, "header": header, "source": "overflow_attr"}
        if spec["has_variants"]:
            variant_meta_defs.append(entry)
            metafield_schema.append({"scope": "variant", "key": f"custom.{skey}", "type": mtype, "header": header, "samples": len(spec["values"])})
        else:
            product_meta_defs.append(entry)
            metafield_schema.append({"scope": "product", "key": f"custom.{skey}", "type": mtype, "header": header, "samples": len(spec["values"])})

    dynamic_product_headers = [d["header"] for d in product_meta_defs]
    dynamic_variant_headers = [d["header"] for d in variant_meta_defs]
    shopify_headers = SHOPIFY_BASE_HEADERS + dynamic_product_headers + dynamic_variant_headers
    matrixify_headers = MATRIXIFY_BASE_HEADERS + dynamic_product_headers + dynamic_variant_headers

    shopify_rows: list[dict[str, str]] = []
    matrixify_rows: list[dict[str, str]] = []
    redirects: list[dict[str, str]] = []
    seen_redirects: set[str] = set()
    seen_skus: set[str] = set()
    used_handles: dict[str, int] = {}

    total_variants = 0
    total_overflow_promoted = 0

    def _add_redirect(src_path: str, dst_path: str, kind: str) -> None:
        key = src_path.lower()
        if key in seen_redirects:
            return
        seen_redirects.add(key)
        redirects.append({"Redirect from": src_path, "Redirect to": dst_path, "Source Type": kind})

    def _find_meta_special(row_a: dict[str, str], row_b: dict[str, str], keys: frozenset[str], extra_cols: tuple[str, ...] = ()) -> str:
        for col in raw_headers:
            cl = col.strip().lower()
            meta_name = cl[5:].strip() if cl.startswith("meta:") else ""
            if meta_name in keys or cl in {e.lower() for e in extra_cols}:
                val = (row_a.get(col) or "").strip() or (row_b.get(col) or "").strip()
                if val:
                    return val
        return ""

    for grp in active_products:
        parent = grp["parent"]
        variations = grp["variations"]
        parent_name = _first_non_empty(parent, col_lookup, "name") or "Untitled Product"
        raw_slug = _first_non_empty(parent, col_lookup, "slug")
        base_handle = slugify_handle(raw_slug or parent_name)
        if base_handle in used_handles:
            used_handles[base_handle] += 1
            handle = f"{base_handle}-{used_handles[base_handle]}"
        else:
            used_handles[base_handle] = 1
            handle = base_handle

        woo_slug = raw_slug or slugify_handle(parent_name)
        _add_redirect(f"/product/{woo_slug}/", f"/products/{handle}", "product")
        _add_redirect(f"/product/{woo_slug}", f"/products/{handle}", "product")

        cats_raw = _first_non_empty(parent, col_lookup, "categories")
        cat_list = [c.strip() for c in cats_raw.split(",") if c.strip()]
        primary_type = cat_list[0].split(">")[-1].strip() if cat_list else ""
        primary_cat = cat_list[0] if cat_list else ""
        if include_category_redirects:
            for cat in cat_list:
                parts = [slugify_handle(seg) for seg in cat.split(">") if seg.strip()]
                if parts:
                    cat_path = "/".join(parts)
                    leaf = parts[-1]
                    _add_redirect(f"/product-category/{cat_path}/", f"/collections/{leaf}", "category")
                    _add_redirect(f"/product-category/{cat_path}", f"/collections/{leaf}", "category")

        published_flag = _is_truthy(_first_non_empty(parent, col_lookup, "published"), default=True)
        published_str = "TRUE" if published_flag else "FALSE"
        status_str = "active" if published_flag else "draft"
        body_html = _first_non_empty(parent, col_lookup, "description", "short description")
        vendor = _first_non_empty(parent, col_lookup, "brands", "brand", "vendor") or "Store"
        tags = _first_non_empty(parent, col_lookup, "tags")
        seo_title = _find_meta_special(parent, parent, SEO_TITLE_KEYS)
        seo_desc = _find_meta_special(parent, parent, SEO_DESC_KEYS)

        parent_images = _split_images(_first_non_empty(parent, col_lookup, "images"))
        parent_attrs = _extract_attributes(parent, col_lookup)

        variant_list = variations if variations else [parent]
        if not variations and _first_non_empty(parent, col_lookup, "type").lower() == "variable":
            warnings.append(f"Variable product '{parent_name}' has no child variation rows.")
        if len(variant_list) > 100:
            warnings.append(
                f"Product '{parent_name}' ({handle}) has {len(variant_list)} variants (exceeds Shopify 100-variant CSV limit)."
            )

        product_meta_row_vals: dict[str, str] = {}
        for mdef in product_meta_defs:
            if mdef["source"] == "meta":
                raw_val = (parent.get(mdef["col"]) or "").strip()
                product_meta_row_vals[mdef["header"]] = _normalize_meta_value(raw_val, mdef["type"])
            else:
                # Overflow attr on simple product
                ov_match = next((av for an, av in parent_attrs[3:] if _snake_key(an) == mdef["key"]), "")
                product_meta_row_vals[mdef["header"]] = _normalize_meta_value(ov_match, mdef["type"])
                if ov_match:
                    total_overflow_promoted += 1

        total_rows_needed = max(len(variant_list), len(parent_images), 1)
        for row_idx in range(total_rows_needed):
            is_first = row_idx == 0
            has_variant = row_idx < len(variant_list)
            img_src = parent_images[row_idx] if row_idx < len(parent_images) else ""
            img_pos = str(row_idx + 1) if img_src else ""

            s_row = {h: "" for h in shopify_headers}
            m_row = {h: "" for h in matrixify_headers}
            s_row["Handle"] = handle
            m_row["Handle"] = handle
            m_row["Command"] = "MERGE"

            if is_first:
                s_row["Title"] = parent_name
                s_row["Body (HTML)"] = body_html
                s_row["Vendor"] = vendor
                s_row["Product Category"] = primary_cat
                s_row["Type"] = primary_type
                s_row["Tags"] = tags
                s_row["Published"] = published_str
                s_row["Status"] = status_str
                s_row["SEO Title"] = seo_title
                s_row["SEO Description"] = seo_desc

                m_row["Title"] = parent_name
                m_row["Body HTML"] = body_html
                m_row["Vendor"] = vendor
                m_row["Type"] = primary_type
                m_row["Tags"] = tags
                m_row["Published"] = published_str
                m_row["Status"] = status_str
                m_row["Metafield: seo.title_tag [single_line_text_field]"] = seo_title
                m_row["Metafield: seo.description_tag [single_line_text_field]"] = seo_desc

                for hdr, val in product_meta_row_vals.items():
                    s_row[hdr] = val
                    m_row[hdr] = val

            if img_src:
                s_row["Image Src"] = img_src
                s_row["Image Position"] = img_pos
                s_row["Image Alt Text"] = parent_name
                m_row["Image Src"] = img_src
                m_row["Image Position"] = img_pos
                m_row["Image Command"] = "MERGE"

            if has_variant:
                total_variants += 1
                vrow = variant_list[row_idx]
                vsku = _first_non_empty(vrow, col_lookup, "sku") or (
                    f"{handle.upper()}-{row_idx + 1}" if variations else _first_non_empty(parent, col_lookup, "sku")
                )
                if vsku:
                    low_sku = vsku.lower()
                    if low_sku in seen_skus:
                        warnings.append(f"Duplicate SKU detected: '{vsku}'.")
                    seen_skus.add(low_sku)

                v_attrs = _extract_attributes(vrow, col_lookup)
                opt_source = v_attrs if v_attrs else parent_attrs

                opt_names = ["", "", ""]
                opt_vals = ["", "", ""]
                if not opt_source and len(variant_list) == 1:
                    opt_names[0] = "Title"
                    opt_vals[0] = "Default Title"
                else:
                    for oi in range(min(3, len(opt_source))):
                        opt_names[oi] = opt_source[oi][0]
                        opt_vals[oi] = opt_source[oi][1].split(",")[0].strip() if "," in opt_source[oi][1] and not variations else opt_source[oi][1]
                    if eff_overflow == "compound" and len(opt_source) > 3:
                        extra_parts = [f"{k}: {v}" for k, v in opt_source[3:] if v]
                        if extra_parts:
                            opt_vals[2] = " / ".join([opt_vals[2], *extra_parts]).strip(" /")
                            total_overflow_promoted += len(extra_parts)

                for oi in range(3):
                    if is_first and opt_names[oi]:
                        s_row[f"Option{oi + 1} Name"] = opt_names[oi]
                        m_row[f"Option{oi + 1} Name"] = opt_names[oi]
                    if opt_vals[oi]:
                        s_row[f"Option{oi + 1} Value"] = opt_vals[oi]
                        m_row[f"Option{oi + 1} Value"] = opt_vals[oi]

                reg_raw = _first_non_empty(vrow, col_lookup, "regular price") or _first_non_empty(parent, col_lookup, "regular price")
                sale_raw = _first_non_empty(vrow, col_lookup, "sale price") or _first_non_empty(parent, col_lookup, "sale price")
                v_price, v_compare = _resolve_sale_and_compare_prices(reg_raw, sale_raw)

                w_col = next(
                    (col_lookup[k] for k in col_lookup if k == "weight" or k.startswith("weight (")),
                    "",
                )
                w_raw = (vrow.get(w_col) or "").strip() if w_col else ""
                if not w_raw and w_col:
                    w_raw = (parent.get(w_col) or "").strip()
                grams = weight_to_grams(w_raw, eff_weight_unit)

                stock_raw = _first_non_empty(vrow, col_lookup, "stock") or _first_non_empty(parent, col_lookup, "stock")
                in_stock_raw = _first_non_empty(vrow, col_lookup, "in stock?") or _first_non_empty(parent, col_lookup, "in stock?")
                if stock_raw and INT_RE.match(stock_raw.strip()):
                    inv_tracker = "shopify"
                    inv_qty = stock_raw.strip()
                elif in_stock_raw and not _is_truthy(in_stock_raw, True):
                    inv_tracker = "shopify"
                    inv_qty = "0"
                else:
                    inv_tracker = ""
                    inv_qty = ""

                cost_val = parse_decimal_str(_find_meta_special(vrow, parent, COST_META_KEYS))
                barcode_val = _find_meta_special(
                    vrow, parent, GTIN_META_KEYS, extra_cols=("GTIN, UPC, EAN, or ISBN",)
                )
                v_images = _split_images(_first_non_empty(vrow, col_lookup, "images"))
                v_image = v_images[0] if v_images else ""

                s_row["Variant SKU"] = vsku
                s_row["Variant Grams"] = str(grams)
                s_row["Variant Inventory Tracker"] = inv_tracker
                s_row["Variant Inventory Qty"] = inv_qty
                s_row["Variant Inventory Policy"] = "deny"
                s_row["Variant Fulfillment Service"] = "manual"
                s_row["Variant Price"] = v_price
                s_row["Variant Compare At Price"] = v_compare
                s_row["Variant Requires Shipping"] = "TRUE"
                s_row["Variant Taxable"] = "TRUE"
                s_row["Variant Barcode"] = barcode_val
                s_row["Variant Image"] = v_image
                s_row["Variant Weight Unit"] = "g" if grams else eff_weight_unit
                s_row["Cost per item"] = cost_val

                m_row["Variant Command"] = "MERGE"
                m_row["Variant SKU"] = vsku
                m_row["Variant Price"] = v_price
                m_row["Variant Compare At Price"] = v_compare
                m_row["Variant Cost"] = cost_val
                m_row["Variant Barcode"] = barcode_val
                m_row["Variant Weight"] = _normalize_decimal_token(w_raw) or "0"
                m_row["Variant Weight Unit"] = eff_weight_unit
                m_row["Variant Grams"] = str(grams)
                m_row["Variant Inventory Tracker"] = inv_tracker
                m_row["Variant Inventory Qty"] = inv_qty
                m_row["Variant Image"] = v_image

                # Populate Variant Metafield: columns
                for vdef in variant_meta_defs:
                    if vdef["source"] == "meta":
                        raw_mv = (vrow.get(vdef["col"]) or "").strip() or (parent.get(vdef["col"]) or "").strip()
                        val = _normalize_meta_value(raw_mv, vdef["type"])
                    else:
                        raw_mv = next((av for an, av in opt_source[3:] if _snake_key(an) == vdef["key"]), "")
                        val = _normalize_meta_value(raw_mv, vdef["type"])
                        if val:
                            total_overflow_promoted += 1
                    s_row[vdef["header"]] = val
                    m_row[vdef["header"]] = val

            shopify_rows.append(s_row)
            matrixify_rows.append(m_row)

    summary = {
        "total_products_in_csv": total_products_found,
        "processed_products": len(active_products),
        "processed_variants": total_variants,
        "shopify_csv_rows": len(shopify_rows),
        "overflow_attributes_promoted": total_overflow_promoted,
        "custom_metafield_columns": len(metafield_schema),
        "redirects_count": len(redirects),
        "warnings_count": len(warnings),
        "overflow_mode": eff_overflow,
        "weight_unit": eff_weight_unit,
    }

    return {
        "ok": True,
        "truncated_by_free_tier": truncated_by_free_tier,
        "free_product_limit": FREE_PRODUCT_LIMIT,
        "summary": summary,
        "metafield_schema": metafield_schema,
        "shopify_headers": shopify_headers,
        "shopify_rows": shopify_rows,
        "matrixify_headers": matrixify_headers,
        "matrixify_rows": matrixify_rows,
        "redirects": redirects,
        "warnings": warnings,
        "errors": errors,
    }


def _dict_rows_to_csv(headers: list[str], rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().rstrip("\n")


def render_shopify_admin_csv(result: dict[str, Any]) -> str:
    """Render standard Shopify Admin multi-row Product CSV."""
    return _dict_rows_to_csv(result["shopify_headers"], result["shopify_rows"])


def render_matrixify_csv(result: dict[str, Any], *, pro_unlocked: bool = False) -> str:
    """Render Pro-gated Matrixify MERGE CSV with typed metafield & variant cost headers."""
    if not pro_unlocked:
        raise PermissionError("Pro license required for Matrixify CSV export.")
    return _dict_rows_to_csv(result["matrixify_headers"], result["matrixify_rows"])


def render_redirects_csv(result: dict[str, Any], *, pro_unlocked: bool = False) -> str:
    """Render Pro-gated Shopify 301 Redirects CSV ('Redirect from,Redirect to')."""
    if not pro_unlocked:
        raise PermissionError("Pro license required for 301 Redirects CSV export.")
    rows = [{"Redirect from": r["Redirect from"], "Redirect to": r["Redirect to"]} for r in result["redirects"]]
    return _dict_rows_to_csv(["Redirect from", "Redirect to"], rows)


def unlock_pro(license_key: str, *, cache_dir: str | None = None) -> dict[str, Any]:
    """Validate and cache a Stripe Managed Payments / Bundle Pro license key."""
    return verify_license(
        license_key,
        provider=PROVIDER,
        product_id=DEFAULT_PRODUCT_ID,
        app_slug=APP_SLUG,
        cache_dir=cache_dir,
    )


def check_pro_gate(*, cache_dir: str | None = None) -> dict[str, Any]:
    """Check cached Pro license state."""
    return require_pro_feature("shopmetashift_pro_exports", app_slug=APP_SLUG, cache_dir=cache_dir)
