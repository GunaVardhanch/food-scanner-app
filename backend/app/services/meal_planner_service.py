#!/usr/bin/env python3
"""
Meal Planner Service - Uses Google Gemini API for AI-powered meal planning
"""

import os
import json
import logging
from typing import Dict, Any, Optional

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class MealPlannerService:
    """Service to generate personalized meal plans using Gemini AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the meal planner with Gemini API key."""
        if not GENAI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. "
                "Set GEMINI_API_KEY environment variable or pass api_key parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def generate_meal_plan(
        self,
        age: int,
        gender: str,
        diet_type: str,
        state: str,
        cuisine: str,
        health_goal: str,
        activity_level: str,
        daily_calories: float,
        weekly_budget: float
    ) -> Dict[str, Any]:
        """
        Generate a personalized meal plan using Gemini AI.
        
        Args:
            age: User age in years
            gender: "Male" or "Female"
            diet_type: "veg", "non-veg", etc.
            state: Indian state (e.g., "maharashtra", "kerala")
            cuisine: Cuisine preference (e.g., "north indian", "south indian")
            health_goal: "lose_weight", "gain_weight", "maintain"
            activity_level: "sedentary", "light", "moderate", "active"
            daily_calories: Daily calorie target
            weekly_budget: Weekly budget in rupees
        
        Returns:
            dict: Meal plan with today's plan, weekly plan, and grocery list
        
        Raises:
            ValueError: If API response is invalid
            Exception: If Gemini API call fails
        """
        
        # Build the prompt
        prompt = self._build_prompt(
            age=age,
            gender=gender,
            diet_type=diet_type,
            state=state,
            cuisine=cuisine,
            health_goal=health_goal,
            activity_level=activity_level,
            daily_calories=daily_calories,
            weekly_budget=weekly_budget
        )
        
        logger.info(f"[MEAL_PLANNER] Calling Gemini API for meal plan generation")
        
        try:
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini API")
            
            logger.info(f"[MEAL_PLANNER] ✅ Gemini response received ({len(response.text)} chars)")
            
            # Parse the response (should be JSON)
            meal_plan = self._parse_response(response.text)
            
            logger.info(f"[MEAL_PLANNER] ✅ Meal plan generated successfully")
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"[MEAL_PLANNER] ❌ Error calling Gemini API: {e}")
            raise
    
    def _build_prompt(
        self,
        age: int,
        gender: str,
        diet_type: str,
        state: str,
        cuisine: str,
        health_goal: str,
        activity_level: str,
        daily_calories: float,
        weekly_budget: float
    ) -> str:
        """Build optimized prompt for faster Gemini generation."""
        
        prompt = f"""Generate a 7-day {cuisine.title()} meal plan for a {age}y {gender.lower()} targeting {health_goal.replace('_', ' ')}.

Budget: ₹{weekly_budget}/week | Diet: {diet_type.upper()} | Calories: {daily_calories:.0f}/day | State: {state}

JSON ONLY (no explanation):
{{
  "today_plan": {{"day": "Monday", "meals": {{"breakfast": {{"meal": "name", "portion": "qty", "calories": 0}}, "lunch": {{"meal": "", "portion": "", "calories": 0}}, "dinner": {{"meal": "", "portion": "", "calories": 0}}, "snacks": [{{"meal": "", "portion": "", "calories": 0}}]}}, "total_calories": 0}},
  "weekly_plan": [
    {{"day": "Monday", "meals": {{"breakfast": {{"meal": "", "portion": "", "calories": 0}}, "lunch": {{"meal": "", "portion": "", "calories": 0}}, "dinner": {{"meal": "", "portion": "", "calories": 0}}, "snacks": [{{"meal": "", "portion": "", "calories": 0}}]}}, "total_calories": 0}}
  ],
  "grocery_list": [{{"item": "", "quantity": "", "estimated_cost": 0}}],
  "total_estimated_cost": 0
}}

Rules: Every day ~{daily_calories:.0f} cal | Match diet & cuisine | Use local {state} ingredients | Realistic portions | No repetition | Budget ₹{weekly_budget} | Valid JSON only"""
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the Gemini response as JSON.
        
        Args:
            response_text: Raw response from Gemini
        
        Returns:
            dict: Parsed meal plan
        
        Raises:
            ValueError: If response is not valid JSON
        """
        
        # Try to extract JSON from response
        try:
            # First try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON block in response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # If we get here, response is not valid JSON
        logger.error(f"[MEAL_PLANNER] Invalid JSON response from Gemini:\n{response_text[:500]}")
        raise ValueError(
            "Gemini API returned invalid JSON. "
            "The response could not be parsed as a meal plan."
        )


def get_meal_planner(api_key: Optional[str] = None) -> MealPlannerService:
    """
    Get or create a MealPlannerService instance.
    
    Args:
        api_key: Optional Gemini API key (uses env var if not provided)
    
    Returns:
        MealPlannerService: Initialized service
    """
    return MealPlannerService(api_key=api_key)
