"""
ColdRescue Simulator — Deterministic scenario factory.

Scenarios are reproducible given a (scenario_id, random_seed) pair.
No randomness is used in the event sequence — only in initial parameter
generation (cargo mass, receiver loads) when not explicitly overridden.

Available scenarios:
    REEFER_UNIT_FAILURE      — refrigeration unit fails; battery backup engaged
    COLD_ROOM_POWER_OUTAGE   — mains power lost; battery backup then depletes
    WAREHOUSE_GRID_OUTAGE    — grid outage → unstable → battery → no cooling
    BACKUP_RUNTIME_LOW       — backup power low warning; grid eventually restores
    BACKUP_POWER_DEPLETED    — backup depleted immediately; no cooling
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

from backend.common.utils import make_incident_id
from simulator.enums import IncidentType, PowerState, ReceiverCategory
from simulator.models import CargoProfile, ReceiverProfile, SimulatedIncident


# ── Predefined Receivers ────────────────────────────────────────────────────
def _default_receivers(rng: random.Random) -> List[ReceiverProfile]:
    """Generate a diverse set of 4 receivers, one per category."""
    return [
        ReceiverProfile(
            receiver_id="recv_cold_storage_01",
            name="Arctic Cold Logistics Hub",
            category=ReceiverCategory.COLD_STORAGE_FACILITY,
            capacity_kg=5000.0,
            current_load_kg=round(rng.uniform(1000, 3000), 1),
            accepts_temp_min_c=-25.0,
            accepts_temp_max_c=8.0,
            distance_km=round(rng.uniform(5, 40), 1),
            is_available=True,
        ),
        ReceiverProfile(
            receiver_id="recv_food_bank_01",
            name="City Food Bank Annex",
            category=ReceiverCategory.FOOD_BANK,
            capacity_kg=800.0,
            current_load_kg=round(rng.uniform(100, 400), 1),
            accepts_temp_min_c=0.0,
            accepts_temp_max_c=8.0,
            distance_km=round(rng.uniform(2, 15), 1),
            is_available=True,
        ),
        ReceiverProfile(
            receiver_id="recv_hospital_01",
            name="General Hospital Pharmacy Cold Room",
            category=ReceiverCategory.HOSPITAL_OR_CLINIC,
            capacity_kg=200.0,
            current_load_kg=round(rng.uniform(50, 150), 1),
            accepts_temp_min_c=2.0,
            accepts_temp_max_c=8.0,
            distance_km=round(rng.uniform(3, 20), 1),
            is_available=True,
        ),
        ReceiverProfile(
            receiver_id="recv_community_cold_01",
            name="Eastside Community Cold Room",
            category=ReceiverCategory.COMMUNITY_COLD_ROOM,
            capacity_kg=300.0,
            current_load_kg=round(rng.uniform(50, 200), 1),
            accepts_temp_min_c=0.0,
            accepts_temp_max_c=10.0,
            distance_km=round(rng.uniform(1, 10), 1),
            is_available=True,
        ),
    ]


# ── Scenario Definitions ────────────────────────────────────────────────────
def _build_reefer_unit_failure(rng: random.Random, seed: int) -> SimulatedIncident:
    cargo = CargoProfile(
        cargo_id="cargo_reefer_001",
        description="Mixed dairy produce — yoghurt and cheese",
        mass_kg=round(rng.uniform(200, 600), 1),
        safe_temp_min_c=2.0,
        safe_temp_max_c=8.0,
        initial_temp_c=4.0,
        backup_runtime_min=90.0,
        time_sensitivity_hours=3.0,
        unloading_duration_min=30.0,
    )
    return SimulatedIncident(
        incident_id=make_incident_id(),
        scenario_id="REEFER_UNIT_FAILURE",
        random_seed=seed,
        incident_type=IncidentType.REEFER_UNIT_FAILURE,
        location_id="vehicle_truck_09",
        location_name="Delivery Truck #09 — Route North",
        cargo=cargo,
        receivers=_default_receivers(rng),
        initial_power_state=PowerState.BATTERY,
    )


def _build_cold_room_power_outage(rng: random.Random, seed: int) -> SimulatedIncident:
    cargo = CargoProfile(
        cargo_id="cargo_cold_room_001",
        description="Fresh poultry — whole chickens",
        mass_kg=round(rng.uniform(400, 1200), 1),
        safe_temp_min_c=0.0,
        safe_temp_max_c=4.0,
        initial_temp_c=2.0,
        backup_runtime_min=120.0,
        time_sensitivity_hours=2.0,
        unloading_duration_min=45.0,
    )
    return SimulatedIncident(
        incident_id=make_incident_id(),
        scenario_id="COLD_ROOM_POWER_OUTAGE",
        random_seed=seed,
        incident_type=IncidentType.COLD_ROOM_POWER_OUTAGE,
        location_id="facility_cold_room_12",
        location_name="Rivergate Meat Processing Cold Room 12",
        cargo=cargo,
        receivers=_default_receivers(rng),
        initial_power_state=PowerState.GRID_UNSTABLE,
    )


def _build_warehouse_grid_outage(rng: random.Random, seed: int) -> SimulatedIncident:
    cargo = CargoProfile(
        cargo_id="cargo_warehouse_001",
        description="Frozen vegetables — mixed assortment",
        mass_kg=round(rng.uniform(1000, 3000), 1),
        safe_temp_min_c=-20.0,
        safe_temp_max_c=-12.0,
        initial_temp_c=-18.0,
        backup_runtime_min=60.0,
        time_sensitivity_hours=4.0,
        unloading_duration_min=90.0,
    )
    return SimulatedIncident(
        incident_id=make_incident_id(),
        scenario_id="WAREHOUSE_GRID_OUTAGE",
        random_seed=seed,
        incident_type=IncidentType.WAREHOUSE_GRID_OUTAGE,
        location_id="facility_warehouse_3",
        location_name="North Harbour Cold Warehouse — Bay 3",
        cargo=cargo,
        receivers=_default_receivers(rng),
        initial_power_state=PowerState.GRID_STABLE,
    )


def _build_backup_runtime_low(rng: random.Random, seed: int) -> SimulatedIncident:
    cargo = CargoProfile(
        cargo_id="cargo_backup_low_001",
        description="Insulin and temperature-sensitive medication",
        mass_kg=round(rng.uniform(20, 80), 1),
        safe_temp_min_c=2.0,
        safe_temp_max_c=8.0,
        initial_temp_c=5.0,
        backup_runtime_min=25.0,  # low — triggers BACKUP_RUNTIME_LOW
        time_sensitivity_hours=1.0,
        unloading_duration_min=15.0,
    )
    return SimulatedIncident(
        incident_id=make_incident_id(),
        scenario_id="BACKUP_RUNTIME_LOW",
        random_seed=seed,
        incident_type=IncidentType.BACKUP_RUNTIME_LOW,
        location_id="facility_pharmacy_cold_01",
        location_name="St. Mary's Hospital Pharmacy Cold Store",
        cargo=cargo,
        receivers=_default_receivers(rng),
        initial_power_state=PowerState.BATTERY,
    )


def _build_backup_power_depleted(rng: random.Random, seed: int) -> SimulatedIncident:
    cargo = CargoProfile(
        cargo_id="cargo_depleted_001",
        description="Chilled fresh produce — salad greens",
        mass_kg=round(rng.uniform(100, 300), 1),
        safe_temp_min_c=1.0,
        safe_temp_max_c=7.0,
        initial_temp_c=3.0,
        backup_runtime_min=0.0,  # already depleted
        time_sensitivity_hours=0.5,
        unloading_duration_min=20.0,
    )
    return SimulatedIncident(
        incident_id=make_incident_id(),
        scenario_id="BACKUP_POWER_DEPLETED",
        random_seed=seed,
        incident_type=IncidentType.BACKUP_POWER_DEPLETED,
        location_id="market_stall_cold_01",
        location_name="Central Market Shared Cold Unit",
        cargo=cargo,
        receivers=_default_receivers(rng),
        initial_power_state=PowerState.NO_COOLING,
    )


# ── Scenario Registry ───────────────────────────────────────────────────────
_SCENARIO_BUILDERS: Dict[str, object] = {
    "REEFER_UNIT_FAILURE": _build_reefer_unit_failure,
    "COLD_ROOM_POWER_OUTAGE": _build_cold_room_power_outage,
    "WAREHOUSE_GRID_OUTAGE": _build_warehouse_grid_outage,
    "BACKUP_RUNTIME_LOW": _build_backup_runtime_low,
    "BACKUP_POWER_DEPLETED": _build_backup_power_depleted,
}

AVAILABLE_SCENARIOS: List[str] = list(_SCENARIO_BUILDERS.keys())


def build_scenario(scenario_id: str, random_seed: int = 0) -> SimulatedIncident:
    """
    Build a deterministic SimulatedIncident for the given scenario_id and seed.

    The same (scenario_id, random_seed) pair always produces the same
    parameter values — cargo mass, receiver loads, distances.

    Parameters
    ----------
    scenario_id  : one of AVAILABLE_SCENARIOS
    random_seed  : integer seed for reproducibility (default 0)

    Returns
    -------
    SimulatedIncident — fully validated Pydantic model

    Raises
    ------
    ValueError : if scenario_id is not in AVAILABLE_SCENARIOS
    """
    if scenario_id not in _SCENARIO_BUILDERS:
        raise ValueError(
            f"Unknown scenario '{scenario_id}'. "
            f"Available: {AVAILABLE_SCENARIOS}"
        )
    rng = random.Random(random_seed)
    builder = _SCENARIO_BUILDERS[scenario_id]
    return builder(rng, random_seed)
