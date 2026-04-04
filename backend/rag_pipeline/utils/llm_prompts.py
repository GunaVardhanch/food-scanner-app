"""
utils/llm_prompts.py
─────────────────────
Warning explanation templates for the RAG pipeline.

This module does NOT call any LLM or external API. It provides deterministic
string templates that are filled in by the rule engine to generate
human-readable explanations for each additive flag and nutrition warning.

If you later want to upgrade to an actual LLM, replace format_warning_explanation()
with an LLM call using these templates as the system prompt.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ── Per-nutrient warning explanations ─────────────────────────────────────────

NUTRIENT_WARNINGS: Dict[str, Dict[str, str]] = {
    "sugar_high": {
        "title": "High Sugar",
        "explanation": (
            "This product contains high levels of sugar (>{threshold}g per 100g). "
            "Excess sugar consumption is strongly linked to obesity, type 2 diabetes, "
            "tooth decay, and cardiovascular disease. FSSAI recommends limiting added "
            "sugar to 25g per day for adults."
        ),
    },
    "sodium_high": {
        "title": "High Sodium",
        "explanation": (
            "Sodium content exceeds {threshold}mg per 100g. High sodium intake "
            "raises blood pressure and increases risk of heart disease and stroke. "
            "FSSAI recommends a maximum of 2000mg sodium per day. "
            "This product may provide a significant fraction of that in one serving."
        ),
    },
    "trans_fat_present": {
        "title": "Contains Trans Fat",
        "explanation": (
            "This product contains trans fats (partially hydrogenated oils / vanaspati). "
            "Trans fats raise LDL (bad) cholesterol and lower HDL (good) cholesterol, "
            "significantly increasing cardiovascular disease risk. FSSAI limits trans fat "
            "to 2g per 100g; WHO recommends eliminating them entirely."
        ),
    },
    "saturated_fat_high": {
        "title": "High Saturated Fat",
        "explanation": (
            "Saturated fat exceeds {threshold}g per 100g. High saturated fat intake "
            "raises LDL cholesterol and is associated with increased heart disease risk."
        ),
    },
    "calories_high": {
        "title": "High Calorie Density",
        "explanation": (
            "Energy density exceeds {threshold} kcal per 100g. "
            "High-calorie-density foods can contribute to weight gain when consumed "
            "regularly without compensating physical activity."
        ),
    },
    "maida_detected": {
        "title": "Contains Refined Wheat Flour (Maida)",
        "explanation": (
            "Refined wheat flour (maida) has a high glycaemic index, causing rapid blood "
            "sugar spikes. It is stripped of natural fibre and nutrients during processing. "
            "Regular consumption is linked to blood sugar dysregulation and gut health issues."
        ),
    },
    "ultra_processed": {
        "title": "Ultra-Processed Product",
        "explanation": (
            "This product contains {count} ultra-processed food markers "
            "(e.g. modified starches, synthetic flavours, emulsifiers). "
            "Ultra-processed foods are associated with higher risks of obesity, "
            "metabolic syndrome, and all-cause mortality according to multiple cohort studies."
        ),
    },
    "allergen_detected": {
        "title": "Allergen Present: {allergen}",
        "explanation": (
            "This product contains or may contain {allergen}, a common food allergen. "
            "Individuals with {allergen} sensitivity or allergy should avoid this product."
        ),
    },
}

# ── Per-additive explanation template ─────────────────────────────────────────

ADDITIVE_TEMPLATE = (
    "{name} ({code}) is a {category} used in this product. "
    "Safety rating: {safety_upper}. "
    "{health_risks}"
    "{banned_note}"
    "{limit_note}"
)

# ── FSSAI compliance template ──────────────────────────────────────────────────

COMPLIANCE_PASS = (
    "No FSSAI-banned additives detected. All identified additives appear within "
    "permitted categories under FSSAI Food Safety and Standards (Food Products Standards "
    "and Food Additives) Regulations 2011."
)

COMPLIANCE_FAIL = (
    "⚠️ FSSAI Compliance Issue: This product contains {banned_list}, which are "
    "banned or not permitted under FSSAI regulations. This may indicate mislabelling "
    "or an illegal product."
)


# ── Public formatting functions ────────────────────────────────────────────────

def format_additive_explanation(entry: Dict[str, Any]) -> str:
    """
    Generate a human-readable explanation string for one additive knowledge base entry.

    Args:
        entry: Single dict from fssai_additives.json.

    Returns:
        Formatted explanation string.
    """
    banned_note = ""
    if entry.get("banned_in_india"):
        banned_note = " ⛔ BANNED under FSSAI regulations in India."

    limit = entry.get("fssai_limit", "")
    limit_note = f" FSSAI permitted limit: {limit}." if limit and limit != "GMP" else ""

    return ADDITIVE_TEMPLATE.format(
        name=entry.get("name", "Unknown"),
        code=entry.get("code", "?"),
        category=entry.get("category", "additive"),
        safety_upper=entry.get("safety", "unknown").upper(),
        health_risks=entry.get("health_risks", "No specific risks documented."),
        banned_note=banned_note,
        limit_note=limit_note,
    ).strip()


def format_nutrient_warning(
    warning_key: str,
    threshold: Optional[float] = None,
    allergen: Optional[str] = None,
    count: Optional[int] = None,
) -> Dict[str, str]:
    """
    Return a {title, explanation} dict for a given nutrient warning key.

    Args:
        warning_key: Key from NUTRIENT_WARNINGS dict.
        threshold: Numerical threshold to embed in the explanation.
        allergen: Allergen name for allergen_detected warnings.
        count: Count for ultra_processed warnings.

    Returns:
        {"title": "...", "explanation": "..."}
    """
    template = NUTRIENT_WARNINGS.get(warning_key)
    if not template:
        return {"title": warning_key, "explanation": "See product label for details."}

    explanation = template["explanation"].format(
        threshold=threshold or "",
        allergen=allergen or "",
        count=count or "",
    )
    title = template["title"].format(allergen=allergen or "")

    return {"title": title, "explanation": explanation}


def build_compliance_message(banned_codes: List[str]) -> str:
    """Return FSSAI compliance pass or fail message."""
    if not banned_codes:
        return COMPLIANCE_PASS
    return COMPLIANCE_FAIL.format(banned_list=", ".join(banned_codes))


def build_healthy_alternative_tip(score: float, detected_issues: List[str]) -> Optional[str]:
    """Return a contextual healthy eating tip based on the score and detected issues."""
    if score >= 7.0:
        return None  # No tip needed for healthy products

    tips = []
    if "High Sugar" in detected_issues or "sugar_high" in detected_issues:
        tips.append("choose fresh fruit instead of packaged sweets")
    if "High Sodium" in detected_issues or "sodium_high" in detected_issues:
        tips.append("opt for low-sodium alternatives or home-cooked meals")
    if "Contains Trans Fat" in detected_issues or "trans_fat_present" in detected_issues:
        tips.append("switch to products using cold-pressed oils")
    if "Contains Refined Wheat Flour (Maida)" in detected_issues:
        tips.append("prefer products made with whole wheat atta")

    if tips:
        return "Healthier alternatives: " + ", ".join(tips) + "."
    return "Try fresh, whole, minimally processed foods as a healthier alternative."
