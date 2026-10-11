"""
Tests for ThermalRiskService.

Tests cover:
  - Nominal unbreached cargo thermal assessment
  - Imminent/active breach detection (current_temp > safe_max)
  - Temperature range boundary validations
  - Passive warming calculations with ambient < safe_max (no breach)
  - Active vs degraded vs failed cooling impacts on safe window
  - Input validation: invalid extreme physical temperatures (-99°C, 99°C)
  - Missing current_temp fallback to midpoint
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from backend.models.domain import CargoItem, CoolingStatus
from backend.services.thermal_risk import ThermalRiskService, ThermalRiskLevel


def _make_cargo(**kwargs) -> CargoItem:
    defaults = {
        "cargo_id": "cargo_test_01",
        "description": "Chilled vaccines",
        "cargo_kg": 250.0,
        "safe_temperature_min_c": 2.0,
        "safe_temperature_max_c": 8.0,
        "current_temperature_c": 4.0,
        "backup_runtime_min": 60.0,
        "unloading_duration_min": 15.0,
    }
    defaults.update(kwargs)
    return CargoItem(**defaults)


def test_nominal_thermal_risk_evaluation():
    cargo = _make_cargo()
    assessment = ThermalRiskService.evaluate_cargo_thermal_risk(
        cargo=cargo,
        ambient_temperature_c=25.0,
        cooling_status=CoolingStatus.OPERATIONAL,
    )
    assert assessment.cargo_id == "cargo_test_01"
    assert assessment.spoilage_breached is False
    assert assessment.active_cooling is True
    assert assessment.estimated_safe_window_min > cargo.backup_runtime_min
    assert assessment.risk_level in [ThermalRiskLevel.LOW, ThermalRiskLevel.MEDIUM]


def test_active_temperature_breach_detected():
    # Cargo already above safe upper limit (9°C > 8°C max)
    cargo = _make_cargo(current_temperature_c=9.0)
    assessment = ThermalRiskService.evaluate_cargo_thermal_risk(
        cargo=cargo,
        ambient_temperature_c=25.0,
        cooling_status=CoolingStatus.FAILED,
    )
    assert assessment.spoilage_breached is True
    assert assessment.risk_level == ThermalRiskLevel.CRITICAL
    assert assessment.estimated_safe_window_min == 0.0
    assert "already exceeds" in assessment.explanation


def test_cooling_status_affects_safe_window():
    cargo = _make_cargo(backup_runtime_min=90.0)

    eval_op = ThermalRiskService.evaluate_cargo_thermal_risk(
        cargo=cargo, cooling_status=CoolingStatus.OPERATIONAL
    )
    eval_deg = ThermalRiskService.evaluate_cargo_thermal_risk(
        cargo=cargo, cooling_status=CoolingStatus.DEGRADED
    )
    eval_fail = ThermalRiskService.evaluate_cargo_thermal_risk(
        cargo=cargo, cooling_status=CoolingStatus.FAILED
    )

    # Operational should provide longest safe window, failed shortest
    assert eval_op.estimated_safe_window_min > eval_deg.estimated_safe_window_min
    assert eval_deg.estimated_safe_window_min > eval_fail.estimated_safe_window_min


def test_cold_ambient_no_overheating():
    # Ambient is 5°C, safe max is 8°C -> ambient will not warm cargo above safe max
    cargo = _make_cargo(current_temperature_c=3.0)
    assessment = ThermalRiskService.evaluate_cargo_thermal_risk(
        cargo=cargo,
        ambient_temperature_c=5.0,
        cooling_status=CoolingStatus.FAILED,
    )
    assert assessment.spoilage_breached is False
    assert assessment.estimated_safe_window_min >= 9000.0


def test_missing_current_temp_uses_midpoint_fallback():
    cargo = _make_cargo(current_temperature_c=None, safe_temperature_min_c=2.0, safe_temperature_max_c=8.0)
    assessment = ThermalRiskService.evaluate_cargo_thermal_risk(cargo=cargo)
    assert assessment.current_temperature_c == 5.0  # (2 + 8) / 2
    assert "Current temperature unmeasured" in assessment.explanation


def test_invalid_ambient_temperature_rejected():
    cargo = _make_cargo()
    with pytest.raises(ValueError, match="outside plausible"):
        ThermalRiskService.evaluate_cargo_thermal_risk(
            cargo=cargo, ambient_temperature_c=120.0
        )


def test_transit_duration_predicts_arrival_temp():
    cargo = _make_cargo(current_temperature_c=4.0, backup_runtime_min=0.0)
    assessment = ThermalRiskService.evaluate_cargo_thermal_risk(
        cargo=cargo,
        ambient_temperature_c=30.0,
        cooling_status=CoolingStatus.FAILED,
        transit_duration_min=45.0,
    )
    assert assessment.predicted_temperature_after_transit_c is not None
    assert assessment.predicted_temperature_after_transit_c > 4.0


def test_surrogate_optimism_cannot_override_physics_safety_window(monkeypatch):
    """Safety-First Regression: A surrogate prediction of 440 min cannot override a 47 min physics window."""
    cargo = _make_cargo(current_temperature_c=4.0, backup_runtime_min=0.0)

    # Simulate an optimistic surrogate prediction
    import unittest.mock as mock
    mock_sm = mock.MagicMock()
    mock_resp = mock.MagicMock()
    mock_resp.read.return_value = b'{"predicted_breach_minutes": 440.0, "model_version": "1.0.1"}'
    mock_sm.invoke_endpoint.return_value = {"Body": mock_resp}

    monkeypatch.setenv("ENABLE_SAGEMAKER_INFERENCE", "true")
    with mock.patch("boto3.client", return_value=mock_sm):
        assessment = ThermalRiskService.evaluate_cargo_thermal_risk(
            cargo=cargo,
            ambient_temperature_c=35.0,
            cooling_status=CoolingStatus.FAILED,
        )

    # Raw surrogate is 440, but physics window is ~30-40 min; effective window must be conservative
    assert assessment.raw_surrogate_window_min == 440.0
    assert assessment.raw_physics_window_min < 50.0
    assert assessment.estimated_safe_window_min == assessment.raw_physics_window_min
    assert assessment.estimated_safe_window_min < 50.0


def test_surrogate_endpoint_failure_falls_back_to_physics(monkeypatch):
    """Verify endpoint failure automatically arms physics fallback without compromising safety."""
    cargo = _make_cargo(current_temperature_c=4.0, backup_runtime_min=0.0)

    import unittest.mock as mock
    from botocore.exceptions import ClientError
    mock_sm = mock.MagicMock()
    mock_sm.invoke_endpoint.side_effect = ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "Endpoint missing"}}, "invoke_endpoint")

    monkeypatch.setenv("ENABLE_SAGEMAKER_INFERENCE", "true")
    with mock.patch("boto3.client", return_value=mock_sm):
        assessment = ThermalRiskService.evaluate_cargo_thermal_risk(
            cargo=cargo,
            ambient_temperature_c=35.0,
            cooling_status=CoolingStatus.FAILED,
        )

    assert assessment.is_fallback is True
    assert assessment.prediction_source == "physics_fallback"
    assert "ClientError" in assessment.fallback_reason
    assert assessment.estimated_safe_window_min > 0.0

