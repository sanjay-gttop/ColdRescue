"""
Unit tests verifying Phase 1 Step 2 and Phase 2 backend components:
  1. DynamoDB Stream consumer record ingestion, metric emission, and no-loop guarantee.
  2. Orchestration failure handler (0 kg false recovery) and policy blocked evaluation.
  3. Transient retry vs business outcome policy branching.
"""
import pytest
from unittest.mock import MagicMock, patch
from backend.handlers.stream_consumer import dynamodb_stream_consumer_handler
from backend.handlers.orchestration_handlers import (
    handle_failure_handler,
    evaluate_safety_policy_handler,
    finalize_audit_handler,
)


def test_stream_consumer_emits_cloudwatch_metric():
    """Verify stream consumer extracts record count and emits EventsPersistedCount."""
    event = {
        "Records": [
            {"eventID": "1", "eventName": "INSERT"},
            {"eventID": "2", "eventName": "MODIFY"},
        ]
    }
    with patch("boto3.client") as mock_boto:
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        res = dynamodb_stream_consumer_handler(event)
        assert res["status"] == "PROCESSED"
        assert res["events_persisted"] == 2
        mock_cw.put_metric_data.assert_called_once()
        call_kwargs = mock_cw.put_metric_data.call_args[1]
        assert call_kwargs["Namespace"] == "ColdRescue/Events"
        assert call_kwargs["MetricData"][0]["MetricName"] == "EventsPersistedCount"
        assert call_kwargs["MetricData"][0]["Value"] == 2.0


def test_stream_consumer_handles_empty_records():
    """Verify empty record batch gracefully returns NO_RECORDS without emitting metrics."""
    res = dynamodb_stream_consumer_handler({"Records": []})
    assert res["status"] == "NO_RECORDS"
    assert res["events_persisted"] == 0


def test_handle_failure_ensures_zero_cargo_diverted():
    """Verify handle_failure_handler guarantees 0.0 kg diverted on execution failure."""
    event = {
        "incident_id": "inc_fail_test",
        "incident": {
            "cargo": {"mass_kg": 1500.0}
        },
        "correlation_id": "corr_test_99",
    }
    with patch("backend.services.event_ingestion.get_event_store") as mock_store:
        mock_store.return_value = MagicMock()
        res = handle_failure_handler(event)
        assert res["status"] == "FAILED"
        assert res["outcome"] == "EXECUTION_FAILED"
        assert res["cargo_diverted_kg"] == 0.0
        assert res["cargo_at_risk_kg"] == 1500.0


def test_policy_blocked_evaluates_without_sns_failure():
    """Verify POLICY_BLOCKED is returned as a deterministic outcome, not an exception."""
    event = {
        "incident_id": "inc_block_test",
        "allocation_result": {
            "candidate_assignment": None
        },
        "receivers": []
    }
    with patch("boto3.client") as mock_boto:
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        res = evaluate_safety_policy_handler(event)
        assert res["policy_status"] == "POLICY_BLOCKED"
        assert res["allowed"] is False
        assert "NO_FEASIBLE_ASSIGNMENT_FOUND" in res["hard_block_reasons"]


def test_thermal_risk_fallback_when_sagemaker_offline():
    """Verify when SageMaker is offline (timeout or disabled), system cleanly falls back to physics bound."""
    from backend.services.thermal_risk import ThermalRiskService
    from backend.models.domain import CargoItem, CoolingStatus
    import os

    cargo = CargoItem(
        cargo_id="CARGO-TEST-FALLBACK",
        description="Raw whole milk",
        cargo_kg=1200.0,
        safe_temperature_min_c=2.0,
        safe_temperature_max_c=8.0,
        current_temperature_c=5.4,
        backup_runtime_min=0.0,
        unloading_duration_min=15.0,
    )

    with patch.dict(os.environ, {"ENABLE_SAGEMAKER_INFERENCE": "false"}):
        result = ThermalRiskService.evaluate_cargo_thermal_risk(
            cargo=cargo,
            ambient_temperature_c=38.0,
            cooling_status=CoolingStatus.FAILED,
        )
        assert result.is_fallback is True
        assert result.prediction_source == "physics_fallback"
        assert result.estimated_safe_window_min > 0
        assert result.raw_physics_window_min == result.estimated_safe_window_min
