"""
nutrition_db.py
───────────────
Non-ML database / API layer.

Responsibility:
    GTIN string  →  structured product dict  (or None if not found)

This module has NO machine-learning code.  It is a pure data-retrieval layer.

Lookup order (fastest / most-reliable first):
    1. Local SQLite cache  — avoids repeat network calls for the same GTIN.
    2. Open Food Facts API — free, global, strong Indian product coverage.
    3. Open Beauty Facts   — fallback for cosmetics/personal care (optional).

If the GTIN is not found in any source, the function returns None and the
caller is responsible for returning a "partial" or "not found" response to
the client.  The CALLER MUST NOT call OCR/NLP/ML to fill missing data.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

# SQLite cache lives next to this file's package (backend/app/data/)
_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_CACHE_DB_PATH = os.path.join(_DB_DIR, "gtin_cache.db")

# OFF API settings
_OFF_BASE = "https://world.openfoodfacts.org/api/v2/product"
_OFF_USER_AGENT = "FoodScannerApp/2.0 (India; contact@foodscanner.app)"
_OFF_TIMEOUT = 10  # seconds

# Fix 4: Cache TTL — re-fetch from OFF after this many seconds (30 days)
_CACHE_TTL_SECONDS = 60 * 60 * 24 * 30
_OFF_FIELDS = (
    "product_name,product_name_en,product_name_hi,product_name_mr,"
    "product_name_ta,product_name_te,product_name_kn,product_name_gu,"
    "abbreviated_product_name,generic_name,generic_name_en,"
    "brands,countries_tags,ingredients_text,"
    "nutriments,serving_size,nutrition_grades,additives_tags,labels_tags"
)

# ─────────────────────────────────────────────────────────────────────────────
# Cache initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_cache() -> None:
    """Create the SQLite cache table if it does not already exist."""
    os.makedirs(_DB_DIR, exist_ok=True)
    with sqlite3.connect(_CACHE_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gtin_cache (
                gtin                    TEXT PRIMARY KEY,
                product_name            TEXT,
                brand                   TEXT,
                country                 TEXT,
                ingredients_json        TEXT,
                nutrition_per_100g_json TEXT,
                nutrition_per_serving_json TEXT,
                serving_size_g          REAL,
                source                  TEXT,
                fetched_at              INTEGER
            )
        """)
        conn.commit()


_init_cache()

# Absolute path to food_scanner.db (seeded by train_and_seed.py)
_MAIN_DB_PATH = os.path.normpath(os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "..", "..", "food_scanner.db"
))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_product_by_gtin(gtin: str) -> Optional[Dict[str, Any]]:
    """
    Look up a product by GTIN. Lookup order:
        1. gtin_cache (app/data/gtin_cache.db)  — fast repeat-lookup cache
        2. nutrition_cache (food_scanner.db)     — seeded by train_and_seed.py
        3. Open Food Facts API                   — network fallback
    """
    gtin = gtin.strip()
    if not gtin:
        return None

    logger.info("GTIN lookup: %s", gtin)

    # 1. Fast dedup cache
    cached = _read_cache(gtin)
    if cached:
        logger.info("GTIN lookup result: gtin_cache hit for %s", gtin)
        return cached

    # 2. Seeded nutrition_cache in food_scanner.db
    seeded = _read_nutrition_cache(gtin)
    if seeded:
        logger.info("GTIN lookup result: nutrition_cache hit for %s", gtin)
        return seeded

    # 3. Open Food Facts API
    off_result = _fetch_from_off(gtin)
    if off_result:
        _write_cache(gtin, off_result)
        logger.info("GTIN lookup result: found on Open Food Facts for %s", gtin)
        return off_result

    logger.info("GTIN lookup result: not found for %s", gtin)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Cache helpers
# ─────────────────────────────────────────────────────────────────────────────

def _read_cache(gtin: str) -> Optional[Dict[str, Any]]:
    """
    Return cached product dict or None.
    Fix 4: Entries older than _CACHE_TTL_SECONDS are treated as expired
    and deleted so the caller falls through to a fresh OFF API fetch.
    """
    try:
        with sqlite3.connect(_CACHE_DB_PATH) as conn:
            row = conn.execute(
                "SELECT * FROM gtin_cache WHERE gtin = ?", (gtin,)
            ).fetchone()
        if not row:
            return None

        (gtin_, name, brand, country, ing_json,
         n100_json, nsrv_json, srv_g, source, fetched_at) = row

        # TTL check — expire stale entries
        if fetched_at and (int(time.time()) - int(fetched_at)) > _CACHE_TTL_SECONDS:
            logger.info("Cache entry for %s is stale (>30 days), expiring.", gtin)
            with sqlite3.connect(_CACHE_DB_PATH) as conn:
                conn.execute("DELETE FROM gtin_cache WHERE gtin = ?", (gtin,))
                conn.commit()
            return None

        return {
            "gtin": gtin_,
            "product_name": name,
            "brand": brand,
            "country": country,
            "ingredients": json.loads(ing_json or "[]"),
            "nutrition_per_100g": json.loads(n100_json or "{}"),
            "nutrition_per_serving": json.loads(nsrv_json or "{}"),
            "source": "cache",
        }
    except Exception as exc:
        logger.warning("Cache read error: %s", exc)
        return None


def _write_cache(gtin: str, product: Dict[str, Any]) -> None:
    """Persist a product dict to the SQLite cache."""
    try:
        srv = product.get("nutrition_per_serving") or {}
        srv_g = srv.get("serving_size_g")
        with sqlite3.connect(_CACHE_DB_PATH) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO gtin_cache
                    (gtin, product_name, brand, country, ingredients_json,
                     nutrition_per_100g_json, nutrition_per_serving_json,
                     serving_size_g, source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gtin,
                    product.get("product_name"),
                    product.get("brand"),
                    product.get("country"),
                    json.dumps(product.get("ingredients", [])),
                    json.dumps(product.get("nutrition_per_100g", {})),
                    json.dumps(product.get("nutrition_per_serving", {})),
                    srv_g,
                    product.get("source", "openfoodfacts"),
                    int(time.time()),
                ),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("Cache write error: %s", exc)


def _read_nutrition_cache(gtin: str) -> Optional[Dict[str, Any]]:
    """
    Read from nutrition_cache in food_scanner.db (seeded by train_and_seed.py).
    Each row stores the full product JSON in the 'data' column.
    """
    if not os.path.exists(_MAIN_DB_PATH):
        logger.warning("nutrition_cache: food_scanner.db not found at %s", _MAIN_DB_PATH)
        return None
    try:
        with sqlite3.connect(_MAIN_DB_PATH) as conn:
            row = conn.execute(
                "SELECT data FROM nutrition_cache WHERE gtin = ?", (gtin,)
            ).fetchone()
        if not row:
            return None
        record = json.loads(row[0])
        return {
            "gtin":                  record.get("gtin", gtin),
            "product_name":          record.get("product_name", "Unknown Product"),
            "brand":                 record.get("brand"),
            "country":               record.get("country", "IN"),
            "ingredients":           record.get("ingredients", []),
            "nutrition_per_100g":    record.get("nutrition_per_100g", {}),
            "nutrition_per_serving": record.get("nutrition_per_serving", {}),
            "source":                "seeded",
        }
    except Exception as exc:
        logger.warning("nutrition_cache read error for %s: %s", gtin, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Open Food Facts fetcher
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_from_off(gtin: str) -> Optional[Dict[str, Any]]:
    """
    Call the Open Food Facts v2 API and normalise the response into our
    canonical product dict format.
    """
    url = f"{_OFF_BASE}/{gtin}"
    try:
        resp = requests.get(
            url,
            params={"fields": _OFF_FIELDS},
            headers={"User-Agent": _OFF_USER_AGENT},
            timeout=_OFF_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.debug("OFF API returned HTTP %s for GTIN %s", resp.status_code, gtin)
            return None

        data = resp.json()
        if data.get("status") != 1:
            return None  # product not in OFF database

        product = data.get("product", {})
        return _normalise_off_product(gtin, product)

    except requests.exceptions.Timeout:
        logger.warning("OFF API timeout for GTIN %s", gtin)
    except Exception as exc:
        logger.warning("OFF API error for GTIN %s: %s", gtin, exc)
    return None


def _normalise_off_product(gtin: str, p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map an Open Food Facts product dict to our canonical schema.
    All keys are standardised; any missing field defaults to None / empty.
    """
    n = p.get("nutriments", {})

    # ── Nutrition per 100 g ──────────────────────────────────────────────────
    per_100g: Dict[str, Any] = {
        # Fix 6: energy_100g in OFF is kJ, not kcal. Always prefer the
        # explicit energy-kcal_100g field. Only fall back to energy_100g
        # if the kcal field is truly absent, and convert kJ → kcal.
        "energy_kcal":     _safe_float(n.get("energy-kcal_100g")) or _kj_to_kcal(n.get("energy_100g")),
        "protein_g":       _safe_float(n.get("proteins_100g")),
        "carbohydrates_g": _safe_float(n.get("carbohydrates_100g")),
        "sugars_g":        _safe_float(n.get("sugars_100g")),
        "fat_g":           _safe_float(n.get("fat_100g")),
        "saturated_fat_g": _safe_float(n.get("saturated-fat_100g")),
        "fiber_g":         _safe_float(n.get("fiber_100g")),
        "sodium_mg":       _safe_float_x1000(n.get("sodium_100g")),  # OFF stores g, we want mg
    }

    # ── Nutrition per serving ────────────────────────────────────────────────
    serving_size_raw = p.get("serving_size", "")
    serving_g = _parse_serving_size_g(serving_size_raw)

    per_serving: Dict[str, Any] = {
        "serving_size_g":  serving_g,
        "energy_kcal":     _safe_float(n.get("energy-kcal_serving") or n.get("energy_serving")),
        "protein_g":       _safe_float(n.get("proteins_serving")),
        "carbohydrates_g": _safe_float(n.get("carbohydrates_serving")),
        "sugars_g":        _safe_float(n.get("sugars_serving")),
        "fat_g":           _safe_float(n.get("fat_serving")),
        "saturated_fat_g": _safe_float(n.get("saturated-fat_serving")),
        "fiber_g":         _safe_float(n.get("fiber_serving")),
        "sodium_mg":       _safe_float_x1000(n.get("sodium_serving")),
    }

    # ── Ingredients ─────────────────────────────────────────────────────────
    ing_text: str = p.get("ingredients_text", "") or ""
    # Fix 5: Smart split that respects parentheses so sub-ingredients like
    # "Vegetable Oil (Palm, Sunflower)" stay as one item instead of splitting
    # into "Vegetable Oil (Palm" and "Sunflower)".
    ingredients = _split_ingredients(ing_text)

    # ── Country ─────────────────────────────────────────────────────────────
    countries = p.get("countries_tags", [])
    country = "IN"  # default for Indian app
    for c in countries:
        if "india" in c.lower():
            country = "IN"
            break
        country = c.replace("en:", "").upper()[:2]

    # ── Best-effort product name ─────────────────────────────────────────────
    # Open Food Facts stores localised names as product_name_XX where XX is the
    # ISO 639-1 language code. Indian products often only have hi/mr/ta/te/kn/gu.
    product_name = (
        p.get("product_name")
        or p.get("product_name_en")
        or p.get("product_name_hi")   # Hindi
        or p.get("product_name_mr")   # Marathi
        or p.get("product_name_ta")   # Tamil
        or p.get("product_name_te")   # Telugu
        or p.get("product_name_kn")   # Kannada
        or p.get("product_name_gu")   # Gujarati
        or p.get("abbreviated_product_name")
        or p.get("generic_name")
        or p.get("generic_name_en")
        or "Unknown Product"
    )
    # Strip leading/trailing whitespace and collapse multiple spaces
    product_name = " ".join(product_name.split()) if product_name else "Unknown Product"

    return {
        "gtin": gtin,
        "product_name": product_name,
        "brand": p.get("brands") or None,
        "country": country,
        "ingredients": ingredients,
        "nutrition_per_100g": per_100g,
        "nutrition_per_serving": per_serving,
        "source": "openfoodfacts",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_float(value: Any) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_float_x1000(value: Any) -> Optional[float]:
    """Convert sodium (stored in g on OFF) to mg."""
    f = _safe_float(value)
    return round(f * 1000, 2) if f is not None else None


def _parse_serving_size_g(raw: str) -> Optional[float]:
    """
    Parse a serving size string like '20 g', '1 piece (30g)', '2 tbsp (28g)' → float grams.
    Returns None if parsing fails.
    """
    import re
    if not raw:
        return None
    # Look for the first number followed by 'g'
    m = re.search(r"([\d.]+)\s*g", raw, re.IGNORECASE)
    if m:
        return _safe_float(m.group(1))
    # Look for just a leading number (assume grams)
    m = re.search(r"^([\d.]+)", raw.strip())
    if m:
        return _safe_float(m.group(1))
    return None


def _kj_to_kcal(value: Any) -> Optional[float]:
    """
    Fix 6: Convert kilojoules to kilocalories (1 kcal = 4.184 kJ).
    Used when OFF only provides energy_100g (kJ) and not energy-kcal_100g.
    Returns None if value is None or not numeric.
    """
    f = _safe_float(value)
    if f is None:
        return None
    return round(f / 4.184, 1)


def _split_ingredients(ing_text: str) -> list:
    """
    Fix 5: Split an ingredients string on commas while respecting
    parentheses, so sub-ingredients like "Vegetable Oil (Palm, Sunflower)"
    are kept as a single item.

    Examples
    --------
    "Sugar, Wheat Flour, Oil (Palm, Sunflower), Salt"
    → ["Sugar", "Wheat Flour", "Oil (Palm, Sunflower)", "Salt"]
    """
    import re
    if not ing_text:
        return []

    items = []
    depth = 0
    current = []

    for char in ing_text:
        if char in ("(", "["):
            depth += 1
            current.append(char)
        elif char in (")", "]"):
            depth = max(0, depth - 1)
            current.append(char)
        elif char == "," and depth == 0:
            token = "".join(current).strip()
            # Strip leading asterisks/bullets used on some labels
            token = re.sub(r"^[\*\-\•]+\s*", "", token)
            if token:
                items.append(token)
            current = []
        else:
            current.append(char)

    # Last item
    token = "".join(current).strip()
    token = re.sub(r"^[\*\-\•]+\s*", "", token)
    if token:
        items.append(token)

    return items
