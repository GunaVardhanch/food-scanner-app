import os
import xgboost as xgb
import numpy as np
import json

from src.configs.config import HEALTH_SCORE_MODEL_PATH

class HealthScoreEnsemble:
    def __init__(self):
        # Try to load a trained XGBoost model if it exists; otherwise fall back to heuristics.
        self.model = None
        if os.path.exists(HEALTH_SCORE_MODEL_PATH):
            try:
                self.model = xgb.Booster()
                self.model.load_model(HEALTH_SCORE_MODEL_PATH)
                print(f"Health Score Ensemble: loaded model from {HEALTH_SCORE_MODEL_PATH}")
            except Exception as e:
                print(f"Health Score Ensemble: failed to load model ({e}), using heuristic fallback.")
                self.model = None
        else:
            print("Health Score Ensemble: no trained model found, using heuristic fallback.")

    def calculate_raw_score(self, features):
        """
        Features: {sugar_g, additive_impact, calories, etc.}
        """
        # If a trained model is available, prefer that.
        if self.model is not None:
            sugar = float(features.get("sugar_g", 0.0))
            fat = float(features.get("fat_g", 0.0))
            carbs = float(features.get("carbs_g", 0.0))
            protein = float(features.get("protein_g", 0.0))
            calories = float(features.get("calories", 0.0))
            additive_impact = float(features.get("additive_impact", 0.0))

            vec = np.array([[sugar, fat, carbs, protein, calories, additive_impact]], dtype=np.float32)
            dmat = xgb.DMatrix(
                vec,
                feature_names=[
                    "sugar_g",
                    "fat_g",
                    "carbs_g",
                    "protein_g",
                    "calories",
                    "additive_impact",
                ],
            )
            score = float(self.model.predict(dmat)[0])
            # Clamp to 0.5–10 for UI consistency
            return max(0.5, min(10.0, score))

        # Heuristic fallback when no trained model is available.
        score = 8.5  # Start higher for clean label

        # Sugar deduction
        score -= (features.get("sugar_g", 0) / 10.0) * 1.5

        # Additive expert impact
        score += features.get("additive_impact", 0)

        # Natural protein boost (simplified)
        score += (features.get("protein_g", 0) / 5.0)

        return max(0.5, min(10.0, score))

    def predict(self, feature_vector):
        if self.model:
            dmat = xgb.DMatrix([feature_vector])
            return self.model.predict(dmat)[0]
        else:
            # Simulated outcome
            return 7.5

if __name__ == "__main__":
    ensemble = HealthScoreEnsemble()
    test_features = {'sugar_g': 30, 'additive_count': 3, 'protein_g': 2}
    print(f"Baseline Score: {ensemble.calculate_raw_score(test_features)}")
