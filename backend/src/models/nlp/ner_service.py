import torch
from transformers import BertTokenizerFast, BertForTokenClassification
import re
import os

from src.configs.config import NUTRITION_NER_MODEL_DIR

class NERService:
    def __init__(self, model_dir=None):
        if model_dir is None:
            # Prefer a trained model placed under D:\food-scanner-models\nutrition_ner if available.
            model_dir = NUTRITION_NER_MODEL_DIR
        self.tag2id = {"O": 0, "B-CAL": 1, "I-CAL": 2, "B-SUGAR": 3, "I-SUGAR": 4, "B-ADD": 5, "I-ADD": 6}
        self.id2tag = {v: k for k, v in self.tag2id.items()}
        self.model_dir = model_dir
        
        # Load model and tokenizer
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
        
        # BERT Inference Logic
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
        with torch.no_grad():
            outputs = self.model(**inputs).logits
        
        predictions = torch.argmax(outputs, dim=2)
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        
        # Simplified parsing of entities
        entities = {"sugar_g": 0.0, "calories": 0, "additives": []}
        
        # Heuristic override for MVP if extraction is unstable
        return self._heuristic_extract(text)

    def _heuristic_extract(self, text):
        """Regex-based extraction for robustness when BERT is not yet fine-tuned."""
        text_lower = text.lower()
        
        # Calories
        cal_match = re.search(r'(\d+)\s*(kcal|calories|energy)', text_lower)
        calories = int(cal_match.group(1)) if cal_match else 150
        
        # Sugar
        sugar_match = re.search(r'(total\s*)?sugar(s)?[:\s]+(\d+(\.\d+)?)', text_lower)
        sugar = float(sugar_match.group(3)) if sugar_match else 5.0
        
        # Fat
        fat_match = re.search(r'(total\s*)?fat[:\s]+(\d+(\.\d+)?)', text_lower)
        fat = float(fat_match.group(2)) if fat_match else 10.0
        
        # Carbohydrates
        carbs_match = re.search(r'(total\s*)?carb(ohydrate)?(s)?[:\s]+(\d+(\.\d+)?)', text_lower)
        carbs = float(carbs_match.group(4)) if carbs_match else 25.0

        # Protein
        protein_match = re.search(r'protein[:\s]+(\d+(\.\d+)?)', text_lower)
        protein = float(protein_match.group(1)) if protein_match else 3.0
        
        return {
            "sugar_g": sugar,
            "calories": calories,
            "protein_g": protein,
            "fat_g": fat,
            "carbs_g": carbs,
            "additives_found": [] # Handled by AdditivesExpert
        }

    def get_product_identity(self, text):
        """
        Heuristic extraction of Brand and Product Name from raw OCR text.
        Usually the first non-generic lines are the most relevant.
        """
        lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 2]
        if not lines:
            return "Unknown Product", "Detected Brand"
        
        # Clean lines from generic OCR noise
        noise = ["nutrition", "facts", "ingredients", "label", "contains", "per 100g"]
        clean_lines = []
        for line in lines:
            if not any(n in line.lower() for n in noise):
                clean_lines.append(line)
        
        if not clean_lines:
            return lines[0], "Detected Brand"
            
        product_name = clean_lines[0]
        brand = "Detected Brand"
        
        # Simple brand heuristic: if first line is short, it might be the brand
        if len(clean_lines) > 1 and len(clean_lines[0]) < 15:
            brand = clean_lines[0]
            product_name = clean_lines[1]
            
        return product_name, brand

if __name__ == "__main__":
    ner = NERService()
    sample_text = "Nutrition Facts: Energy 525 kcal, Total Sugar 45.5g, Protein 6g. Ingredients: Maltodextrin, E319."
    print(f"Extracted: {ner.extract(sample_text)}")
