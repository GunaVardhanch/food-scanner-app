import sqlite3
import json
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "nutrition_cache.db")
OFF_API_URL = "https://world.openfoodfacts.org/api/v2/product/"

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
        Lookup product by GTIN. 
        First checks local DB, then queries Open Food Facts API.
        """
        # 1. Check local DB
        local_data = self._get_from_local(gtin)
        if local_data:
            logger.info(f"Database: Local cache hit for {gtin}")
            return local_data

        # 2. Query External API (Open Food Facts)
        logger.info(f"Database: Cache miss for {gtin}. Querying Open Food Facts...")
        external_data = self._query_off_api(gtin)
        
        if external_data:
            # 3. Cache the result
            self.save_product(gtin, external_data, source="api")
            return external_data

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

    def _query_off_api(self, gtin: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(f"{OFF_API_URL}{gtin}", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    product = data.get("product", {})
                    
                    # Normalize data
                    nutriments = product.get("nutriments", {})
                    ingredients = [i.strip() for i in product.get("ingredients_text", "").split(",")] if product.get("ingredients_text") else []
                    
                    return {
                        "gtin": gtin,
                        "product_name": product.get("product_name", "Unknown Product"),
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
                        }
                    }
            return None
        except Exception as e:
            logger.error(f"Database: Error querying OFF API: {e}")
            return None

    def save_product(self, gtin: str, product_data: Dict[str, Any], source: str = "ocr_nlp"):
        """Save or update product in local DB."""
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
                logger.info(f"Database: Saved/Updated product {gtin}")
        except Exception as e:
            logger.error(f"Database: Error saving to local cache: {e}")

nutrition_db = NutritionDB()
