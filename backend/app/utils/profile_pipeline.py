import time
import base64
import os
import sys
import json

# Add necessary paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, '..', 'research'))

from ocr_pipeline import AdvancedOCRPipeline
from health_scoring import HealthScoreEnsemble
from xai_service import XAIService
from additives_expert import AdditivesExpert
from ner_service import NERService

def profile_pipeline(json_output=False):
    timings = {}

    # --- Service Initialization ---
    start_init = time.time()
    ocr_pipeline = AdvancedOCRPipeline()
    scoring_engine = HealthScoreEnsemble()
    xai_service = XAIService()
    additives_expert = AdditivesExpert()
    ner_service = NERService()
    timings["init"] = round(time.time() - start_init, 4)
    if not json_output:
        print(f"Service Initialization: {timings['init']}s")

    # Create dummy image if needed
    dummy_img = "test_img.jpg"
    if not os.path.exists(dummy_img):
        from PIL import Image
        img = Image.new('RGB', (800, 600), color=(255, 255, 255))
        img.save(dummy_img)

    if not json_output:
        print("\nStarting Pipeline Profiling...")
    
    # 1. OCR Stage
    t0 = time.time()
    ocr_result = ocr_pipeline.process_label(dummy_img)
    raw_text = ocr_result.get("raw_text", "Sample ingredient list with INS 102 and Sugar.")
    timings["ocr"] = round(time.time() - t0, 4)

    # 2. NER Stage
    t1 = time.time()
    extracted_features = ner_service.extract(raw_text)
    timings["ner"] = round(time.time() - t1, 4)

    # 3. Additive Expert + Risk Assessment
    t2 = time.time()
    detected_additives, additive_impact = additives_expert.analyze_text(raw_text)
    risk_summary = additives_expert.get_risk_summary(detected_additives)
    extracted_features["additive_impact"] = additive_impact
    timings["additives"] = round(time.time() - t2, 4)

    # 4. Health Scoring
    t3 = time.time()
    health_score = scoring_engine.calculate_raw_score(extracted_features)
    timings["scoring"] = round(time.time() - t3, 4)

    # 5. XAI Stage
    t4 = time.time()
    shap_explanations = xai_service.explain_score(
        scoring_engine.model, 
        extracted_features, 
        ["sugar_g", "additive_impact", "calories", "protein_g"]
    )
    timings["xai"] = round(time.time() - t4, 4)

    # Total pipeline (excluding init)
    timings["pipeline_total"] = round(
        timings["ocr"] + timings["ner"] + timings["additives"] + timings["scoring"] + timings["xai"], 4
    )
    timings["total_with_init"] = round(timings["init"] + timings["pipeline_total"], 4)

    if json_output:
        result = {
            "timings": timings,
            "target_met": timings["pipeline_total"] < 5.0,
            "risk_summary": risk_summary,
            "detected_additives": len(detected_additives),
            "health_score": round(health_score, 1)
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"  PIPELINE PROFILING RESULTS")
        print(f"{'='*50}")
        print(f"  OCR Stage:        {timings['ocr']:.4f}s")
        print(f"  NER Stage:        {timings['ner']:.4f}s")
        print(f"  Additive Expert:  {timings['additives']:.4f}s")
        print(f"  Scoring Engine:   {timings['scoring']:.4f}s")
        print(f"  XAI Stage:        {timings['xai']:.4f}s")
        print(f"{'='*50}")
        print(f"  Pipeline Total:   {timings['pipeline_total']:.4f}s")
        print(f"  + Init Overhead:  {timings['init']:.4f}s")
        print(f"  Grand Total:      {timings['total_with_init']:.4f}s")
        print(f"{'='*50}")
        
        if timings["pipeline_total"] > 5:
            print("  [FAIL] WARNING: Pipeline exceeded 5s target.")
        else:
            print("  [PASS] SUCCESS: Pipeline is within latency target.")
        
        print(f"  Additives Found:  {len(detected_additives)}")
        print(f"  Risk Tier:        {risk_summary.get('risk_tier', 'N/A')}")
        print(f"  Health Score:     {round(health_score, 1)}/10")
        print(f"{'='*50}")

if __name__ == "__main__":
    json_flag = "--json" in sys.argv
    profile_pipeline(json_output=json_flag)
