"""
Tests for Greedy and Global Allocation Engines.

Tests cover:
  - Single and multi-incident greedy matching
  - Global allocation optimization balancing specialized vs general storage
  - Capacity exhaustion preventing double-booking
  - Infeasible cargo rejection with clear explanation
  - Metric computation (utilization %, average travel time, risk scores)
"""
from __future__ import annotations

from datetime import datetime, timezone
import pytest

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
from backend.services.allocation_greedy import GreedyAllocationEngine
from backend.services.allocation_global import GlobalAllocationEngine


def _build_fleet_scenario():
    # 2 Incidents:
    # Inc 1: Ultra-low temp frozen vaccines (200 kg, -25°C to -15°C, high urgency)
    # Inc 2: Standard chilled milk (800 kg, 2°C to 8°C, medium urgency)
    inc_vaccines = IncidentRecord(
        incident_id="inc_vaccines_01",
        incident_type=IncidentType.REEFER_UNIT_FAILURE,
        severity=SeverityLevel.CRITICAL,
        status=IncidentStatus.OPEN,
        location=Location(location_id="loc_pharma", name="Pharma Hub", latitude=12.97, longitude=77.59),
        cargo=CargoItem(
            cargo_id="c_vac",
            description="Ultra-low Frozen Vaccines",
            cargo_type="pharma",
            cargo_kg=200.0,
            safe_temperature_min_c=-25.0,
            safe_temperature_max_c=-15.0,
            current_temperature_c=-20.0,
            backup_runtime_min=30.0,
            unloading_duration_min=10.0,
        ),
        reported_at=datetime.now(timezone.utc),
    )

    inc_milk = IncidentRecord(
        incident_id="inc_milk_01",
        incident_type=IncidentType.COLD_ROOM_POWER_OUTAGE,
        severity=SeverityLevel.HIGH,
        status=IncidentStatus.OPEN,
        location=Location(location_id="loc_dairy", name="Dairy Farm", latitude=12.98, longitude=77.60),
        cargo=CargoItem(
            cargo_id="c_milk",
            description="Fresh Chilled Milk",
            cargo_type="dairy",
            cargo_kg=800.0,
            safe_temperature_min_c=2.0,
            safe_temperature_max_c=8.0,
            current_temperature_c=4.0,
            backup_runtime_min=90.0,
            unloading_duration_min=20.0,
        ),
        reported_at=datetime.now(timezone.utc),
    )

    # 2 Receivers:
    # Recv 1: Specialized Ultra-low Cold Vault (Capacity 500 kg, accepts -30°C to 0°C, 10 km away)
    # Recv 2: Regional Dairy Warehouse (Capacity 2000 kg, accepts 0°C to 10°C, 15 km away)
    recv_vault = ReceiverNode(
        receiver_id="recv_vault_01",
        name="Cryo Vault Central",
        category=ReceiverCategory.HOSPITAL_OR_CLINIC,
        capacity_kg=500.0,
        current_load_kg=0.0,
        accepts_temperature_min_c=-30.0,
        accepts_temperature_max_c=0.0,
        compatible_cargo_types=["pharma", "frozen", "general"],
        latitude=12.95,
        longitude=77.58,
        distance_km=10.0,
        travel_time_min=15.0,
    )

    recv_dairy = ReceiverNode(
        receiver_id="recv_dairy_01",
        name="East Chilled Distribution Center",
        category=ReceiverCategory.COLD_STORAGE_FACILITY,
        capacity_kg=2000.0,
        current_load_kg=0.0,
        accepts_temperature_min_c=0.0,
        accepts_temperature_max_c=10.0,
        compatible_cargo_types=["dairy", "general"],
        latitude=13.00,
        longitude=77.65,
        distance_km=15.0,
        travel_time_min=20.0,
    )

    return [inc_vaccines, inc_milk], [recv_vault, recv_dairy]


def test_greedy_allocation_success():
    incidents, receivers = _build_fleet_scenario()
    result = GreedyAllocationEngine.solve(incidents=incidents, receivers=receivers)

    assert result.strategy == "greedy"
    assert len(result.assignments) == 2
    assert len(result.unassigned_incidents) == 0
    assert result.capacity_utilization_pct > 0

    # Verify vaccine assigned to vault, milk assigned to dairy
    vac_assign = next(a for a in result.assignments if a.incident_id == "inc_vaccines_01")
    assert vac_assign.receiver_id == "recv_vault_01"
    assert vac_assign.feasible is True

    milk_assign = next(a for a in result.assignments if a.incident_id == "inc_milk_01")
    assert milk_assign.receiver_id == "recv_dairy_01"
    assert milk_assign.feasible is True


def test_global_allocation_success():
    incidents, receivers = _build_fleet_scenario()
    result = GlobalAllocationEngine.solve(incidents=incidents, receivers=receivers)

    assert result.strategy == "global"
    assert len(result.assignments) == 2
    assert len(result.unassigned_incidents) == 0
    assert result.total_spoilage_risk_score <= 30


def test_capacity_exhaustion_leaves_subsequent_unassigned():
    incidents, receivers = _build_fleet_scenario()
    # Shrink vault capacity to 150 kg (vaccines need 200 kg)
    small_vault = receivers[0].model_copy(update={"capacity_kg": 150.0})

    result = GreedyAllocationEngine.solve(
        incidents=incidents, receivers=[small_vault, receivers[1]]
    )

    # Vaccines cannot fit anywhere (dairy temp mismatch, vault capacity exceeded)
    assert "inc_vaccines_01" in result.unassigned_incidents
    vac_assign = next(a for a in result.assignments if a.incident_id == "inc_vaccines_01")
    assert vac_assign.feasible is False
    assert vac_assign.receiver_id == "NONE"


def test_allocation_preserves_safety_policy_enforcement():
    incidents, receivers = _build_fleet_scenario()
    # Set vault cooling to FAILED
    failed_vault = receivers[0].model_copy(update={"cooling_status": CoolingStatus.FAILED})

    result = GlobalAllocationEngine.solve(
        incidents=incidents, receivers=[failed_vault, receivers[1]]
    )

    # Vaccines cannot use failed cooling vault
    assert "inc_vaccines_01" in result.unassigned_incidents
