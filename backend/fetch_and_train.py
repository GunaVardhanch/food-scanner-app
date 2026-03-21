"""
fetch_and_train.py
══════════════════
Fetches Indian food products from Open Food Facts, trains the XGBoost
health-score model, and seeds the local DB.

Key design decisions
────────────────────
1. Training TARGET uses OFF's own nutriscore_grade field (A–E) as ground
   truth — this is computed by OFF from real lab data using the official EU
   algorithm, so it's more reliable than re-deriving it ourselves.
   Grade → score mapping: A=9.0, B=7.5, C=5.5, D=3.5, E=1.5
   Additive impact is added on top as a fine-tune signal.

2. Target count bumped to 1000 — XGBoost needs at least 800–1000 samples
   to generalise; 200 was too small and caused overfitting.

3. Light Gaussian noise is injected into training features to simulate
   OCR measurement variance (e.g. "12g" read as "11.8" or "12.3").
   This makes the model more robust to noisy label-scan inputs.

4. calculate_nutriscore() is imported from health_scoring (now exists).

Run:
    python fetch_and_train.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional

import numpy as np
import requests
import xgboost as xgb

sys.path.insert(0, os.path.dirname(__file__))
from app.config import HEALTH_SCORE_MODEL_PATH, MODEL_DIR
from app.services.additives_expert import AdditivesExpert
from app.services.health_scoring import calculate_nutriscore, build_feature_vector, FEATURE_NAMES
from app.services.nutrition_db import _normalise_off_product, _fetch_from_off

DB_PATH = os.path.join(os.path.dirname(__file__), "food_scanner.db")

# ── OFF India search config ───────────────────────────────────────────────────
_OFF_SEARCH = "https://world.openfoodfacts.org/api/v2/search"
_OFF_INDIA  = "https://in.openfoodfacts.org/api/v2/search"
_USER_AGENT = "NutriScannerTrainer/2.0 (India; training pipeline)"
_TIMEOUT    = 15

_INDIA_CATEGORIES = [
    "biscuits-and-cakes",
    "snacks",
    "beverages",
    "instant-noodles",
    "dairy",
    "breakfast-cereals",
    "chocolates",
    "chips-and-crisps",
    "juices",
    "sauces-and-condiments",
    "breads",
    "frozen-foods",
    "ready-meals",
    "spices",
    "oils",
]

_FALLBACK_GTINS = [
    "8906042711014", "8901262173034", "8904109601200", "8901826100016",
    "8800025000290", "5000159484695", "8901058002085", "8901826400043",
    "8901491100108", "8901030706615", "8901063151849", "8906001200014",
    "8901058852424", "8901491502230", "8901764004404", "8902102901013",
    "8901058501898", "7622201169091", "8901058505476", "8901764001052",
    "5449000000996", "4008400404127", "8901030712395", "8901058863642",
    "8901491101518", "8901491101839", "8901764002622", "8902102300052",
    "8901058001674", "8901063100018", "8901719126987", "8906003980015",
]

# Grade → numeric score midpoint
_GRADE_SCORE = {"A": 9.0, "B": 7.5, "C": 5.5, "D": 3.5, "E": 1.5}


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Fetch products from OFF India
# ─────────────────────────────────────────────────────────────────────────────

def fetch_india_products(target_count: int = 1000) -> List[Dict[str, Any]]:
    """
    Pull Indian food products from OFF using category search.
    Falls back to GTIN list if search fails.
    Returns normalised product dicts.
    """
    print(f"\n[1/4] Fetching up to {target_count} Indian products from Open Food Facts…")
    products: List[Dict] = []
    seen_gtins: set = set()

    per_page = 50
    fields = (
        "code,product_name,product_name_en,product_name_hi,"
        "brands,countries_tags,ingredients_text,nutriments,"
        "serving_size,nutrition_grades,nutriscore_grade,"
        "additives_tags,nova_group"
    )

    for category in _INDIA_CATEGORIES:
        if len(products) >= target_count:
            break

        # Try multiple pages per category to get more samples
        for page in range(1, 5):
            if len(products) >= target_count:
                break

            for base_url in [_OFF_INDIA, _OFF_SEARCH]:
                try:
                    params = {
                        "categories_tags": category,
                        "countries_tags":  "en:india",
                        "fields":          fields,
                        "page_size":       per_page,
                        "page":            page,
                        "sort_by":         "unique_scans_n",
                        "json":            1,
                    }
                    resp = requests.get(
                        base_url, params=params,
                        headers={"User-Agent": _USER_AGENT},
                        timeout=_TIMEOUT,
                    )
                    if resp.status_code != 200:
                        continue

                    items = resp.json().get("products", [])
                    if not items:
                        break  # no more pages

                    added = 0
                    for item in items:
                        gtin = item.get("code", "")
                        if not gtin or gtin in seen_gtins:
                            continue
                        norm = _normalise_off_product(gtin, item)
                        if not norm or not norm.get("nutrition_per_100g"):
                            continue
                        n = norm["nutrition_per_100g"]
                        if not any(n.get(k) for k in ("energy_kcal", "fat_g", "sugars_g", "protein_g")):
                            continue

                        # Attach OFF's nutriscore_grade — this is our primary training target
                        off_grade = (item.get("nutriscore_grade") or "").upper()
                        norm["off_nutriscore_grade"] = off_grade if off_grade in "ABCDE" else None
                        norm["nova_group"] = item.get("nova_group")
                        seen_gtins.add(gtin)
                        products.append(norm)
                        added += 1

                    if added:
                        print(f"   {category} p{page}: +{added} (total {len(products)})")
                        time.sleep(0.3)
                    break  # got results from this URL

                except requests.exceptions.Timeout:
                    print(f"   {category} p{page}: timeout, trying next…")
                except Exception as exc:
                    print(f"   {category} p{page}: error ({exc})")

    # GTIN fallback
    if len(products) < 30:
        print(f"   Search returned only {len(products)} — using GTIN fallback…")
        for gtin in _FALLBACK_GTINS:
            if gtin in seen_gtins:
                continue
            try:
                norm = _fetch_from_off(gtin)
                if norm and norm.get("nutrition_per_100g"):
                    norm["off_nutriscore_grade"] = None
                    norm["nova_group"] = None
                    seen_gtins.add(gtin)
                    products.append(norm)
                    time.sleep(0.4)
            except Exception:
                pass

    print(f"   Fetched {len(products)} valid products total.")
    return products[:target_count]


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Compute training targets
# ─────────────────────────────────────────────────────────────────────────────

def enrich_products(products: List[Dict]) -> List[Dict]:
    """
    For each product compute the training target score:

    Priority:
      1. Use OFF's nutriscore_grade if available — it's computed from real
         lab data using the official EU algorithm, so it's the best signal.
      2. Fall back to our calculate_nutriscore() if OFF grade is missing.

    Additive impact is added as a fine-tune delta on top of the grade score.
    """
    print(f"\n[2/4] Computing training targets for {len(products)} products…")
    expert = AdditivesExpert()
    enriched = []
    off_grade_used = 0
    our_grade_used = 0

    for p in products:
        n100     = p.get("nutrition_per_100g", {})
        ing_text = ", ".join(p.get("ingredients", []))

        # Additive analysis
        detected, additive_impact = expert.analyze_text(ing_text)
        risk_summary = expert.get_risk_summary(detected)
        add_feats = getattr(expert, "last_additive_features", {
            "additive_count": len(detected), "has_critical_additive": 0
        })

        # ── Determine grade ───────────────────────────────────────────────
        off_grade = p.get("off_nutriscore_grade")
        if off_grade and off_grade in _GRADE_SCORE:
            # Use OFF's grade as ground truth
            grade     = off_grade
            ns_result = calculate_nutriscore(n100)  # still compute for points
            ns_points = ns_result["nutriscore_points"]
            off_grade_used += 1
        else:
            # Fall back to our algorithm
            ns_result = calculate_nutriscore(n100)
            grade     = ns_result["nutriscore_grade"]
            ns_points = ns_result["nutriscore_points"]
            our_grade_used += 1

        # Target: grade midpoint + small fine-tune from raw points + additive impact
        base   = _GRADE_SCORE[grade]
        fine   = -ns_points * 0.04   # small nudge within the grade band
        target = round(max(0.5, min(10.0, base + fine + additive_impact)), 1)

        enriched.append({
            **p,
            "nutriscore_grade":   grade,
            "nutriscore_points":  ns_points,
            "target_score":       target,
            "additive_impact":    additive_impact,
            "additive_features":  add_feats,
            "detected_additives": detected,
            "risk_summary":       risk_summary,
        })

    print(f"   Grade source: OFF={off_grade_used}, ours={our_grade_used}")
    print(f"   Grade distribution: {_grade_dist(enriched)}")
    return enriched


def _grade_dist(products: List[Dict]) -> Dict[str, int]:
    dist: Dict[str, int] = {}
    for p in products:
        g = p.get("nutriscore_grade", "?")
        dist[g] = dist.get(g, 0) + 1
    return dict(sorted(dist.items()))


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Build training matrix (with noise augmentation)
# ─────────────────────────────────────────────────────────────────────────────

def build_training_data(products: List[Dict], augment: bool = True) -> tuple:
    """
    Feature vector (12 features via build_feature_vector — matches inference exactly):
        sugar_g, fat_g, saturated_fat_g, carbs_g, protein_g, calories,
        fiber_g, sodium_mg, additive_impact, additive_count,
        has_critical_additive, nova_group

    augment=True: adds 2 noisy copies of each sample to simulate OCR variance.
    Noise is Gaussian with std = 3% of each feature value (clipped to >= 0).
    Columns 8–11 (additive_impact, additive_count, has_critical, nova_group)
    are left clean — they're categorical/discrete, not OCR-measured.
    """
    X_clean, y_clean = [], []

    for p in products:
        n = p["nutrition_per_100g"]
        # Build the features dict the same way routes.py does at inference time
        add_feats = p.get("additive_features", {})
        feat = {
            "sugar_g":               float(n.get("sugars_g",        0) or 0),
            "fat_g":                 float(n.get("fat_g",           0) or 0),
            "saturated_fat_g":       float(n.get("saturated_fat_g", 0) or 0),
            "carbs_g":               float(n.get("carbohydrates_g", 0) or 0),
            "protein_g":             float(n.get("protein_g",       0) or 0),
            "calories":              float(n.get("energy_kcal",     0) or 0),
            "fiber_g":               float(n.get("fiber_g",         0) or 0),
            "sodium_mg":             float(n.get("sodium_mg",       0) or 0),
            "additive_impact":       float(p.get("additive_impact", 0) or 0),
            "additive_count":        float(add_feats.get("additive_count", 0)),
            "has_critical_additive": float(add_feats.get("has_critical_additive", 0)),
            "nova_group":            p.get("nova_group"),
        }
        X_clean.append(build_feature_vector(feat))
        y_clean.append(p["target_score"])

    X = np.array(X_clean, dtype=np.float32)
    y = np.array(y_clean, dtype=np.float32)

    if augment and len(X) > 0:
        rng = np.random.default_rng(42)
        noisy_copies = []
        for _ in range(2):
            noise = rng.normal(0, 0.03, size=X.shape) * X
            # Don't perturb discrete/categorical columns (indices 8–11)
            noise[:, 8:] = 0.0
            X_noisy = np.clip(X + noise, 0.0, None).astype(np.float32)
            noisy_copies.append((X_noisy, y.copy()))

        X = np.vstack([X] + [c[0] for c in noisy_copies])
        y = np.concatenate([y] + [c[1] for c in noisy_copies])
        print(f"   Augmented: {len(X_clean)} → {len(X)} samples (2x noise copies)")

    return X, y


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Train XGBoost
# ─────────────────────────────────────────────────────────────────────────────

def train_model(X: np.ndarray, y: np.ndarray) -> xgb.Booster:
    print(f"\n[3/4] Training XGBoost on {len(X)} samples…")
    dtrain = xgb.DMatrix(X, label=y, feature_names=FEATURE_NAMES)

    if len(X) >= 50:
        split        = int(len(X) * 0.85)
        dtrain_main  = xgb.DMatrix(X[:split], label=y[:split], feature_names=FEATURE_NAMES)
        dval         = xgb.DMatrix(X[split:], label=y[split:], feature_names=FEATURE_NAMES)
        evals        = [(dtrain_main, "train"), (dval, "val")]
        early_stop   = 40
    else:
        dtrain_main  = dtrain
        evals        = [(dtrain, "train")]
        early_stop   = None

    params = {
        "objective":        "reg:squarederror",
        "eval_metric":      "rmse",
        "max_depth":        5,
        "eta":              0.05,
        "subsample":        0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 2,
        "reg_alpha":        0.1,
        "reg_lambda":       1.5,
        "seed":             42,
    }

    callbacks = []
    if early_stop:
        callbacks.append(
            xgb.callback.EarlyStopping(rounds=early_stop, metric_name="rmse", save_best=True)
        )

    model = xgb.train(
        params, dtrain_main,
        num_boost_round=800,
        evals=evals,
        verbose_eval=100,
        callbacks=callbacks if callbacks else None,
    )
    return model


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Seed database
# ─────────────────────────────────────────────────────────────────────────────

def seed_database(products: List[Dict]) -> None:
    print(f"\n[4/4] Seeding {len(products)} products into nutrition_cache…")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_cache (
            gtin       TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

    inserted = 0
    for p in products:
        record = {
            "gtin":                  p["gtin"],
            "product_name":          p.get("product_name", "Unknown"),
            "brand":                 p.get("brand"),
            "country":               p.get("country", "IN"),
            "source":                "off_india_fetched",
            "nutriscore_grade":      p.get("nutriscore_grade"),
            "nova_group":            p.get("nova_group"),
            "ingredients":           p.get("ingredients", []),
            "nutrition_per_100g":    p.get("nutrition_per_100g", {}),
            "nutrition_per_serving": p.get("nutrition_per_serving", {}),
        }
        conn.execute(
            "INSERT OR REPLACE INTO nutrition_cache (gtin, data) VALUES (?, ?)",
            (p["gtin"], json.dumps(record))
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"   Seeded {inserted} products.")


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate(products: List[Dict], model: xgb.Booster) -> None:
    # Validate on clean data only (no augmentation)
    X, y = build_training_data(products, augment=False)
    dmat  = xgb.DMatrix(X, feature_names=FEATURE_NAMES)
    preds = np.clip(model.predict(dmat), 0.5, 10.0)

    rmse = float(np.sqrt(np.mean((preds - y) ** 2)))

    grade_correct = sum(
        1 for pred, target in zip(preds, y)
        if (
            ("GREEN"  if pred   >= 7.0 else ("YELLOW" if pred   >= 4.0 else "RED"))
            ==
            ("GREEN"  if target >= 7.0 else ("YELLOW" if target >= 4.0 else "RED"))
        )
    )
    acc = grade_correct / len(y) * 100
    print(f"\n   Validation — RMSE: {rmse:.3f} | Grade accuracy: {acc:.1f}% ({grade_correct}/{len(y)})")

    scores = model.get_score(importance_type="gain")
    top    = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    print("   Top features by gain:", ", ".join(f"{k}={v:.1f}" for k, v in top))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  NutriScanner — OFF India Fetch & Train")
    print("  Target: 1000 products | Noise augmentation: ON")
    print("  Training target: OFF nutriscore_grade (ground truth)")
    print("=" * 65)

    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] {DB_PATH} not found.")
        print("  Run 'python run_local.py' once first to create the database.")
        sys.exit(1)

    products = fetch_india_products(target_count=1000)
    if len(products) < 10:
        print("Not enough products fetched. Check your internet connection.")
        sys.exit(1)

    enriched = enrich_products(products)

    X, y = build_training_data(enriched, augment=True)
    print(f"\n   Training matrix: {X.shape} | score range [{y.min():.1f}, {y.max():.1f}]")

    model = train_model(X, y)
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ── Model versioning: only replace active model if new RMSE is better ────
    X_clean, y_clean = build_training_data(enriched, augment=False)
    dmat_val  = xgb.DMatrix(X_clean, feature_names=FEATURE_NAMES)
    preds_new = np.clip(model.predict(dmat_val), 0.5, 10.0)
    new_rmse  = float(np.sqrt(np.mean((preds_new - y_clean) ** 2)))
    print(f"\n   New model RMSE (clean data): {new_rmse:.4f}")

    # Check existing model RMSE if one exists
    promote = True
    if os.path.exists(HEALTH_SCORE_MODEL_PATH):
        try:
            old_model = xgb.Booster()
            old_model.load_model(HEALTH_SCORE_MODEL_PATH)
            preds_old = np.clip(old_model.predict(dmat_val), 0.5, 10.0)
            old_rmse  = float(np.sqrt(np.mean((preds_old - y_clean) ** 2)))
            print(f"   Existing model RMSE:        {old_rmse:.4f}")
            if new_rmse >= old_rmse:
                print(f"   ⚠ New model is NOT better — keeping existing model.")
                promote = False
        except Exception as e:
            print(f"   Could not load existing model for comparison ({e}) — promoting new model.")

    # Save versioned copy regardless
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_path = os.path.join(MODEL_DIR, f"health_score_{ts}_rmse{new_rmse:.3f}.ubj")
    model.save_model(versioned_path)
    print(f"   Versioned model saved → {versioned_path}")

    if promote:
        model.save_model(HEALTH_SCORE_MODEL_PATH)
        print(f"   Active model updated  → {HEALTH_SCORE_MODEL_PATH}")
    else:
        print(f"   Active model unchanged → {HEALTH_SCORE_MODEL_PATH}")

    seed_database(enriched)
    validate(enriched, model)

    print("\n" + "=" * 65)
    print("  Done. Restart the backend to load the new model.")
    print("  python run_local.py")
    print("=" * 65)


if __name__ == "__main__":
    main()
