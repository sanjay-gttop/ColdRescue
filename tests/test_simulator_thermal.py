import pytest

from simulator.engine import run_simulation
from simulator.scenario import build_scenario
from simulator.thermal import ThermalModel


def test_cooling_active_keeps_temperature_stable():
    model = ThermalModel(
        initial_temp_c=5.0,
        safe_temp_max_c=8.0,
        ambient_temp_c=25.0,
    )

    steps = model.simulate(
        duration_min=10,
        cooling_lost_at_min=10,
    )

    assert len(steps) == 10
    assert all(step.cooling_active for step in steps)
    assert model.current_temperature_c == 5.0


def test_temperature_rises_after_cooling_is_lost():
    model = ThermalModel(
        initial_temp_c=4.0,
        safe_temp_max_c=8.0,
        ambient_temp_c=25.0,
    )

    steps = model.simulate(
        duration_min=10,
        cooling_lost_at_min=0,
    )

    assert all(not step.cooling_active for step in steps)
    assert model.current_temperature_c > 4.0


@pytest.mark.parametrize(
    (
        "scenario_id",
        "expected_cooling_on",
        "expected_cooling_off",
        "expected_duration",
    ),
    [
        ("REEFER_UNIT_FAILURE", 90, 30, 120),
        ("COLD_ROOM_POWER_OUTAGE", 120, 30, 150),
        ("WAREHOUSE_GRID_OUTAGE", 60, 30, 90),
        ("BACKUP_RUNTIME_LOW", 55, 0, 55),
        ("BACKUP_POWER_DEPLETED", 0, 30, 30),
    ],
)
def test_scenario_cooling_duration(
    scenario_id,
    expected_cooling_on,
    expected_cooling_off,
    expected_duration,
):
    result = run_simulation(scenario_id, seed=42)

    cooling_on = sum(step.cooling_active for step in result.thermal_steps)
    cooling_off = len(result.thermal_steps) - cooling_on

    assert cooling_on == expected_cooling_on
    assert cooling_off == expected_cooling_off
    assert len(result.thermal_steps) == expected_duration


def test_backup_runtime_low_restores_cooling():
    incident = build_scenario("BACKUP_RUNTIME_LOW", random_seed=42)
    result = run_simulation("BACKUP_RUNTIME_LOW", seed=42)

    assert incident.initial_power_state.value == "BATTERY"
    assert result.final_power_state.value == "GRID_STABLE"
    assert all(step.cooling_active for step in result.thermal_steps)
    assert result.final_temp_c == incident.cargo.initial_temp_c


def test_fractional_door_open_time_is_not_skipped():
    model = ThermalModel(
        initial_temp_c=4.0,
        safe_temp_max_c=8.0,
        ambient_temp_c=25.0,
        door_open_pulse_c=0.5,
    )

    steps = model.simulate(
        duration_min=15,
        cooling_lost_at_min=15,
        door_open_times_min=[12.5],
    )

    door_steps = [step for step in steps if step.door_opened]

    assert len(door_steps) == 1
    assert door_steps[0].temperature_c == 4.5