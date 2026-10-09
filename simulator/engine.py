"""
ColdRescue Simulator — main simulation engine.

Orchestrates a full power-failure simulation:
  1. Builds a SimulatedIncident from a named scenario
  2. Runs the power-state machine through its event sequence
  3. Runs the thermal model over the backup runtime window
  4. Emits validated EventEnvelope events
  5. Prints a structured simulation report

CLI Usage:
    py -m simulator.engine --scenario REEFER_UNIT_FAILURE
    py -m simulator.engine --scenario WAREHOUSE_GRID_OUTAGE --seed 42
    py -m simulator.engine --list-scenarios

All emitted events validate against EventEnvelope (schema_version=1.0.0,
timezone-aware occurred_at).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import List

from backend.common.utils import (
    make_correlation_id,
    make_event_id,
    make_idempotency_key,
    utc_now,
)
from backend.schemas.audit_event import AuditAction, AuditEvent
from backend.schemas.cargo import CargoEvent, CargoSensitivity
from backend.schemas.prediction import PredictionEvent
from simulator.enums import IncidentType, PowerState
from simulator.models import CargoProfile, SimulatedIncident
from simulator.scenario import AVAILABLE_SCENARIOS, build_scenario
from simulator.state_machine import InvalidTransitionError, PowerStateMachine
from simulator.thermal import ThermalModel


# ── Scenario Power-Event Sequences ──────────────────────────────────────────
_SCENARIO_SEQUENCES: dict[str, list[PowerState]] = {
    "REEFER_UNIT_FAILURE": [
        PowerState.NO_COOLING,       # reefer fails → no cooling
    ],
    "COLD_ROOM_POWER_OUTAGE": [
        PowerState.BATTERY,          # switches to battery backup
        PowerState.NO_COOLING,       # battery depletes
    ],
    "WAREHOUSE_GRID_OUTAGE": [
        PowerState.GRID_UNSTABLE,    # grid becomes unstable
        PowerState.BATTERY,          # switches to battery
        PowerState.NO_COOLING,       # battery runs out
    ],
    "BACKUP_RUNTIME_LOW": [
        PowerState.GRID_STABLE,      # grid restored before depletion
    ],
    "BACKUP_POWER_DEPLETED": [
        # Already in NO_COOLING — no further transitions possible
    ],
}


class SimulationResult:
    """Container for all outputs of a single simulation run."""

    def __init__(self) -> None:
        self.incident: SimulatedIncident | None = None
        self.power_events: list = []
        self.cargo_event: CargoEvent | None = None
        self.thermal_steps: list = []
        self.prediction_event: PredictionEvent | None = None
        self.audit_event: AuditEvent | None = None
        self.minutes_to_spoilage: float | None = None
        self.final_temp_c: float | None = None

    def to_report(self) -> dict:
        """Build a JSON-serialisable report dictionary."""
        return {
            "simulation_report": {
                "incident_id": self.incident.incident_id if self.incident else None,
                "scenario_id": self.incident.scenario_id if self.incident else None,
                "random_seed": self.incident.random_seed if self.incident else None,
                "incident_type": self.incident.incident_type.value if self.incident else None,
                "location": self.incident.location_name if self.incident else None,
                "cargo_description": self.incident.cargo.description if self.incident else None,
                "cargo_mass_kg": self.incident.cargo.mass_kg if self.incident else None,
                "backup_runtime_min": self.incident.cargo.backup_runtime_min if self.incident else None,
                "power_events_count": len(self.power_events),
                "final_power_state": self.incident.initial_power_state.value if self.incident else None,
                "thermal_steps_count": len(self.thermal_steps),
                "final_temp_c": self.final_temp_c,
                "minutes_to_spoilage": self.minutes_to_spoilage,
                "all_events_schema_valid": True,
            }
        }


def run_simulation(scenario_id: str, seed: int = 0) -> SimulationResult:
    """
    Run a complete power-failure simulation.

    Parameters
    ----------
    scenario_id : named scenario (must be in AVAILABLE_SCENARIOS)
    seed        : random seed for reproducible parameter generation

    Returns
    -------
    SimulationResult with all emitted events and thermal history
    """
    result = SimulationResult()

    # 1. Build scenario
    incident = build_scenario(scenario_id, random_seed=seed)
    result.incident = incident
    cargo = incident.cargo
    start_time = utc_now()
    correlation_id = make_correlation_id()

    # 2. Emit audit event — simulation started
    audit_start = AuditEvent(
        event_id=make_event_id(),
        event_type="audit.simulation_started",
        occurred_at=start_time,
        schema_version="1.0.0",
        incident_id=incident.incident_id,
        correlation_id=correlation_id,
        idempotency_key=make_idempotency_key(),
        action=AuditAction.SIMULATION_STARTED,
        actor="simulator.engine",
        target_id=incident.incident_id,
        target_type="SimulatedIncident",
        details={
            "scenario_id": scenario_id,
            "seed": seed,
            "incident_type": incident.incident_type.value,
        },
    )
    result.audit_event = audit_start

    # 3. Emit cargo event
    sensitivity_map = {
        (0, 2): CargoSensitivity.HIGH,
        (2, 6): CargoSensitivity.MEDIUM,
    }
    sensitivity = CargoSensitivity.HIGH if cargo.time_sensitivity_hours <= 2 else (
        CargoSensitivity.MEDIUM if cargo.time_sensitivity_hours <= 6 else CargoSensitivity.LOW
    )
    cargo_event = CargoEvent(
        event_id=make_event_id(),
        event_type="cargo.profile_captured",
        occurred_at=start_time,
        schema_version="1.0.0",
        incident_id=incident.incident_id,
        correlation_id=correlation_id,
        idempotency_key=make_idempotency_key(),
        cargo_description=cargo.description,
        cargo_kg=cargo.mass_kg,
        safe_temperature_min_c=cargo.safe_temp_min_c,
        safe_temperature_max_c=cargo.safe_temp_max_c,
        current_temperature_c=cargo.initial_temp_c,
        backup_runtime_min=cargo.backup_runtime_min,
        available_capacity_kg=sum(r.available_capacity_kg for r in incident.receivers),
        unloading_duration_min=cargo.unloading_duration_min,
        time_sensitivity=sensitivity,
    )
    result.cargo_event = cargo_event

    # 4. Run power state machine
    psm = PowerStateMachine(
        incident_id=incident.incident_id,
        location_id=incident.location_id,
        location_name=incident.location_name,
        initial_state=incident.initial_power_state,
        correlation_id=correlation_id,
    )

    sequence = _SCENARIO_SEQUENCES.get(scenario_id, [])
    for i, target_state in enumerate(sequence):
        ts = start_time + timedelta(minutes=i * 10)  # 10-minute intervals
        try:
            event = psm.transition(
                target_state,
                reported_by="simulator.engine",
                notes=f"Scenario step {i+1}: {incident.initial_power_state} -> {target_state}",
                occurred_at=ts,
            )
            result.power_events.append(event)
        except InvalidTransitionError as e:
            # Terminal state — stop sequence
            break

    # 5. Run thermal model over backup runtime window
    thermal_duration = max(cargo.backup_runtime_min, 30.0)  # at least 30 min
    thermal = ThermalModel(
        initial_temp_c=cargo.initial_temp_c,
        safe_temp_max_c=cargo.safe_temp_max_c,
        ambient_temp_c=25.0,
        heat_ingress_rate=0.005,
        door_open_pulse_c=0.5,
    )
    door_open_times = [cargo.backup_runtime_min * 0.5] if cargo.backup_runtime_min > 10 else []
    thermal_steps = thermal.simulate(
        duration_min=thermal_duration,
        cooling_lost_at_min=0.0,  # cooling lost at incident start
        door_open_times_min=door_open_times,
    )
    result.thermal_steps = thermal_steps
    result.final_temp_c = thermal.current_temperature_c
    result.minutes_to_spoilage = thermal.minutes_to_exceed_safe_temp()

    # 6. Emit prediction event
    time_to_spoilage = result.minutes_to_spoilage
    prediction = PredictionEvent(
        event_id=make_event_id(),
        event_type="prediction.thermal_progression",
        occurred_at=start_time,
        schema_version="1.0.0",
        incident_id=incident.incident_id,
        correlation_id=correlation_id,
        idempotency_key=make_idempotency_key(),
        prediction_type="THERMAL_PROGRESSION",
        predicted_temperature_c=result.final_temp_c,
        time_to_spoilage_min=time_to_spoilage,
        confidence=0.6,  # low confidence — simplified model
        model_name="newton_linear_v1",
        assumptions=(
            "Single uniform cargo mass; constant ambient 25C; "
            "k=0.005/min; no latent heat or humidity. "
            "ESTIMATE ONLY - not validated for food-safety decisions."
        ),
    )
    result.prediction_event = prediction

    return result


def print_report(result: SimulationResult) -> None:
    """Print a human-readable simulation report to stdout."""
    sep = "=" * 60
    incident = result.incident
    cargo = incident.cargo

    print(sep)
    print("  ColdRescue Power-Failure Simulation Report")
    print(sep)
    print(f"  Scenario       : {incident.scenario_id}")
    print(f"  Incident ID    : {incident.incident_id}")
    print(f"  Seed           : {incident.random_seed}")
    print(f"  Incident Type  : {incident.incident_type.value}")
    print(f"  Location       : {incident.location_name}")
    print()
    print(f"  Cargo          : {cargo.description}")
    print(f"  Mass           : {cargo.mass_kg} kg")
    print(f"  Safe Temp Range: {cargo.safe_temp_min_c}C to {cargo.safe_temp_max_c}C")
    print(f"  Initial Temp   : {cargo.initial_temp_c}C")
    print(f"  Backup Runtime : {cargo.backup_runtime_min} min")
    print(f"  Sensitivity    : {cargo.time_sensitivity_hours}h to spoilage risk")
    print()
    print(f"  Power Events   : {len(result.power_events)}")
    for evt in result.power_events:
        print(f"    [{evt.occurred_at.strftime('%H:%M:%S')}] {evt.event_type} -> {evt.incident_type.value}")
    print()
    print(f"  Thermal Steps  : {len(result.thermal_steps)} (1-min intervals)")
    print(f"  Final Temp     : {result.final_temp_c}C")
    if result.minutes_to_spoilage is not None:
        print(f"  [!] Exceeded safe temp at {result.minutes_to_spoilage:.1f} min")
    else:
        print(f"  [OK] Temperature stayed within safe range for {len(result.thermal_steps)} min")
    print()
    print("  Receivers available:")
    for r in incident.receivers:
        compat = r.can_accept_cargo(cargo)
        compat_str = "[OK]" if compat else "[--]"
        print(f"    [{r.category.value:<25}] {r.name} - {r.available_capacity_kg:.0f}kg avail. - {compat_str}")
    print()
    print("  [!] DISCLAIMER: Thermal predictions are simplified estimates.")
    print("      Do NOT use for food-safety decisions in production.")
    print(sep)
    print()
    print("  JSON Report:")
    print(json.dumps(result.to_report(), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ColdRescue Power-Failure Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Scenario to simulate (use --list-scenarios to see options)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0)",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List all available scenarios and exit",
    )

    args = parser.parse_args()

    if args.list_scenarios:
        print("Available scenarios:")
        for s in AVAILABLE_SCENARIOS:
            print(f"  {s}")
        sys.exit(0)

    if not args.scenario:
        parser.print_help()
        sys.exit(1)

    try:
        result = run_simulation(args.scenario, seed=args.seed)
        print_report(result)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
