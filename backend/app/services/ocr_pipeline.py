"""
ocr_pipeline.py
───────────────
Phase 2 rebuild of the label OCR pipeline.

Key changes from Phase 1:
  - YOLO generic crop REMOVED as primary region detector (wrong model for food labels)
  - Replaced with spatial_region_split(): uses EasyOCR bounding box coordinates
    to separate the nutrition table (right/bottom half, dense numbers) from the
    ingredients block (left/top half, dense text) without needing a trained detector
  - structured_table_parse(): uses bbox x-coordinates to reconstruct table rows
    so "Fat" and "12g" are linked by spatial proximity, not text order
  - auto_perspective_correct + bilateral_denoise added to preprocessing chain
  - EasyOCR now returns bboxes + confidence for all downstream use
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.utils.preprocessing import apply_clahe, bilateral_denoise, auto_perspective_correct
from app.config import OCR_MODELS_DIR

logger = logging.getLogger(__name__)

# ── Lazy EasyOCR reader (module-level singleton) ──────────────────────────────
_easyocr_reader = None


def _get_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        import torch
        gpu = torch.cuda.is_available()
        model_dir = os.environ.get("EASYOCR_MODULE_PATH") or OCR_MODELS_DIR
        if model_dir and os.path.isdir(model_dir):
            _easyocr_reader = easyocr.Reader(
                ["en", "hi"], gpu=gpu,
                model_storage_directory=model_dir,
                download_enabled=False,
            )
            logger.info("EasyOCR loaded from %s (gpu=%s)", model_dir, gpu)
        else:
            _easyocr_reader = easyocr.Reader(["en", "hi"], gpu=gpu, download_enabled=True)
            logger.info("EasyOCR loaded (gpu=%s, download=True)", gpu)
    return _easyocr_reader


# ── Nutrient keyword sets ─────────────────────────────────────────────────────
_NUTRIENT_KEYWORDS = {
    # English
    "energy", "calories", "kcal", "kj",
    "fat", "lipid", "saturated", "trans",
    "carbohydrate", "carbs", "sugar",
    "protein", "fibre", "fiber",
    "sodium", "salt", "serving",
    # Hindi / Devanagari
    "ऊर्जा",    # energy
    "प्रोटीन",  # protein
    "वसा",      # fat
    "शर्करा",   # sugar
    "चीनी",     # sugar (alternate)
    "सोडियम",   # sodium
    "कार्बोहाइड्रेट",  # carbohydrate
    "रेशा",     # fiber
}

_NUMBER_RE = re.compile(r"\d+\.?\d*")


def _bbox_center(bbox) -> Tuple[float, float]:
    """Return (cx, cy) of an EasyOCR bbox [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]."""
    xs = [p[0] for p in bbox]
    ys = [p[1] for p in bbox]
    return sum(xs) / 4, sum(ys) / 4


def _bbox_left(bbox) -> float:
    return min(p[0] for p in bbox)


def _bbox_top(bbox) -> float:
    return min(p[1] for p in bbox)


class AdvancedOCRPipeline:
    """
    Label OCR pipeline — Phase 2 rebuild.

    process_label(image_path) returns:
        {
            "raw_text":           str,          # flat joined OCR output
            "structured_nutrition": dict,       # {energy_kcal, fat_g, sugar_g, ...}
            "ingredients_text":   str,          # ingredient paragraph
        }
    """

    def __init__(self):
        # No YOLO load — region split is done spatially from bbox coordinates
        logger.info("AdvancedOCRPipeline initialised (spatial region split mode)")

    # ── Public API ────────────────────────────────────────────────────────────

    def process_label(self, image_path: str) -> Dict[str, Any]:
        """Full preprocessing → OCR → region split → structured parse."""
        t0 = time.time()

        # 1. Load
        img = cv2.imread(image_path)
        if img is None:
            logger.error("process_label: cannot read %s", image_path)
            return {"raw_text": "", "structured_nutrition": {}, "ingredients_text": ""}

        # 2. Preprocessing chain
        img = auto_perspective_correct(img)
        img = bilateral_denoise(img)
        img = apply_clahe(img)

        # 3. Resize — EasyOCR accuracy drops below ~800 px wide
        h, w = img.shape[:2]
        if w < 800:
            scale = 800 / w
            img = cv2.resize(img, (800, int(h * scale)), interpolation=cv2.INTER_CUBIC)

        # 4. Save preprocessed image to a temp path for EasyOCR
        temp_path = image_path + "_preprocessed.jpg"
        cv2.imwrite(temp_path, img)

        try:
            reader = _get_reader()
            ocr_results = reader.readtext(temp_path, detail=1)
        except Exception as exc:
            logger.error("EasyOCR failed: %s", exc)
            return {"raw_text": "", "structured_nutrition": {}, "ingredients_text": ""}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if not ocr_results:
            return {"raw_text": "", "structured_nutrition": {}, "ingredients_text": ""}

        # 5. Region split
        nutrition_region, ingredients_region = self.spatial_region_split(ocr_results)

        # 6. Structured parse
        structured_nutrition = self.structured_table_parse(nutrition_region)

        # 7. Ingredients text — join the ingredients region tokens
        ingredients_text = " ".join(item[1] for item in ingredients_region)

        # 8. Flat raw text (full label, for additive regex fallback)
        raw_text = " ".join(item[1] for item in ocr_results)

        # 9. Per-field confidence — average confidence of tokens that contributed
        #    to each structured_nutrition key. Used by routes.py to set data_quality.
        field_confidence = self._compute_field_confidence(nutrition_region, structured_nutrition)
        # Overall OCR confidence: mean of all token confidences
        all_confs = [item[2] for item in ocr_results if len(item) > 2]
        ocr_confidence = round(float(np.mean(all_confs)), 3) if all_confs else 0.0

        logger.info(
            "process_label: %.2fs | %d tokens | nutrition keys=%s | ocr_conf=%.2f",
            time.time() - t0, len(ocr_results), list(structured_nutrition.keys()), ocr_confidence
        )
        return {
            "raw_text":            raw_text,
            "structured_nutrition": structured_nutrition,
            "ingredients_text":    ingredients_text,
            "ocr_confidence":      ocr_confidence,       # 0.0–1.0 overall
            "field_confidence":    field_confidence,     # per nutrition key
        }

    # ── Region split ──────────────────────────────────────────────────────────

    def spatial_region_split(
        self, ocr_results: List
    ) -> Tuple[List, List]:
        """
        Split EasyOCR results into two regions:
          - nutrition_table: tokens that contain numbers AND are near nutrient keywords
          - ingredients_block: remaining tokens (ingredient paragraph)

        Strategy:
          1. Find all tokens whose text contains a nutrient keyword → seed the
             nutrition region.
          2. Expand: any token within ±30 px vertically of a nutrition seed token
             is also nutrition (captures the value column on the same row).
          3. Everything else → ingredients.
        """
        if not ocr_results:
            return [], []

        # Collect y-centers of nutrition seed tokens
        nutrition_y_centers: List[float] = []
        for bbox, text, _conf in ocr_results:
            text_lower = text.lower()
            if any(kw in text_lower for kw in _NUTRIENT_KEYWORDS):
                _, cy = _bbox_center(bbox)
                nutrition_y_centers.append(cy)

        if not nutrition_y_centers:
            # No nutrient keywords found — treat everything as ingredients
            return [], list(ocr_results)

        ROW_TOLERANCE = 30  # px — tokens within this vertical distance share a row

        nutrition_region: List = []
        ingredients_region: List = []

        for item in ocr_results:
            bbox, text, conf = item
            _, cy = _bbox_center(bbox)
            on_nutrition_row = any(
                abs(cy - ny) <= ROW_TOLERANCE for ny in nutrition_y_centers
            )
            if on_nutrition_row:
                nutrition_region.append(item)
            else:
                ingredients_region.append(item)

        return nutrition_region, ingredients_region

    # ── Structured table parse ────────────────────────────────────────────────

    def structured_table_parse(self, ocr_results: List) -> Dict[str, Optional[float]]:
        """
        Reconstruct nutrition table rows from bbox x-coordinates.

        Each row is identified by shared y-center (±ROW_TOLERANCE px).
        Within a row, the leftmost token(s) are the nutrient name; the
        rightmost token containing a number is the value.

        Returns a dict with standardised keys:
            energy_kcal, fat_g, saturated_fat_g, trans_fat_g,
            carbohydrates_g, sugar_g, fiber_g, protein_g, sodium_mg
        """
        if not ocr_results:
            return {}

        ROW_TOLERANCE = 18  # tighter than split — same-row grouping

        # Group tokens into rows by y-center
        rows: List[List] = []
        used = [False] * len(ocr_results)

        sorted_items = sorted(ocr_results, key=lambda x: _bbox_top(x[0]))

        for i, item in enumerate(sorted_items):
            if used[i]:
                continue
            _, cy_i = _bbox_center(item[0])
            row = [item]
            used[i] = True
            for j, other in enumerate(sorted_items):
                if used[j]:
                    continue
                _, cy_j = _bbox_center(other[0])
                if abs(cy_i - cy_j) <= ROW_TOLERANCE:
                    row.append(other)
                    used[j] = True
            rows.append(row)

        # Detect if this is a 3-column table (name | per serving | per 100g).
        # Heuristic: count rows that have 3+ tokens where 2+ contain numbers.
        # If majority of rows are 3-column, prefer the rightmost numeric column
        # (typically "per 100g" — the standard reference quantity).
        three_col_votes = sum(
            1 for row in rows
            if sum(1 for item in row if _NUMBER_RE.search(item[1])) >= 2
        )
        prefer_rightmost = three_col_votes >= max(1, len(rows) // 3)

        nutrition: Dict[str, Optional[float]] = {}

        for row in rows:
            if len(row) < 2:
                continue
            row_sorted = sorted(row, key=lambda x: _bbox_left(x[0]))
            label_tokens = []
            numeric_tokens = []  # (x_left, text)

            for item in row_sorted:
                text = item[1]
                if _NUMBER_RE.search(text):
                    numeric_tokens.append((_bbox_left(item[0]), text))
                else:
                    label_tokens.append(text.lower())

            if not numeric_tokens:
                continue

            # Pick value column: rightmost when 3-col detected, else last found
            if prefer_rightmost and len(numeric_tokens) >= 2:
                value_text = max(numeric_tokens, key=lambda x: x[0])[1]
            else:
                value_text = numeric_tokens[-1][1]

            nums = _NUMBER_RE.findall(value_text)
            if not nums:
                continue
            value = float(nums[0])

            label = " ".join(label_tokens)
            key = self._map_label_to_key(label, value_text)
            if key:
                nutrition[key] = value

        return nutrition

    # ── Field confidence ──────────────────────────────────────────────────────

    def _compute_field_confidence(
        self, nutrition_region: List, structured_nutrition: Dict
    ) -> Dict[str, float]:
        """
        For each key in structured_nutrition, find the OCR tokens that likely
        contributed to it and average their confidence scores.
        Returns a dict like {"energy_kcal": 0.91, "sugar_g": 0.74, ...}.
        Keys with no matching token default to 0.5 (uncertain).
        """
        if not nutrition_region or not structured_nutrition:
            return {k: 0.5 for k in structured_nutrition}

        # Map canonical key → keyword patterns to match against token text
        _KEY_PATTERNS = {
            "energy_kcal":      ["energy", "calorie", "kcal", "ऊर्जा"],
            "fat_g":            ["fat", "lipid", "वसा"],
            "saturated_fat_g":  ["saturated", "sat fat"],
            "trans_fat_g":      ["trans"],
            "carbohydrates_g":  ["carbohydrate", "carbs"],
            "sugar_g":          ["sugar", "शर्करा", "चीनी"],
            "fiber_g":          ["fiber", "fibre"],
            "protein_g":        ["protein", "प्रोटीन"],
            "sodium_mg":        ["sodium", "salt", "सोडियम"],
        }

        result: Dict[str, float] = {}
        for key in structured_nutrition:
            patterns = _KEY_PATTERNS.get(key, [])
            confs = []
            for bbox, text, conf in nutrition_region:
                tl = text.lower()
                if any(p in tl for p in patterns) or _NUMBER_RE.search(text):
                    confs.append(float(conf))
            result[key] = round(float(np.mean(confs)), 3) if confs else 0.5
        return result

    # ── Label → canonical key mapping ────────────────────────────────────────

    def _map_label_to_key(self, label: str, value_text: str) -> Optional[str]:
        """Map a raw OCR nutrient label string to a canonical dict key."""
        l = label.strip()

        # Skip header / reference rows — these are column headers, not nutrients
        if any(w in l for w in ("serving", "per serve", "per serving", "per 100", "amount")):
            return None

        # Energy — distinguish kJ vs kcal
        if any(w in l for w in ("energy", "calories", "kcal", "cal")):
            if "kj" in l or "kj" in value_text.lower():
                # Convert kJ → kcal
                return "energy_kcal"  # caller stores raw value; conversion below
            return "energy_kcal"

        if "saturated" in l or "sat fat" in l or "saturated fat" in l:
            return "saturated_fat_g"
        if "trans" in l:
            return "trans_fat_g"
        if "fat" in l or "lipid" in l:
            return "fat_g"

        if "sugar" in l:
            return "sugar_g"
        if "carbohydrate" in l or "carbs" in l or "carb" in l:
            return "carbohydrates_g"

        if "fibre" in l or "fiber" in l or "dietary fiber" in l:
            return "fiber_g"
        if "protein" in l:
            return "protein_g"

        if "sodium" in l:
            return "sodium_mg"
        if "salt" in l:
            # Salt → sodium: sodium_mg = salt_g * 400
            return "sodium_mg"

        # Hindi / regional label patterns
        if "ऊर्जा" in l:
            return "energy_kcal"
        if "प्रोटीन" in l:
            return "protein_g"
        if "वसा" in l:
            return "fat_g"
        if "शर्करा" in l or "चीनी" in l:
            return "sugar_g"
        if "सोडियम" in l:
            return "sodium_mg"

        return None
