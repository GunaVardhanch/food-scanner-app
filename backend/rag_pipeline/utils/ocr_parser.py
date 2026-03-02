"""
utils/ocr_parser.py
────────────────────
Parse raw OCR text from food labels into structured dicts and lists.

Handles the messy, inconsistent output typical of EasyOCR on Indian product labels:
  - Inconsistent spacing / newlines
  - Units fused with numbers (e.g. "15g" or "15 g" or "15gm")
  - Multiple languages mixed in
  - Row-merged nutrition tables
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


# ─── Nutrition Table Parser ───────────────────────────────────────────────────

# Comprehensive set of regex patterns to extract each nutrient value.
# Each pattern returns one named capture group "value" (float or int).
NUTRITION_PATTERNS: Dict[str, List[str]] = {
    "calories": [
        r"(?:energy|calories?|cal|kcal|kj)[^\d]{0,10}([\d]+(?:\.\d+)?)\s*(?:kcal|cal|kj)?",
        r"([\d]+(?:\.\d+)?)\s*(?:kcal|cal)\b",
    ],
    "protein_g": [
        r"protein[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"([\d]+(?:\.\d+)?)\s*g\s+protein",
    ],
    "fat_g": [
        r"(?:total\s+)?fat[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"(?:total\s+)?lipid[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
    ],
    "saturated_fat_g": [
        r"saturated\s+(?:fat|fatty\s+acid)[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"sat[.]\s*fat[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
    ],
    "trans_fat_g": [
        r"trans\s+(?:fat|fatty\s+acid)[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"trans[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
    ],
    "carbohydrates_g": [
        r"(?:total\s+)?carb(?:ohydrate)?s?[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"carbs?[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
    ],
    "sugars_g": [
        r"(?:total\s+)?sug(?:ar)?s?[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"sug(?:ar)?s?\s*[:\-–|]?\s*([\d]+(?:\.\d+)?)\s*g",
    ],
    "fiber_g": [
        r"(?:dietary\s+)?fib(?:re|er)[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"roughage[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
    ],
    "sodium_mg": [
        r"sodium[^\d]{0,10}([\d]+(?:\.\d+)?)\s*(?:mg|milligrams?)",
        r"salt[^\d]{0,10}([\d]+(?:\.\d+)?)\s*(?:mg)",
        r"([\d]+(?:\.\d+)?)\s*mg\s+sodium",
    ],
    "cholesterol_mg": [
        r"cholesterol[^\d]{0,10}([\d]+(?:\.\d+)?)\s*(?:mg)",
    ],
    "calcium_mg": [
        r"calcium[^\d]{0,10}([\d]+(?:\.\d+)?)\s*(?:mg)",
    ],
    "iron_mg": [
        r"\biron\b[^\d]{0,10}([\d]+(?:\.\d+)?)\s*(?:mg)",
    ],
    "serving_size_g": [
        r"serving\s+size[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"per\s+serve[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"per\s+serving[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
        r"per\s+packet[^\d]{0,10}([\d]+(?:\.\d+)?)\s*g",
    ],
}


def parse_nutrition_text(raw: str) -> Dict[str, Optional[float]]:
    """
    Extract nutrition values from raw OCR text of a nutrition panel.

    Args:
        raw: Raw OCR text as a single string (can have newlines).

    Returns:
        Dict with keys matching NUTRITION_PATTERNS. Values are floats or None.
        e.g. {"calories": 250.0, "protein_g": 5.0, "sodium_mg": 820.0, ...}
    """
    if not raw:
        return {}

    # Normalise: lowercase, collapse whitespace, remove soft-hyphens
    text = raw.lower()
    text = re.sub(r"[\u00ad\u200b\ufeff]", "", text)  # zero-width / soft-hyphen
    text = re.sub(r"\s+", " ", text)

    result: Dict[str, Optional[float]] = {}

    for nutrient, patterns in NUTRITION_PATTERNS.items():
        value: Optional[float] = None
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        result[nutrient] = value

    # Calories: kJ → kcal fallback
    if result.get("calories") is None:
        kj_match = re.search(r"([\d]+(?:\.\d+)?)\s*kj", text, re.IGNORECASE)
        if kj_match:
            result["calories"] = round(float(kj_match.group(1)) / 4.184, 1)

    return result


# ─── Ingredients List Parser ──────────────────────────────────────────────────

# Separator patterns between ingredients
_INGREDIENT_SEPARATORS = re.compile(r"[,;:|()\[\]{}]+")

# Strings that indicate the start of an ingredients section
_INGREDIENT_SECTION_TRIGGERS = re.compile(
    r"\b(?:ingredients?|contains?|made\s+(?:with|from)|composition)[:\s]",
    re.IGNORECASE,
)

# Strings to strip from individual tokens
_NOISE_TOKENS = re.compile(
    r"^(?:and|or|with|contains?|as|in|of|the|for|from|made|prepared|a|an)$",
    re.IGNORECASE,
)

# Remove percentage values like "(5%)" from ingredient tokens  
_PERCENTAGE_PATTERN = re.compile(r"\(?\s*[\d]+(?:\.\d+)?\s*%\s*\)?")


def parse_ingredients_text(raw: str) -> List[str]:
    """
    Convert a raw ingredients string into a clean list of ingredient tokens.

    Handles:
    - "Ingredients: wheat flour, salt, sugar (5%), ..."
    - Nested parentheses with sub-ingredients
    - Multiple separators (,  ;  |  :)
    - Mixed case

    Args:
        raw: Raw ingredients text.

    Returns:
        List of lowercase stripped ingredient strings.
    """
    if not raw:
        return []

    text = raw.strip()

    # Try to isolate the ingredients section if the full label text is provided
    trigger_match = _INGREDIENT_SECTION_TRIGGERS.search(text)
    if trigger_match:
        text = text[trigger_match.end():]

    # Truncate at common section-ending phrases
    for end_phrase in [
        r"\b(?:contains?|allergen|manufactured\s+in|best\s+before|expiry|mfg|dist|net\s+wt|net\s+weight|nutritional|nutrition\s+info|storage|keep)",
    ]:
        end_match = re.search(end_phrase, text, re.IGNORECASE)
        if end_match and end_match.start() > 20:
            text = text[: end_match.start()]

    # Remove percentage values
    text = _PERCENTAGE_PATTERN.sub("", text)

    # Strip common OCR artefacts
    text = re.sub(r"[\*\^\u00ae\u2122]", "", text)  # ®, ™, *
    text = re.sub(r"\s+", " ", text)

    # Split on separators
    raw_tokens = _INGREDIENT_SEPARATORS.split(text)

    ingredients: List[str] = []
    for token in raw_tokens:
        token = token.strip().lower()
        # Skip very short, empty, or obvious noise tokens
        if len(token) < 2:
            continue
        if _NOISE_TOKENS.match(token):
            continue
        if re.match(r"^[\d\s%.]+$", token):  # pure numbers / percentages
            continue
        ingredients.append(token)

    return ingredients


# ─── Combined Parser ──────────────────────────────────────────────────────────

def parse_label_text(
    raw_text: str,
    *,
    nutrition_raw: Optional[str] = None,
    ingredients_raw: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper that parses both nutrition and ingredients from
    either a single combined text blob or separate texts.

    Args:
        raw_text: Full label OCR text (used if separate texts not provided).
        nutrition_raw: Optional separate nutrition panel text.
        ingredients_raw: Optional separate ingredients text.

    Returns:
        {
            "nutrition": {calories: ..., protein_g: ..., ...},
            "ingredients": ["wheat flour", "salt", ...]
        }
    """
    nutrition_source = nutrition_raw if nutrition_raw else raw_text
    ingredients_source = ingredients_raw if ingredients_raw else raw_text

    return {
        "nutrition": parse_nutrition_text(nutrition_source),
        "ingredients": parse_ingredients_text(ingredients_source),
    }
