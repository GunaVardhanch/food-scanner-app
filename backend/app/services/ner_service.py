import torch
from transformers import BertTokenizerFast, BertForTokenClassification
import re
import os

from app.config import NUTRITION_NER_MODEL_DIR

class NERService:
    def __init__(self, model_dir=None):
        if model_dir is None:
            model_dir = NUTRITION_NER_MODEL_DIR
        self.tag2id = {"O": 0, "B-CAL": 1, "I-CAL": 2, "B-SUGAR": 3, "I-SUGAR": 4, "B-ADD": 5, "I-ADD": 6}
        self.id2tag = {v: k for k, v in self.tag2id.items()}
        self.model_dir = model_dir

        try:
            if os.path.exists(model_dir) and any(
                f.endswith(".bin") or f.endswith(".safetensors") for f in os.listdir(model_dir)
            ):
                self.tokenizer = BertTokenizerFast.from_pretrained('bert-base-multilingual-cased')
                self.model = BertForTokenClassification.from_pretrained(model_dir)
                self.is_ready = True
                print(f"NERService: Loaded model from {model_dir}")
            else:
                self.is_ready = False
                print("NERService: Model not found. Running in heuristic fallback mode.")
        except Exception as e:
            print(f"NERService: Error loading model: {e}")
            self.is_ready = False

    def extract(self, text):
        if not self.is_ready:
            return self._heuristic_extract(text)

        # BERT Inference
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
        with torch.no_grad():
            outputs = self.model(**inputs).logits

        predictions = torch.argmax(outputs, dim=2)
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        bert_result = self._parse_bert_entities(tokens, predictions[0])

        # Fill any missing fields with heuristic (BERT may not have all tags)
        heuristic_result = self._heuristic_extract(text)
        for key, value in heuristic_result.items():
            if bert_result.get(key) is None:
                bert_result[key] = value

        return bert_result

    def _parse_bert_entities(self, tokens, predictions):
        """Parse BERT token-level predictions into structured nutrition entities."""
        entities = {
            "sugar_g": None, "calories": None, "protein_g": None,
            "fat_g": None, "carbs_g": None, "additives_found": []
        }
        current_tag = None
        current_span = []

        for token, pred in zip(tokens, predictions):
            tag = self.id2tag.get(pred.item(), "O")
            if token in ['[CLS]', '[SEP]', '[PAD]']:
                continue
            if tag.startswith("B-"):
                if current_tag and current_span:
                    self._assign_entity(entities, current_tag, current_span)
                current_tag = tag[2:]
                current_span = [token]
            elif tag.startswith("I-") and current_tag == tag[2:]:
                current_span.append(token)
            else:
                if current_tag and current_span:
                    self._assign_entity(entities, current_tag, current_span)
                current_tag = None
                current_span = []

        if current_tag and current_span:
            self._assign_entity(entities, current_tag, current_span)

        return entities

    def _assign_entity(self, entities, tag, tokens):
        """Convert a BERT entity span to a numeric value."""
        span_text = "".join(t.replace("##", "") for t in tokens)
        nums = re.findall(r'\d+\.?\d*', span_text)
        if not nums:
            return
        value = float(nums[0])
        if tag == "CAL":
            entities["calories"] = int(value)
        elif tag == "SUGAR":
            entities["sugar_g"] = value

    def _heuristic_extract(self, text):
        """
        Robust multi-pattern regex extraction.
        Returns None for fields that could not be found — avoids biasing
        health scores with wrong assumed defaults.
        """
        text_lower = text.lower()

        # ── Calories ────────────────────────────────────────────────────────────
        calories = None
        cal_patterns = [
            r'energy[:\s]+(\d+)\s*(?:kcal|cal\b)',       # Energy: 350 kcal
            r'(\d+)\s*kcal',                              # 350 kcal
            r'calories?[:\s]+(\d+)',                      # Calories: 350
            r'(\d+)\s*cal(?:ories?)?\b',                  # 350 Cal
            r'(\d+)\s*kj',                                # 350 kJ (kilojoules)
        ]
        for pat in cal_patterns:
            m = re.search(pat, text_lower)
            if m:
                raw = int(m.group(1))
                # Convert kJ → kcal if the pattern matched kilojoules and value looks like kJ
                if 'kj' in pat and raw > 400:
                    raw = round(raw / 4.184)
                calories = raw
                break

        # ── Sugar ───────────────────────────────────────────────────────────────
        sugar = None
        sugar_patterns = [
            r'of which sugars?[:\s]+(\d+\.?\d*)',         # of which sugars: 12.5
            r'(?:total\s*)?sugars?[:\s]+(\d+\.?\d*)\s*g', # Total Sugars: 12.5g
            r'sugars?[:\s]+(\d+\.?\d*)',                   # Sugars: 12.5
        ]
        for pat in sugar_patterns:
            m = re.search(pat, text_lower)
            if m:
                sugar = float(m.group(1))
                break

        # ── Fat ─────────────────────────────────────────────────────────────────
        fat = None
        fat_patterns = [
            r'(?:total\s*)?fat[:\s]+(\d+\.?\d*)\s*g',    # Total Fat: 10g
            r'fat[:\s]+(\d+\.?\d*)',                       # Fat: 10
            r'lipids?[:\s]+(\d+\.?\d*)',                   # Lipids: 10 (European labels)
        ]
        for pat in fat_patterns:
            m = re.search(pat, text_lower)
            if m:
                fat = float(m.group(1))
                break

        # ── Carbohydrates ────────────────────────────────────────────────────────
        carbs = None
        carbs_patterns = [
            r'(?:total\s*)?carbohydrates?[:\s]+(\d+\.?\d*)\s*g', # Total Carbohydrates: 30g
            r'(?:total\s*)?carbohydrates?[:\s]+(\d+\.?\d*)',      # Total Carbohydrates: 30
            r'carbs?[:\s]+(\d+\.?\d*)\s*g',                       # Carbs: 30g
            r'carbs?[:\s]+(\d+\.?\d*)',                            # Carbs: 30
        ]
        for pat in carbs_patterns:
            m = re.search(pat, text_lower)
            if m:
                carbs = float(m.group(1))
                break

        # ── Protein ──────────────────────────────────────────────────────────────
        protein = None
        protein_patterns = [
            r'proteins?[:\s]+(\d+\.?\d*)\s*g',           # Protein: 5g
            r'proteins?[:\s]+(\d+\.?\d*)',                # Protein: 5
        ]
        for pat in protein_patterns:
            m = re.search(pat, text_lower)
            if m:
                protein = float(m.group(1))
                break

        return {
            "sugar_g": sugar,        # None if OCR text doesn't contain it
            "calories": calories,    # None if OCR text doesn't contain it
            "protein_g": protein,    # None if OCR text doesn't contain it
            "fat_g": fat,            # None if OCR text doesn't contain it
            "carbs_g": carbs,        # None if OCR text doesn't contain it
            "additives_found": []    # Handled by AdditivesExpert
        }

if __name__ == "__main__":
    ner = NERService()
    tests = [
        "Nutrition Facts: Energy 525 kcal, Total Sugars 45.5g, Protein 6g, Total Fat 18g, Carbohydrates 62g.",
        "Per 100g: Calories 200, Fat 10.2g, Carbs 25g, of which sugars 5.1g, Protein 3.5g.",
        "Energy 1200kJ, Lipids 15g, Carbohydrates 30g, of which sugars 8g, Proteins 4g.",
        "No nutrition info here.",
    ]
    for t in tests:
        print(f"\nText: {t[:60]}...\nResult: {ner.extract(t)}")
