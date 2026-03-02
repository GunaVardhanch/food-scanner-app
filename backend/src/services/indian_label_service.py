"""
indian_label_service.py
───────────────────────
Side pipeline for Indian food products.

Responsibility:
  product_name (str) + raw_ocr_text (str)
       →  structured product dict   (or best-effort partial dict)

Data sources (tried in order):
  1. Open Food Facts India  (in.openfoodfacts.org)  — name search
  2. Open Food Facts World  (world.openfoodfacts.org) — name search
  3. FSSAI public product portal search              — HTML scrape
  4. Pure OCR / NER extraction from raw label text   — always available

This module does NOT modify the barcode-first pipeline.
It is called ONLY by the /api/scan-label endpoint.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# ── API endpoints ──────────────────────────────────────────────────────────────
_OFF_INDIA_SEARCH   = "https://in.openfoodfacts.org/cgi/search.pl"
_OFF_WORLD_SEARCH   = "https://world.openfoodfacts.org/cgi/search.pl"
_OFF_HEADERS        = {"User-Agent": "FoodScannerApp/2.0 (India; contact@foodscanner.app)"}
_OFF_TIMEOUT        = 10

# FSSAI public product search (no auth required)
_FSSAI_SEARCH_URL   = "https://foscos.fssai.gov.in/api/searchProduct"
_FSSAI_TIMEOUT      = 8


# ─────────────────────────────────────────────────────────────────────────────
# Public entry-point
# ─────────────────────────────────────────────────────────────────────────────

def lookup_indian_product(
    product_name: str,
    raw_ocr_text: str = "",
) -> Dict[str, Any]:
    """
    Try every available source for an Indian product and return the
    best-effort structured dict that the frontend can render.

    Always returns a dict (never None).  `source` key indicates origin.
    """
    product_name = product_name.strip()

    # 1. OFF India name search
    result = _search_off(product_name, _OFF_INDIA_SEARCH, "off_india")
    if result:
        logger.info("Indian lookup: found on OFF India for '%s'", product_name)
        return result

    # 2. OFF World name search
    result = _search_off(product_name, _OFF_WORLD_SEARCH, "off_world")
    if result:
        logger.info("Indian lookup: found on OFF World for '%s'", product_name)
        return result

    # 3. FSSAI search
    result = _search_fssai(product_name)
    if result:
        logger.info("Indian lookup: found on FSSAI for '%s'", product_name)
        return result

    # 4. OCR-only extraction (always succeeds with partial data)
    logger.info("Indian lookup: all APIs exhausted, using OCR extraction for '%s'", product_name)
    return _extract_from_ocr(product_name, raw_ocr_text)


# ─────────────────────────────────────────────────────────────────────────────
# Open Food Facts name search
# ─────────────────────────────────────────────────────────────────────────────

def _search_off(
    product_name: str,
    base_url: str,
    source_label: str,
) -> Optional[Dict[str, Any]]:
    """Search OFF by product name. Returns first reasonable match or None."""
    try:
        params = {
            "search_terms": product_name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5,
            "fields": (
                "product_name,product_name_en,product_name_hi,brands,"
                "ingredients_text,nutriments,serving_size,additives_tags"
            ),
        }
        resp = requests.get(base_url, params=params,
                            headers=_OFF_HEADERS, timeout=_OFF_TIMEOUT)
        if resp.status_code != 200:
            return None

        data = resp.json()
        products = data.get("products", [])
        if not products:
            return None

        # Pick the best match: prefer exact name match, else first result
        best = None
        pn_lower = product_name.lower()
        for p in products:
            name = (p.get("product_name") or p.get("product_name_en") or "").lower()
            if pn_lower in name or name in pn_lower:
                best = p
                break
        if best is None:
            best = products[0]

        return _normalise_off_result(best, source_label, product_name)

    except Exception as exc:
        logger.warning("OFF search error (%s): %s", source_label, exc)
        return None


def _normalise_off_result(
    p: Dict[str, Any],
    source: str,
    fallback_name: str,
) -> Dict[str, Any]:
    n = p.get("nutriments", {})
    name = (
        p.get("product_name")
        or p.get("product_name_en")
        or p.get("product_name_hi")
        or fallback_name
    )
    name = " ".join(name.split())

    ing_text = p.get("ingredients_text", "") or ""
    ingredients = [i.strip() for i in ing_text.split(",") if i.strip()]

    def _f(key: str) -> Optional[float]:
        v = n.get(key)
        try:
            return round(float(v), 1) if v is not None else None
        except Exception:
            return None

    return {
        "product_name": name,
        "brand":        p.get("brands") or "Unknown Brand",
        "source":       source,
        "ingredients":  ingredients,
        "nutrition": {
            "calories":  _f("energy-kcal_100g"),
            "protein":   _f("proteins_100g"),
            "carbs":     _f("carbohydrates_100g"),
            "sugar":     _f("sugars_100g"),
            "fat":       _f("fat_100g"),
            "fiber":     _f("fiber_100g"),
            "sodium":    round(float(n["sodium_100g"]) * 1000, 1)
                         if n.get("sodium_100g") is not None else None,
        },
        "additives_tags": p.get("additives_tags", []),
        "data_quality":  "api_verified",
    }


# ─────────────────────────────────────────────────────────────────────────────
# FSSAI FOSCOS search
# ─────────────────────────────────────────────────────────────────────────────

def _search_fssai(product_name: str) -> Optional[Dict[str, Any]]:
    """
    Query FSSAI FOSCOS (Food Safety & Standards Authority of India).
    Returns a minimal product dict if found, else None.

    FOSCOS public API is rate-limited but does not need an API key.
    """
    try:
        params = {"productName": product_name, "pageNo": 1, "pageSize": 5}
        resp = requests.get(
            _FSSAI_SEARCH_URL, params=params, timeout=_FSSAI_TIMEOUT,
            headers={"Accept": "application/json"}
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        # FOSCOS response structure varies; try common fields
        items = (
            data.get("data")
            or data.get("products")
            or data.get("result")
            or []
        )
        if not items:
            return None

        item = items[0]
        name = (
            item.get("productName")
            or item.get("product_name")
            or product_name
        )
        brand = item.get("brandName") or item.get("brand") or "Unknown Brand"

        return {
            "product_name": name.strip(),
            "brand":        brand.strip(),
            "source":       "fssai",
            "ingredients":  [],     # FOSCOS rarely returns full ingredient list
            "nutrition":    {},
            "fssai_license": item.get("licenseNo") or item.get("fssaiNo"),
            "data_quality": "fssai_partial",
        }

    except Exception as exc:
        logger.warning("FSSAI search error: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# OCR extraction (always-available fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_from_ocr(
    product_name: str,
    raw_text: str,
) -> Dict[str, Any]:
    """
    Parse nutrition values and ingredients directly from raw OCR text.
    Returns a best-effort dict with `data_quality = 'ocr_extracted'`.
    """
    text_lower = raw_text.lower()

    def _find_number(patterns: list[str]) -> Optional[float]:
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
        return None

    # ── Nutrition extraction ─────────────────────────────────────────────────
    calories = _find_number([
        r"energy[^\d]*(\d+(?:\.\d+)?)\s*k?cal",
        r"calories?[^\d]*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*k?cal",
    ])
    protein = _find_number([
        r"protein[^\d]*(\d+(?:\.\d+)?)\s*g",
        r"protien[^\d]*(\d+(?:\.\d+)?)\s*g",   # common OCR misspelling
    ])
    fat = _find_number([
        r"total\s+fat[^\d]*(\d+(?:\.\d+)?)\s*g",
        r"fat[^\d]*(\d+(?:\.\d+)?)\s*g",
    ])
    carbs = _find_number([
        r"total\s+carbo[^\d]*(\d+(?:\.\d+)?)\s*g",
        r"carbohydrate[^\d]*(\d+(?:\.\d+)?)\s*g",
        r"carbs?[^\d]*(\d+(?:\.\d+)?)\s*g",
    ])
    sugar = _find_number([
        r"sugar[^\d]*(\d+(?:\.\d+)?)\s*g",
        r"of which sugar[^\d]*(\d+(?:\.\d+)?)\s*g",
    ])
    sodium = _find_number([
        r"sodium[^\d]*(\d+(?:\.\d+)?)\s*m?g",
        r"salt[^\d]*(\d+(?:\.\d+)?)\s*g",
    ])
    fiber = _find_number([
        r"dietary\s+fiber[^\d]*(\d+(?:\.\d+)?)\s*g",
        r"fibre[^\d]*(\d+(?:\.\d+)?)\s*g",
        r"fiber[^\d]*(\d+(?:\.\d+)?)\s*g",
    ])

    # ── Ingredients extraction ───────────────────────────────────────────────
    ingredients: list[str] = []
    ing_match = re.search(
        r"ingredients?\s*:?\s*([^\.]{10,400})",
        raw_text,
        re.IGNORECASE | re.DOTALL,
    )
    if ing_match:
        raw_ing = ing_match.group(1)
        # Split on commas, semicolons, or newlines
        parts = re.split(r"[,;\n]+", raw_ing)
        ingredients = [p.strip() for p in parts if len(p.strip()) > 1][:30]

    # ── Warning flags ────────────────────────────────────────────────────────
    warnings: list[str] = []
    flag_patterns = {
        "High Sugar Content": sugar and sugar > 20,
        "High Sodium": sodium and sodium > 600,
        "High Saturated Fat": fat and fat > 20,
        "Very High Calorie Density": calories and calories > 450,
        "Contains INS Additives": bool(re.search(r"\bins\s*\d{3,}", text_lower)),
        "Contains Artificial Colors": bool(re.search(r"colour|color|tartrazine|sunset yellow|carmoisine", text_lower)),
        "Contains Preservatives": bool(re.search(r"preservative|sodium benzoate|potassium sorbate", text_lower)),
        "Contains MSG": bool(re.search(r"msg|monosodium glutamate|e621", text_lower)),
    }
    for label, triggered in flag_patterns.items():
        if triggered:
            warnings.append(label)

    return {
        "product_name":  product_name,
        "brand":         _extract_brand(raw_text) or "Unknown Brand",
        "source":        "ocr_extracted",
        "ingredients":   ingredients,
        "nutrition": {
            "calories": calories,
            "protein":  protein,
            "fat":      fat,
            "carbs":    carbs,
            "sugar":    sugar,
            "sodium":   sodium,
            "fiber":    fiber,
        },
        "warnings":     warnings,
        "raw_ocr_text": raw_text[:800],     # pass first 800 chars for debugging
        "data_quality": "ocr_extracted",
    }


def _extract_brand(text: str) -> Optional[str]:
    """Heuristic: look for 'by <Brand>' or 'Mfg by: <Brand>' patterns."""
    m = re.search(
        r"(?:manufactured\s+by|mfg\.?\s*by|marketed\s+by|brand)\s*:?\s*([A-Z][A-Za-z\s&\.]{2,40})",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return None
