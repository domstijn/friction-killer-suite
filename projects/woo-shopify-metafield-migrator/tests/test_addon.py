"""Deterministic unit & CLI tests for ShopMetaShift (woo-shopify-metafield-migrator)."""

from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from addon import (  # noqa: E402
    APP_SLUG,
    FREE_PRODUCT_LIMIT,
    SAMPLE_WOO_CSV,
    compile_woo_to_shopify,
    infer_metafield_type,
    parse_decimal_str,
    render_matrixify_csv,
    render_redirects_csv,
    render_shopify_admin_csv,
    slugify_handle,
    unlock_pro,
    weight_to_grams,
)
from cli import main as cli_main  # noqa: E402


class TestShopMetaShift(unittest.TestCase):
    def test_variable_variation_joining_prices_weights_and_gallery_rows(self) -> None:
        res = compile_woo_to_shopify(SAMPLE_WOO_CSV, pro_unlocked=False)
        self.assertTrue(res["ok"])
        self.assertEqual(res["summary"]["processed_products"], 2)
        self.assertEqual(res["summary"]["processed_variants"], 4)

        rows = res["shopify_rows"]
        # Alpine Shell Jacket has 3 variants (2 parent images <= 3 variants) -> 3 rows
        # Daypack 24L has 1 variant & 2 gallery images -> 1 variant row + 1 extra image-only row = 2 rows
        self.assertEqual(len(rows), 5)

        r1, r2, r3, r4, r5 = rows
        self.assertEqual(r1["Handle"], "alpine-shell-jacket")
        self.assertEqual(r1["Title"], "Alpine Shell Jacket")
        self.assertEqual(r1["Variant SKU"], "JKT-ALP-NVY-M")
        self.assertEqual(r1["Variant Price"], "149.50")
        self.assertEqual(r1["Variant Compare At Price"], "199.00")
        self.assertEqual(r1["Variant Grams"], "850")
        self.assertEqual(r1["Image Src"], "https://cdn.example.com/woo/alpine-main.jpg")
        self.assertEqual(r1["Image Position"], "1")
        self.assertEqual(r1["Variant Image"], "https://cdn.example.com/woo/alpine-navy.jpg")

        # Variations 2 & 3 joined by both parent SKU and id:101, keeping product-level fields blank
        self.assertEqual(r2["Handle"], "alpine-shell-jacket")
        self.assertEqual(r2["Title"], "")
        self.assertEqual(r2["Variant SKU"], "JKT-ALP-BLK-L")
        self.assertEqual(r2["Variant Price"], "199.00")
        self.assertEqual(r2["Variant Compare At Price"], "")
        self.assertEqual(r2["Image Position"], "2")

        self.assertEqual(r3["Handle"], "alpine-shell-jacket")
        self.assertEqual(r3["Title"], "")
        self.assertEqual(r3["Variant SKU"], "JKT-ALP-OLV-XL")
        self.assertEqual(r3["Variant Price"], "179.00")
        self.assertEqual(r3["Variant Compare At Price"], "209.00")

        # Daypack extra gallery image-only row
        self.assertEqual(r4["Handle"], "daypack-24l")
        self.assertEqual(r4["Variant SKU"], "BAG-24L")
        self.assertEqual(r5["Handle"], "daypack-24l")
        self.assertEqual(r5["Title"], "")
        self.assertEqual(r5["Variant SKU"], "")
        self.assertEqual(r5["Image Src"], "https://cdn.example.com/woo/daypack-inside.jpg")
        self.assertEqual(r5["Image Position"], "2")

        # Helpers check
        self.assertEqual(parse_decimal_str("€1.299,00"), "1299.00")
        self.assertEqual(weight_to_grams("2", "lb"), 907)
        self.assertEqual(slugify_handle("Café Brûlée Coat!"), "cafe-brulee-coat")

    def test_overflow_attributes_metafield_and_compound_modes(self) -> None:
        res_meta = compile_woo_to_shopify(SAMPLE_WOO_CSV, overflow_mode="metafield", pro_unlocked=False)
        overflow_hdr = "Variant Metafield: custom.waterproof_rating [single_line_text_field]"
        self.assertIn(overflow_hdr, res_meta["shopify_headers"])
        self.assertEqual(res_meta["shopify_rows"][0][overflow_hdr], "20000mm")
        self.assertEqual(res_meta["shopify_rows"][2][overflow_hdr], "15000mm")
        self.assertGreaterEqual(res_meta["summary"]["overflow_attributes_promoted"], 3)

        res_comp = compile_woo_to_shopify(SAMPLE_WOO_CSV, overflow_mode="compound", pro_unlocked=False)
        self.assertNotIn(overflow_hdr, res_comp["shopify_headers"])
        self.assertEqual(res_comp["shopify_rows"][0]["Option3 Name"], "Material")
        self.assertEqual(res_comp["shopify_rows"][0]["Option3 Value"], "Gore-Tex / Waterproof Rating: 20000mm")

    def test_metafield_autotyping_special_fields_redirects_and_warnings(self) -> None:
        res = compile_woo_to_shopify(SAMPLE_WOO_CSV, include_category_redirects=True, pro_unlocked=False)
        headers = res["shopify_headers"]

        self.assertIn("Metafield: custom.warranty_years [number_integer]", headers)
        self.assertIn("Metafield: custom.fabric_oz_yd [number_decimal]", headers)
        self.assertIn("Metafield: custom.is_limited_edition [boolean]", headers)
        self.assertIn("Metafield: custom.release_date [date]", headers)
        self.assertIn("Metafield: custom.spec_sheet_url [url]", headers)
        self.assertIn("Metafield: custom.care_instructions [multi_line_text_field]", headers)
        self.assertIn("Variant Metafield: custom.fill_weight_g [number_integer]", headers)
        self.assertIn("Variant Metafield: custom.specs_json [json]", headers)

        # Internal WP noise stripped; SEO/Cost/GTIN mapped cleanly
        self.assertFalse(any("_edit_lock" in h for h in headers))
        r1 = res["shopify_rows"][0]
        self.assertEqual(r1["SEO Title"], "Alpine Shell Jacket | NordPeak")
        self.assertEqual(r1["Cost per item"], "42.50")
        self.assertEqual(r1["Variant Barcode"], "4006381333931")

        # 301 Redirects for products + hierarchical categories
        redir_map = {r["Redirect from"]: r["Redirect to"] for r in res["redirects"]}
        self.assertEqual(redir_map.get("/product/alpine-shell-jacket/"), "/products/alpine-shell-jacket")
        self.assertEqual(redir_map.get("/product-category/apparel/outerwear/"), "/collections/outerwear")
        self.assertEqual(redir_map.get("/product-category/winter-gear/"), "/collections/winter-gear")

        # Type inferencer direct check
        self.assertEqual(infer_metafield_type(["10", "20"]), "number_integer")
        self.assertEqual(infer_metafield_type(["10", "20.5"]), "number_decimal")
        self.assertEqual(infer_metafield_type(["yes", "NO"]), "boolean")
        self.assertEqual(infer_metafield_type(["2026-11-23"]), "date")
        self.assertEqual(infer_metafield_type(["https://example.com/a"]), "url")
        self.assertEqual(infer_metafield_type(['{"a":1}']), "json")

        # Orphan variation + duplicate SKU warning checks
        bad_csv = (
            "ID,Type,SKU,Name,Parent,Regular price\n"
            "1,simple,DUP-1,Prod One,,10.00\n"
            "2,simple,DUP-1,Prod Two,,12.00\n"
            "3,variation,ORPHAN-1,Orphan Child,id:999,15.00\n"
        )
        res_bad = compile_woo_to_shopify(bad_csv, pro_unlocked=False)
        joined_warnings = "\n".join(res_bad["warnings"])
        self.assertIn("Duplicate SKU detected: 'DUP-1'", joined_warnings)
        self.assertIn("Orphan variation 'ORPHAN-1'", joined_warnings)

    def test_free_limit_pro_gate_and_cli_out_dir_unlock(self) -> None:
        lines = ["ID,Type,SKU,Name,Slug,Regular price"]
        for i in range(1, 21):
            lines.append(f"{i},simple,SKU-{i:02d},Product {i},product-{i:02d},25.00")
        big_csv = "\n".join(lines)

        free_res = compile_woo_to_shopify(big_csv, pro_unlocked=False)
        self.assertTrue(free_res["truncated_by_free_tier"])
        self.assertEqual(free_res["summary"]["total_products_in_csv"], 20)
        self.assertEqual(free_res["summary"]["processed_products"], FREE_PRODUCT_LIMIT)

        # Free CSV preview succeeds, Pro exporters raise PermissionError
        shopify_csv = render_shopify_admin_csv(free_res)
        parsed = list(csv.DictReader(io.StringIO(shopify_csv)))
        self.assertEqual(len(parsed), FREE_PRODUCT_LIMIT)

        with self.assertRaises(PermissionError):
            render_matrixify_csv(free_res, pro_unlocked=False)
        with self.assertRaises(PermissionError):
            render_redirects_csv(free_res, pro_unlocked=False)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            cache_dir = tmp_dir / "lic_cache"
            in_csv = tmp_dir / "catalog.csv"
            out_dir = tmp_dir / "out"
            in_csv.write_text(big_csv, encoding="utf-8")

            # Unlicensed CLI --out-dir must exit with code 2
            rc_locked = cli_main(["--input", str(in_csv), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)])
            self.assertEqual(rc_locked, 2)
            self.assertFalse(out_dir.exists())

            # Activate Stripe key in isolated cache_dir (no network -> valid cs_live format fallback)
            lic = unlock_pro("cs_live_TestShopMetaShiftKey1234567890", cache_dir=str(cache_dir))
            self.assertTrue(lic["valid"])

            rc_unlocked = cli_main(
                ["--input", str(in_csv), "--out-dir", str(out_dir), "--cache-dir", str(cache_dir)]
            )
            self.assertEqual(rc_unlocked, 0)
            for fname in (
                "shopify-admin-products.csv",
                "matrixify-products.csv",
                "shopify-301-redirects.csv",
                "migration-audit.json",
            ):
                self.assertTrue((out_dir / fname).is_file(), f"Missing {fname}")

            audit = json.loads((out_dir / "migration-audit.json").read_text(encoding="utf-8"))
            self.assertEqual(audit["summary"]["processed_products"], 20)
            matrixify_rows = list(csv.DictReader(io.StringIO((out_dir / "matrixify-products.csv").read_text(encoding="utf-8"))))
            self.assertEqual(len(matrixify_rows), 20)
            self.assertEqual(matrixify_rows[0]["Command"], "MERGE")


if __name__ == "__main__":
    unittest.main()
