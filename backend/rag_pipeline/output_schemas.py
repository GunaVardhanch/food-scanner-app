"""
output_schemas.py
──────────────────
Pydantic v2 output models for the RAG pipeline.

These define the exact JSON shape that rag_analyzer.analyze_label_text() returns,
ensuring downstream consumers (routes.py, tests) can always rely on a known structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

try:
    from pydantic import BaseModel, Field
    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False
    # Minimal stub so the rest of the module can be imported even without pydantic
    class BaseModel:  # type: ignore[no-redef]
        def __init__(self, **data):
            for k, v in data.items():
                setattr(self, k, v)

        def model_dump(self) -> dict:
            return self.__dict__

    def Field(*args, **kwargs):  # type: ignore[misc]
        return None


class AdditiveFlag(BaseModel):
    """One detected additive with its risk classification."""
    code: str = Field(description="INS/E code or common name, e.g. 'INS 621'")
    name: str = Field(description="Full name, e.g. 'Monosodium Glutamate'")
    category: str = Field(description="Additive category, e.g. 'Flavour Enhancer'")
    risk: Literal["high", "moderate", "low", "unknown"] = Field(
        default="unknown",
        description="Detected risk level from harmful_flags.json",
    )
    safety_color: Literal["red", "yellow", "green"] = Field(
        default="yellow",
        description="Traffic light safety colour from fssai_additives.json",
    )
    banned_in_india: bool = Field(default=False)
    fssai_limit: Optional[str] = Field(
        default=None, description="FSSAI permitted limit string, e.g. '200 mg/kg'"
    )
    health_risks: Optional[str] = Field(
        default=None, description="Short health risk summary"
    )
    explanation: Optional[str] = Field(
        default=None, description="Full human-readable explanation"
    )
    match_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How confident we are this ingredient matched this additive entry",
    )


class NutritionSummary(BaseModel):
    """Parsed and structured nutrition values from the label OCR."""
    calories_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    sugars_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    serving_size_g: Optional[float] = None

    # Derived flags
    sugar_high: bool = False
    sodium_high: bool = False
    trans_fat_present: bool = False
    saturated_fat_high: bool = False
    calories_high: bool = False


class RAGAnalysisResult(BaseModel):
    """
    Complete output of rag_pipeline.analyze_label_text().

    This is the dict added to routes.py as   results["rag_analysis"].
    """
    # Core outputs
    nutrition_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted and structured nutrition values"
    )
    additive_flags: List[AdditiveFlag] = Field(
        default_factory=list,
        description="All detected additives with risk ratings"
    )
    fssai_compliance: bool = Field(
        default=True,
        description="False if any banned additive is detected"
    )
    compliance_message: str = Field(default="")

    # Warnings
    warnings: List[str] = Field(
        default_factory=list,
        description="Human-readable warning strings (high sugar, MSG, etc.)"
    )
    warning_details: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Structured {title, explanation} dicts for each warning"
    )

    # Score
    score: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="RAG health score 0–10 (10 = healthiest)",
    )
    score_grade: Literal["GREEN", "YELLOW", "RED"] = Field(default="YELLOW")

    # Metadata
    ingredients_detected: List[str] = Field(
        default_factory=list,
        description="All ingredient tokens extracted from label"
    )
    ultra_processed_markers_found: List[str] = Field(default_factory=list)
    allergens_detected: List[str] = Field(default_factory=list)
    healthy_alternative: Optional[str] = None

    # Pipeline info
    pipeline_version: str = "1.0.0"
    retrieval_backend: Literal["faiss", "keyword", "none"] = "none"

    def to_dict(self) -> Dict[str, Any]:
        """Plain dict for JSON serialisation (works with or without pydantic)."""
        if _PYDANTIC_AVAILABLE:
            d = self.model_dump()
            # Convert AdditiveFlag objects to dicts
            d["additive_flags"] = [
                f.model_dump() if hasattr(f, "model_dump") else f.__dict__
                for f in self.additive_flags
            ]
            return d
        return self.__dict__
