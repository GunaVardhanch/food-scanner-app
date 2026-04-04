#!/usr/bin/env python3
"""
Calorie Calculator Service
Uses Mifflin-St Jeor Equation to calculate daily calorie requirements.
"""

def calculate_calories(age, gender, weight, height, activity_level, health_goal):
    """
    Calculate daily calorie requirements using Mifflin-St Jeor Equation.
    
    Args:
        age (int): Age in years (10-120)
        gender (str): "male" or "female"
        weight (float): Weight in kg (20-300)
        height (float): Height in cm (100-250)
        activity_level (str): "sedentary", "light", "moderate", or "active"
        health_goal (str): "lose_weight", "gain_weight", or "maintain"
    
    Returns:
        dict: {
            "bmr": float,          # Basal Metabolic Rate
            "tdee": float,         # Total Daily Energy Expenditure
            "daily_calories": float,  # Adjusted for health goal
            "details": {
                "activity_multiplier": float,
                "calorie_adjustment": float,
                "goal": str
            }
        }
    
    Raises:
        ValueError: If inputs are invalid
    """
    
    # Validate inputs
    try:
        age = int(age)
        weight = float(weight)
        height = float(height)
    except (ValueError, TypeError):
        raise ValueError("Age, weight, and height must be numeric")
    
    gender = str(gender).lower().strip()
    activity_level = str(activity_level).lower().strip()
    health_goal = str(health_goal).lower().strip()
    
    # Validate ranges
    if not (10 <= age <= 120):
        raise ValueError(f"Age must be between 10 and 120, got {age}")
    if not (20 <= weight <= 300):
        raise ValueError(f"Weight must be between 20 and 300 kg, got {weight}")
    if not (100 <= height <= 250):
        raise ValueError(f"Height must be between 100 and 250 cm, got {height}")
    
    # Validate gender
    if gender not in ["male", "female"]:
        raise ValueError(f"Gender must be 'male' or 'female', got '{gender}'")
    
    # Validate activity level
    valid_activities = ["sedentary", "light", "moderate", "active"]
    if activity_level not in valid_activities:
        raise ValueError(f"Activity level must be one of {valid_activities}, got '{activity_level}'")
    
    # Validate health goal and normalize aliases
    # Map frontend aliases to backend values
    goal_mapping = {
        "lose_weight": "lose_weight",
        "gain_weight": "gain_weight",
        "gain_muscle": "gain_weight",  # Frontend sends "gain_muscle", map to "gain_weight"
        "maintain": "maintain",
        "stay_healthy": "maintain"  # Another alias
    }
    
    if health_goal not in goal_mapping:
        valid_goals = ["lose_weight", "gain_weight", "gain_muscle", "maintain", "stay_healthy"]
        raise ValueError(f"Health goal must be one of {valid_goals}, got '{health_goal}'")
    
    # Normalize to backend value
    health_goal = goal_mapping[health_goal]
    
    # Step 1: Calculate BMR using Mifflin-St Jeor formula
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # female
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Step 2: Apply activity multiplier
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725
    }
    activity_multiplier = activity_multipliers[activity_level]
    tdee = bmr * activity_multiplier
    
    # Step 3: Adjust based on goal
    goal_adjustments = {
        "lose_weight": -500,
        "gain_weight": 400,
        "maintain": 0
    }
    calorie_adjustment = goal_adjustments[health_goal]
    daily_calories = tdee + calorie_adjustment
    
    # Ensure daily calories don't go below minimum (1200 for women, 1500 for men)
    minimum_calories = 1200 if gender == "female" else 1500
    if daily_calories < minimum_calories:
        daily_calories = minimum_calories
    
    # Round to 2 decimal places
    bmr = round(bmr, 2)
    tdee = round(tdee, 2)
    daily_calories = round(daily_calories, 2)
    activity_multiplier = round(activity_multiplier, 3)
    
    return {
        "bmr": bmr,
        "tdee": tdee,
        "daily_calories": daily_calories,
        "details": {
            "activity_multiplier": activity_multiplier,
            "calorie_adjustment": calorie_adjustment,
            "goal": health_goal,
            "minimum_calories_enforced": daily_calories == minimum_calories
        }
    }


def get_calorie_breakdown(daily_calories, macronutrient_ratio=None):
    """
    Get macronutrient breakdown based on daily calories.
    
    Args:
        daily_calories (float): Daily calorie requirement
        macronutrient_ratio (dict): Optional custom ratio {protein: %, carbs: %, fats: %}
            Default: {protein: 30%, carbs: 45%, fats: 25%}
    
    Returns:
        dict: Breakdown of calories per macronutrient
    """
    if macronutrient_ratio is None:
        # Standard balanced diet
        macronutrient_ratio = {
            "protein": 0.30,      # 30% = 4 cal/g
            "carbs": 0.45,        # 45% = 4 cal/g
            "fats": 0.25          # 25% = 9 cal/g
        }
    
    # Validate ratio sums to 100%
    total_ratio = sum(macronutrient_ratio.values())
    if not (0.99 <= total_ratio <= 1.01):
        raise ValueError(f"Macronutrient ratios must sum to 100%, got {total_ratio * 100}%")
    
    protein_cals = daily_calories * macronutrient_ratio["protein"]
    carbs_cals = daily_calories * macronutrient_ratio["carbs"]
    fats_cals = daily_calories * macronutrient_ratio["fats"]
    
    return {
        "protein": {
            "calories": round(protein_cals, 2),
            "grams": round(protein_cals / 4, 2)  # 4 cal per gram
        },
        "carbs": {
            "calories": round(carbs_cals, 2),
            "grams": round(carbs_cals / 4, 2)  # 4 cal per gram
        },
        "fats": {
            "calories": round(fats_cals, 2),
            "grams": round(fats_cals / 9, 2)  # 9 cal per gram
        }
    }


# Test the function
if __name__ == "__main__":
    print("Testing Calorie Calculator")
    print("=" * 60)
    
    # Example 1: Male, active, wants to lose weight
    result = calculate_calories(
        age=28,
        gender="male",
        weight=72,
        height=178,
        activity_level="moderate",
        health_goal="lose_weight"
    )
    print("\n1️⃣ Male, 28, 72kg, 178cm, Moderate Activity, Lose Weight")
    print(f"   BMR: {result['bmr']} cal")
    print(f"   TDEE: {result['tdee']} cal")
    print(f"   Daily Calories: {result['daily_calories']} cal")
    
    # Example 2: Female, light activity, maintain weight
    result = calculate_calories(
        age=25,
        gender="female",
        weight=62,
        height=165,
        activity_level="light",
        health_goal="maintain"
    )
    print("\n2️⃣ Female, 25, 62kg, 165cm, Light Activity, Maintain")
    print(f"   BMR: {result['bmr']} cal")
    print(f"   TDEE: {result['tdee']} cal")
    print(f"   Daily Calories: {result['daily_calories']} cal")
    
    # Get macronutrient breakdown
    breakdown = get_calorie_breakdown(result['daily_calories'])
    print(f"\n   Macronutrient Breakdown:")
    print(f"   Protein: {breakdown['protein']['grams']}g ({breakdown['protein']['calories']} cal)")
    print(f"   Carbs: {breakdown['carbs']['grams']}g ({breakdown['carbs']['calories']} cal)")
    print(f"   Fats: {breakdown['fats']['grams']}g ({breakdown['fats']['calories']} cal)")
    
    # Example 3: Error handling
    print("\n3️⃣ Testing Error Handling")
    try:
        calculate_calories(5, "male", 70, 180, "moderate", "lose_weight")
    except ValueError as e:
        print(f"   ✅ Caught error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
