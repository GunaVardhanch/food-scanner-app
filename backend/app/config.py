import os

from pathlib import Path


def _prefer_d_drive_path(subpath: str) -> str:
    """
    Return a path under D:\\ for large artifacts if D: exists,
    otherwise fall back to the backend directory.
    """
    d_root = Path("D:\\")
    if d_root.exists():
        return str(d_root.joinpath(subpath))
    # Fallback: inside backend directory
    backend_root = Path(__file__).resolve().parents[2]
    return str(backend_root.joinpath(subpath))


# Directory where trained models should be stored (XGBoost, NER, etc.)
MODEL_DIR = _prefer_d_drive_path("food-scanner-models")

# Specific model artifact paths (these are expected to be created by training scripts)
HEALTH_SCORE_MODEL_PATH = os.path.join(MODEL_DIR, "health_ensemble.xgb")
NUTRITION_NER_MODEL_DIR = os.path.join(MODEL_DIR, "nutrition_ner")

# Optional: OCR-related models directory (if you want to keep them off C:)
OCR_MODELS_DIR = os.path.join(MODEL_DIR, "ocr_models")

# ── RAG pipeline ──────────────────────────────────────────────────────────────
# RAG enrichment runs as an ADDITIONAL stage — it never overrides the main
# health_score (which comes from XGBoost/heuristic + verified nutrition DB).
# It contributes: allergens, ultra-processed markers, FSSAI compliance,
# maida detection, richer additive explanations, and warning_details.
#
# RAG_LABEL_ENABLED  — label/OCR scan path (/api/scan-label)  [default: true]
# RAG_BARCODE_ENABLED — barcode scan path (/api/scan)          [default: true]
#   On the barcode path RAG uses pre_parsed_ingredients from the DB,
#   so it never touches the score — only adds allergen/UP-marker metadata.
RAG_ENABLED = False  # legacy flag kept for /analyze endpoint compat
RAG_LABEL_ENABLED   = os.getenv("RAG_LABEL_ENABLED",   "true").lower() == "true"
RAG_BARCODE_ENABLED = os.getenv("RAG_BARCODE_ENABLED", "true").lower() == "true"

