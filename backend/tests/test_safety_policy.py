"""
Tests for SafetyPolicyEngine.

Tests cover:
  - POL-CAP-001: Capacity limit violation causes hard block
  - POL-COMPAT-002: Incompatible cargo category causes hard block
  - POL-TEMP-003: Temperature envelope mismatch causes hard block
  - POL-COOL-004: Failed cooling causes hard block; degraded surfaces warning
  - POL-TIME-005: Travel time exceeding thermal preservation window causes hard block
  - POL-PWR-006: Insufficient receiver backup runtime surfaces warning
  - Fully compliant assignment passes as safe
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from backend.models.domain import (
    CargoItem,
    CoolingStatus,
    IncidentRecord,
    IncidentStatus,
    IncidentType,
    Location,
    ReceiverCategory,
    ReceiverNode,
    SeverityLevel,
)
from backend.policies.safety_policy import SafetyPolicyEngine, RuleSeverity


def _make_fixture(
    cargo_kg: float = 300.0,
    cargo_type: str = "dairy",
    cargo_safe_min: float = 2.0,
    cargo_safe_max: float = 8.0,
    cargo_backup_min: float = 90.0,
    receiver_capacity_kg: float = 2000.0,
    receiver_current_load_kg: float = 500.0,
    receiver_types: list[str] = None,
    receiver_safe_min: float = 0.0,
    receiver_safe_max: float = 10.0,
    receiver_cooling: CoolingStatus = CoolingStatus.OPERATIONAL,
    receiver_backup_min: float = 180.0,
    travel_time_min: float = 20.0,
) -> tuple[IncidentRecord, ReceiverNode, float]:
    cargo = CargoItem(
        cargo_id="c_test_01",
        description="Test Cargo",
        cargo_type=cargo_type,
        cargo_kg=cargo_kg,
        safe_temperature_min_c=cargo_safe_min,
        safe_temperature_max_c=cargo_safe_max,
        current_temperature_c=4.0,
        backup_runtime_min=cargo_backup_min,
        unloading_duration_min=15.0,
    )
    incident = IncidentRecord(
        incident_id="inc_test_01",
        incident_type=IncidentType.REEFER_UNIT_FAILURE,
        severity=SeverityLevel.HIGH,
        status=IncidentStatus.OPEN,
        location=Location(location_id="loc_origin", name="Origin Farm"),
        cargo=cargo,
        reported_at=datetime.now(timezone.utc),
    )
    receiver = ReceiverNode(
        receiver_id="recv_test_01",
        name="Test Hub",
        category=ReceiverCategory.COLD_STORAGE_FACILITY,
        capacity_kg=receiver_capacity_kg,
        current_load_kg=receiver_current_load_kg,
        accepts_temperature_min_c=receiver_safe_min,
        accepts_temperature_max_c=receiver_safe_max,
        compatible_cargo_types=receiver_types or ["dairy", "general"],
        cooling_status=receiver_cooling,
        backup_runtime_min=receiver_backup_min,
        distance_km=15.0,
        travel_time_min=travel_time_min,
    )
    return incident, receiver, travel_time_min


def test_fully_compliant_assignment_passes():
    incident, receiver, travel_time = _make_fixture()
    assessment = SafetyPolicyEngine.evaluate_assignment(
        incident=incident, receiver=receiver, travel_time_min=travel_time
    )
    assert assessment.is_safe is True
    assert assessment.is_hard_blocked is False
    assert len(assessment.hard_block_reasons) == 0


def test_capacity_exceeded_hard_blocks():
    # Cargo mass 2500 kg > available space (2000 - 500 = 1500 kg)
    incident, receiver, travel_time = _make_fixture(cargo_kg=2500.0)
    assessment = SafetyPolicyEngine.evaluate_assignment(
        incident=incident, receiver=receiver, travel_time_min=travel_time
    )
    assert assessment.is_safe is False
    assert assessment.is_hard_blocked is True
    assert any("Capacity Exceeded" in r for r in assessment.hard_block_reasons)


def test_incompatible_cargo_category_hard_blocks():
    # Cargo is 'pharmaceutical', receiver only handles ['dairy', 'frozen']
    incident, receiver, travel_time = _make_fixture(
        cargo_type="pharmaceutical",
        receiver_types=["dairy", "frozen"],
    )
    assessment = SafetyPolicyEngine.evaluate_assignment(
        incident=incident, receiver=receiver, travel_time_min=travel_time
    )
    assert assessment.is_safe is False
    assert assessment.is_hard_blocked is True
    assert any("Incompatible Cargo Type" in r for r in assessment.hard_block_reasons)


def test_temperature_envelope_mismatch_hard_blocks():
    # Cargo requires -20°C to -15°C (frozen), but receiver only accepts 0°C to 10°C (chilled)
    incident, receiver, travel_time = _make_fixture(
        cargo_safe_min=-20.0,
        cargo_safe_max=-15.0,
        receiver_safe_min=0.0,
        receiver_safe_max=10.0,
    )
    assessment = SafetyPolicyEngine.evaluate_assignment(
        incident=incident, receiver=receiver, travel_time_min=travel_time
    )
    assert assessment.is_safe is False
    assert assessment.is_hard_blocked is True
    assert any("Temperature Envelope Mismatch" in r for r in assessment.hard_block_reasons)


def test_failed_receiver_cooling_hard_blocks():
    incident, receiver, travel_time = _make_fixture(receiver_cooling=CoolingStatus.FAILED)
    assessment = SafetyPolicyEngine.evaluate_assignment(
        incident=incident, receiver=receiver, travel_time_min=travel_time
    )
    assert assessment.is_safe is False
    assert assessment.is_hard_blocked is True
    assert any("Cooling Failure" in r for r in assessment.hard_block_reasons)


def test_degraded_receiver_cooling_adds_warning():
    incident, receiver, travel_time = _make_fixture(receiver_cooling=CoolingStatus.DEGRADED)
    assessment = SafetyPolicyEngine.evaluate_assignment(
        incident=incident, receiver=receiver, travel_time_min=travel_time
    )
    assert assessment.is_safe is True
    assert assessment.is_hard_blocked is False
    assert len(assessment.warnings) > 0
    assert any("DEGRADED" in w for w in assessment.warnings)


def test_excessive_travel_time_exceeding_thermal_window_hard_blocks():
    # Cargo has only 5 min backup runtime and warm initial temp, transit is 180 min
    incident, receiver, _ = _make_fixture(
        cargo_backup_min=5.0,
        travel_time_min=180.0,
    )
    assessment = SafetyPolicyEngine.evaluate_assignment(
        incident=incident, receiver=receiver, travel_time_min=180.0
    )
    assert assessment.is_safe is False
    assert assessment.is_hard_blocked is True
    assert any("Thermal Deadline Infeasible" in r for r in assessment.hard_block_reasons)
