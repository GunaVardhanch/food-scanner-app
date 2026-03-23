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

# NOVA group → score penalty (tightened — ultra-processed gets a hard hit)
_NOVA_PENALTY = {1: 0.0, 2: -0.3, 3: -0.8, 4: -1.8}

# NutriScore grade → max allowed health score (cross-check ceiling)
# Prevents a high-fiber ultra-processed food from sneaking into GREEN
_NUTRISCORE_CEILING = {"A": 10.0, "B": 9.0, "C": 7.4, "D": 5.0, "E": 3.5}

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
        Uses calibrated heuristic + NutriScore ceiling.
        XGBoost model is bypassed — the trained model produced unreliable
        scores (e.g. Apple=3.7/RED) due to noisy training labels.
        """
        return self._heuristic_score(features)

    def _apply_nutriscore_ceiling(self, score: float, features: dict) -> float:
        """Cap score using official NutriScore so C/D/E products can't be GREEN."""
        ns = calculate_nutriscore({
            "energy_kcal":     features.get("calories"),
            "saturated_fat_g": float(features.get("saturated_fat_g") or 0),
            "sugars_g":        float(features.get("sugar_g") or 0),
            "sodium_mg":       float(features.get("sodium_mg") or 0),
            "fiber_g":         float(features.get("fiber_g") or 0),
            "protein_g":       float(features.get("protein_g") or 0),
        })
        ceiling = _NUTRISCORE_CEILING.get(ns["nutriscore_grade"], 7.4)
        return max(0.5, min(ceiling, score))

    def _heuristic_score(self, features: dict) -> float:
        """
        Calibrated heuristic anchored to NutriScore points.
        Uses official NutriScore as the base, then adjusts for additives and NOVA.
        This avoids penalising natural sugars in whole foods (e.g. fruit).
        """
        sugar_g         = float(features.get("sugar_g")         or 0)
        fat_g           = float(features.get("fat_g")           or 0)
        protein_g       = float(features.get("protein_g")       or 0)
        fiber_g         = float(features.get("fiber_g")         or 0)
        sodium_mg       = float(features.get("sodium_mg")       or 0)
        sat_fat         = float(features.get("saturated_fat_g") or 0)
        calories        = float(features.get("calories")        or 0)
        additive_impact = float(features.get("additive_impact") or 0)
        has_critical    = float(features.get("has_critical_additive") or 0)
        additive_count  = float(features.get("additive_count")  or 0)

        nova_raw = features.get("nova_group")
        try:
            nova = int(nova_raw) if nova_raw is not None else 3
        except (TypeError, ValueError):
            nova = 3

        # ── Step 1: Base score from official NutriScore points ─────────────
        # NutriScore total ranges roughly from -15 (best) to +40 (worst).
        # We map it to a 0.5–10 scale: lower points = higher score.
        ns = calculate_nutriscore({
            "energy_kcal":     calories,
            "saturated_fat_g": sat_fat,
            "sugars_g":        sugar_g,
            "sodium_mg":       sodium_mg,
            "fiber_g":         fiber_g,
            "protein_g":       protein_g,
        })
        ns_points = ns["nutriscore_points"]  # lower is better
        # Map: -5 pts → 9.5, 0 pts → 8.0, 5 pts → 7.0, 10 pts → 6.0,
        #       18 pts → 4.5, 25 pts → 3.0, 40 pts → 1.0
        base = max(1.0, 8.0 - (ns_points * 0.18))

        # ── Step 2: Additive adjustments (not in NutriScore) ───────────────
        base -= min(additive_count * 0.15, 1.5)
        base += additive_impact          # already negative from AdditivesExpert
        if has_critical:
            base -= 2.0

        # ── Step 3: NOVA penalty ───────────────────────────────────────────
        base += _NOVA_PENALTY.get(nova, -0.8)

        # ── Step 4: NutriScore ceiling ─────────────────────────────────────
        ns_grade   = ns["nutriscore_grade"]
        ns_ceiling = _NUTRISCORE_CEILING.get(ns_grade, 7.4)
        base = min(base, ns_ceiling)

        return max(0.5, min(10.0, round(base, 2)))

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
