import os
import xgboost as xgb
import numpy as np
import json

from app.config import HEALTH_SCORE_MODEL_PATH

class HealthScoreEnsemble:
    def __init__(self):
        self.model = None
        if os.path.exists(HEALTH_SCORE_MODEL_PATH):
            try:
                self.model = xgb.Booster()
                self.model.load_model(HEALTH_SCORE_MODEL_PATH)
                print(f"HealthScoreEnsemble: loaded model from {HEALTH_SCORE_MODEL_PATH}")
            except Exception as e:
                print(f"HealthScoreEnsemble: failed to load model ({e}), using heuristic fallback.")
                self.model = None
        else:
            print("HealthScoreEnsemble: no trained model found, using heuristic fallback.")

    def calculate_raw_score(self, features):
        """
        Compute a health score 0.5–10.0.
        Features dict keys: sugar_g, fat_g, carbs_g, protein_g, calories, additive_impact.
        Values may be None if OCR/NER could not extract them — handled gracefully.
        """
        if self.model is not None:
            sugar = float(features.get("sugar_g") or 0.0)
            fat = float(features.get("fat_g") or 0.0)
            carbs = float(features.get("carbs_g") or 0.0)
            protein = float(features.get("protein_g") or 0.0)
            calories = float(features.get("calories") or 0.0)
            additive_impact = float(features.get("additive_impact") or 0.0)

            vec = np.array([[sugar, fat, carbs, protein, calories, additive_impact]], dtype=np.float32)
            dmat = xgb.DMatrix(
                vec,
                feature_names=["sugar_g", "fat_g", "carbs_g", "protein_g", "calories", "additive_impact"],
            )
            score = float(self.model.predict(dmat)[0])
            return max(0.5, min(10.0, score))

        # ── Heuristic Fallback ────────────────────────────────────────────────
        # Start perfect and deduct. None values = nutrient unknown; skip that penalty.
        # References: WHO free sugar limit 25 g/day, ICMR 2000 kcal/day, fat 65 g/day.
        score = 10.0

        # Sugar penalty (max –3.5 pts)
        sugar_g = features.get("sugar_g")
        if sugar_g is not None:
            sugar_pct = sugar_g / 25.0
            score -= min(sugar_pct * 3.5, 3.5)

        # Fat penalty (max –2.0 pts)
        fat_g = features.get("fat_g")
        if fat_g is not None:
            fat_pct = fat_g / 65.0
            score -= min(fat_pct * 2.0, 2.0)

        # Calorie penalty — only kicks in above 25 % of daily intake per serving (max –1.5 pts)
        calories = features.get("calories")
        if calories is not None:
            cal_pct = calories / 2000.0
            if cal_pct > 0.25:
                score -= min((cal_pct - 0.25) * 4.0, 1.5)

        # Carb penalty — only for very high values >60 g per serving (max –1.0 pts)
        carbs_g = features.get("carbs_g")
        if carbs_g is not None and carbs_g > 60:
            score -= min((carbs_g - 60) / 40.0, 1.0)

        # Additive impact (already negative for harmful additives, from AdditivesExpert)
        additive_impact = features.get("additive_impact") or 0
        score += additive_impact

        # Protein bonus (capped at +1.0 pts)
        protein_g = features.get("protein_g")
        if protein_g is not None:
            score += min(protein_g / 10.0, 1.0)

        return round(max(0.5, min(10.0, score)), 1)

    def predict(self, feature_vector):
        if self.model:
            dmat = xgb.DMatrix([feature_vector])
            return self.model.predict(dmat)[0]
        return 7.5

if __name__ == "__main__":
    ensemble = HealthScoreEnsemble()
    bad = {'sugar_g': 38, 'fat_g': 20, 'carbs_g': 75, 'protein_g': 2, 'calories': 550, 'additive_impact': -3.5}
    print(f"Bad product score (expect ~2-4): {ensemble.calculate_raw_score(bad)}")
    good = {'sugar_g': 2, 'fat_g': 3, 'carbs_g': 20, 'protein_g': 8, 'calories': 120, 'additive_impact': 0}
    print(f"Good product score (expect ~8-10): {ensemble.calculate_raw_score(good)}")
    mid = {'sugar_g': 12, 'fat_g': 8, 'carbs_g': 40, 'protein_g': 4, 'calories': 280, 'additive_impact': -1.5}
    print(f"Mid product score (expect ~5-7): {ensemble.calculate_raw_score(mid)}")
