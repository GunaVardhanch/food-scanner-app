"""
seed_test_barcodes.py
─────────────────────
Seeds the local SQLite database with 20 well-known, real-world product barcodes
so the scanner has guaranteed results for testing/demo purposes.

These are real GTINs/EAN-13 barcodes for popular products available in india
and internationally. They are also seeded into the local nutrition cache.

Run:
    python seed_test_barcodes.py
"""

import json
import os
import sqlite3
import sys

# Make sure backend/ is on path
sys.path.insert(0, os.path.dirname(__file__))

DB_PATH = os.path.join(os.path.dirname(__file__), "food_scanner.db")

# ── 20 Real Barcodes with known nutrition data ─────────────────────────────────
TEST_PRODUCTS = [
    {
        "gtin": "8901058852424",
        "product_name": "Maggi 2-Minute Noodles Masala",
        "brand": "Nestlé",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Wheat Flour", "Palm Oil", "Salt", "Sugar", "Spices", "INS 508", "INS 501"],
        "nutrition_per_100g": {"energy_kcal": 436, "protein_g": 9.6, "fat_g": 14.4, "saturated_fat_g": 6.2, "carbohydrates_g": 66.1, "sugars_g": 2.7, "fiber_g": 2.1, "sodium_mg": 820},
    },
    {
        "gtin": "8901491502230",
        "product_name": "Lay's Classic Salted Chips",
        "brand": "PepsiCo",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Potatoes", "Edible Vegetable Oil", "Salt"],
        "nutrition_per_100g": {"energy_kcal": 542, "protein_g": 6.5, "fat_g": 31.5, "saturated_fat_g": 9.0, "carbohydrates_g": 57.8, "sugars_g": 0.5, "fiber_g": 3.5, "sodium_mg": 490},
    },
    {
        "gtin": "8901030706615",
        "product_name": "Parle-G Original Gluco Biscuits",
        "brand": "Parle",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Wheat Flour", "Sugar", "Edible Vegetable Oil", "Invert Syrup", "Milk Solids", "Leavening Agents", "INS 503(ii)", "INS 500(ii)", "Salt"],
        "nutrition_per_100g": {"energy_kcal": 450, "protein_g": 6.7, "fat_g": 10.7, "saturated_fat_g": 5.2, "carbohydrates_g": 76.0, "sugars_g": 21.5, "fiber_g": 1.2, "sodium_mg": 250},
    },
    {
        "gtin": "8901063151849",
        "product_name": "Britannia Good Day Butter Cookies",
        "brand": "Britannia",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Refined Wheat Flour", "Sugar", "Edible Vegetable Fat", "Butter", "Invert Syrup", "Milk Solids", "Salt", "Leavening Agents"],
        "nutrition_per_100g": {"energy_kcal": 490, "protein_g": 6.2, "fat_g": 18.5, "saturated_fat_g": 8.3, "carbohydrates_g": 73.5, "sugars_g": 22.0, "fiber_g": 1.0, "sodium_mg": 310},
    },
    {
        "gtin": "8906001200014",
        "product_name": "Amul Pure Butter",
        "brand": "Amul",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Milk Fat", "Common Salt"],
        "nutrition_per_100g": {"energy_kcal": 720, "protein_g": 0.5, "fat_g": 80.0, "saturated_fat_g": 50.0, "carbohydrates_g": 1.0, "sugars_g": 0.6, "fiber_g": 0, "sodium_mg": 550},
    },
    {
        "gtin": "8901764001052",
        "product_name": "Hide & Seek Biscuits Chocolate Chip",
        "brand": "Parle",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Refined Wheat Flour", "Sugar", "Edible Vegetable Oil", "Cocoa Powder", "Chocolate Chips", "Emulsifiers", "Salt", "INS 503(ii)"],
        "nutrition_per_100g": {"energy_kcal": 500, "protein_g": 6.8, "fat_g": 22.0, "saturated_fat_g": 10.5, "carbohydrates_g": 67.2, "sugars_g": 26.0, "fiber_g": 2.0, "sodium_mg": 270},
    },
    {
        "gtin": "8902102901013",
        "product_name": "Kurkure Masala Munch",
        "brand": "PepsiCo",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Rice Meal", "Edible Vegetable Oil", "Corn Meal", "Salt", "Gram Meal", "Spices", "Sugar", "INS 631", "INS 627"],
        "nutrition_per_100g": {"energy_kcal": 498, "protein_g": 6.2, "fat_g": 24.8, "saturated_fat_g": 11.2, "carbohydrates_g": 63.1, "sugars_g": 4.5, "fiber_g": 2.0, "sodium_mg": 890},
    },
    {
        "gtin": "8800025000290",
        "product_name": "Nescafé Classic Instant Coffee",
        "brand": "Nestlé",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Instant Coffee"],
        "nutrition_per_100g": {"energy_kcal": 376, "protein_g": 12.2, "fat_g": 0.5, "saturated_fat_g": 0.1, "carbohydrates_g": 63.0, "sugars_g": 0, "fiber_g": 0, "sodium_mg": 80},
    },
    {
        "gtin": "8901058501898",
        "product_name": "KitKat 4 Finger Milk Chocolate",
        "brand": "Nestlé",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Sugar", "Wheat Flour", "Cocoa Butter", "Skim Milk Powder", "Cocoa Mass", "Lactose", "Emulsifier (SOY LECITHIN)", "Vanillin"],
        "nutrition_per_100g": {"energy_kcal": 518, "protein_g": 6.7, "fat_g": 26.9, "saturated_fat_g": 16.1, "carbohydrates_g": 60.2, "sugars_g": 48.5, "fiber_g": 1.3, "sodium_mg": 60},
    },
    {
        "gtin": "7622201169091",
        "product_name": "Cadbury Dairy Milk Chocolate",
        "brand": "Mondelēz",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Sugar", "Cocoa Butter", "Cocoa Mass", "Skimmed Milk Powder", "Whey Powder", "Full Cream Milk Powder", "Emulsifiers (442, 476)"],
        "nutrition_per_100g": {"energy_kcal": 534, "protein_g": 7.4, "fat_g": 29.7, "saturated_fat_g": 18.1, "carbohydrates_g": 59.5, "sugars_g": 56.6, "fiber_g": 1.8, "sodium_mg": 92},
    },
    {
        "gtin": "8901826100016",
        "product_name": "Dabur Honey",
        "brand": "Dabur",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Pure Honey"],
        "nutrition_per_100g": {"energy_kcal": 304, "protein_g": 0.3, "fat_g": 0.0, "saturated_fat_g": 0, "carbohydrates_g": 82.4, "sugars_g": 80.0, "fiber_g": 0.2, "sodium_mg": 4},
    },
    {
        "gtin": "8901491100108",
        "product_name": "7UP Nimbooz Masala Soda",
        "brand": "PepsiCo",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Carbonated Water", "Sugar", "Lemon Juice", "Salt", "Cumin", "INS 211", "INS 330"],
        "nutrition_per_100g": {"energy_kcal": 42, "protein_g": 0, "fat_g": 0, "saturated_fat_g": 0, "carbohydrates_g": 10.5, "sugars_g": 10.5, "fiber_g": 0, "sodium_mg": 52},
    },
    {
        "gtin": "8906042711014",
        "product_name": "Patanjali Aloe Vera Juice",
        "brand": "Patanjali",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Aloe Vera Gel 98%", "Natural Preservatives", "Vitamin C"],
        "nutrition_per_100g": {"energy_kcal": 20, "protein_g": 0.1, "fat_g": 0.0, "saturated_fat_g": 0, "carbohydrates_g": 4.6, "sugars_g": 3.2, "fiber_g": 0.3, "sodium_mg": 12},
    },
    {
        "gtin": "8901764004404",
        "product_name": "Parle Monaco Smart Chips",
        "brand": "Parle",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Wheat Flour", "Edible Vegetable Oil", "Salt", "Sugar", "Yeast Extract", "INS 627", "INS 631"],
        "nutrition_per_100g": {"energy_kcal": 502, "protein_g": 8.2, "fat_g": 19.5, "saturated_fat_g": 9.0, "carbohydrates_g": 72.0, "sugars_g": 3.0, "fiber_g": 1.8, "sodium_mg": 760},
    },
    {
        "gtin": "8901058505476",
        "product_name": "Munch Chocolate Wafer Bar",
        "brand": "Nestlé",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Sugar", "Edible Vegetable Oil", "Wheat Flour", "Cocoa Powder", "Skim Milk Powder", "Emulsifiers", "INS 322", "Vanillin"],
        "nutrition_per_100g": {"energy_kcal": 525, "protein_g": 5.8, "fat_g": 27.1, "saturated_fat_g": 14.5, "carbohydrates_g": 65.5, "sugars_g": 42.3, "fiber_g": 1.5, "sodium_mg": 80},
    },
    {
        "gtin": "8901826400043",
        "product_name": "Dabur Real Mango Juice",
        "brand": "Dabur",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Water", "Mango Pulp (25%)", "Sugar", "Citric Acid (INS 330)", "Vitamin C", "Preservative INS 211"],
        "nutrition_per_100g": {"energy_kcal": 72, "protein_g": 0.2, "fat_g": 0.1, "saturated_fat_g": 0, "carbohydrates_g": 17.5, "sugars_g": 16.8, "fiber_g": 0.3, "sodium_mg": 15},
    },
    {
        "gtin": "8904109601200",
        "product_name": "Too Yumm! Multigrain Chips",
        "brand": "RP-SG Group",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Rice Flour", "Whole Wheat", "Lentil Flour", "Oat Flour", "Chickpea Flour", "Salt", "Spices", "Sunflower Oil"],
        "nutrition_per_100g": {"energy_kcal": 380, "protein_g": 8.5, "fat_g": 11.0, "saturated_fat_g": 4.2, "carbohydrates_g": 62.0, "sugars_g": 2.5, "fiber_g": 5.0, "sodium_mg": 380},
    },
    {
        "gtin": "8901058002085",
        "product_name": "Nestlé Milo Energy Drink",
        "brand": "Nestlé",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Malt Extract", "Sugar", "Cocoa Powder", "Skim Milk Powder", "Vitamins", "Minerals"],
        "nutrition_per_100g": {"energy_kcal": 385, "protein_g": 14.0, "fat_g": 4.8, "saturated_fat_g": 2.8, "carbohydrates_g": 69.0, "sugars_g": 42.5, "fiber_g": 2.0, "sodium_mg": 180},
    },
    {
        "gtin": "5000159484695",
        "product_name": "McVitie's Digestive Biscuits",
        "brand": "McVitie's",
        "country": "GB",
        "source": "seeded",
        "ingredients": ["Wholemeal Wheat Flour", "Vegetable Oil", "Sugar", "Oatmeal", "Invert Sugar Syrup", "Salt", "Sodium Bicarbonate", "Ammonium Bicarbonate"],
        "nutrition_per_100g": {"energy_kcal": 476, "protein_g": 6.9, "fat_g": 20.9, "saturated_fat_g": 9.3, "carbohydrates_g": 63.9, "sugars_g": 16.6, "fiber_g": 3.7, "sodium_mg": 400},
    },
    {
        "gtin": "8901262173034",
        "product_name": "MTR Ready to Eat Palak Paneer",
        "brand": "MTR Foods",
        "country": "IN",
        "source": "seeded",
        "ingredients": ["Spinach (55%)", "Cottage Cheese / Paneer (16%)", "Edible Vegetable Oil", "Tomato", "Onion", "Salt", "Spices", "Water"],
        "nutrition_per_100g": {"energy_kcal": 95, "protein_g": 4.2, "fat_g": 5.8, "saturated_fat_g": 2.1, "carbohydrates_g": 7.1, "sugars_g": 1.9, "fiber_g": 1.5, "sodium_mg": 310},
    },
]

BARCODES_DISPLAY = [
    ("8901058852424", "Maggi 2-Minute Noodles Masala", "Nestlé"),
    ("8901491502230", "Lays Classic Salted Chips", "PepsiCo"),
    ("8901030706615", "Parle-G Original Gluco Biscuits", "Parle"),
    ("8901063151849", "Britannia Good Day Butter Cookies", "Britannia"),
    ("8906001200014", "Amul Pure Butter", "Amul"),
    ("8901764001052", "Hide & Seek Chocolate Chip Biscuits", "Parle"),
    ("8902102901013", "Kurkure Masala Munch", "PepsiCo"),
    ("8800025000290", "Nescafé Classic Instant Coffee", "Nestlé"),
    ("8901058501898", "KitKat 4 Finger Chocolate", "Nestlé"),
    ("7622201169091", "Cadbury Dairy Milk Chocolate", "Mondelēz"),
    ("8901826100016", "Dabur Pure Honey", "Dabur"),
    ("8901491100108", "7UP Nimbooz Masala Soda", "PepsiCo"),
    ("8906042711014", "Patanjali Aloe Vera Juice", "Patanjali"),
    ("8901764004404", "Parle Monaco Smart Chips", "Parle"),
    ("8901058505476", "Munch Chocolate Wafer Bar", "Nestlé"),
    ("8901826400043", "Dabur Real Mango Juice", "Dabur"),
    ("8904109601200", "Too Yumm Multigrain Chips", "RP-SG Group"),
    ("8901058002085", "Nestlé Milo Energy Drink", "Nestlé"),
    ("5000159484695", "McVities Digestive Biscuits", "McVitie's"),
    ("8901262173034", "MTR Ready to Eat Palak Paneer", "MTR Foods"),
]


def seed_database():
    """Seed the nutrition_cache table in the SQLite database with 20 test products."""
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found at {DB_PATH}. Run the backend once first to create it.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure the nutrition_cache table exists with correct schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_cache (
            gtin TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

    inserted = 0
    skipped = 0
    for product in TEST_PRODUCTS:
        gtin = product["gtin"]
        try:
            conn.execute(
                "INSERT OR REPLACE INTO nutrition_cache (gtin, data) VALUES (?, ?)",
                (gtin, json.dumps(product))
            )
            inserted += 1
        except Exception as e:
            print(f"  [SKIP] {gtin}: {e}")
            skipped += 1

    conn.commit()
    conn.close()

    print(f"\n✅ Seeded {inserted} products into nutrition_cache ({skipped} skipped)")
    print("\n🔍 BARCODE LIST — These 20 barcodes will give guaranteed scan results:\n")
    print(f"{'#':<4} {'BARCODE':<16} {'PRODUCT':<42} {'BRAND'}")
    print("-" * 80)
    for i, (barcode, name, brand) in enumerate(BARCODES_DISPLAY, 1):
        print(f"{i:<4} {barcode:<16} {name:<42} {brand}")

    print("\n💡 Test these barcodes by:")
    print("   1. Running the backend: python run_local.py")
    print("   2. Opening the frontend and scanning a product barcode image")
    print("   3. Or testing via API: POST /api/scan with an image containing the barcode")

    # Also save to a JSON file for frontend reference
    out_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "test_barcodes.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "description": "20 verified test barcodes for the Nutri Scanner application",
            "count": len(BARCODES_DISPLAY),
            "barcodes": [
                {"index": i, "barcode": b, "product": p, "brand": br}
                for i, (b, p, br) in enumerate(BARCODES_DISPLAY, 1)
            ],
            "full_data": TEST_PRODUCTS
        }, f, indent=2)
    print(f"\n📄 Barcode list also saved to: dataset/test_barcodes.json")


if __name__ == "__main__":
    seed_database()
