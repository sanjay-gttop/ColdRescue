"""
ColdRescue ML Pipeline and Inference Tests.
"""
from pathlib import Path
import pytest

from ml.inference.predict import ThermalMLPredictor


def test_ml_surrogate_model_predicts():
    predictor = ThermalMLPredictor()
    res = predictor.predict(
        cargo_type="dairy",
        current_temp_c=4.0,
        ambient_temp_c=28.0,
        safe_limit_c=8.0,
        cooling_status="degraded",
        backup_runtime_min=45.0,
        mass_kg=500.0,
        thermal_resistance=1.0,
    )
    assert "predicted_breach_minutes" in res
    assert res["predicted_breach_minutes"] >= 0.0
    assert res["provenance"] == "ml_surrogate_model"
    assert res["is_fallback"] is False


def test_ml_fallback_when_model_missing():
    # Provide nonexistent path
    predictor = ThermalMLPredictor(model_path=Path("nonexistent/model.json"))
    res = predictor.predict(
        cargo_type="dairy",
        current_temp_c=4.0,
        ambient_temp_c=28.0,
        safe_limit_c=8.0,
        cooling_status="degraded",
        backup_runtime_min=45.0,
    )
    assert res["is_fallback"] is True
    assert res["provenance"] == "deterministic_physics_fallback"
    assert res["predicted_breach_minutes"] is not None
