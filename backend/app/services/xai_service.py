"""
xai_service.py  -  Phase 2 rebuild
Real SHAP when XGBoost model is available.
Rule-based feature contributions when heuristic path is used.
Removes all hardcoded fake values.
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class XAIService:
    def __init__(self):
        self._explainer = None
        logger.info("XAIService initialised")

    def explain_score(
        self,
        model,
        features: Dict[str, Any],
        feature_names: List[str],
    ) -> Dict[str, float]:
        """
        Return per-feature impact on the health score.

        - If an XGBoost Booster is passed, use shap.TreeExplainer for real SHAP values.
        - Otherwise compute rule-based contributions from the actual feature values
          (same weights used in health_scoring NutriScore path).

        Returns a dict mapping human-readable label -> impact (positive = good, negative = bad).
        """
        if model is not None:
            return self._shap_explain(model, features, feature_names)
        return self._rule_based_explain(features)

    # ── Real SHAP ─────────────────────────────────────────────────────────────

    def _shap_explain(
        self, model, features: Dict[str, Any], feature_names: List[str]
    ) -> Dict[str, float]:
        try:
            import shap
            import numpy as np

            if self._explainer is None:
                self._explainer = shap.TreeExplainer(model)

            vec = np.array([[
                float(features.get("sugar_g")   or 0.0),
                float(features.get("fat_g")     or 0.0),
                float(features.get("carbs_g")   or 0.0),
                float(features.get("protein_g") or 0.0),
                float(features.get("calories")  or 0.0),
                float(features.get("additive_impact") or 0.0),
            ]], dtype=np.float32)

            shap_values = self._explainer.shap_values(vec)[0]
            labels = ["Sugar", "Fat", "Carbs", "Protein", "Calories", "Additives"]
            return {
                label: round(float(sv), 3)
                for label, sv in zip(labels, shap_values)
            }
        except Exception as exc:
            logger.warning("SHAP explain failed (%s), falling back to rule-based", exc)
            return self._rule_based_explain(features)

    # ── Rule-based contributions ──────────────────────────────────────────────

    def _rule_based_explain(self, features: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute approximate per-feature contributions using the same
        NutriScore negative/positive point logic as health_scoring.py.
        Each contribution is scaled to a -5 to +5 range for UI display.
        """
        from app.services.health_scoring import _pts, _SUGAR, _SAT_FAT, _ENERGY_KJ, _SODIUM, _FIBER, _PROTEIN

        def _fv(key, *aliases) -> float:
            for k in (key, *aliases):
                v = features.get(k)
                if v is not None:
                    try:
                        return float(v)
                    except Exception:
                        pass
            return 0.0

        energy_kj  = _fv("calories", "energy_kcal") * 4.184
        sat_fat    = _fv("saturated_fat_g")
        sugar      = _fv("sugar_g", "sugars_g")
        sodium     = _fv("sodium_mg")
        fiber      = _fv("fiber_g")
        protein    = _fv("protein_g")
        additives  = _fv("additive_impact")

        # Max negative points per category = 10; scale to -5
        scale_neg = -5.0 / 10.0
        scale_pos =  5.0 / 5.0   # max positive points = 5

        contributions: Dict[str, float] = {}

        e_pts = _pts(energy_kj, _ENERGY_KJ)
        if e_pts > 0:
            contributions["Calories"] = round(e_pts * scale_neg, 2)

        sf_pts = _pts(sat_fat, _SAT_FAT)
        if sf_pts > 0:
            contributions["Saturated Fat"] = round(sf_pts * scale_neg, 2)

        s_pts = _pts(sugar, _SUGAR)
        if s_pts > 0:
            contributions["Sugar"] = round(s_pts * scale_neg, 2)

        na_pts = _pts(sodium, _SODIUM)
        if na_pts > 0:
            contributions["Sodium"] = round(na_pts * scale_neg, 2)

        f_pts = _pts(fiber, _FIBER)
        if f_pts > 0:
            contributions["Fiber"] = round(f_pts * scale_pos, 2)

        p_pts = _pts(protein, _PROTEIN)
        if p_pts > 0:
            contributions["Protein"] = round(p_pts * scale_pos, 2)

        if additives != 0:
            contributions["Additives"] = round(additives, 2)

        # If nothing was extractable, return an empty dict (not fake values)
        return contributions

    def get_gradcam_heatmap(self, model, image):
        """Placeholder — Grad-CAM requires a CNN model, not XGBoost."""
        import cv2
        import numpy as np
        heatmap = np.zeros(image.shape[:2], dtype=np.float32)
        return cv2.applyColorMap(np.uint8(255 * heatmap), cv2.COLORMAP_JET)


if __name__ == "__main__":
    xai = XAIService()
    feat = {"sugar_g": 18, "fat_g": 15, "saturated_fat_g": 6, "calories": 480,
            "sodium_mg": 300, "fiber_g": 2, "protein_g": 6, "additive_impact": -1.5}
    print("Rule-based XAI:", xai.explain_score(None, feat, []))
