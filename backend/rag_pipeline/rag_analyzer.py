"""
rag_analyzer.py
────────────────
Main entrypoint for the RAG side pipeline.

Usage:
    from rag_pipeline import analyze_label_text

    result = analyze_label_text(
        nutrition_text="Calories 250 kcal  Protein 4g  Fat 12g  Sodium 820mg ...",
        ingredients_text="Wheat flour, edible vegetable oil, salt, INS 621, INS 319 ..."
    )
    # result is a plain dict ready for JSON serialisation

Pipeline:
    1. OCR text → structured nutrition dict + ingredients list   (ocr_parser)
    2. Ingredient tokens → fuzzy-matched against fssai_additives.json  (rapidfuzz / exact)
    3. FAISS context retrieval for top matches                   (embedder)
    4. Rule engine evaluates nutrition against FSSAI limits      (harmful_flags + nutrition_guidelines)
    5. Score computed, warnings and explanations formatted       (llm_prompts)
    6. Pydantic RAGAnalysisResult validated and returned as dict (output_schemas)
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Knowledge base paths ───────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_KB = _HERE / "knowledge_base"

# Lazy-loaded knowledge base caches
_additives_db: Optional[List[Dict[str, Any]]] = None
_harmful_flags: Optional[Dict[str, Any]] = None
_nutrition_guidelines: Optional[Dict[str, Any]] = None

# Build alias → entry lookup on first load
_alias_index: Optional[Dict[str, Dict[str, Any]]] = None


# ── Knowledge base loaders ─────────────────────────────────────────────────────

def _load_additives_db() -> Tuple[List[Dict], Dict[str, Dict]]:
    global _additives_db, _alias_index
    if _additives_db is not None:
        return _additives_db, _alias_index  # type: ignore[return-value]
    with open(_KB / "fssai_additives.json", encoding="utf-8") as f:
        _additives_db = json.load(f)
    # Build alias index: every alias and the code itself → entry
    _alias_index = {}
    for entry in _additives_db:
        code_lower = entry.get("code", "").lower().strip()
        if code_lower:
            _alias_index[code_lower] = entry
        for alias in entry.get("aliases", []):
            alias_lower = alias.lower().strip()
            if alias_lower:
                _alias_index[alias_lower] = entry
    return _additives_db, _alias_index


def _load_harmful_flags() -> Dict[str, Any]:
    global _harmful_flags
    if _harmful_flags is None:
        with open(_KB / "harmful_flags.json", encoding="utf-8") as f:
            _harmful_flags = json.load(f)
    return _harmful_flags


def _load_nutrition_guidelines() -> Dict[str, Any]:
    global _nutrition_guidelines
    if _nutrition_guidelines is None:
        with open(_KB / "nutrition_guidelines.json", encoding="utf-8") as f:
            _nutrition_guidelines = json.load(f)
    return _nutrition_guidelines


# ── Additive matching ──────────────────────────────────────────────────────────

# Try to import rapidfuzz for fuzzy OCR correction; fall back to exact match.
try:
    from rapidfuzz import process as _rp_process, fuzz as _rp_fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False
    logger.info("rapidfuzz not installed — additive matching uses exact/substring only.")


def _fuzzy_match_ingredient(
    token: str,
    alias_index: Dict[str, Dict],
    threshold: int = 80,
) -> Optional[Dict[str, Any]]:
    """
    Match a single ingredient token against the alias index.

    Strategy (in order):
    1. Exact alias match (O(1), case-insensitive)
    2. Substring containment (catches "contains INS 621" type strings)
    3. rapidfuzz WRatio ≥ threshold (handles OCR typos: "E62l" → "E621")
    4. Return None if no match

    Returns matched entry dict or None.
    """
    token_lower = token.lower().strip()

    # 1. Exact match
    if token_lower in alias_index:
        return alias_index[token_lower]

    # 2. Substring: check if any alias appears inside the token string
    for alias, entry in alias_index.items():
        if len(alias) >= 3 and alias in token_lower:
            return entry

    # 3. Fuzzy match via rapidfuzz
    if _RAPIDFUZZ_AVAILABLE and len(token_lower) >= 4:
        match_result = _rp_process.extractOne(
            token_lower,
            list(alias_index.keys()),
            scorer=_rp_fuzz.WRatio,
            score_cutoff=threshold,
        )
        if match_result:
            matched_alias = match_result[0]
            return alias_index.get(matched_alias)

    # 4. INS/E code pattern heuristic: "ins621" → "INS 621"
    ins_pattern = re.match(r"(?:ins|e)\s*(\d{2,4}[a-z]?)", token_lower)
    if ins_pattern:
        normalised = f"INS {ins_pattern.group(1).upper()}"
        normalised_lower = normalised.lower()
        if normalised_lower in alias_index:
            return alias_index[normalised_lower]

    return None


def _detect_additives(
    ingredients: List[str],
    alias_index: Dict[str, Dict],
    harmful_flags: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Scan the ingredients list for known FSSAI additives.

    Returns list of AdditiveFlag-shaped dicts.
    """
    from rag_pipeline.utils.embedder import retrieve_context
    from rag_pipeline.utils.llm_prompts import format_additive_explanation

    high_risk_codes = set(c.lower() for c in harmful_flags.get("risk_tiers", {}).get("high_risk", []))
    moderate_risk_codes = set(c.lower() for c in harmful_flags.get("risk_tiers", {}).get("moderate_risk", []))
    banned_codes = set(c.lower() for c in harmful_flags.get("risk_tiers", {}).get("banned_in_india", []))

    found: Dict[str, Dict] = {}  # code → flag dict (deduplicate)

    for token in ingredients:
        entry = _fuzzy_match_ingredient(token, alias_index)
        if entry is None:
            continue

        code = entry.get("code", "UNKNOWN")
        if code in found:
            continue  # already recorded

        code_lower = code.lower()
        if code_lower in high_risk_codes:
            risk = "high"
        elif code_lower in moderate_risk_codes:
            risk = "moderate"
        else:
            risk = "low" if entry.get("safety") == "green" else "moderate"

        # Use FAISS to enrich with KB context (gets health_risks, etc.)
        context_entries = retrieve_context(f"{code} {entry.get('name', '')}", top_k=1)
        enriched = context_entries[0] if context_entries else entry

        explanation = format_additive_explanation(enriched)
        retrieval_backend = "faiss" if context_entries and "_similarity_score" in context_entries[0] else "keyword"

        found[code] = {
            "code": code,
            "name": enriched.get("name", entry.get("name", "Unknown")),
            "category": enriched.get("category", entry.get("category", "Unknown")),
            "risk": risk,
            "safety_color": enriched.get("safety", entry.get("safety", "yellow")),
            "banned_in_india": bool(entry.get("banned_in_india") or code_lower in banned_codes),
            "fssai_limit": enriched.get("fssai_limit", entry.get("fssai_limit")),
            "health_risks": enriched.get("health_risks", entry.get("health_risks")),
            "explanation": explanation,
            "match_confidence": 1.0,
            "_retrieval_backend": retrieval_backend,
        }

    return list(found.values())


# ── Nutrition rule engine ──────────────────────────────────────────────────────

def _evaluate_nutrition(
    nutrition: Dict[str, Optional[float]],
    guidelines: Dict[str, Any],
    harmful_flags: Dict[str, Any],
) -> Tuple[List[str], List[Dict[str, str]], float]:
    """
    Compare extracted nutrition values against FSSAI thresholds.

    Returns:
        (warnings_list, warning_details_list, score_deduction)
    """
    from rag_pipeline.utils.llm_prompts import format_nutrient_warning

    thresholds = guidelines.get("fssai_traffic_light_thresholds_per_100g", {})
    deductions = guidelines.get("score_deductions", {})
    additions = guidelines.get("score_additions", {})

    warnings: List[str] = []
    warning_details: List[Dict[str, str]] = []
    score = 10.0  # start at perfect score

    # ── Sugar ─────────────────────────────────────────────────────────────────
    sugar = nutrition.get("sugars_g")
    if sugar is not None:
        sugar_high_thresh = thresholds.get("total_sugars_g", {}).get("high", 22.5)
        sugar_med_thresh = thresholds.get("total_sugars_g", {}).get("medium", 12.5)
        if sugar >= sugar_high_thresh:
            warnings.append("High Sugar")
            warning_details.append(format_nutrient_warning("sugar_high", threshold=sugar_high_thresh))
            score -= deductions.get("sugar_above_22g", 3.0)
        elif sugar >= sugar_med_thresh:
            score -= deductions.get("sugar_above_12g", 1.5)
        elif sugar < 5.0:
            score += additions.get("low_sugar_below_5g", 0.5)

    # ── Sodium ────────────────────────────────────────────────────────────────
    sodium = nutrition.get("sodium_mg")
    if sodium is not None:
        sodium_high = thresholds.get("sodium_mg", {}).get("high", 600)
        sodium_med = thresholds.get("sodium_mg", {}).get("medium", 400)
        if sodium >= sodium_high:
            warnings.append("High Sodium")
            warning_details.append(format_nutrient_warning("sodium_high", threshold=sodium_high))
            score -= deductions.get("sodium_above_600mg", 2.5)
        elif sodium >= sodium_med:
            score -= deductions.get("sodium_above_400mg", 1.0)
        elif sodium < 120:
            score += additions.get("low_sodium_below_120mg", 0.5)

    # ── Trans fat ─────────────────────────────────────────────────────────────
    trans_fat = nutrition.get("trans_fat_g")
    if trans_fat is not None and trans_fat > 0.1:
        warnings.append("Contains Trans Fat")
        warning_details.append(format_nutrient_warning("trans_fat_present"))
        score -= deductions.get("trans_fat_above_1g", 4.0) if trans_fat >= 1.0 else deductions.get("trans_fat_above_0.2g", 2.0)

    # ── Saturated fat ─────────────────────────────────────────────────────────
    sat_fat = nutrition.get("saturated_fat_g")
    if sat_fat is not None:
        sat_high = thresholds.get("saturated_fat_g", {}).get("high", 5.0)
        if sat_fat >= sat_high:
            warnings.append("High Saturated Fat")
            warning_details.append(format_nutrient_warning("saturated_fat_high", threshold=sat_high))
            score -= deductions.get("saturated_fat_above_5g", 2.0)

    # ── Calories ──────────────────────────────────────────────────────────────
    calories = nutrition.get("calories")
    if calories is not None:
        cal_high = thresholds.get("energy_kcal", {}).get("high", 400)
        if calories >= cal_high:
            warnings.append("High Calorie Density")
            warning_details.append(format_nutrient_warning("calories_high", threshold=cal_high))
            score -= deductions.get("calories_above_400kcal", 1.5)

    # ── Protein bonus ─────────────────────────────────────────────────────────
    protein = nutrition.get("protein_g")
    if protein is not None and protein >= 10:
        score += additions.get("protein_above_10g", 1.0)

    # ── Fibre bonus ───────────────────────────────────────────────────────────
    fiber = nutrition.get("fiber_g")
    if fiber is not None:
        if fiber >= 6:
            score += additions.get("fiber_above_6g", 2.0)
        elif fiber >= 3:
            score += additions.get("fiber_above_3g", 1.0)

    return warnings, warning_details, max(0.0, min(10.0, score))


# ── Ultra-processed marker detection ──────────────────────────────────────────

def _detect_ultra_processed(
    ingredients: List[str],
    harmful_flags: Dict[str, Any],
) -> List[str]:
    """Return list of ultra-processed marker strings found in ingredients."""
    markers = harmful_flags.get("ultra_processed_markers", [])
    found = []
    ingredients_str = " ".join(ingredients).lower()
    for marker in markers:
        if marker.lower() in ingredients_str:
            found.append(marker)
    return found


# ── Allergen detection ─────────────────────────────────────────────────────────

def _detect_allergens(
    ingredients: List[str],
    harmful_flags: Dict[str, Any],
) -> List[str]:
    """Return list of allergens found in the ingredients text."""
    allergen_list = harmful_flags.get("allergens", {}).get("list", [])
    ingredients_str = " ".join(ingredients).lower()
    found = []
    for allergen in allergen_list:
        if allergen.lower() in ingredients_str:
            found.append(allergen)
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for a in found:
        if a not in seen:
            seen.add(a)
            deduped.append(a)
    return deduped


# ── Public entrypoint ──────────────────────────────────────────────────────────

def analyze_label_text(
    nutrition_text: str = "",
    ingredients_text: str = "",
    *,
    pre_parsed_nutrition: Optional[Dict[str, Any]] = None,
    pre_parsed_ingredients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyse food label text and return a structured RAG analysis result.

    Args:
        nutrition_text: Raw OCR text of the nutrition panel (can be empty string).
        ingredients_text: Raw OCR text of the ingredients list (can be empty string).
        pre_parsed_nutrition: Optional already-parsed nutrition dict (skips ocr_parser).
        pre_parsed_ingredients: Optional already-parsed ingredients list (skips ocr_parser).

    Returns:
        Plain dict matching the RAGAnalysisResult schema. Always safe to JSON-serialise.
        Keys: nutrition_summary, additive_flags, fssai_compliance, compliance_message,
              warnings, warning_details, score, score_grade, ingredients_detected,
              ultra_processed_markers_found, allergens_detected, healthy_alternative,
              pipeline_version, retrieval_backend.
    """
    t0 = time.time()

    from rag_pipeline.utils.ocr_parser import parse_nutrition_text, parse_ingredients_text
    from rag_pipeline.utils.llm_prompts import (
        build_compliance_message,
        build_healthy_alternative_tip,
        format_nutrient_warning,
    )
    from rag_pipeline.output_schemas import RAGAnalysisResult, AdditiveFlag

    # ── Step 1: Parse OCR text ─────────────────────────────────────────────────
    nutrition = pre_parsed_nutrition or parse_nutrition_text(
        " ".join([nutrition_text, ingredients_text])
    )
    ingredients = pre_parsed_ingredients or parse_ingredients_text(ingredients_text or nutrition_text)

    # ── Step 2: Load knowledge bases ──────────────────────────────────────────
    _, alias_index = _load_additives_db()
    harmful_flags = _load_harmful_flags()
    guidelines = _load_nutrition_guidelines()

    # ── Step 3: Detect additives ───────────────────────────────────────────────
    additive_flag_dicts = _detect_additives(ingredients, alias_index, harmful_flags)

    # ── Step 4: Nutrition rule engine ─────────────────────────────────────────
    warnings, warning_details, nutrition_score = _evaluate_nutrition(
        nutrition, guidelines, harmful_flags
    )

    # ── Step 5: Ultra-processed markers ───────────────────────────────────────
    ultra_processed = _detect_ultra_processed(ingredients, harmful_flags)
    deductions = guidelines.get("score_deductions", {})
    up_deduction = min(
        len(ultra_processed) * deductions.get("ultra_processed_marker_each", 0.25),
        2.0,  # cap at 2 points
    )
    score = max(0.0, nutrition_score - up_deduction)

    if len(ultra_processed) > 2:
        warnings.append("Ultra-Processed Product")
        warning_details.append(
            format_nutrient_warning("ultra_processed", count=len(ultra_processed))
        )

    # ── Step 6: Allergens ─────────────────────────────────────────────────────
    allergens = _detect_allergens(ingredients, harmful_flags)
    for allergen in allergens[:3]:  # show top 3 allergen warnings
        warnings.append(f"Allergen: {allergen.title()}")
        warning_details.append(
            format_nutrient_warning("allergen_detected", allergen=allergen.title())
        )
    score -= len(allergens) * deductions.get("allergen_present", 0.5)
    score = max(0.0, score)

    # ── Step 7: Additive score adjustments ────────────────────────────────────
    banned_in_product = []
    for flag in additive_flag_dicts:
        if flag.get("banned_in_india"):
            score -= deductions.get("banned_additive_each", 3.0)
            banned_in_product.append(flag["code"])
        elif flag.get("risk") == "high":
            score -= deductions.get("high_risk_additive_each", 2.0)
        elif flag.get("risk") == "moderate":
            score -= deductions.get("moderate_risk_additive_each", 0.75)

    score = max(0.0, min(10.0, score))

    # No additives bonus
    if not additive_flag_dicts:
        score = min(10.0, score + guidelines.get("score_additions", {}).get("no_additives", 1.0))

    score = round(score, 1)

    # ── Step 8: Grade and compliance ──────────────────────────────────────────
    grade_map = guidelines.get("score_to_grade_map", {})
    if score >= grade_map.get("GREEN", {}).get("min", 7.0):
        score_grade = "GREEN"
    elif score >= grade_map.get("YELLOW", {}).get("min", 4.0):
        score_grade = "YELLOW"
    else:
        score_grade = "RED"

    fssai_compliant = len(banned_in_product) == 0
    compliance_message = build_compliance_message(banned_in_product)

    # ── Step 9: Maida detection (special case for Indian products) ────────────
    maida_tokens = {"maida", "refined flour", "refined wheat flour", "all purpose flour", "bleached flour"}
    if any(t in " ".join(ingredients) for t in maida_tokens):
        warnings.append("Contains Refined Wheat Flour (Maida)")
        warning_details.append(format_nutrient_warning("maida_detected"))

    # ── Step 10: Healthy alternative tip ─────────────────────────────────────
    healthy_alternative = build_healthy_alternative_tip(score, warnings)

    # ── Step 11: Determine retrieval backend used ─────────────────────────────
    retrieval_backends = {f.get("_retrieval_backend", "keyword") for f in additive_flag_dicts}
    if "faiss" in retrieval_backends:
        retrieval_backend = "faiss"
    elif additive_flag_dicts:
        retrieval_backend = "keyword"
    else:
        retrieval_backend = "none"

    # Strip internal fields before output
    clean_flags = []
    for flag in additive_flag_dicts:
        clean_flag = {k: v for k, v in flag.items() if not k.startswith("_")}
        clean_flags.append(clean_flag)

    elapsed = round(time.time() - t0, 3)
    logger.info(
        "RAG pipeline complete in %.3fs — score=%.1f (%s), additives=%d, warnings=%d",
        elapsed, score, score_grade, len(clean_flags), len(warnings),
    )

    return {
        "nutrition_summary": nutrition,
        "additive_flags": clean_flags,
        "fssai_compliance": fssai_compliant,
        "compliance_message": compliance_message,
        "warnings": warnings,
        "warning_details": warning_details,
        "score": score,
        "score_grade": score_grade,
        "ingredients_detected": ingredients,
        "ultra_processed_markers_found": ultra_processed,
        "allergens_detected": allergens,
        "healthy_alternative": healthy_alternative,
        "pipeline_version": "1.0.0",
        "retrieval_backend": retrieval_backend,
        "analysis_time_s": elapsed,
    }
