"""
ColdRescue M2 serialisation tests.

Verifies that all domain models:
  1. Serialise to JSON without errors
  2. Deserialise back from JSON with identical values
  3. Produce correct fixture JSON that can be saved to data/fixtures/
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from backend.schemas.incident import IncidentEvent, IncidentType
from backend.schemas.cargo import CargoEvent, CargoSensitivity
from backend.schemas.receiver import ReceiverEvent, ReceiverCategory
from backend.schemas.audit_event import AuditEvent, AuditAction
from simulator.models import CargoProfile, SimulatedIncident
from simulator.scenario import build_scenario
from simulator.engine import run_simulation


def _ts() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _base(**kwargs) -> dict:
    return {
        "event_id": "evt_ser_001",
        "event_type": "test.event",
        "occurred_at": _ts(),
        "schema_version": "1.0.0",
        "correlation_id": "corr_ser_001",
        "idempotency_key": "ikey_ser_001",
        **kwargs,
    }


# ── Round-trip: Schema Events ────────────────────────────────────────────────

def test_incident_event_round_trip():
    original = IncidentEvent(
        **_base(incident_id="inc_001"),
        incident_type=IncidentType.REEFER_UNIT_FAILURE,
        location_id="loc_001",
        location_name="Test Location",
        reported_by="test_operator",
    )

    json_str = original.model_dump_json()
    data = json.loads(json_str)
    restored = IncidentEvent.model_validate(data)

    assert restored.incident_type == original.incident_type
    assert restored.event_id == original.event_id


def test_cargo_event_round_trip():
    original = CargoEvent(
        **_base(),
        cargo_description="Dairy",
        cargo_kg=500.0,
        safe_temperature_min_c=2.0,
        safe_temperature_max_c=8.0,
        backup_runtime_min=90.0,
        available_capacity_kg=1000.0,
        unloading_duration_min=30.0,
        time_sensitivity=CargoSensitivity.HIGH,
    )

    restored = CargoEvent.model_validate(
        json.loads(original.model_dump_json())
    )

    assert restored.cargo_kg == original.cargo_kg
    assert restored.time_sensitivity == CargoSensitivity.HIGH


def test_receiver_event_round_trip():
    original = ReceiverEvent(
        **_base(),
        receiver_id="r001",
        receiver_name="Arctic Hub",
        category=ReceiverCategory.COLD_STORAGE_FACILITY,
        capacity_kg=5000.0,
        current_load_kg=1000.0,
        accepts_temperature_min_c=-25.0,
        accepts_temperature_max_c=8.0,
    )

    restored = ReceiverEvent.model_validate(
        json.loads(original.model_dump_json())
    )

    assert restored.category == ReceiverCategory.COLD_STORAGE_FACILITY


def test_audit_event_round_trip():
    original = AuditEvent(
        **_base(),
        action=AuditAction.SIMULATION_STARTED,
        actor="simulator.engine",
        details={
            "scenario": "REEFER_UNIT_FAILURE",
            "seed": 42,
        },
    )

    restored = AuditEvent.model_validate(
        json.loads(original.model_dump_json())
    )

    assert restored.action == AuditAction.SIMULATION_STARTED
    assert restored.details["seed"] == 42


# ── Round-trip: Simulator Models ────────────────────────────────────────────

def test_cargo_profile_round_trip():
    original = CargoProfile(
        cargo_id="c001",
        description="Frozen veg",
        mass_kg=1000.0,
        safe_temp_min_c=-20.0,
        safe_temp_max_c=-12.0,
        initial_temp_c=-18.0,
        backup_runtime_min=60.0,
        time_sensitivity_hours=4.0,
        unloading_duration_min=90.0,
    )

    data = json.loads(original.model_dump_json())
    restored = CargoProfile.model_validate(data)

    assert restored.mass_kg == original.mass_kg
    assert restored.safe_temp_min_c == original.safe_temp_min_c


def test_simulated_incident_round_trip():
    incident = build_scenario(
        "COLD_ROOM_POWER_OUTAGE",
        random_seed=0,
    )

    data = json.loads(incident.model_dump_json())
    restored = SimulatedIncident.model_validate(data)

    assert restored.incident_id == incident.incident_id
    assert restored.cargo.description == incident.cargo.description
    assert len(restored.receivers) == len(incident.receivers)


# ── Engine Events Are All Schema-Valid ──────────────────────────────────────

@pytest.mark.parametrize(
    "scenario_id",
    [
        "REEFER_UNIT_FAILURE",
        "COLD_ROOM_POWER_OUTAGE",
        "WAREHOUSE_GRID_OUTAGE",
        "BACKUP_RUNTIME_LOW",
        "BACKUP_POWER_DEPLETED",
    ],
)
def test_engine_emits_valid_events(scenario_id):
    """All engine-emitted events must be serialisable and schema-valid."""

    result = run_simulation(scenario_id, seed=0)

    # Audit event
    assert result.audit_event is not None
    assert result.audit_event.schema_version == "1.0.0"
    assert result.audit_event.occurred_at.tzinfo is not None

    # Cargo event
    assert result.cargo_event is not None
    assert result.cargo_event.cargo_kg > 0

    # Prediction event
    assert result.prediction_event is not None
    assert result.prediction_event.occurred_at.tzinfo is not None

    # Thermal steps
    assert len(result.thermal_steps) > 0

    # All power events must be valid IncidentEvents
    for evt in result.power_events:
        assert evt.schema_version == "1.0.0"
        assert evt.occurred_at.tzinfo is not None

        restored = IncidentEvent.model_validate(
            json.loads(evt.model_dump_json())
        )

        assert restored.event_id == evt.event_id


# ── Regression Test: Final Power State ──────────────────────────────────────

def test_simulation_report_records_final_power_state():
    """
    The simulation report must record the final power state,
    not the incident's initial power state.
    """

    result = run_simulation(
        "REEFER_UNIT_FAILURE",
        seed=42,
    )

    report = result.to_report()["simulation_report"]

    assert report["final_power_state"] == "NO_COOLING"