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
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from functools import wraps
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from flask import Blueprint, jsonify, request, send_from_directory

# ── Barcode-first services (primary flow) ─────────────────────────────────────
from app.services.barcode_service import extract_barcode_from_image
from app.services.nutrition_db import get_product_by_gtin

# ── History & analytics service ───────────────────────────────────────────────
from app.services.history_service import save_scan, get_history, get_analytics, init_db

# ── Legacy OCR/NLP services (kept for research, NOT called in primary flow) ───
from app.services.ocr_pipeline import AdvancedOCRPipeline
from app.services.health_scoring import HealthScoreEnsemble  # also used in primary flow for scoring
from app.services.additives_expert import AdditivesExpert
from app.services.ner_service import NERService
from app.services.xai_service import XAIService
from app import config as _config

# ── JWT secret (change in production via env var) ────────────────────────────
_JWT_SECRET = os.getenv("JWT_SECRET", "nutriscan-dev-secret-change-in-prod")
_JWT_ALGORITHM = "HS256"
_TOKEN_TTL = 60 * 60 * 24 * 30  # 30 days


def _hash_password(password: str) -> str:
    """Simple PBKDF2-HMAC-SHA256 hash (no extra deps)."""
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"{salt}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, dk_hex = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _make_token(user_id: int, email: str) -> str:
    import base64 as _b64
    header = _b64.urlsafe_b64encode(json.dumps({"alg": _JWT_ALGORITHM, "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = _b64.urlsafe_b64encode(json.dumps({
        "sub": user_id, "email": email,
        "exp": int(time.time()) + _TOKEN_TTL,
    }).encode()).decode().rstrip("=")
    sig = hmac.new(_JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{sig}"


def _decode_token(token: str) -> Optional[Dict]:
    try:
        import base64 as _b64
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected_sig = hmac.new(_JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        pad = 4 - len(payload) % 4
        data = json.loads(_b64.urlsafe_b64decode(payload + "=" * pad))
        if data.get("exp", 0) < int(time.time()):
            return None
        return data
    except Exception:
        return None


def _get_current_user_id() -> Optional[int]:
    """Extract user_id from Bearer token in Authorization header (optional)."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    payload = _decode_token(auth[7:])
    return payload["sub"] if payload else None

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

    # ── Step 4: Run AdditivesExpert on ingredient list from DB ───────────────
    n100 = product.get("nutrition_per_100g") or {}
    ingredients_list = product.get("ingredients") or []
    ingredients_text = ", ".join(ingredients_list)

    additives_expert = AdditivesExpert()
    detected_additives, additive_impact = additives_expert.analyze_text(ingredients_text)
    coloring_agents = [a for a in detected_additives if a.get("category") == "Colour"]
    risk_summary = additives_expert.get_risk_summary(detected_additives)

    logger.info(
        "POST /api/scan — additives: %d detected (impact=%.1f, risk=%s)",
        len(detected_additives), additive_impact, risk_summary.get("risk_tier")
    )

    # ── Step 5: Health score using nutrition + additive impact ────────────────
    features = {
        "sugar_g":         n100.get("sugars_g"),
        "fat_g":           n100.get("fat_g"),
        "carbs_g":         n100.get("carbohydrates_g"),
        "protein_g":       n100.get("protein_g"),
        "calories":        n100.get("energy_kcal"),
        "additive_impact": additive_impact,
    }
    scoring_engine = _get_scoring_engine()
    score_value = round(scoring_engine.calculate_raw_score(features), 1)

    risk_tier = risk_summary.get("risk_tier", "SAFE")
    if risk_tier in ("CRITICAL", "HIGH_RISK"):
        health_score = "RED"
    elif risk_tier == "MODERATE_RISK" and score_value >= 7.0:
        health_score = "YELLOW"
    else:
        health_score = (
            "GREEN"  if score_value >= 7.0 else
            "YELLOW" if score_value >= 4.0 else
            "RED"
        )

    # ── Step 5a: Build flat nutrition dict the frontend expects ───────────────
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

    # ── Step 5b: Load user preferences and apply dietary overrides ────────────
    user_id = _get_current_user_id()   # resolve early — needed for prefs lookup AND history save
    prefs = {"vegan": False, "no_sugar": False, "low_sodium": False, "gluten_free": False}
    preference_warnings = []
    try:
        from app.services.history_service import _get_conn as _hconn
        with _hconn() as _pc:
            _prow = _pc.execute(
                "SELECT vegan, no_sugar, low_sodium, gluten_free FROM preferences WHERE user_id=?",
                (user_id or 0,)
            ).fetchone()
            if _prow:
                prefs = {
                    "vegan":       bool(_prow[0]),
                    "no_sugar":    bool(_prow[1]),
                    "low_sodium":  bool(_prow[2]),
                    "gluten_free": bool(_prow[3]),
                }
    except Exception as _pe:
        logger.warning("Preferences load failed (non-fatal): %s", _pe)

    # Check each preference against the product's data
    ing_lower = ingredients_text.lower()
    if prefs["vegan"]:
        animal_keywords = ["milk", "cheese", "paneer", "butter", "ghee", "cream",
                           "egg", "meat", "chicken", "fish", "gelatin", "honey",
                           "whey", "lactose", "casein", "lard"]
        violations = [kw for kw in animal_keywords if kw in ing_lower]
        if violations:
            preference_warnings.append(
                f"⚠️ Not vegan: contains {', '.join(violations[:3])}"
            )
            health_score = "RED"  # hard violation

    if prefs["no_sugar"]:
        sugar_g = n100.get("sugars_g") or 0
        sugar_keywords = ["sugar", "sucrose", "glucose syrup", "corn syrup", "dextrose",
                          "fructose", "maltose", "molasses", "cane juice"]
        has_sugar_ing = any(kw in ing_lower for kw in sugar_keywords)
        if sugar_g > 5 or has_sugar_ing:
            preference_warnings.append(
                f"⚠️ High sugar: {sugar_g}g per 100g — not suitable for no-sugar diet"
            )
            if health_score == "GREEN":
                health_score = "YELLOW"

    if prefs["low_sodium"]:
        sodium_mg = n100.get("sodium_mg") or 0
        if sodium_mg > 400:
            preference_warnings.append(
                f"⚠️ High sodium: {sodium_mg}mg per 100g — exceeds low-sodium limit"
            )
            if health_score == "GREEN":
                health_score = "YELLOW"
            if sodium_mg > 800:
                health_score = "RED"

    if prefs["gluten_free"]:
        gluten_keywords = ["wheat", "barley", "rye", "oat", "gluten", "wheat flour",
                           "maida", "semolina", "atta"]
        violations = [kw for kw in gluten_keywords if kw in ing_lower]
        if violations:
            preference_warnings.append(
                f"⚠️ Contains gluten: {', '.join(violations[:3])}"
            )
            health_score = "RED"  # hard violation for celiac

    # Build personalised healthy_alt
    if preference_warnings:
        healthy_alt = " | ".join(preference_warnings)
    elif score_value < 5.0:
        healthy_alt = "Try fresh fruits or homemade alternatives to reduce additives and sugar."
    else:
        healthy_alt = None

    # ── Step 5c: XAI Explanations ───────────────────────────────────────────
    global _xai_service
    if _xai_service is None:
        _xai_service = XAIService()
        
    xai_explanations = _xai_service.explain_score(
        None, features, ["sugar_g", "additive_impact", "calories", "protein_g"]
    )

    # ── Step 6: Return enriched response ─────────────────────────────────────
    response_body: Dict[str, Any] = {
        **product,
        "health_score":          health_score,
        "score_value":           score_value,
        "nutrition":             flat_nutrition,
        "additives":             detected_additives,
        "coloring_agents":       coloring_agents,
        "risk_summary":          risk_summary,
        "healthy_alternative":   healthy_alt,
        "preference_warnings":   preference_warnings,
        "active_preferences":    prefs,
        "scan_mode":             "barcode",
        "xai":                   {"shap_impacts": xai_explanations},
    }

    # ── Step 7: Auto-save scan to history ────────────────────────────────────
    try:
        save_scan(
            product_name=product.get("product_name"),
            brand=product.get("brand"),
            gtin=gtin,
            health_score=health_score,
            score_value=score_value,
            nutrition=n100,
            ingredients=ingredients_list,
            flagged_additives=detected_additives,
            healthy_alternative=healthy_alt,
            source=product.get("source"),
            user_id=user_id,
        )
        logger.info(
            "Scan saved — user=%s | %s | %s %.1f | %d additives",
            user_id, gtin, health_score, score_value, len(detected_additives)
        )
    except Exception as _hist_exc:
        logger.warning("History save failed (non-fatal): %s", _hist_exc)

    logger.info(
        "POST /api/scan — GTIN %s | source=%s | %s %.1f | %d additives",
        gtin, product.get("source"), health_score, score_value, len(detected_additives)
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
        if getattr(_config, "RAG_ENABLED", False):  # always False for barcode path
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
    """Return real scan history from SQLite."""
    limit = min(int(request.args.get("limit", 50)), 200)
    user_id = _get_current_user_id()
    return jsonify(get_history(limit=limit, user_id=user_id))


@bp.route("/analytics", methods=["GET"])
def analytics():
    """Return real analytics computed from scan history."""
    user_id = _get_current_user_id()
    return jsonify(get_analytics(user_id=user_id))


# ─────────────────────────────────────────────────────────────────────────────
# INDIAN LABEL SIDE-PIPELINE — POST /api/scan-label
# Does NOT touch the barcode-first /api/scan pipeline.
# ─────────────────────────────────────────────────────────────────────────────

@bp.route("/api/scan-label", methods=["POST"])
def scan_label():
    """
    Indian food label side-pipeline.

    Request body (JSON)
    -------------------
    {
      "image"        : "<base64 of ingredients/nutrition table photo>",
      "product_name" : "Maggi 2-Minute Noodles"   # required: entered by user
    }
    """
    import sys as _sys
    import os as _os
    # Make sure src/ is importable
    _backend_root = _os.path.dirname(_os.path.dirname(__file__))
    if _backend_root not in _sys.path:
        _sys.path.insert(0, _backend_root)

    from app.services.additives_expert import AdditivesExpert
    from app.services.health_scoring import HealthScoreEnsemble
    from app.services.ocr_pipeline import AdvancedOCRPipeline

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    product_name = (data.get("product_name") or "").strip()
    if not product_name:
        return jsonify({"error": "product_name is required"}), 400

    image_b64  = data.get("image") or data.get("ingredients_image")
    img_path   = None
    raw_ocr_text = ""

    try:
        # ── Step 1: OCR the label image (if provided) ───────────────────────
        if image_b64:
            temp_id  = str(uuid.uuid4())
            img_path = f"label_{temp_id}.jpg"
            try:
                if _save_temp_image(image_b64, img_path):
                    ocr_pipeline = AdvancedOCRPipeline()
                    ocr_result   = ocr_pipeline.process_label(img_path)
                    raw_ocr_text = ocr_result.get("raw_text", "")
                    logger.info("scan-label: OCR extracted %d chars", len(raw_ocr_text))
            except MemoryError:
                logger.warning("scan-label: OCR MemoryError, skipping OCR")
                raw_ocr_text = ""
            except Exception as exc:
                logger.warning("scan-label: OCR failed: %s", exc)
                raw_ocr_text = ""

        # ── Step 2: Indian product lookup (FSSAI, OFF India, OFF World, OCR) ─
        try:
            from src.services.indian_label_service import lookup_indian_product
        except ImportError:
            # Fallback: use OCR-only extraction without external API lookups
            lookup_indian_product = None

        if lookup_indian_product:
            product = lookup_indian_product(product_name, raw_ocr_text)
        else:
            # Pure OCR fallback
            product = _ocr_only_extract(product_name, raw_ocr_text)

        # ── Step 3: Enrich with additives & health score ──────────────────
        nutr = product.get("nutrition") or {}
        ingredients_text = ", ".join(product.get("ingredients", []))
        if raw_ocr_text and not ingredients_text:
            ingredients_text = raw_ocr_text

        additives_expert = AdditivesExpert()
        detected_additives, additive_impact = additives_expert.analyze_text(ingredients_text)
        coloring_agents = [a for a in detected_additives if a.get("category") == "Colour"]

        features = {
            "sugar_g":         nutr.get("sugar") or 0,
            "fat_g":           nutr.get("fat") or 0,
            "carbs_g":         nutr.get("carbs") or 0,
            "protein_g":       nutr.get("protein") or 0,
            "calories":        nutr.get("calories") or 0,
            "additive_impact": additive_impact,
        }
        scoring_engine = _get_scoring_engine()
        health_score   = scoring_engine.calculate_raw_score(features)
        risk_tier      = additives_expert.get_risk_summary(detected_additives).get("risk_tier", "SAFE")

        if risk_tier in ("CRITICAL", "HIGH_RISK"):
            health_color = "RED"
        elif risk_tier == "MODERATE_RISK":
            health_color = "YELLOW"
        else:
            health_color = "GREEN" if health_score >= 6.5 else ("YELLOW" if health_score >= 4.0 else "RED")

        # ── Step 4: Flat nutrition dict for frontend ────────────────────────
        def _fmt(val, unit="g"):
            try:
                return f"{round(float(val), 1)}{unit}" if val is not None else "N/A"
            except Exception:
                return "N/A"

        flat_nutrition = {
            "calories":  _fmt(nutr.get("calories"), " kcal"),
            "protein":   _fmt(nutr.get("protein")),
            "total_fat": _fmt(nutr.get("fat")),
            "carbs":     _fmt(nutr.get("carbs")),
            "sugar":     _fmt(nutr.get("sugar")),
            "fiber":     _fmt(nutr.get("fiber")),
            "sodium":    _fmt(nutr.get("sodium"), " mg"),
        }

        healthy_alt = (
            "Try fresh homemade alternatives to reduce additives and sugar."
            if health_score < 5.0 else None
        )

        response_body: Dict[str, Any] = {
            **product,
            "health_score":        health_color,
            "score_value":         round(health_score, 1),
            "nutrition":           flat_nutrition,
            "additives":           detected_additives,
            "coloring_agents":     coloring_agents,
            "warnings":            product.get("warnings", []),
            "healthy_alternative": healthy_alt,
            "scan_mode":           "label",
        }

        # ── RAG enrichment (label scan path only, never barcode path) ──────
        if getattr(_config, "RAG_LABEL_ENABLED", True):
            try:
                from rag_pipeline import analyze_label_text as _rag_analyze
                _rag_result = _rag_analyze(
                    nutrition_text=raw_ocr_text,
                    ingredients_text=ingredients_text,
                )
                response_body["rag_analysis"] = _rag_result
                logger.info("RAG label analysis complete — score=%.1f (%s)",
                    _rag_result.get("score", 0), _rag_result.get("score_grade", "?"))
            except Exception as _rag_exc:
                logger.warning("RAG pipeline skipped (non-fatal): %s", _rag_exc)

        # ── Step 5: Auto-save to history ──────────────────────────────────
        try:
            user_id = _get_current_user_id()
            save_scan(
                product_name=product.get("product_name") or product_name,
                brand=product.get("brand"),
                health_score=health_color,
                score_value=round(health_score, 1),
                nutrition=nutr,
                ingredients=product.get("ingredients", []),
                flagged_additives=detected_additives,
                healthy_alternative=healthy_alt,
                source=product.get("source", "ocr_extracted"),
                user_id=user_id,
            )
            logger.info("scan-label: saved to history (user_id=%s)", user_id)
        except Exception as _he:
            logger.warning("scan-label: history save failed (non-fatal): %s", _he)

        logger.info(
            "scan-label: '%s' scored %s (%.1f) via %s",
            product_name, health_color, health_score, product.get("source")
        )
        return jsonify(response_body), 200

    except MemoryError:
        return jsonify({"error": "Server out of memory. Please try a smaller image."}), 500
    except Exception as exc:
        logger.error("scan-label error: %s", exc, exc_info=True)
        return jsonify({"error": "Unexpected error during label analysis.", "detail": str(exc)}), 500
    finally:
        if img_path and _os.path.exists(img_path):
            _os.remove(img_path)


def _ocr_only_extract(product_name: str, raw_text: str) -> dict:
    """Pure regex-based OCR extraction fallback (no external service needed)."""
    import re
    text_lower = raw_text.lower()

    def _find(patterns):
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m:
                try:
                    return float(m.group(1))
                except Exception:
                    pass
        return None

    calories = _find([r"energy[^\d]*(\d+(?:\.\d+)?)\s*k?cal", r"calories?[^\d]*(\d+(?:\.\d+)?)", r"(\d+(?:\.\d+)?)\s*k?cal"])
    protein  = _find([r"protein[^\d]*(\d+(?:\.\d+)?)\s*g"])
    fat      = _find([r"total\s+fat[^\d]*(\d+(?:\.\d+)?)\s*g", r"fat[^\d]*(\d+(?:\.\d+)?)\s*g"])
    carbs    = _find([r"total\s+carbo[^\d]*(\d+(?:\.\d+)?)\s*g", r"carbohydrate[^\d]*(\d+(?:\.\d+)?)\s*g", r"carbs?[^\d]*(\d+(?:\.\d+)?)\s*g"])
    sugar    = _find([r"sugar[^\d]*(\d+(?:\.\d+)?)\s*g"])
    sodium   = _find([r"sodium[^\d]*(\d+(?:\.\d+)?)\s*m?g", r"salt[^\d]*(\d+(?:\.\d+)?)\s*g"])
    fiber    = _find([r"(?:dietary\s+)?fi(?:e)?r(?:e)?[^\d]*(\d+(?:\.\d+)?)\s*g"])

    ing_match = re.search(r"ingredients?\s*:?\s*([^.]{10,400})", raw_text, re.IGNORECASE | re.DOTALL)
    ingredients = []
    if ing_match:
        parts = re.split(r"[,;\n]+", ing_match.group(1))
        ingredients = [p.strip() for p in parts if len(p.strip()) > 1][:30]

    warnings = []
    if sugar and sugar > 20:    warnings.append("High Sugar Content")
    if sodium and sodium > 600: warnings.append("High Sodium")
    if fat and fat > 20:        warnings.append("High Saturated Fat")
    if re.search(r"\bins\s*\d{3,}", text_lower):      warnings.append("Contains INS Additives")
    if re.search(r"colour|color|tartrazine", text_lower): warnings.append("Contains Artificial Colors")
    if re.search(r"preservative|sodium benzoate", text_lower): warnings.append("Contains Preservatives")
    if re.search(r"msg|monosodium glutamate", text_lower):     warnings.append("Contains MSG")

    return {
        "product_name":  product_name,
        "brand":         "Unknown Brand",
        "source":        "ocr_extracted",
        "ingredients":   ingredients,
        "nutrition":     {"calories": calories, "protein": protein, "fat": fat, "carbs": carbs, "sugar": sugar, "sodium": sodium, "fiber": fiber},
        "warnings":      warnings,
        "raw_ocr_text":  raw_text[:800],
        "data_quality":  "ocr_extracted",
    }


# ─────────────────────────────────────────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@bp.route("/auth/register", methods=["POST"])
def auth_register():
    """Register a new user. Body: {name, email, password}"""
    from app.services.history_service import _get_conn
    data = request.get_json(silent=True) or {}
    name     = (data.get("name")     or "").strip()
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if "@" not in email:
        return jsonify({"error": "Invalid email address"}), 400

    try:
        hashed = _hash_password(password)
        with _get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?,?,?)",
                (name, email, hashed)
            )
            conn.commit()
            user_id = cur.lastrowid
        token = _make_token(user_id, email)
        return jsonify({"token": token, "user": {"id": user_id, "name": name, "email": email}}), 201
    except Exception as exc:
        if "UNIQUE" in str(exc):
            return jsonify({"error": "Email already registered"}), 409
        logger.error("Register error: %s", exc)
        return jsonify({"error": "Registration failed"}), 500


@bp.route("/auth/login", methods=["POST"])
def auth_login():
    """Login. Body: {email, password}"""
    from app.services.history_service import _get_conn
    data = request.get_json(silent=True) or {}
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, email, password FROM users WHERE email=?", (email,)
        ).fetchone()

    if not row or not _verify_password(password, row["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = _make_token(row["id"], row["email"])
    return jsonify({
        "token": token,
        "user": {"id": row["id"], "name": row["name"], "email": row["email"]}
    })


@bp.route("/auth/me", methods=["GET"])
def auth_me():
    """Return current user info from token."""
    from app.services.history_service import _get_conn
    user_id = _get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id=?", (user_id,)
        ).fetchone()
    if not row:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(row))


@bp.route("/preferences", methods=["GET", "POST"])
def preferences():
    """Persist dietary preferences per user (or globally for guests)."""
    from app.services.history_service import _get_conn
    user_id = _get_current_user_id()

    with _get_conn() as conn:
        # Ensure preferences table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                user_id   INTEGER PRIMARY KEY,
                vegan     INTEGER DEFAULT 0,
                no_sugar  INTEGER DEFAULT 0,
                low_sodium INTEGER DEFAULT 0,
                gluten_free INTEGER DEFAULT 0
            )
        """)
        conn.commit()

        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            uid = user_id if user_id is not None else 0
            conn.execute("""
                INSERT INTO preferences (user_id, vegan, no_sugar, low_sodium, gluten_free)
                VALUES (?,?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET
                    vegan=excluded.vegan,
                    no_sugar=excluded.no_sugar,
                    low_sodium=excluded.low_sodium,
                    gluten_free=excluded.gluten_free
            """, (
                uid,
                1 if data.get("vegan") else 0,
                1 if data.get("no_sugar") else 0,
                1 if data.get("low_sodium") else 0,
                1 if data.get("gluten_free") else 0,
            ))
            conn.commit()
            return jsonify({"status": "updated"})

        # GET
        uid = user_id if user_id is not None else 0
        row = conn.execute(
            "SELECT * FROM preferences WHERE user_id=?", (uid,)
        ).fetchone()
        if not row:
            return jsonify({"vegan": False, "no_sugar": False, "low_sodium": False, "gluten_free": False})
        return jsonify({
            "vegan": bool(row["vegan"]),
            "no_sugar": bool(row["no_sugar"]),
            "low_sodium": bool(row["low_sodium"]),
            "gluten_free": bool(row["gluten_free"]),
        })


@bp.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(os.path.join("static", path)):
        return send_from_directory("static", path)
    return jsonify({"error": "File not found"}), 404
