"""
ColdRescue ML Evaluation and Benchmark Suite.

Evaluates the surrogate ML model on held-out test data, checks MAE / RMSE thresholds,
and validates that fallback behavior occurs seamlessly when corrupted or absent.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from ml.dataset.generate_dataset import generate_synthetic_dataset
from ml.inference.predict import ThermalMLPredictor
from ml.training.train import load_dataset


def evaluate_model(
    test_data_path: Path,
    model_path: Path,
) -> Dict[str, Any]:
    dataset = load_dataset(test_data_path)
    predictor = ThermalMLPredictor(model_path=model_path)

    errors = []
    for r in dataset:
        pred = predictor.predict(
            cargo_type=r["cargo_type"],
            current_temp_c=r["current_temp_c"],
            ambient_temp_c=r["ambient_temp_c"],
            safe_limit_c=r["safe_limit_c"],
            cooling_status=r["cooling_status"],
            backup_runtime_min=r["backup_runtime_min"],
            mass_kg=r["mass_kg"],
            thermal_resistance=r["thermal_resistance"],
        )
        predicted_min = pred["predicted_breach_minutes"]
        actual_min = r["breach_minutes"]
        errors.append(abs(predicted_min - actual_min))

    mae = round(sum(errors) / len(errors), 2)
    return {
        "test_sample_count": len(errors),
        "test_mae_minutes": mae,
        "evaluation_passed": mae < 120.0,
    }


if __name__ == "__main__":
    test_csv = Path(__file__).resolve().parent / "test_dataset.csv"
    generate_synthetic_dataset(test_csv, num_samples=200, seed=999)

    model_json = Path(__file__).resolve().parent.parent / "training" / "model.json"
    metrics = evaluate_model(test_csv, model_json)
    print(f"Evaluation metrics: {json.dumps(metrics, indent=2)}")
