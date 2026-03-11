"""
fetch_and_train.py
══════════════════
A script that:
  1. Fetches ~150 popular Indian products from Open Food Facts API with full nutrition data.
  2. Cleans and computes their 'Target Score' based on NutriScore + Additive Impact.
  3. Trains the XGBoost model on this real-world dataset.
  4. Seeds the local `nutrition_cache` SQLite DB so they scan instantly offline.
  
Run:
    python fetch_and_train.py
"""

import json
import os
import sqlite3
import sys
import time
import requests
import numpy as np
import xgboost as xgb

sys.path.insert(0, os.path.dirname(__file__))
from app.config import HEALTH_SCORE_MODEL_PATH, MODEL_DIR
from app.services.additives_expert import AdditivesExpert
from app.services.nutrition_db import _normalise_off_product

DB_PATH = os.path.join(os.path.dirname(__file__), "food_scanner.db")
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

def fetch_off_products(target_count=50):
    print(f"Fetching {target_count} products from Open Food Facts...")
    products = []
    
    # Pre-defined list of popular GTINs as fallback to ensure success if API acts up
    fallback_gtins = [
        "8906042711014", "8901262173034", "8904109601200", "8901826100016", 
        "8800025000290", "5000159484695", "8901058002085", "8901826400043", 
        "8901491100108", "8901030706615", "8901063151849", "8906001200014", 
        "8901058852424", "8901491502230", "8901764004404", "8902102901013", 
        "8901058501898", "7622201169091", "8901058505476", "8901764001052",
        # Some additional global/Indian popular ones
        "5449000000996", "4008400404127", "8901030712395", "8901058863642",
        "8901491101518", "8901491101839", "8901764002622", "8902102300052"
    ]
    
    # Try fetching GTINs from search, if it fails, use fallback
    gtins_to_fetch = set(fallback_gtins)
    params = {
        'countries_tags_en': 'india',
        'fields': 'code',
        'sort_by': 'unique_scans_n',
        'page_size': 50
    }
    
    try:
        resp = requests.get("https://world.openfoodfacts.org/api/v2/search", params=params, headers={"User-Agent": "FoodScannerApp/2.0"}, timeout=15)
        if resp.status_code == 200:
            items = resp.json().get("products", [])
            for p in items:
                code = p.get("code")
                if code and code.isdigit() and len(code) >= 8:
                    gtins_to_fetch.add(code)
    except Exception as e:
        print(f"Search API timed out or failed, using {len(gtins_to_fetch)} fallback GTINs. ({e})")
        
    print(f"Found {len(gtins_to_fetch)} GTINs to process...")
    
    from app.services.nutrition_db import _fetch_from_off
    
    for gtin in list(gtins_to_fetch)[:target_count]:
        try:
            # We use the method already imported from nutrition_db
            norm_p = _fetch_from_off(gtin)
            if not norm_p or not norm_p.get("nutrition_per_100g"):
                continue
                
            # Randomly distribute NutriScores for the Target Score since we didn't fetch them
            # We map actual nutritional values to simulate the grade
            sugar = norm_p["nutrition_per_100g"].get("sugars_g") or 0
            sodium = norm_p["nutrition_per_100g"].get("sodium_mg") or 0
            if sugar > 20 or sodium > 600:
                nutriscore = "E"
            elif sugar > 10 or sodium > 300:
                nutriscore = "D"
            elif sugar < 5 and sodium < 100:
                nutriscore = "A"
            else:
                nutriscore = "C"

            norm_p["nutriscore"] = nutriscore
            products.append(norm_p)
            print(f" + {gtin}: {norm_p.get('product_name')}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching {gtin}: {e}")
            
    print(f"Successfully fetched {len(products)} valid products with full data.")
    return products

def calibrate_target_score(nutriscore):
    # Base scores for NutriScore tiers
    mapping = {
        "A": 9.0,
        "B": 7.5,
        "C": 6.0,
        "D": 4.5,
        "E": 2.5
    }
    return mapping.get(nutriscore, 5.0)

def compute_additive_features(products):
    expert = AdditivesExpert()
    enriched = []
    for p in products:
        ing_text = ", ".join(p.get("ingredients", []))
        detected, impact = expert.analyze_text(ing_text)
        risk_summary = expert.get_risk_summary(detected)
        
        # Calculate final target score combining NutriScore + Additive penalty
        base_score = calibrate_target_score(p["nutriscore"])
        final_score = max(0.5, min(10.0, base_score + (impact * 0.5)))
        
        expected_grade = "GREEN" if final_score >= 7.0 else ("YELLOW" if final_score >= 4.0 else "RED")
        
        enriched.append({
            **p,
            "target_score": round(final_score, 1),
            "expected_grade": expected_grade,
            "additive_impact": impact,
            "detected_additives": detected,
            "risk_summary": risk_summary,
        })
    return enriched, expert

def build_training_data(enriched_products):
    X, y = [], []
    for p in enriched_products:
        n = p["nutrition_per_100g"]
        features = [
            float(n.get("sugars_g", 0) or 0),
            float(n.get("fat_g", 0) or 0),
            float(n.get("carbohydrates_g", 0) or 0),
            float(n.get("protein_g", 0) or 0),
            float(n.get("energy_kcal", 0) or 0),
            float(p.get("additive_impact", 0) or 0),
        ]
        X.append(features)
        y.append(p["target_score"])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

def train_model(X, y):
    feature_names = ["sugar_g", "fat_g", "carbs_g", "protein_g", "calories", "additive_impact"]
    dtrain = xgb.DMatrix(X, label=y, feature_names=feature_names)

    params = {
        "objective":        "reg:squarederror",
        "eval_metric":      "rmse",
        "max_depth":        5,
        "eta":              0.05,
        "subsample":        0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 1,
        "reg_alpha":        0.1,
        "reg_lambda":       1.5,
        "seed":             42,
    }
    
    evals_result = {}
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=600,
        evals=[(dtrain, "train")],
        verbose_eval=100,
        evals_result=evals_result,
    )
    return model

def seed_database(products):
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_cache (
            gtin TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

    inserted = 0
    barcodes_for_md = []
    
    for p in products:
        record = {
            "gtin":               p["gtin"],
            "product_name":       p["product_name"],
            "brand":              p.get("brand"),
            "country":            p.get("country", "IN"),
            "source":             "off_fetched",
            "ingredients":        p.get("ingredients", []),
            "nutrition_per_100g": p.get("nutrition_per_100g", {}),
        }
        conn.execute(
            "INSERT OR REPLACE INTO nutrition_cache (gtin, data) VALUES (?, ?)",
            (p["gtin"], json.dumps(record))
        )
        inserted += 1
        
        # Save a few for the README
        if inserted <= 25:
            barcodes_for_md.append(p)

    conn.commit()
    conn.close()
    print(f"\n✅ Seeded {inserted} products into nutrition_cache")
    return barcodes_for_md

def update_barcodes_md(sample_products):
    md_path = os.path.join(os.path.dirname(__file__), "..", "BARCODES.md")
    
    content = "# 🍱 NutriScanner — Generated Barcodes from Open Food Facts API\n\n"
    content += "These barcodes have been dynamically fetched from the Open Food Facts API and seeded into your local database.\n"
    content += "Scan them at **http://localhost:3000**.\n\n"
    
    content += "## 📋 Sample Fetched Barcodes\n\n"
    content += "| # | Barcode | Product | Brand | Score | Expected |\n"
    content += "|---|---------|---------|-------|-------|----------|\n"
    
    for i, p in enumerate(sample_products, 1):
        brand = (p.get("brand") or "Unknown").split(",")[0][:15]
        name = p["product_name"][:30]
        grade = p["expected_grade"]
        score = p["target_score"]
        emoji = "🟢" if grade == "GREEN" else ("🟡" if grade == "YELLOW" else "🔴")
        content += f"| {i} | `{p['gtin']}` | {name} | {brand} | {score} | {emoji} {grade} |\n"
        
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"✅ Updated {md_path} with new fetched barcodes.")

def main():
    print("=" * 60)
    print("  NutriScanner — Dynamic OFF Fetch & Train")
    print("=" * 60)
    
    # 1. Fetch
    products = fetch_off_products(50)  # Reduced to 50 for faster execution
    if not products:
        print("Failed to fetch products.")
        sys.exit(1)
        
    # 2. Enrich Additives & Targets
    enriched, expert = compute_additive_features(products)
    
    # 3. Build data
    X, y = build_training_data(enriched)
    
    # 4. Train Model
    print("\nTraining XGBoost model...")
    model = train_model(X, y)
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_model(HEALTH_SCORE_MODEL_PATH)
    print(f"✅ Model saved → {HEALTH_SCORE_MODEL_PATH}")
    
    # 5. Seed DB
    sample_products = seed_database(enriched)
    
    # 6. Update README
    update_barcodes_md(sample_products)
    print("Done!")

if __name__ == "__main__":
    main()
