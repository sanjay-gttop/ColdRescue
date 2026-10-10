"""
ColdRescue Thermal ML Model Training Script.

Trains a gradient-boosted or linear regression surrogate model to predict remaining safe
thermal window before food/medicine spoilage occurs.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple


def load_dataset(csv_path: Path) -> List[Dict[str, Any]]:
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "cargo_type": r["cargo_type"],
                "cooling_status": r["cooling_status"],
                "current_temp_c": float(r["current_temp_c"]),
                "ambient_temp_c": float(r["ambient_temp_c"]),
                "safe_limit_c": float(r["safe_limit_c"]),
                "mass_kg": float(r["mass_kg"]),
                "thermal_resistance": float(r["thermal_resistance"]),
                "backup_runtime_min": float(r["backup_runtime_min"]),
                "door_open_count": int(r["door_open_count"]),
                "breach_minutes": float(r["breach_minutes"]),
            })
    return rows


def featurize(row: Dict[str, Any]) -> List[float]:
    # Feature engineering:
    # 0: temp buffer remaining = safe_limit_c - current_temp_c
    # 1: thermal gradient = ambient_temp_c - current_temp_c
    # 2: backup runtime
    # 3: thermal resistance
    # 4: cooling status (failed=0, degraded=0.5, active=1.0)
    # 5: mass log scale
    temp_buffer = max(0.0, row["safe_limit_c"] - row["current_temp_c"])
    gradient = max(0.1, row["ambient_temp_c"] - row["current_temp_c"])
    cooling_val = 0.0 if row["cooling_status"] == "failed" else 0.5 if row["cooling_status"] == "degraded" else 1.0
    mass_log = math.log(max(1.0, row["mass_kg"]))

    return [
        1.0,  # bias
        temp_buffer,
        gradient,
        row["backup_runtime_min"],
        row["thermal_resistance"],
        cooling_val,
        mass_log,
    ]


def train_linear_surrogate(
    dataset_path: Path,
    output_model_path: Path,
) -> Dict[str, Any]:
    data = load_dataset(dataset_path)
    if not data:
        raise ValueError("Empty dataset")

    # Regularized least squares (Ridge regression)
    X = [featurize(r) for r in data]
    y = [r["breach_minutes"] for r in data]
    n_features = len(X[0])
    n_samples = len(X)

    # Compute X^T * X + lambda * I and X^T * y
    lambda_reg = 0.1
    XtX = [[0.0] * n_features for _ in range(n_features)]
    Xty = [0.0] * n_features

    for i in range(n_samples):
        for j in range(n_features):
            Xty[j] += X[i][j] * y[i]
            for k in range(n_features):
                XtX[j][k] += X[i][j] * X[i][k]

    for j in range(n_features):
        XtX[j][j] += lambda_reg

    # Simple Gaussian elimination solver
    A = [row[:] for row in XtX]
    b = Xty[:]
    for i in range(n_features):
        pivot = A[i][i]
        for col in range(i, n_features):
            A[i][col] /= pivot
        b[i] /= pivot
        for row in range(n_features):
            if row != i:
                factor = A[row][i]
                for col in range(i, n_features):
                    A[row][col] -= factor * A[i][col]
                b[row] -= factor * b[i]

    weights = b

    # Compute training metrics (MAE and RMSE)
    errors = []
    for i in range(n_samples):
        pred = sum(weights[j] * X[i][j] for j in range(n_features))
        errors.append(abs(pred - y[i]))

    mae = round(sum(errors) / n_samples, 2)
    rmse = round(math.sqrt(sum(e * e for e in errors) / n_samples), 2)

    model_artifact = {
        "model_type": "LinearThermalSurrogateModel",
        "version": "1.0.0",
        "feature_names": [
            "bias",
            "temp_buffer_c",
            "ambient_gradient_c",
            "backup_runtime_min",
            "thermal_resistance",
            "cooling_status_factor",
            "mass_log_kg",
        ],
        "weights": [round(w, 4) for w in weights],
        "metrics": {
            "train_mae_minutes": mae,
            "train_rmse_minutes": rmse,
            "sample_count": n_samples,
        },
    }

    output_model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_model_path, "w", encoding="utf-8") as f:
        json.dump(model_artifact, f, indent=2)

    return model_artifact


if __name__ == "__main__":
    data_path = Path(__file__).resolve().parent.parent / "dataset" / "dataset.csv"
    model_path = Path(__file__).resolve().parent / "model.json"
    result = train_linear_surrogate(data_path, model_path)
    print(f"Model trained and saved to {model_path}")
    print(f"Metrics: MAE = {result['metrics']['train_mae_minutes']} min, RMSE = {result['metrics']['train_rmse_minutes']} min")
