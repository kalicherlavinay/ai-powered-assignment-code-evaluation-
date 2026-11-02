"""Small supervised quality model trained from the bundled labeled CSV."""
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "labeled_examples.csv"
FEATURES = [
    "passed_tests", "total_tests", "syntax_valid", "line_count",
    "function_count", "loop_count", "branch_count", "docstring_count",
]


def train_model() -> tuple[RandomForestRegressor, int]:
    data = pd.read_csv(DATA_PATH)
    model = RandomForestRegressor(n_estimators=120, random_state=42, max_depth=5)
    model.fit(data[FEATURES], data["quality_score"])
    return model, len(data)


def predict_quality(features: dict[str, int]) -> tuple[float, int]:
    model, sample_count = train_model()
    row = pd.DataFrame([{name: int(features.get(name, 0)) for name in FEATURES}])
    score = float(model.predict(row)[0])
    return round(max(0.0, min(100.0, score)), 1), sample_count
