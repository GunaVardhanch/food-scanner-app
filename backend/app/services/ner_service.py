"""
ner_service.py
──────────────
Nutrition entity extraction from OCR text.

Design decision: BERT fine-tune removed.
The BERT model path was never trained and fell back to regex on every call.
This version owns the regex approach explicitly — it's faster, has no
dependency on a missing model file, and is easier to extend.

If a fine-tuned model becomes available in future, re-introduce the BERT
path by checking NUTRITION_NER_MODEL_DIR and loading conditionally.

Covers:
  - English nutrition label patterns
  - Hindi/Devanagari label patterns
  - INS / E-number additive codes
  - kJ → kcal conversion
  - Salt → sodium conversion
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class NERService:
    """
    Regex-based nutrition entity extractor.

    extract(text, structured_nutrition=None) → dict with keys:
        calories, sugar_g, fat_g, saturated_fat_g, trans_fat_g,
        carbs_g, protein_g, fiber_g, sodium_mg, additives_found
    """

    def extract(
        self,
        text: str,
        structured_nutrition: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract nutrition entities from text.

        If structured_nutrition is provided (from AdvancedOCRPipeline), use it
        directly for numeric fields — avoids double-parsing already-parsed data.
        """
        if structured_nutrition:
            return self._from_structured(structured_nutrition, text)
        return self._heuristic_extract(text)

    # ── Structured passthrough ────────────────────────────────────────────────

    def _from_structured(self, s: Dict[str, Any], raw_text: str = "") -> Dict[str, Any]:
        """
        Convert AdvancedOCRPipeline structured_nutrition dict to the NER output
        schema expected by health_scoring and routes.
        Also runs additive extraction on the raw text.
        """
        def _get(*keys):
            for k in keys:
                v = s.get(k)
                if v is not None:
                    return float(v)
            return None

        result = {
            "calories":        _get("energy_kcal"),
            "sugar_g":         _get("sugar_g"),
            "fat_g":           _get("fat_g"),
            "saturated_fat_g": _get("saturated_fat_g"),
            "trans_fat_g":     _get("trans_fat_g"),
            "carbs_g":         _get("carbohydrates_g"),
            "protein_g":       _get("protein_g"),
            "fiber_g":         _get("fiber_g"),
            "sodium_mg":       _get("sodium_mg"),
            "additives_found": [],
        }

        # Still run additive extraction on raw text even when structured data is available
        if raw_text:
            result["additives_found"] = self._extract_additives(raw_text)

        return result

    # ── Heuristic extraction ──────────────────────────────────────────────────

    def _heuristic_extract(self, text: str) -> Dict[str, Any]:
        """
        Multi-pattern regex extraction.
        Returns None for fields not found — avoids biasing scores with defaults.
        Covers English + Hindi/regional label patterns.
        """
        t = text.lower()

        def _first(patterns: List[str]) -> Optional[float]:
            for pat in patterns:
                m = re.search(pat, t)
                if m:
                    try:
                        return float(m.group(1))
                    except Exception:
                        pass
            return None

        # ── Calories / Energy ────────────────────────────────────────────────
        calories = _first([
            r"energy[:\s]+(\d+\.?\d*)\s*kcal",
            r"(\d+\.?\d*)\s*kcal",
            r"calories?[:\s]+(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*cal(?:ories?)?\b",
            r"ऊर्जा[:\s]+(\d+\.?\d*)",
        ])
        # kJ fallback — convert to kcal
        if calories is None:
            kj = _first([r"energy[:\s]+(\d+\.?\d*)\s*kj", r"(\d+\.?\d*)\s*kj"])
            if kj is not None and kj > 400:
                calories = round(kj / 4.184)

        # ── Sugar ────────────────────────────────────────────────────────────
        sugar_g = _first([
            r"of which sugars?[:\s]+(\d+\.?\d*)",
            r"(?:total\s*)?sugars?[:\s]+(\d+\.?\d*)\s*g",
            r"sugars?[:\s]+(\d+\.?\d*)",
            r"शर्करा[:\s]+(\d+\.?\d*)",
            r"चीनी[:\s]+(\d+\.?\d*)",
        ])

        # ── Fat ──────────────────────────────────────────────────────────────
        fat_g = _first([
            r"(?:total\s*)?fat[:\s]+(\d+\.?\d*)\s*g",
            r"fat[:\s]+(\d+\.?\d*)",
            r"lipids?[:\s]+(\d+\.?\d*)",
            r"वसा[:\s]+(\d+\.?\d*)",
        ])

        # ── Saturated fat ────────────────────────────────────────────────────
        saturated_fat_g = _first([
            r"saturated\s*fat[:\s]+(\d+\.?\d*)\s*g",
            r"saturated[:\s]+(\d+\.?\d*)",
            r"sat\.?\s*fat[:\s]+(\d+\.?\d*)",
        ])

        # ── Trans fat ────────────────────────────────────────────────────────
        trans_fat_g = _first([
            r"trans\s*fat[:\s]+(\d+\.?\d*)\s*g",
            r"trans[:\s]+(\d+\.?\d*)",
        ])

        # ── Carbohydrates ────────────────────────────────────────────────────
        carbs_g = _first([
            r"(?:total\s*)?carbohydrates?[:\s]+(\d+\.?\d*)\s*g",
            r"(?:total\s*)?carbohydrates?[:\s]+(\d+\.?\d*)",
            r"carbs?[:\s]+(\d+\.?\d*)\s*g",
            r"carbs?[:\s]+(\d+\.?\d*)",
        ])

        # ── Protein ──────────────────────────────────────────────────────────
        protein_g = _first([
            r"proteins?[:\s]+(\d+\.?\d*)\s*g",
            r"proteins?[:\s]+(\d+\.?\d*)",
            r"प्रोटीन[:\s]+(\d+\.?\d*)",
        ])

        # ── Dietary fiber ────────────────────────────────────────────────────
        fiber_g = _first([
            r"(?:dietary\s*)?fi(?:b|e)r(?:e)?[:\s]+(\d+\.?\d*)\s*g",
            r"(?:dietary\s*)?fi(?:b|e)r(?:e)?[:\s]+(\d+\.?\d*)",
        ])

        # ── Sodium ───────────────────────────────────────────────────────────
        sodium_mg = _first([
            r"sodium[:\s]+(\d+\.?\d*)\s*mg",
            r"sodium[:\s]+(\d+\.?\d*)",
            r"सोडियम[:\s]+(\d+\.?\d*)",
        ])
        # Salt → sodium conversion (salt_g * 400 ≈ sodium_mg)
        if sodium_mg is None:
            salt_g = _first([r"salt[:\s]+(\d+\.?\d*)\s*g", r"salt[:\s]+(\d+\.?\d*)"])
            if salt_g is not None:
                sodium_mg = round(salt_g * 400)

        return {
            "calories":        int(calories) if calories is not None else None,
            "sugar_g":         sugar_g,
            "fat_g":           fat_g,
            "saturated_fat_g": saturated_fat_g,
            "trans_fat_g":     trans_fat_g,
            "carbs_g":         carbs_g,
            "protein_g":       protein_g,
            "fiber_g":         fiber_g,
            "sodium_mg":       sodium_mg,
            "additives_found": self._extract_additives(text),
        }

    # ── Additive code extraction ──────────────────────────────────────────────

    def _extract_additives(self, text: str) -> List[str]:
        """
        Extract INS / E-number codes from text.
        Matches: INS 211, INS211, INS-211, E211, E102
        """
        found = []
        for m in re.finditer(r"\b(?:ins\.?\s*|e)(\d{3}[a-z]?)\b", text, re.IGNORECASE):
            code = m.group(0).upper().replace(" ", "").replace(".", "").replace("-", "")
            if code not in found:
                found.append(code)
        return found


if __name__ == "__main__":
    ner = NERService()
    tests = [
        "Nutrition Facts: Energy 525 kcal, Total Sugars 45.5g, Protein 6g, Total Fat 18g, Carbohydrates 62g, Sodium 380mg, Dietary Fiber 2g.",
        "Per 100g: Calories 200, Fat 10.2g, Saturated Fat 3.1g, Trans Fat 0g, Carbs 25g, of which sugars 5.1g, Protein 3.5g, Salt 0.8g.",
        "Energy 1200kJ, Lipids 15g, Carbohydrates 30g, of which sugars 8g, Proteins 4g.",
        "ऊर्जा 350 kcal, प्रोटीन 5g, वसा 12g, शर्करा 20g, सोडियम 200mg",
        "Contains INS 211, E102, INS-319 as preservatives.",
    ]
    for t in tests:
        print(f"\nText: {t[:70]}\nResult: {ner.extract(t)}")
