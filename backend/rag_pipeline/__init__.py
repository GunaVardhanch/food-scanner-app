"""
rag_pipeline/__init__.py
─────────────────────────
Public API for the RAG side pipeline module.

Usage from routes.py (or anywhere in the backend):

    from rag_pipeline import analyze_label_text

    result = analyze_label_text(
        nutrition_text="Calories 250 kcal  Protein 4g ...",
        ingredients_text="Wheat flour, salt, INS 621, INS 319 ...",
    )
    # result is a dict ready for JSON serialisation

The function is always safe to call — it catches its own exceptions and
returns a minimal error dict rather than crashing the parent endpoint.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

__version__ = "1.0.0"
__all__ = ["analyze_label_text"]


def analyze_label_text(
    nutrition_text: str = "",
    ingredients_text: str = "",
    *,
    pre_parsed_nutrition: Optional[Dict[str, Any]] = None,
    pre_parsed_ingredients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyse a food label and return structured RAG analysis.

    This is the single public entrypoint. All arguments are optional —
    pass whatever OCR text you have available.

    Args:
        nutrition_text: Raw OCR text of the nutrition panel.
        ingredients_text: Raw OCR text of the ingredients list.
        pre_parsed_nutrition: Pre-parsed nutrition dict (skips OCR parser).
        pre_parsed_ingredients: Pre-parsed ingredient list (skips OCR parser).

    Returns:
        Dict with keys:
            nutrition_summary, additive_flags, fssai_compliance,
            compliance_message, warnings, warning_details, score,
            score_grade, ingredients_detected, ultra_processed_markers_found,
            allergens_detected, healthy_alternative, pipeline_version,
            retrieval_backend, analysis_time_s
    """
    try:
        from rag_pipeline.rag_analyzer import analyze_label_text as _analyze
        return _analyze(
            nutrition_text=nutrition_text,
            ingredients_text=ingredients_text,
            pre_parsed_nutrition=pre_parsed_nutrition,
            pre_parsed_ingredients=pre_parsed_ingredients,
        )
    except Exception as exc:
        logger.error("RAG pipeline error: %s", exc, exc_info=True)
        return {
            "error": str(exc),
            "nutrition_summary": {},
            "additive_flags": [],
            "fssai_compliance": True,
            "compliance_message": "RAG pipeline encountered an error.",
            "warnings": [],
            "warning_details": [],
            "score": 5.0,
            "score_grade": "YELLOW",
            "ingredients_detected": [],
            "ultra_processed_markers_found": [],
            "allergens_detected": [],
            "healthy_alternative": None,
            "pipeline_version": __version__,
            "retrieval_backend": "none",
            "analysis_time_s": 0.0,
        }
