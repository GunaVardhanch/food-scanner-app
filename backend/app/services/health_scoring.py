"""
health_scoring.py
─────────────────
Health score computation for NutriScanner.

Feature vector (12 features — matches fetch_and_train.py exactly):
    sugar_g, fat_g, saturated_fat_g, carbs_g, protein_g, calories,
    fiber_g, sodium_mg, additive_impact, additive_count,
    has_critical_additive, nova_group

NutriScore lookup tables and calculate_nutriscore() are module-level so
xai_service.py and fetch_and_train.py can import them directly.
"""
import os
import numpy as np

try:
    import xgboost as xgb
    _XGB_AVAILABLE = True
except ImportError:
    _XGB_AVAILABLE = False

try:
    from app import config as _config
    HEALTH_SCORE_MODEL_PATH = _config.HEALTH_SCORE_MODEL_PATH
except Exception:
    HEALTH_SCORE_MODEL_PATH = ""

# ── NutriScore lookup tables ──────────────────────────────────────────────────
_ENERGY_KJ = [(3350, 10), (3015, 9), (2680, 8), (2345, 7), (2010, 6),
              (1675, 5), (1340, 4), (1005, 3), (670, 2), (335, 1)]
_SUGAR     = [(45, 10), (40, 9), (36, 8), (31, 7), (27, 6),
              (22, 5), (18, 4), (13, 3), (9, 2), (4.5, 1)]
_SAT_FAT   = [(10, 10), (9, 9), (8, 8), (7, 7), (6, 6),
              (5, 5), (4, 4), (3, 3), (2, 2), (1, 1)]
_SODIUM    = [(900, 10), (810, 9), (720, 8), (630, 7), (540, 6),
              (450, 5), (360, 4), (270, 3), (180, 2), (90, 1)]
_FIBER     = [(4.7, 5), (3.7, 4), (2.8, 3), (1.9, 2), (0.9, 1)]
_PROTEIN   = [(8, 5), (6.4, 4), (4.8, 3), (3.2, 2), (1.6, 1)]

# NOVA group → score penalty
_NOVA_PENALTY = {1: 0.0, 2: -0.2, 3: -0.5, 4: -1.0}

# Canonical feature list — shared between training and inference
FEATURE_NAMES = [
    "sugar_g", "fat_g", "saturated_fat_g", "carbs_g",
    "protein_g", "calories", "fiber_g", "sodium_mg",
    "additive_impact", "additive_count", "has_critical_additive", "nova_group",
]


def _pts(value: float, table: list) -> int:
    """Return NutriScore points for a value against a threshold table."""
    for threshold, pts in table:
        if value >= threshold:
            return pts
    return 0


def calculate_nutriscore(n100: dict) -> dict:
    """
    Compute NutriScore grade (A–E) and raw points from a nutrition_per_100g dict.
    EU/UK 2023 general food specification.
    """
    energy_kj = float(n100.get("energy_kcal") or 0) * 4.184
    sat_fat   = float(n100.get("saturated_fat_g") or 0)
    sugar     = float(n100.get("sugars_g") or n100.get("sugar_g") or 0)
    sodium    = float(n100.get("sodium_mg") or 0)
    fiber     = float(n100.get("fiber_g") or 0)
    protein   = float(n100.get("protein_g") or 0)

    neg_pts = (
        _pts(energy_kj, _ENERGY_KJ)
        + _pts(sat_fat, _SAT_FAT)
        + _pts(sugar, _SUGAR)
        + _pts(sodium, _SODIUM)
    )
    pos_pts = _pts(fiber, _FIBER) + _pts(protein, _PROTEIN)

    # Protein capped when neg_pts >= 11 and fiber < 5
    if neg_pts >= 11 and fiber < 5:
        pos_pts = _pts(fiber, _FIBER)

    total = neg_pts - pos_pts
    if total <= 0:    grade = "A"
    elif total <= 2:  grade = "B"
    elif total <= 10: grade = "C"
    elif total <= 18: grade = "D"
    else:             grade = "E"

    return {
        "nutriscore_grade":  grade,
        "nutriscore_points": total,
        "negative_points":   neg_pts,
        "positive_points":   pos_pts,
    }


def build_feature_vector(features: dict) -> list:
    """
    Build the canonical 12-feature vector from a features dict.
    Called by both fetch_and_train.py (training) and HealthScoreEnsemble
    (inference) to guarantee train/serve consistency.
    """
    nova_raw = features.get("nova_group")
    try:
        nova = float(nova_raw) if nova_raw is not None else 2.0
    except (TypeError, ValueError):
        nova = 2.0

    return [
        float(features.get("sugar_g")               or 0),
        float(features.get("fat_g")                 or 0),
        float(features.get("saturated_fat_g")       or 0),
        float(features.get("carbs_g")               or 0),
        float(features.get("protein_g")             or 0),
        float(features.get("calories")              or 0),
        float(features.get("fiber_g")               or 0),
        float(features.get("sodium_mg")             or 0),
        float(features.get("additive_impact")       or 0),
        float(features.get("additive_count")        or 0),
        float(features.get("has_critical_additive") or 0),
        nova,
    ]


class HealthScoreEnsemble:
    def __init__(self):
        self.model = None
        if _XGB_AVAILABLE and HEALTH_SCORE_MODEL_PATH and os.path.exists(HEALTH_SCORE_MODEL_PATH):
            try:
                self.model = xgb.Booster()
                self.model.load_model(HEALTH_SCORE_MODEL_PATH)
                print(f"HealthScoreEnsemble: loaded model from {HEALTH_SCORE_MODEL_PATH}")
            except Exception as e:
                print(f"HealthScoreEnsemble: model load failed ({e}), using heuristic.")
                self.model = None
        else:
            print("HealthScoreEnsemble: no model found, using heuristic fallback.")

    def calculate_raw_score(self, features: dict) -> float:
        """
        Calculate health score (0.5–10) from a features dict.

        XGBoost path: builds the full 12-feature vector via build_feature_vector(),
                      runs model.predict().
        Heuristic path: NutriScore-based formula + NOVA penalty + additive impact.
        """
        if self.model is not None and _XGB_AVAILABLE:
            try:
                vec  = np.array([build_feature_vector(features)], dtype=np.float32)
                dmat = xgb.DMatrix(vec, feature_names=FEATURE_NAMES)
                score = float(self.model.predict(dmat)[0])
                return max(0.5, min(10.0, score))
            except Exception:
                pass  # fall through to heuristic

        # ── Heuristic fallback ─────────────────────────────────────────────
        score = 8.5

        sugar_g         = float(features.get("sugar_g")         or 0)
        protein_g       = float(features.get("protein_g")       or 0)
        fiber_g         = float(features.get("fiber_g")         or 0)
        sodium_mg       = float(features.get("sodium_mg")       or 0)
        sat_fat         = float(features.get("saturated_fat_g") or 0)
        additive_impact = float(features.get("additive_impact") or 0)
        has_critical    = float(features.get("has_critical_additive") or 0)

        nova_raw = features.get("nova_group")
        try:
            nova = int(nova_raw) if nova_raw is not None else 2
        except (TypeError, ValueError):
            nova = 2

        score -= (sugar_g   / 10.0) * 1.5
        score -= (sodium_mg / 400.0) * 0.5
        score -= (sat_fat   / 5.0)  * 0.5
        score += (protein_g / 5.0)  * 0.5
        score += (fiber_g   / 3.0)  * 0.3
        score += additive_impact
        if has_critical:
            score -= 1.5
        score += _NOVA_PENALTY.get(nova, -0.3)

        return max(0.5, min(10.0, score))

    def predict(self, feature_vector) -> float:
        """Legacy predict method kept for compatibility."""
        if self.model and _XGB_AVAILABLE:
            try:
                dmat = xgb.DMatrix([feature_vector])
                return float(self.model.predict(dmat)[0])
            except Exception:
                pass
        return 7.5

    def get_nutriscore(self, features: dict) -> dict:
        score = self.calculate_raw_score(features)
        if score >= 8.0:   grade, color = "A", "#1a7a1a"
        elif score >= 6.5: grade, color = "B", "#6db33f"
        elif score >= 5.0: grade, color = "C", "#f5c518"
        elif score >= 3.5: grade, color = "D", "#e07b00"
        else:              grade, color = "E", "#d32f2f"
        return {
            "grade":       grade,
            "color":       color,
            "score_value": round(score, 1),
            "label":       f"Nutri-Score {grade}",
        }


if __name__ == "__main__":
    ensemble = HealthScoreEnsemble()
    test = {
        "sugar_g": 30, "fat_g": 15, "saturated_fat_g": 6,
        "calories": 480, "sodium_mg": 300, "fiber_g": 2, "protein_g": 6,
        "additive_impact": -1.5, "additive_count": 3,
        "has_critical_additive": 0, "nova_group": 4,
    }
    print(f"Score: {ensemble.calculate_raw_score(test)}")
    print(f"Nutriscore: {ensemble.get_nutriscore(test)}")
