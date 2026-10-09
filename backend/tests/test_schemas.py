"""
ColdRescue M0 + M2 schema tests.

Tests for:
  - EventEnvelope base validation (timezone-aware, schema_version)
  - IncidentEvent (all 5 incident types)
  - CargoEvent (field validation, temperature range)
  - ReceiverEvent (all 4 categories)
  - RouteEvent, AssignmentEvent, ApprovalEvent, PredictionEvent, AuditEvent
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from backend.schemas.common import EventEnvelope
from backend.schemas.incident import IncidentEvent, IncidentType, IncidentStatus
from backend.schemas.cargo import CargoEvent, CargoSensitivity
from backend.schemas.receiver import ReceiverEvent, ReceiverCategory
from backend.schemas.route import RouteEvent, RouteStatus
from backend.schemas.assignment import AssignmentEvent, AssignmentStatus
from backend.schemas.approval import ApprovalEvent, ApprovalDecision
from backend.schemas.prediction import PredictionEvent
from backend.schemas.audit_event import AuditEvent, AuditAction
from pydantic import ValidationError


# ── Helpers ──────────────────────────────────────────────────────────────────
def _ts() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _base_envelope(**kwargs) -> dict:
    return {
        "event_id": "evt_test_001",
        "event_type": "test.event",
        "occurred_at": _ts(),
        "schema_version": "1.0.0",
        "correlation_id": "corr_test_001",
        "idempotency_key": "ikey_test_001",
        **kwargs,
    }


# ── EventEnvelope Validation ─────────────────────────────────────────────────
def test_event_envelope_rejects_naive_datetime():
    """occurred_at must be timezone-aware."""
    with pytest.raises(ValidationError, match="timezone-aware"):
        EventEnvelope(
            **{
                **_base_envelope(),
                "occurred_at": datetime(2024, 6, 1, 12, 0, 0),  # naive
            }
        )


def test_event_envelope_rejects_wrong_schema_version():
    """schema_version must equal '1.0.0'."""
    with pytest.raises(ValidationError, match="schema_version"):
        EventEnvelope(**{**_base_envelope(), "schema_version": "2.0.0"})


def test_event_envelope_accepts_valid_data():
    env = EventEnvelope(**_base_envelope())
    assert env.schema_version == "1.0.0"
    assert env.occurred_at.tzinfo is not None


# ── IncidentEvent — 5 Incident Types ────────────────────────────────────────
@pytest.mark.parametrize("incident_type", list(IncidentType))
def test_incident_event_all_types(incident_type):
    """All 5 IncidentType values must be accepted."""
    evt = IncidentEvent(
        **_base_envelope(incident_id="inc_test_001"),
        incident_type=incident_type,
        location_id="loc_001",
        location_name="Test Location",
        reported_by="test_operator",
    )
    assert evt.incident_type == incident_type
    assert evt.status == IncidentStatus.OPEN


# ── CargoEvent ───────────────────────────────────────────────────────────────
def test_cargo_event_valid():
    evt = CargoEvent(
        **_base_envelope(incident_id="inc_001"),
        cargo_description="Dairy produce",
        cargo_kg=500.0,
        safe_temperature_min_c=2.0,
        safe_temperature_max_c=8.0,
        backup_runtime_min=90.0,
        available_capacity_kg=1000.0,
        unloading_duration_min=30.0,
    )
    assert evt.cargo_kg == 500.0


def test_cargo_event_rejects_negative_mass():
    with pytest.raises(ValidationError):
        CargoEvent(
            **_base_envelope(),
            cargo_description="Test",
            cargo_kg=-10.0,
            safe_temperature_min_c=2.0,
            safe_temperature_max_c=8.0,
            backup_runtime_min=90.0,
            available_capacity_kg=1000.0,
            unloading_duration_min=30.0,
        )


def test_cargo_event_rejects_inverted_temp_range():
    with pytest.raises(ValidationError, match="must not exceed"):
        CargoEvent(
            **_base_envelope(),
            cargo_description="Test",
            cargo_kg=100.0,
            safe_temperature_min_c=10.0,   # > max — invalid
            safe_temperature_max_c=5.0,
            backup_runtime_min=60.0,
            available_capacity_kg=500.0,
            unloading_duration_min=15.0,
        )


def test_cargo_event_rejects_negative_backup_runtime():
    with pytest.raises(ValidationError):
        CargoEvent(
            **_base_envelope(),
            cargo_description="Test",
            cargo_kg=100.0,
            safe_temperature_min_c=2.0,
            safe_temperature_max_c=8.0,
            backup_runtime_min=-5.0,
            available_capacity_kg=500.0,
            unloading_duration_min=15.0,
        )


# ── ReceiverEvent — 4 Categories ────────────────────────────────────────────
@pytest.mark.parametrize("category", list(ReceiverCategory))
def test_receiver_event_all_categories(category):
    """All 4 ReceiverCategory values must be accepted."""
    evt = ReceiverEvent(
        **_base_envelope(),
        receiver_id="recv_001",
        receiver_name="Test Receiver",
        category=category,
        capacity_kg=1000.0,
        current_load_kg=200.0,
        accepts_temperature_min_c=0.0,
        accepts_temperature_max_c=8.0,
    )
    assert evt.category == category


# ── RouteEvent ───────────────────────────────────────────────────────────────
def test_route_event_valid():
    evt = RouteEvent(
        **_base_envelope(),
        route_id="route_001",
        driver_id="driver_001",
        receiver_id="recv_001",
        total_distance_km=25.0,
        estimated_duration_min=45.0,
    )
    assert evt.status == RouteStatus.PLANNED


# ── AssignmentEvent ──────────────────────────────────────────────────────────
def test_assignment_event_valid():
    evt = AssignmentEvent(
        **_base_envelope(),
        assignment_id="assign_001",
        receiver_id="recv_001",
        driver_id="driver_001",
        cargo_kg=300.0,
    )
    assert evt.status == AssignmentStatus.PENDING


# ── ApprovalEvent ────────────────────────────────────────────────────────────
def test_approval_event_approved():
    evt = ApprovalEvent(
        **_base_envelope(),
        approval_id="approval_001",
        assignment_id="assign_001",
        decision=ApprovalDecision.APPROVED,
        approved_by="operator_jane",
    )
    assert evt.decision == ApprovalDecision.APPROVED


# ── PredictionEvent ──────────────────────────────────────────────────────────
def test_prediction_event_valid():
    evt = PredictionEvent(
        **_base_envelope(),
        prediction_type="THERMAL_PROGRESSION",
        predicted_temperature_c=12.5,
        time_to_spoilage_min=45.0,
        confidence=0.7,
    )
    assert evt.model_name == "newton_linear_v1"


# ── AuditEvent ───────────────────────────────────────────────────────────────
def test_audit_event_simulation_started():
    evt = AuditEvent(
        **_base_envelope(),
        action=AuditAction.SIMULATION_STARTED,
        actor="simulator.engine",
        details={"scenario_id": "REEFER_UNIT_FAILURE"},
    )
    assert evt.action == AuditAction.SIMULATION_STARTED
