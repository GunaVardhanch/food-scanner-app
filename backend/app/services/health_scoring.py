import xgboost as xgb
import numpy as np
import json

class HealthScoreEnsemble:
    def __init__(self):
        # Placeholder for trained booster
        self.model = None
        print("Health Score Ensemble (XGBoost) structure ready.")

    def calculate_raw_score(self, features):
        """
        Features: {sugar_g, additive_impact, calories, etc.}
        """
        score = 8.5 # Start higher for clean label
        
        # Sugar deduction
        score -= (features.get('sugar_g', 0) / 10.0) * 1.5
        
        # Additive expert impact
        score += features.get('additive_impact', 0)
        
        # Natural protein boost (simplified)
        score += (features.get('protein_g', 0) / 5.0)
        
        return max(0.5, min(10.0, score))

    def predict(self, feature_vector):
        if self.model:
            dmat = xgb.DMatrix([feature_vector])
            return self.model.predict(dmat)[0]
        else:
            # Simulated outcome
            return 7.5

if __name__ == "__main__":
    ensemble = HealthScoreEnsemble()
    test_features = {'sugar_g': 30, 'additive_count': 3, 'protein_g': 2}
    print(f"Baseline Score: {ensemble.calculate_raw_score(test_features)}")
