"""
Seed script: Pre-populates the local SQLite cache with popular Indian food products.
Run once to ensure top Indian brands always work offline without hitting external APIs.
GTINs sourced from product labels and Open Food Facts India.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database.nutrition_db import nutrition_db

INDIAN_PRODUCTS = [
    {
        "gtin": "8901030860270",
        "product_name": "Parle-G Original Gluco Biscuits",
        "brand": "Parle",
        "ingredients": ["Wheat Flour", "Sugar", "Edible Vegetable Oil", "Invert Syrup",
                        "Leavening Agents", "Salt", "Milk Solids", "Dough Conditioner"],
        "nutrition": {"calories": 484, "protein": 7.0, "carbs": 75.0, "fat": 16.0,
                      "sugar": 20.0, "fiber": 1.5, "sodium": 0.4},
        "source": "seed_india"
    },
    {
        "gtin": "8901262040701",
        "product_name": "Amul Gold Full Cream Milk",
        "brand": "Amul",
        "ingredients": ["Full Cream Standardized Milk"],
        "nutrition": {"calories": 61, "protein": 3.2, "carbs": 4.7, "fat": 3.5,
                      "sugar": 4.7, "fiber": 0, "sodium": 0.05},
        "source": "seed_india"
    },
    {
        "gtin": "8902080000048",
        "product_name": "Maggi 2-Minute Noodles Masala",
        "brand": "Nestle",
        "ingredients": ["Wheat Flour", "Palm Oil", "Salt", "Spices", "Dehydrated Vegetables",
                        "Flavor Enhancers (INS 627, INS 631)", "Acidity Regulator (INS 330)"],
        "nutrition": {"calories": 361, "protein": 8.8, "carbs": 53.0, "fat": 12.6,
                      "sugar": 1.9, "fiber": 2.0, "sodium": 2.5},
        "source": "seed_india"
    },
    {
        "gtin": "8901058002770",
        "product_name": "Britannia Good Day Butter Cookies",
        "brand": "Britannia",
        "ingredients": ["Wheat Flour", "Sugar", "Edible Vegetable Oil", "Butter",
                        "Invert Syrup", "Salt", "Leavening Agents"],
        "nutrition": {"calories": 503, "protein": 6.5, "carbs": 65.0, "fat": 23.0,
                      "sugar": 22.0, "fiber": 1.0, "sodium": 0.5},
        "source": "seed_india"
    },
    {
        "gtin": "8901764100009",
        "product_name": "Haldiram's Aloo Bhujia",
        "brand": "Haldiram's",
        "ingredients": ["Besan", "Potato", "Refined Vegetable Oil", "Spices", "Salt",
                        "Citric Acid (INS 330)"],
        "nutrition": {"calories": 536, "protein": 13.0, "carbs": 53.0, "fat": 30.0,
                      "sugar": 2.0, "fiber": 5.5, "sodium": 1.1},
        "source": "seed_india"
    },
    {
        "gtin": "8901826100012",
        "product_name": "Lay's India Classic Salted Potato Chips",
        "brand": "Lay's",
        "ingredients": ["Potatoes", "Edible Vegetable Oil", "Salt"],
        "nutrition": {"calories": 536, "protein": 6.0, "carbs": 53.0, "fat": 33.0,
                      "sugar": 0.5, "fiber": 4.0, "sodium": 1.3},
        "source": "seed_india"
    },
    {
        "gtin": "8902519600012",
        "product_name": "Kurkure Masala Munch",
        "brand": "Kurkure",
        "ingredients": ["Rice Meal", "Edible Vegetable Oil", "Corn Meal", "Gram Meal",
                        "Spices & Condiments", "Salt", "Sugar", "Added Flavours"],
        "nutrition": {"calories": 533, "protein": 7.5, "carbs": 56.0, "fat": 30.0,
                      "sugar": 5.0, "fiber": 1.5, "sodium": 1.8},
        "source": "seed_india"
    },
    {
        "gtin": "8901764200213",
        "product_name": "Haldiram's Navratan Mixture",
        "brand": "Haldiram's",
        "ingredients": ["Besan", "Refined Oil", "Peanuts", "Cashews", "Spices", "Salt"],
        "nutrition": {"calories": 548, "protein": 14.0, "carbs": 50.0, "fat": 32.0,
                      "sugar": 3.5, "fiber": 4.0, "sodium": 0.9},
        "source": "seed_india"
    },
    {
        "gtin": "8901764100191",
        "product_name": "Haldiram's Sev Bhujia",
        "brand": "Haldiram's",
        "ingredients": ["Besan", "Refined Vegetable Oil", "Spices", "Salt"],
        "nutrition": {"calories": 530, "protein": 13.5, "carbs": 51.0, "fat": 31.0,
                      "sugar": 2.5, "fiber": 4.5, "sodium": 1.0},
        "source": "seed_india"
    },
    {
        "gtin": "8901058001674",
        "product_name": "Britannia Marie Gold Biscuits",
        "brand": "Britannia",
        "ingredients": ["Wheat Flour", "Sugar", "Edible Vegetable Oil", "Invert Syrup", "Salt"],
        "nutrition": {"calories": 433, "protein": 9.0, "carbs": 73.0, "fat": 11.5,
                      "sugar": 17.5, "fiber": 1.5, "sodium": 0.6},
        "source": "seed_india"
    },
    {
        "gtin": "8901063100018",
        "product_name": "Cadbury Dairy Milk Chocolate",
        "brand": "Cadbury",
        "ingredients": ["Sugar", "Cocoa Butter", "Cocoa Mass", "Milk Solids",
                        "Emulsifier (INS 442)", "Vanilla Flavouring"],
        "nutrition": {"calories": 544, "protein": 7.8, "carbs": 57.3, "fat": 29.7,
                      "sugar": 56.8, "fiber": 0.5, "sodium": 0.1},
        "source": "seed_india"
    },
    {
        "gtin": "8901719126987",
        "product_name": "Yippee Magic Masala Noodles",
        "brand": "Sunfeast",
        "ingredients": ["Wheat Flour", "Palm Oil", "Tapioca Starch", "Salt", "Spices",
                        "Flavor Enhancer (INS 627, 631)"],
        "nutrition": {"calories": 370, "protein": 8.0, "carbs": 55.0, "fat": 13.0,
                      "sugar": 2.0, "fiber": 1.8, "sodium": 2.1},
        "source": "seed_india"
    },
    {
        "gtin": "8906003980015",
        "product_name": "Paper Boat Aam Panna",
        "brand": "Paper Boat",
        "ingredients": ["Water", "Raw Mango Pulp", "Sugar", "Salt", "Spices", "Acidity Regulator"],
        "nutrition": {"calories": 48, "protein": 0.2, "carbs": 11.5, "fat": 0.1,
                      "sugar": 11.0, "fiber": 0.1, "sodium": 0.15},
        "source": "seed_india"
    },
    {
        "gtin": "8906010490015",
        "product_name": "Real Fruit Power Orange Juice",
        "brand": "Dabur",
        "ingredients": ["Orange Juice", "Water", "Sugar", "Acidity Regulator (Citric Acid)"],
        "nutrition": {"calories": 55, "protein": 0.5, "carbs": 13.0, "fat": 0.1,
                      "sugar": 12.0, "fiber": 0.1, "sodium": 0.01},
        "source": "seed_india"
    },
    {
        "gtin": "8901063121300",
        "product_name": "Bournvita Health Drink",
        "brand": "Cadbury",
        "ingredients": ["Sugar", "Wheat Flour", "Cocoa Solids", "Malt Extract",
                        "Milk Solids", "Vitamins", "Minerals"],
        "nutrition": {"calories": 388, "protein": 7.5, "carbs": 79.5, "fat": 4.5,
                      "sugar": 70.5, "fiber": 1.2, "sodium": 0.2},
        "source": "seed_india"
    },
]


def seed_all():
    print(f"Seeding {len(INDIAN_PRODUCTS)} Indian products into local cache...")
    for product in INDIAN_PRODUCTS:
        gtin = product["gtin"]
        # Only seed if not already in cache
        existing = nutrition_db._get_from_local(gtin)
        if existing:
            print(f"  [SKIP] {gtin} — {product['product_name']} (already cached)")
        else:
            nutrition_db.save_product(gtin, product, source=product.get("source", "seed_india"))
            print(f"  [SEED] {gtin} — {product['product_name']}")
    print("Seeding complete!")


if __name__ == "__main__":
    seed_all()
