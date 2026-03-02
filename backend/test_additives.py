import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from additives_expert import AdditivesExpert

def test_additives():
    expert = AdditivesExpert()
    passed = 0
    failed = 0
    
    test_cases = [
        # --- Original test cases ---
        {
            "text": "Ingredients: Water, Sugar, INS 102, Tartrazine, Sodium Benzoate.",
            "expected_count": 2,
            "desc": "Name and INS code for same additive (Tartrazine=INS 102 deduped), plus Sodium Benzoate"
        },
        {
            "text": "Contains flavor enhancer 621 and preservative E319.",
            "expected_count": 2,
            "desc": "Short codes and E-prefix (MSG + TBHQ)"
        },
        {
            "text": "Natural emulsifier (INS 322) and thickener 415.",
            "expected_count": 2,
            "desc": "Green additives (Lecithin + Xanthan Gum)"
        },
        {
            "text": "This product is clean and has no additives.",
            "expected_count": 0,
            "desc": "Clean label - no matches"
        },
        
        # --- New: High-Risk Detection ---
        {
            "text": "Ingredients: Tartrazine, MSG, TBHQ, Aspartame, Palm Oil",
            "expected_count": 5,
            "desc": "Multiple RED additives - should trigger HIGH_RISK tier",
            "expected_tier": "HIGH_RISK"
        },
        
        # --- New: Banned Substance ---
        {
            "text": "Ingredients: Wheat Flour (treated with Potassium Bromate), Sugar",
            "expected_count": 1,
            "desc": "FSSAI-banned substance - should trigger CRITICAL tier",
            "expected_tier": "CRITICAL"
        },
        
        # --- New: Interaction Warning (Sodium Benzoate + Vitamin C) ---
        {
            "text": "Ingredients: Sodium Benzoate, Ascorbic Acid, Sugar, Water.",
            "expected_count": 2,
            "desc": "Interaction warning: Sodium Benzoate + Ascorbic Acid -> Benzene risk",
            "expected_interactions": 1
        },
        
        # --- New: Safe product ---
        {
            "text": "Ingredients: Curcumin, Citric Acid, Pectin, Guar Gum.",
            "expected_count": 4,
            "desc": "All GREEN additives - should be SAFE tier",
            "expected_tier": "SAFE"
        },

        # --- New: Indian-specific additives ---
        {
            "text": "Ingredients: Vanaspati, Partially Hydrogenated Vegetable Oil, INS 282.",
            "expected_count": 3,
            "desc": "Indian-specific: Vanaspati + PHVO + Calcium Propionate"
        },

        # --- New: BHA + BHT interaction ---
        {
            "text": "Contains BHA (INS 320) and BHT (INS 321) as antioxidants.",
            "expected_count": 2,
            "desc": "BHA + BHT interaction warning pair",
            "expected_interactions": 1
        }
    ]
    
    print("=" * 60)
    print("  FSSAI ADDITIVES EXPERT - TEST SUITE")
    print("=" * 60)
    
    for i, case in enumerate(test_cases):
        print(f"\nTest {i+1}: {case['desc']}")
        detected, impact = expert.analyze_text(case['text'])
        risk_summary = expert.get_risk_summary(detected)
        
        print(f"  Input:    {case['text'][:80]}...")
        print(f"  Detected: {[d['name'] for d in detected]}")
        print(f"  Impact:   {impact}")
        print(f"  Tier:     {risk_summary['risk_tier']}")
        
        # Validate count
        count_ok = len(detected) == case['expected_count']
        
        # Validate tier if specified
        tier_ok = True
        if 'expected_tier' in case:
            tier_ok = risk_summary['risk_tier'] == case['expected_tier']
            if not tier_ok:
                print(f"  [FAIL] TIER MISMATCH: expected {case['expected_tier']}, got {risk_summary['risk_tier']}")

        # Validate interactions if specified
        interaction_ok = True
        if 'expected_interactions' in case:
            actual_interactions = len(risk_summary.get('interaction_warnings', []))
            interaction_ok = actual_interactions >= case['expected_interactions']
            if interaction_ok:
                for w in risk_summary['interaction_warnings']:
                    print(f"  [WARN] {w}")
            else:
                print(f"  [FAIL] INTERACTION MISMATCH: expected {case['expected_interactions']}, got {actual_interactions}")

        if count_ok and tier_ok and interaction_ok:
            print(f"  [PASS] PASSED (count={len(detected)})")
            passed += 1
        else:
            if not count_ok:
                print(f"  [FAIL] COUNT MISMATCH: expected {case['expected_count']}, got {len(detected)}")
            failed += 1
        
        print("-" * 60)
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"  Database size: {len(expert.additives)} additives loaded")
    print(f"{'=' * 60}")
    
    return failed == 0

if __name__ == "__main__":
    success = test_additives()
    sys.exit(0 if success else 1)
