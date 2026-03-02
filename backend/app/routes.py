"""
routes.py
─────────
Flask API routes for the Food Scanner backend.

Pipeline architecture
─────────────────────
PRIMARY (barcode-first)   →  POST /api/scan
    1. Decode image from base64.
    2. Barcode-only model → GTIN string.
    3. GTIN → nutrition DB / API lookup (non-ML).
    4. Return structured JSON.
    The image is NEVER sent to OCR or NLP in this flow.

LEGACY (OCR-based)        →  POST /analyze
    kept for research / debugging, not called by default frontend.
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from typing import Any, Dict, Optional

import cv2
import numpy as np
from flask import Blueprint, jsonify, request, send_from_directory

# ── Barcode-first services (primary flow) ─────────────────────────────────────
from app.services.barcode_service import extract_barcode_from_image
from app.services.nutrition_db import get_product_by_gtin

# ── Legacy OCR/NLP services (kept for research, NOT called in primary flow) ───
from app.services.ocr_pipeline import AdvancedOCRPipeline
from app.services.health_scoring import HealthScoreEnsemble  # also used in primary flow for scoring
from app.services.additives_expert import AdditivesExpert
from app.services.ner_service import NERService
from app.services.xai_service import XAIService
from app import config as _config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint("api", __name__)

# ── Lazy-init: scoring engine (used in primary /api/scan flow) ───────────────
_scoring_engine: Optional[HealthScoreEnsemble] = None


def _get_scoring_engine() -> HealthScoreEnsemble:
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = HealthScoreEnsemble()
    return _scoring_engine


# ── Lazy-init legacy services (only constructed if /analyze is called) ────────
_ocr_pipeline: Optional[AdvancedOCRPipeline] = None
_additives_expert: Optional[AdditivesExpert] = None
_ner_service: Optional[NERService] = None
_xai_service: Optional[XAIService] = None


def _get_legacy_services():
    global _ocr_pipeline, _additives_expert, _ner_service, _xai_service
    if _ocr_pipeline is None:
        logger.info("Initialising legacy OCR/NLP services (first call to /analyze)…")
        _ocr_pipeline    = AdvancedOCRPipeline()
        _additives_expert = AdditivesExpert()
        _ner_service     = NERService()
        _xai_service     = XAIService()
    return _ocr_pipeline, _get_scoring_engine(), _additives_expert, _ner_service, _xai_service


# ─────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _decode_base64_image(b64_string: str) -> Optional[np.ndarray]:
    """
    Decode a base64-encoded image string (with or without data-URI header)
    to a BGR numpy array suitable for cv2 operations.

    Returns None on any error.
    """
    try:
        if "," in b64_string:
            _, b64_string = b64_string.split(",", 1)
        raw_bytes = base64.b64decode(b64_string)
        arr = np.frombuffer(raw_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception as exc:
        logger.warning("Image decode failed: %s", exc)
        return None


def _save_temp_image(b64_string: str, path: str) -> bool:
    """Save a base64 image string to a file path. Returns True on success."""
    try:
        if "," in b64_string:
            _, b64_string = b64_string.split(",", 1)
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64_string))
        return True
    except Exception as exc:
        logger.warning("Failed to save temp image: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@bp.route("/", methods=["GET"])
@bp.route("/api/health", methods=["GET"])
def read_root():
    return jsonify({"status": "ok", "message": "Food Scanner API is running!"})


# ─────────────────────────────────────────────────────────────────────────────
# PRIMARY ENDPOINT — barcode-first pipeline
# ─────────────────────────────────────────────────────────────────────────────

@bp.route("/api/scan", methods=["POST"])
def scan():
    """
    Barcode-first product scan.

    Request body (JSON)
    -------------------
    {
        "image": "<base64-encoded image of the product>"
    }

    Response — success (HTTP 200)
    ------------------------------
    {
        "gtin":               "8901234567890",
        "product_name":       "...",
        "brand":              "...",
        "country":            "IN",
        "ingredients":        ["...", ...],
        "nutrition_per_100g": { "energy_kcal": 110, "protein_g": 1.2, ... },
        "nutrition_per_serving": { "serving_size_g": 20, ... },
        "source":             "cache" | "openfoodfacts"
    }

    Response — barcode not found (HTTP 422)
    ----------------------------------------
    { "status": "error", "message": "barcode_not_found" }

    Response — product not in any DB (HTTP 200, partial)
    -----------------------------------------------------
    { "status": "partial", "gtin": "...", "message": "nutrition_unavailable" }
    """
    data = request.get_json(silent=True)
    if not data or not data.get("image"):
        return jsonify({"status": "error", "message": "image field is required"}), 400

    # ── Step 1: Decode image ──────────────────────────────────────────────────
    image = _decode_base64_image(data["image"])
    if image is None:
        return jsonify({"status": "error", "message": "invalid_image"}), 400

    logger.info("POST /api/scan — image decoded (%dx%d)", image.shape[1], image.shape[0])

    # ── Step 2: Barcode-only model ────────────────────────────────────────────
    gtin = extract_barcode_from_image(image)

    if not gtin:
        logger.info("POST /api/scan — no barcode detected")
        return jsonify({
            "status": "error",
            "message": "barcode_not_found",
            "hint": "Make sure the barcode is clearly visible and well-lit."
        }), 422

    logger.info("POST /api/scan — barcode detected: %s", gtin)

    # ── Step 3: Non-ML DB/API lookup ──────────────────────────────────────────
    product = get_product_by_gtin(gtin)

    if product is None:
        logger.info("POST /api/scan — GTIN %s not found in any database", gtin)
        return jsonify({
            "status": "partial",
            "gtin": gtin,
            "message": "nutrition_unavailable",
            "hint": "Product barcode was read but no nutrition data was found."
        }), 200

    # ── Step 4: Compute health score from nutrition data ──────────────────────
    n100 = product.get("nutrition_per_100g") or {}
    features = {
        "sugar_g":    n100.get("sugars_g"),
        "fat_g":      n100.get("fat_g"),
        "carbs_g":    n100.get("carbohydrates_g"),
        "protein_g":  n100.get("protein_g"),
        "calories":   n100.get("energy_kcal"),
        "additive_impact": 0,  # no additive OCR in barcode path
    }
    scoring_engine = _get_scoring_engine()
    score_value = round(scoring_engine.calculate_raw_score(features), 1)
    health_score = (
        "GREEN"  if score_value >= 7.0 else
        "YELLOW" if score_value >= 4.0 else
        "RED"
    )

    # ── Step 5: Build flat nutrition dict the frontend expects ────────────────
    def _fmt(val, unit="g"):
        return f"{round(val, 1)}{unit}" if val is not None else "N/A"

    flat_nutrition = {
        "calories":   _fmt(n100.get("energy_kcal"), " kcal"),
        "protein":    _fmt(n100.get("protein_g")),
        "total_fat":  _fmt(n100.get("fat_g")),
        "sugar":      _fmt(n100.get("sugars_g")),
        "carbs":      _fmt(n100.get("carbohydrates_g")),
        "sodium":     _fmt(n100.get("sodium_mg"), " mg"),
        "fiber":      _fmt(n100.get("fiber_g")),
    }

    healthy_alt = (
        "Try fresh fruits or homemade alternatives to reduce additives and sugar."
        if score_value < 5.0 else None
    )

    # ── Step 6: Return enriched response ─────────────────────────────────────
    response_body: Dict[str, Any] = {
        **product,
        "health_score":        health_score,
        "score_value":         score_value,
        "nutrition":           flat_nutrition,
        "additives":           [],
        "coloring_agents":     [],
        "healthy_alternative": healthy_alt,
    }

    # ── RAG side pipeline (non-intrusive, optional) ──────────────────
    if getattr(_config, "RAG_ENABLED", False):
        try:
            from rag_pipeline import analyze_label_text as _rag_analyze
            _ingredients_raw = " ".join(product.get("ingredients") or [])
            _rag_result = _rag_analyze(
                nutrition_text="",
                ingredients_text=_ingredients_raw,
                pre_parsed_nutrition={
                    "calories": n100.get("energy_kcal"),
                    "protein_g": n100.get("protein_g"),
                    "fat_g": n100.get("fat_g"),
                    "saturated_fat_g": n100.get("saturated_fat_g"),
                    "trans_fat_g": n100.get("trans_fat_g"),
                    "carbohydrates_g": n100.get("carbohydrates_g"),
                    "sugars_g": n100.get("sugars_g"),
                    "fiber_g": n100.get("fiber_g"),
                    "sodium_mg": n100.get("sodium_mg"),
                },
            )
            response_body["rag_analysis"] = _rag_result
            logger.info(
                "RAG analysis complete for GTIN %s — score=%.1f (%s)",
                gtin, _rag_result.get("score", 0), _rag_result.get("score_grade", "?")
            )
        except Exception as _rag_exc:
            logger.warning("RAG pipeline skipped (non-fatal): %s", _rag_exc)

    logger.info(
        "POST /api/scan — returning enriched product data for GTIN %s "
        "(source: %s, score: %s %s)",
        gtin, product.get("source"), health_score, score_value
    )
    return jsonify(response_body), 200


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY ENDPOINT — OCR-based pipeline (research / debugging only)
# ─────────────────────────────────────────────────────────────────────────────

@bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Legacy OCR + NLP analysis pipeline.

    WARNING: This endpoint is NOT part of the primary barcode-first flow.
    It is kept for research and debugging purposes only.
    The frontend should use POST /api/scan instead.

    Request body (JSON)
    -------------------
    { "ingredients_image": "<base64>" }
    """
    logger.info("POST /analyze — legacy OCR pipeline (research mode)")
    ocr_pipeline, scoring_engine, additives_expert, ner_service, xai_service = _get_legacy_services()

    data = request.get_json(silent=True)
    if not data or not data.get("ingredients_image"):
        return jsonify({"error": "ingredients_image is required"}), 400

    temp_id = str(uuid.uuid4())
    img_path = f"target_{temp_id}.jpg"

    try:
        if not _save_temp_image(data["ingredients_image"], img_path):
            return jsonify({"error": "invalid image data"}), 400

        # OCR
        ocr_result = ocr_pipeline.process_label(img_path)
        raw_text = ocr_result.get("raw_text", "").strip()
        logger.info("OCR raw text (%d chars): %s", len(raw_text), raw_text[:200])

        # Optional second nutrition-panel image
        nutrition_image_b64 = data.get("nutrition_image")
        if nutrition_image_b64 and nutrition_image_b64 != data.get("ingredients_image"):
            nutr_path = f"target_nutr_{temp_id}.jpg"
            try:
                if _save_temp_image(nutrition_image_b64, nutr_path):
                    nutr_result = ocr_pipeline.process_label(nutr_path)
                    nutr_text = nutr_result.get("raw_text", "").strip()
                    if nutr_text:
                        raw_text = raw_text + " " + nutr_text
                        logger.info("Nutrition panel OCR appended (%d chars)", len(nutr_text))
            except Exception as ne:
                logger.warning("Nutrition panel OCR failed: %s", ne)
            finally:
                if os.path.exists(nutr_path):
                    os.remove(nutr_path)

        if not raw_text:
            return jsonify({"error": "Could not read label text. Try a clearer, well-lit photo."}), 422

        # NER + Additives + Scoring + XAI
        features = ner_service.extract(raw_text)
        detected_additives, additive_impact = additives_expert.analyze_text(raw_text)
        risk_summary = additives_expert.get_risk_summary(detected_additives)
        features["additive_impact"] = additive_impact
        coloring_agents = [a for a in detected_additives if a.get("category") == "Colour"]
        health_score = scoring_engine.calculate_raw_score(features)
        xai_explanations = xai_service.explain_score(
            None, features, ["sugar_g", "additive_impact", "calories", "protein_g"]
        )

        risk_tier = risk_summary.get("risk_tier", "SAFE")
        health_color = (
            "RED"    if risk_tier in ("CRITICAL", "HIGH_RISK") else
            "YELLOW" if risk_tier in ("MODERATE_RISK", "LOW_RISK") else
            "GREEN"
        )

        def fmt(val, unit="g"):
            return f"{val}{unit}" if val is not None else "N/A"

        result = {
            "product_name": "Product Scan Result (OCR)",
            "health_score": health_color,
            "score_value": round(health_score, 1),
            "raw_ocr_text": raw_text[:500],
            "additives": detected_additives,
            "coloring_agents": coloring_agents,
            "nutrition": {
                "calories":   fmt(features.get("calories"), " kcal"),
                "protein":    fmt(features.get("protein_g")),
                "total_fat":  fmt(features.get("fat_g")),
                "carbs":      fmt(features.get("carbs_g")),
                "sugar":      fmt(features.get("sugar_g")),
            },
            "xai": {"shap_impacts": xai_explanations},
            "healthy_alternative": (
                "Fresh fruits or homemade organic snacks." if health_score < 6 else None
            ),
        }

        # ── RAG side pipeline (non-intrusive, optional) ──────────────────
        if getattr(_config, "RAG_ENABLED", False):
            try:
                from rag_pipeline import analyze_label_text as _rag_analyze
                _rag_result = _rag_analyze(
                    nutrition_text=raw_text,
                    ingredients_text=raw_text,
                )
                result["rag_analysis"] = _rag_result
                logger.info(
                    "RAG analysis (legacy /analyze) complete — score=%.1f (%s)",
                    _rag_result.get("score", 0), _rag_result.get("score_grade", "?")
                )
            except Exception as _rag_exc:
                logger.warning("RAG pipeline skipped (non-fatal): %s", _rag_exc)

        return jsonify(result)

    except Exception as exc:
        logger.error("Legacy pipeline error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


# ─────────────────────────────────────────────────────────────────────────────
# Other endpoints
# ─────────────────────────────────────────────────────────────────────────────

@bp.route("/search", methods=["GET"])
def search():
    q = request.args.get("q", "").strip()
    logger.info("GET /search — query: %s", q)
    return jsonify({"products": [{"name": f"Mock result for {q}", "health_score": "YELLOW"}]})


@bp.route("/history", methods=["GET"])
def history():
    return jsonify([
        {"product_name": "Sample Label Scan", "timestamp": "Just now",
         "health_score": "YELLOW", "score_value": 5.4}
    ])


@bp.route("/analytics", methods=["GET"])
def analytics():
    return jsonify({
        "avg_score": 7.2,
        "history_trend": [4, 5, 5, 6, 8, 7, 9],
        "top_additives": [
            {"name": "INS 102", "count": 12},
            {"name": "MSG",     "count": 8},
        ],
    })


@bp.route("/preferences", methods=["GET", "POST"])
def preferences():
    if request.method == "POST":
        return jsonify({"status": "updated"})
    return jsonify({
        "vegan": False, "no_sugar": False,
        "low_sodium": False, "gluten_free": False,
    })


@bp.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(os.path.join("static", path)):
        return send_from_directory("static", path)
    return jsonify({"error": "File not found"}), 404
