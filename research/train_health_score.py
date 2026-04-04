"""
Training script for the Food Scanner health score model.

This trains an XGBoost regressor to predict a 0–10 health score from
tabular features derived from nutrition + additives, then saves the
booster under D:\\food-scanner-models\\health_ensemble.xgb (or a
fallback directory if D: is not available).

Expected input dataset:
- A CSV file at D:\\food-scanner-data\\products.csv (by default)
- Each row is a product:
  columns like:
    product_name, calories, sugar_g, fat_g, carbs_g, protein_g,
    additive_impact, expert_score
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from app.config import MODEL_DIR, HEALTH_SCORE_MODEL_PATH


def get_default_data_path() -> str:
    d_root = Path("D:\\")
    if d_root.exists():
        return str(d_root.joinpath("food-scanner-data", "products.csv"))
    # Fallback: inside repo
    repo_root = Path(__file__).resolve().parents[1]
    return str(repo_root.joinpath("data", "products.csv"))


def load_dataset(csv_path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(csv_path)

    # Basic feature set; extend as your dataset grows
    feature_cols = [
        "sugar_g",
        "fat_g",
        "carbs_g",
        "protein_g",
        "calories",
        "additive_impact",
    ]
    target_col = "expert_score"

    missing = [c for c in feature_cols + [target_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")

    X = df[feature_cols].astype(float).to_numpy()
    y = df[target_col].astype(float).to_numpy()
    return X, y


def train_and_save(csv_path: str | None = None) -> None:
    if csv_path is None:
        csv_path = get_default_data_path()

    print(f"Loading dataset from {csv_path}")
    X, y = load_dataset(csv_path)

    dtrain = xgb.DMatrix(
        X,
        label=y,
        feature_names=[
            "sugar_g",
            "fat_g",
            "carbs_g",
            "protein_g",
            "calories",
            "additive_impact",
        ],
    )

    params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "max_depth": 4,
        "eta": 0.1,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "seed": 42,
    }

    print("Training XGBoost health score model...")
    booster = xgb.train(params, dtrain, num_boost_round=300)

    # Ensure model directory exists
    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)

    print(f"Saving model to {HEALTH_SCORE_MODEL_PATH}")
    booster.save_model(HEALTH_SCORE_MODEL_PATH)

    print("Done.")


if __name__ == "__main__":
    train_and_save()

