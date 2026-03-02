import base64
import os
import uuid
import logging
from flask import Blueprint, request, jsonify, send_from_directory
from typing import Dict, Any, Optional

# New modular imports
from src.models.ocr.ocr_pipeline import AdvancedOCRPipeline
from src.models.health_scoring import HealthScoreEnsemble
from src.models.additives_expert import AdditivesExpert
from src.models.nlp.ner_service import NERService
from src.models.xai_service import XAIService
from src.utils.barcode import extract_barcode
from src.database.nutrition_db import nutrition_db
# Indian label side-pipeline (does NOT touch barcode-first pipeline)
from src.services.indian_label_service import lookup_indian_product

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)

# Initialize Services
ocr_pipeline = AdvancedOCRPipeline()
scoring_engine = HealthScoreEnsemble()
additives_expert = AdditivesExpert()
ner_service = NERService()
xai_service = XAIService()

@bp.route("/", methods=["GET"])
@bp.route("/api/health", methods=["GET"])
def read_root():
    return jsonify({"message": "Food Scanner API is running!"})

@bp.route("/analyze", methods=["POST"])
@bp.route("/api/scan", methods=["POST"])
def analyze():
    """
    Main inference endpoint.
    Flow: Barcode (GTIN) -> DB/API Lookup -> Fallback to OCR/NLP.
    """
    logger.info("Starting refined analysis pipeline...")

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    scan_stage = data.get("scan_stage")  # "barcode" | "ingredients" | None (legacy)
    user_product_name = data.get("product_name")
    gtin = data.get('gtin')
    img_path = None
    source = "ocr_nlp"
    product_data = None

    try:
        # 1. PROCESS IMAGE IF PROVIDED
        # Accept both 'image' (new /api/scan key) and legacy 'ingredients_image'
        ingredients_image_b64 = data.get('image') or data.get('ingredients_image')
        if ingredients_image_b64:
            temp_id = str(uuid.uuid4())
            img_path = f"target_{temp_id}.jpg"
            header, encoded = ingredients_image_b64.split(",", 1) if ',' in ingredients_image_b64 else ("", ingredients_image_b64)
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(encoded))

            # Try to extract barcode from image if not provided explicitly
            if not gtin:
                gtin = extract_barcode(img_path)

        # 2. GTIN LOOKUP
        if gtin:
            product_data = nutrition_db.get_product_by_gtin(gtin)
            if product_data:
                source = product_data.get("source", "database|api")
                logger.info(f"Pipeline: Successfully retrieved data for GTIN {gtin} from {source}")

            # If this request is explicitly a barcode-only stage and we still don't
            # have usable product data, signal the frontend to fall back to
            # ingredients scanning + manual product name instead of doing OCR here.
            if scan_stage == "barcode" and not product_data:
                if img_path and os.path.exists(img_path):
                    os.remove(img_path)
                return jsonify({
                    "error": "No barcode or product data found. Please scan the ingredients label and enter the product name.",
                    "error_code": "NO_BARCODE_OR_DATA",
                    "next_step": "ingredients"
                }), 422

        # 3. FALLBACK TO OCR/NLP IF NO DATA FOUND
        if not product_data and img_path:
            logger.info("Pipeline: Falling back to OCR/NLP analysis...")
            ocr_result = ocr_pipeline.process_label(img_path)
            raw_text = ocr_result.get("raw_text", "")

            if not raw_text:
                raw_text = "Ingredients: Sugar, Palm Oil, INS 102, INS 211, Maltodextrin."  # Fallback text

            features = ner_service.extract(raw_text)
            product_name_extracted, brand_extracted = ner_service.get_product_identity(raw_text)

            detected_additives, additive_impact = additives_expert.analyze_text(raw_text)
            features["additive_impact"] = additive_impact

            product_data = {
                "gtin": gtin,
                # Allow user-provided product name (from ingredients stage) to
                # override the heuristic NER-based name.
                "product_name": user_product_name or product_name_extracted,
                "brand": brand_extracted,
                "ingredients": [a.get("name") for a in detected_additives],
                "nutrition": {
                    "calories": features.get('calories', 0),
                    "protein": features.get('protein_g', 0),
                    "fat": features.get('fat_g', 0),
                    "carbs": features.get('carbs_g', 0),
                    "sugar": features.get('sugar_g', 0)
                }
            }

            # Save to DB if we have a GTIN
            if gtin:
                nutrition_db.save_product(gtin, product_data, source="ocr_nlp")

        if not product_data:
            return jsonify({"error": "Could not extract data from image or barcode", "error_code": "NO_PRODUCT_DATA"}), 422

        # If product data came from an external source but the user supplied a
        # product name in an ingredients-stage request, prefer the user label for
        # display while keeping nutrition from the database/API.
        if scan_stage == "ingredients" and user_product_name and product_data.get("product_name"):
            product_data["product_name"] = user_product_name

        # 4. ENRICH WITH SCORING AND XAI
        # Prep features for scoring engine
        features = {
            "sugar_g": product_data["nutrition"].get("sugar", 0),
            "fat_g": product_data["nutrition"].get("fat", 0),
            "carbs_g": product_data["nutrition"].get("carbs", 0),
            "protein_g": product_data["nutrition"].get("protein", 0),
            "calories": product_data["nutrition"].get("calories", 0),
        }

        # Additives check if not already done (e.g. if source was API)
        ingredients_text = ", ".join(product_data.get("ingredients", []))
        detected_additives, additive_impact = additives_expert.analyze_text(ingredients_text)
        features["additive_impact"] = additive_impact

        health_score = scoring_engine.calculate_raw_score(features)
        risk_summary = additives_expert.get_risk_summary(detected_additives)
        coloring_agents = [a for a in detected_additives if a.get("category") == "Colour"]

        # 5. DETERMINE HEALTH COLOR using BOTH numeric score AND additive risk
        risk_tier = risk_summary.get("risk_tier", "SAFE")

        # Additive-based override (takes precedence if additives are bad)
        if risk_tier in ["CRITICAL", "HIGH_RISK"]:
            health_color = "RED"
        elif risk_tier in ["MODERATE_RISK"]:
            health_color = "YELLOW"
        else:
            # No serious additive risk: fall back to numeric score bands
            if health_score < 4.0:
                health_color = "RED"
            elif health_score < 6.5:
                health_color = "YELLOW"
            else:
                health_color = "GREEN"

        response = {
            "gtin": product_data.get("gtin"),
            "product_name": product_data.get("product_name"),
            "brand": product_data.get("brand"),
            "health_score": health_color,
            "score_value": round(health_score, 1),
            "additives": detected_additives,
            "coloring_agents": coloring_agents,
            "nutrition": {
                "calories": f"{product_data['nutrition'].get('calories', 0)} kcal",
                "protein": f"{product_data['nutrition'].get('protein', 0)}g",
                "total_fat": f"{product_data['nutrition'].get('fat', 0)}g",
                "carbs": f"{product_data['nutrition'].get('carbs', 0)}g",
                "sugar": f"{product_data['nutrition'].get('sugar', 0)}g"
            },
            "ingredients": product_data.get("ingredients", []),
            "source": source,
            "xai": {
                "shap_impacts": xai_service.explain_score(None, features, ["sugar_g", "additive_impact", "calories"])
            }
        }

        return jsonify(response)

    except MemoryError as e:
        logger.error("Pipeline ran out of memory during analysis", exc_info=True)
        return jsonify({
            "error": "Server ran out of memory while analyzing this image. Try a clearer, smaller photo or barcode-only scan.",
            "error_code": "OUT_OF_MEMORY"
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        return jsonify({
            "error": "Unexpected error during analysis. Please try again with a different image.",
            "error_code": "INTERNAL_ERROR"
        }), 500
    finally:
        if img_path and os.path.exists(img_path):
            os.remove(img_path)

@bp.route("/history", methods=["GET"])
def history():
    return jsonify([
        {"product_name": "Sample Label Scan", "timestamp": "Just now", "health_score": "YELLOW", "score_value": 5.4}
    ])

# ... (rest of search, analytics, preferences remain same but can be updated later)

@bp.route("/search", methods=["GET"])
def search():
    q = request.args.get('q', '')
    return jsonify({"products": [{"name": f"Mock result for {q}", "health_score": "YELLOW"}]})

@bp.route("/analytics", methods=["GET"])
def analytics():
    return jsonify({"avg_score": 7.2, "history_trend": [4, 5, 5, 6, 8, 7, 9]})

@bp.route("/preferences", methods=["GET", "POST"])
def preferences():
    if request.method == "POST": return jsonify({"status": "updated"})
    return jsonify({"vegan": False, "no_sugar": False, "low_sodium": False, "gluten_free": False})


# ─────────────────────────────────────────────────────────────────────────────
# INDIAN LABEL SIDE-PIPELINE  POST /api/scan-label
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

    Response (HTTP 200)
    -------------------
    {
      "product_name"  : "...",
      "brand"         : "...",
      "source"        : "off_india" | "off_world" | "fssai" | "ocr_extracted",
      "data_quality"  : "api_verified" | "fssai_partial" | "ocr_extracted",
      "ingredients"   : [...],
      "nutrition"     : { "calories": 380, "protein": 8.5, ... },
      "health_score"  : "RED" | "YELLOW" | "GREEN",
      "score_value"   : 5.2,
      "additives"     : [...],
      "warnings"      : ["High Sugar Content", ...],
      "raw_ocr_text"  : "..."   (first 800 chars, for debugging)
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    product_name = (data.get("product_name") or "").strip()
    if not product_name:
        return jsonify({"error": "product_name is required"}), 400

    image_b64   = data.get("image") or data.get("ingredients_image")
    img_path    = None
    raw_ocr_text = ""

    try:
        # ── Step 1: OCR the label image (if provided) ───────────────────────
        if image_b64:
            temp_id  = str(uuid.uuid4())
            img_path = f"label_{temp_id}.jpg"
            header, encoded = (
                image_b64.split(",", 1) if "," in image_b64
                else ("", image_b64)
            )
            with open(img_path, "wb") as fh:
                import base64 as _b64
                fh.write(_b64.b64decode(encoded))

            try:
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
        product = lookup_indian_product(product_name, raw_ocr_text)

        # ── Step 3: Enrich with additives & health score ──────────────────
        nutr = product.get("nutrition") or {}
        ingredients_text = ", ".join(product.get("ingredients", []))
        if raw_ocr_text and not ingredients_text:
            ingredients_text = raw_ocr_text   # let additive expert scan full OCR text

        detected_additives, additive_impact = additives_expert.analyze_text(ingredients_text)
        coloring_agents = [a for a in detected_additives if a.get("category") == "Colour"]

        features = {
            "sugar_g":        nutr.get("sugar") or 0,
            "fat_g":          nutr.get("fat") or 0,
            "carbs_g":        nutr.get("carbs") or 0,
            "protein_g":      nutr.get("protein") or 0,
            "calories":       nutr.get("calories") or 0,
            "additive_impact": additive_impact,
        }
        health_score = scoring_engine.calculate_raw_score(features)
        risk_tier    = additives_expert.get_risk_summary(detected_additives).get("risk_tier", "SAFE")

        if risk_tier in ("CRITICAL", "HIGH_RISK"):
            health_color = "RED"
        elif risk_tier == "MODERATE_RISK":
            health_color = "YELLOW"
        else:
            health_color = "GREEN" if health_score >= 6.5 else ("YELLOW" if health_score >= 4.0 else "RED")

        # ── Step 4: Format flat nutrition dict for frontend ─────────────────
        def _fmt(val, unit="g"):
            return f"{round(float(val), 1)}{unit}" if val is not None else "N/A"

        flat_nutrition = {
            "calories":  _fmt(nutr.get("calories"), " kcal"),
            "protein":   _fmt(nutr.get("protein")),
            "total_fat": _fmt(nutr.get("fat")),
            "carbs":     _fmt(nutr.get("carbs")),
            "sugar":     _fmt(nutr.get("sugar")),
            "fiber":     _fmt(nutr.get("fiber")),
            "sodium":    _fmt(nutr.get("sodium"), " mg"),
        }

        response = {
            **product,
            "health_score":     health_color,
            "score_value":      round(health_score, 1),
            "nutrition":        flat_nutrition,
            "additives":        detected_additives,
            "coloring_agents":  coloring_agents,
            "warnings":         product.get("warnings", []),
            "healthy_alternative": (
                "Try fresh homemade alternatives to reduce additives and sugar."
                if health_score < 5.0 else None
            ),
        }

        logger.info(
            "scan-label: '%s' scored %s (%s) via %s",
            product_name, health_color, round(health_score, 1), product.get("source")
        )
        return jsonify(response), 200

    except MemoryError:
        return jsonify({"error": "Server out of memory. Please try a smaller image."}), 500
    except Exception as exc:
        logger.error("scan-label error: %s", exc, exc_info=True)
        return jsonify({"error": "Unexpected error during label analysis."}), 500
    finally:
        if img_path and os.path.exists(img_path):
            os.remove(img_path)
