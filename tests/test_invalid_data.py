"""
ColdRescue M2 invalid-data rejection tests.

Verifies that invalid inputs are consistently rejected with ValidationError
or the appropriate custom exception types.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from backend.schemas.common import EventEnvelope
from backend.schemas.cargo import CargoEvent
from backend.schemas.receiver import ReceiverEvent, ReceiverCategory
from simulator.models import CargoProfile, ReceiverProfile
from simulator.state_machine import (
    InvalidTransitionError,
    DuplicateEventError,
    PowerStateMachine,
)
from simulator.enums import PowerState


def _ts() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _base(**kwargs) -> dict:
    return {
        "event_id": "evt_001",
        "event_type": "test.event",
        "occurred_at": _ts(),
        "schema_version": "1.0.0",
        "correlation_id": "corr_001",
        "idempotency_key": "ikey_001",
        **kwargs,
    }


# ── EventEnvelope Invalid Data ───────────────────────────────────────────────
def test_reject_naive_datetime():
    with pytest.raises(ValidationError, match="timezone-aware"):
        EventEnvelope(**{**_base(), "occurred_at": datetime(2024, 1, 1)})


def test_reject_wrong_schema_version():
    with pytest.raises(ValidationError, match="schema_version"):
        EventEnvelope(**{**_base(), "schema_version": "99.0.0"})


def test_reject_extra_fields():
    """EventEnvelope must reject unknown fields (extra='forbid')."""
    with pytest.raises(ValidationError):
        EventEnvelope(**{**_base(), "unexpected_field": "bad"})


# ── CargoEvent Invalid Data ──────────────────────────────────────────────────
def test_reject_cargo_negative_kg():
    with pytest.raises(ValidationError):
        CargoEvent(
            **_base(),
            cargo_description="Test",
            cargo_kg=-1.0,
            safe_temperature_min_c=2.0,
            safe_temperature_max_c=8.0,
            backup_runtime_min=60.0,
            available_capacity_kg=500.0,
            unloading_duration_min=15.0,
        )


def test_reject_cargo_negative_unloading():
    with pytest.raises(ValidationError):
        CargoEvent(
            **_base(),
            cargo_description="Test",
            cargo_kg=100.0,
            safe_temperature_min_c=2.0,
            safe_temperature_max_c=8.0,
            backup_runtime_min=60.0,
            available_capacity_kg=500.0,
            unloading_duration_min=-5.0,
        )


def test_reject_cargo_negative_capacity():
    with pytest.raises(ValidationError):
        CargoEvent(
            **_base(),
            cargo_description="Test",
            cargo_kg=100.0,
            safe_temperature_min_c=2.0,
            safe_temperature_max_c=8.0,
            backup_runtime_min=60.0,
            available_capacity_kg=-1.0,
            unloading_duration_min=15.0,
        )


def test_reject_cargo_inverted_temp_range():
    with pytest.raises(ValidationError, match="must not exceed"):
        CargoEvent(
            **_base(),
            cargo_description="Test",
            cargo_kg=100.0,
            safe_temperature_min_c=15.0,
            safe_temperature_max_c=5.0,  # less than min
            backup_runtime_min=60.0,
            available_capacity_kg=500.0,
            unloading_duration_min=15.0,
        )


# ── ReceiverProfile Invalid Data ─────────────────────────────────────────────
def test_reject_receiver_overloaded():
    with pytest.raises(ValidationError, match="exceeds"):
        ReceiverProfile(
            receiver_id="r_bad",
            name="Overloaded",
            category=ReceiverCategory.FOOD_BANK,
            capacity_kg=100.0,
            current_load_kg=500.0,  # > capacity
            accepts_temp_min_c=0.0,
            accepts_temp_max_c=8.0,
            distance_km=5.0,
        )


def test_reject_receiver_negative_distance():
    with pytest.raises(ValidationError):
        ReceiverProfile(
            receiver_id="r_neg",
            name="Bad distance",
            category=ReceiverCategory.COLD_STORAGE_FACILITY,
            capacity_kg=1000.0,
            current_load_kg=100.0,
            accepts_temp_min_c=0.0,
            accepts_temp_max_c=8.0,
            distance_km=-5.0,  # invalid
        )


# ── State Machine Invalid Transitions ────────────────────────────────────────
def test_reject_invalid_transition_from_no_cooling():
    """NO_COOLING is terminal — all transitions must be rejected."""
    psm = PowerStateMachine(
        incident_id="inc_001",
        location_id="loc_001",
        location_name="Test Location",
        initial_state=PowerState.NO_COOLING,
    )
    with pytest.raises(InvalidTransitionError):
        psm.transition(PowerState.GRID_STABLE)


def test_reject_invalid_transition_grid_stable_to_no_cooling():
    """GRID_STABLE cannot jump directly to NO_COOLING."""
    psm = PowerStateMachine(
        incident_id="inc_002",
        location_id="loc_002",
        location_name="Test",
        initial_state=PowerState.GRID_STABLE,
    )
    with pytest.raises(InvalidTransitionError):
        psm.transition(PowerState.NO_COOLING)


def test_reject_duplicate_idempotency_key():
    """Duplicate idempotency key must raise DuplicateEventError."""
    psm = PowerStateMachine(
        incident_id="inc_003",
        location_id="loc_003",
        location_name="Test",
        initial_state=PowerState.GRID_STABLE,
    )
    key = "duplicate_key_123"
    psm.transition(PowerState.GRID_UNSTABLE, idempotency_key=key)
    with pytest.raises(DuplicateEventError):
        psm.transition(PowerState.GRID_STABLE, idempotency_key=key)
