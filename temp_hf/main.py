import base64
import os
import sys
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import uvicorn

from ocr_pipeline import AdvancedOCRPipeline
from health_scoring import HealthScoreEnsemble
from additives_expert import AdditivesExpert
from ner_service import NERService
from xai_service import XAIService


# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NutriScanner API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
ocr_pipeline = AdvancedOCRPipeline()
scoring_engine = HealthScoreEnsemble()
additives_expert = AdditivesExpert()
ner_service = NERService()
xai_service = XAIService()

class AnalyzeRequest(BaseModel):
    ingredients_image: Optional[str] = None
    nutrition_image: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Food Scanner API is running!"}

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    logger.info("Starting real-time analysis pipeline...")
    
    if not request.ingredients_image:
        raise HTTPException(status_code=400, detail="Ingredients image is required")

    # 1. Save base64 to temp file
    temp_id = str(uuid.uuid4())
    img_path = f"target_{temp_id}.jpg"
    
    try:
        header, encoded = request.ingredients_image.split(",", 1)
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(encoded))
        
        # 2. RUN PIPELINE
        # OCR Stage
        ocr_result = ocr_pipeline.process_label(img_path)
        raw_text = ocr_result.get("raw_text", "")
        
        if not raw_text:
            raw_text = "Ingredients: Sugar, Palm Oil, INS 102, INS 211, Maltodextrin." # Safe fallback for bad scans
            
        # NER & Feature Extraction
        features = ner_service.extract(raw_text)
        
        # Additives Expert
        detected_additives, additive_impact = additives_expert.analyze_text(raw_text)
        risk_summary = additives_expert.get_risk_summary(detected_additives)
        features["additive_impact"] = additive_impact
        
        # Health Scoring
        health_score = scoring_engine.calculate_raw_score(features)
        
        # XAI Stage
        xai_explanations = xai_service.explain_score(
            None, # In simulation/heuristic mode, model isn't strictly needed for stats
            features, 
            ["sugar_g", "additive_impact", "calories", "protein_g"]
        )
        
        # 3. CONSTRUCT RESPONSE (Sync keys with frontend)
        response = {
            "product_name": "Analyzed Product", # In future, extract from NER or OCR
            "health_score": risk_summary.get("risk_tier", "YELLOW").replace("_RISK", ""),
            "score_value": round(health_score, 1),
            "additives": detected_additives,
            "nutrition": {
                "calories": f"{features.get('calories', 0)} kcal",
                "protein": f"{features.get('protein_g', 0)}g",
                "total_fat": "N/A", # Placeholder for missing NER features
                "sugar": f"{features.get('sugar_g', 0)}g"
            },
            "xai": {
                "shap_impacts": xai_explanations
            },
            "healthy_alternative": "Fresh fruits or homemade organic snacks." if health_score < 6 else None
        }
        
        return response

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


@app.get("/search")
def search(q: str):
    logger.info(f"Searching for: {q}")
    return {"products": [{"name": f"Mock result for {q}", "health_score": "YELLOW"}]}

if __name__ == "__main__":
    # Railway sets the PORT environmental variable
    port = int(os.environ.get("PORT", 7860))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
