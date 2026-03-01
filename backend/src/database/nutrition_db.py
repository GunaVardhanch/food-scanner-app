import sqlite3
import json
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "nutrition_cache.db")
OFF_WORLD_API_URL = "https://world.openfoodfacts.org/api/v2/product/"
OFF_INDIA_API_URL = "https://in.openfoodfacts.org/api/v2/product/"
GO_UPC_API_URL = "https://go-upc.com/api/v1/code/"
DATAKICK_API_URL = "https://www.datakick.org/api/items/"


class NutritionDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for GTIN caching."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    gtin TEXT PRIMARY KEY,
                    product_name TEXT,
                    brand TEXT,
                    ingredients_json TEXT,
                    nutrition_json TEXT,
                    source TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            conn.commit()

    def get_product_by_gtin(self, gtin: str) -> Optional[Dict[str, Any]]:
        """
        Multi-source lookup:
        1. Local SQLite cache  (instant)
        2. Open Food Facts World API
        3. Open Food Facts India API
        4. go-UPC API
        5. Datakick API
        """
        # 1. Local cache first
        local_data = self._get_from_local(gtin)
        if local_data:
            logger.info(f"Database: Local cache hit for {gtin}")
            return local_data

        # 2. OFF World
        logger.info(f"Database: Trying Open Food Facts World for {gtin}...")
        data = self._query_off_api(OFF_WORLD_API_URL, gtin, source="off_world")
        if data:
            self.save_product(gtin, data, source="off_world")
            return data

        # 3. OFF India
        logger.info(f"Database: Trying Open Food Facts India for {gtin}...")
        data = self._query_off_api(OFF_INDIA_API_URL, gtin, source="off_india")
        if data:
            self.save_product(gtin, data, source="off_india")
            return data

        # 4. go-UPC
        logger.info(f"Database: Trying go-UPC for {gtin}...")
        data = self._query_go_upc(gtin)
        if data:
            self.save_product(gtin, data, source="go_upc")
            return data

        # 5. Datakick
        logger.info(f"Database: Trying Datakick for {gtin}...")
        data = self._query_datakick(gtin)
        if data:
            self.save_product(gtin, data, source="datakick")
            return data

        logger.warning(f"Database: All sources exhausted for GTIN {gtin}")
        return None

    def _get_from_local(self, gtin: str) -> Optional[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products WHERE gtin = ?", (gtin,))
                row = cursor.fetchone()
                if row:
                    return {
                        "gtin": row["gtin"],
                        "product_name": row["product_name"],
                        "brand": row["brand"],
                        "ingredients": json.loads(row["ingredients_json"]),
                        "nutrition": json.loads(row["nutrition_json"]),
                        "source": row["source"]
                    }
        except Exception as e:
            logger.error(f"Database: Error reading local cache: {e}")
        return None

    def _query_off_api(self, base_url: str, gtin: str, source: str) -> Optional[Dict[str, Any]]:
        """Query an Open Food Facts endpoint (world or india)."""
        try:
            response = requests.get(f"{base_url}{gtin}", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    product = data.get("product", {})
                    nutriments = product.get("nutriments", {})
                    ingredients_text = product.get("ingredients_text", "")
                    ingredients = [i.strip() for i in ingredients_text.split(",")] if ingredients_text else []
                    return {
                        "gtin": gtin,
                        "product_name": product.get("product_name") or product.get("product_name_en", "Unknown Product"),
                        "brand": product.get("brands", "Unknown Brand"),
                        "ingredients": ingredients,
                        "nutrition": {
                            "calories": nutriments.get("energy-kcal_100g", 0),
                            "protein": nutriments.get("proteins_100g", 0),
                            "carbs": nutriments.get("carbohydrates_100g", 0),
                            "fat": nutriments.get("fat_100g", 0),
                            "sugar": nutriments.get("sugars_100g", 0),
                            "fiber": nutriments.get("fiber_100g", 0),
                            "sodium": nutriments.get("sodium_100g", 0)
                        },
                        "source": source
                    }
        except Exception as e:
            logger.error(f"Database: Error querying {source} API: {e}")
        return None

    def _query_go_upc(self, gtin: str) -> Optional[Dict[str, Any]]:
        """Query go-UPC. Free tier: 100 req/day; all results are cached to SQLite."""
        try:
            headers = {"accept": "application/json"}
            response = requests.get(f"{GO_UPC_API_URL}{gtin}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                if not product or not product.get("name"):
                    return None
                nutrients = {n.get("name", "").lower(): n.get("value", 0)
                             for n in (product.get("nutrients") or [])}
                return {
                    "gtin": gtin,
                    "product_name": product.get("name", "Unknown Product"),
                    "brand": product.get("brand", "Unknown Brand"),
                    "ingredients": [i.strip() for i in (product.get("ingredients") or "").split(",") if i.strip()],
                    "nutrition": {
                        "calories": nutrients.get("calories", 0),
                        "protein": nutrients.get("protein", 0),
                        "carbs": nutrients.get("total carbohydrate", 0),
                        "fat": nutrients.get("total fat", 0),
                        "sugar": nutrients.get("sugars", 0),
                        "fiber": nutrients.get("dietary fiber", 0),
                        "sodium": nutrients.get("sodium", 0),
                    },
                    "source": "go_upc"
                }
        except Exception as e:
            logger.error(f"Database: Error querying go-UPC: {e}")
        return None

    def _query_datakick(self, gtin: str) -> Optional[Dict[str, Any]]:
        """Query Datakick crowd-sourced product DB."""
        try:
            response = requests.get(f"{DATAKICK_API_URL}{gtin}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data or not data.get("name"):
                    return None
                serving = float(data.get("serving_size") or 100)

                def per100(val):
                    try:
                        return round(float(val or 0) * 100 / (serving or 100), 1)
                    except Exception:
                        return 0

                return {
                    "gtin": gtin,
                    "product_name": data.get("name", "Unknown Product"),
                    "brand": data.get("brand_name", "Unknown Brand"),
                    "ingredients": [i.strip() for i in (data.get("ingredients") or "").split(",") if i.strip()],
                    "nutrition": {
                        "calories": per100(data.get("calories")),
                        "protein": per100(data.get("protein")),
                        "carbs": per100(data.get("total_carbohydrate")),
                        "fat": per100(data.get("total_fat")),
                        "sugar": per100(data.get("sugars")),
                        "fiber": per100(data.get("dietary_fiber")),
                        "sodium": per100(data.get("sodium")),
                    },
                    "source": "datakick"
                }
        except Exception as e:
            logger.error(f"Database: Error querying Datakick: {e}")
        return None

    def save_product(self, gtin: str, product_data: Dict[str, Any], source: str = "ocr_nlp"):
        """Save or update product in local SQLite cache."""
        try:
            now = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO products
                    (gtin, product_name, brand, ingredients_json, nutrition_json, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    gtin,
                    product_data.get("product_name"),
                    product_data.get("brand"),
                    json.dumps(product_data.get("ingredients", [])),
                    json.dumps(product_data.get("nutrition", {})),
                    source,
                    now,
                    now
                ))
                conn.commit()
                logger.info(f"Database: Saved/Updated product {gtin} from {source}")
        except Exception as e:
            logger.error(f"Database: Error saving to local cache: {e}")


nutrition_db = NutritionDB()
