"""
ColdRescue Simulator — Newton-type linear thermal model.

⚠️  DISCLAIMER
This model is a simplified estimate intended for simulation and testing only.
It is NOT scientifically validated for food-safety decisions in production.

Thermal equation (Newton's law of cooling — linear approximation):
    dT/dt = k * (T_ambient - T_current)

Where:
    T_current  : current cargo temperature (°C)
    T_ambient  : ambient temperature when cooling is lost (°C)
    k          : heat-ingress rate constant (1/min) — configurable per cargo
    dt         : simulation time step (minutes)

Door-open events:
    Each door-open event adds a configurable heat pulse (°C)
    representing rapid air exchange during door opening.

Assumptions:
    1. Cargo is a single thermally uniform mass.
    2. Heat ingress is proportional to (T_ambient - T_current).
    3. When cooling is active, temperature is held at initial_temp_c.
    4. Door-open pulses are instantaneous.
    5. No latent heat, phase change, or humidity effects.
    6. Ambient temperature is constant throughout the simulation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# Default constants (override per-cargo or per-scenario as needed)
DEFAULT_AMBIENT_TEMP_C: float = 25.0      # Indoor ambient without cooling (°C)
DEFAULT_HEAT_INGRESS_RATE: float = 0.005  # k constant (°C change per °C delta per minute)
DEFAULT_DOOR_OPEN_PULSE_C: float = 0.5   # Temperature rise per door-open event (°C)
SIMULATION_STEP_MIN: float = 1.0          # One-minute time steps


@dataclass
class ThermalStep:
    """Single time-step output from the thermal model."""
    time_min: float
    temperature_c: float
    cooling_active: bool
    door_opened: bool
    delta_c: float  # change from previous step


@dataclass
class ThermalModel:
    """
    Configurable Newton-type linear thermal progression model.

    Parameters
    ----------
    initial_temp_c      : starting cargo temperature (°C)
    safe_temp_max_c     : upper bound of safe temperature range (°C)
    ambient_temp_c      : ambient temperature when cooling is lost (°C)
    heat_ingress_rate   : k constant — heat ingress fraction per minute
    door_open_pulse_c   : instantaneous temperature rise per door-open event (°C)
    """

    initial_temp_c: float
    safe_temp_max_c: float
    ambient_temp_c: float = DEFAULT_AMBIENT_TEMP_C
    heat_ingress_rate: float = DEFAULT_HEAT_INGRESS_RATE
    door_open_pulse_c: float = DEFAULT_DOOR_OPEN_PULSE_C

    # Internal state
    _history: List[ThermalStep] = field(default_factory=list, init=False)
    _current_temp_c: float = field(init=False)
    _time_elapsed_min: float = field(init=False)

    def __post_init__(self) -> None:
        self._current_temp_c = self.initial_temp_c
        self._time_elapsed_min = 0.0
        self._history = []

    def step(
        self,
        cooling_active: bool,
        door_opened: bool = False,
    ) -> ThermalStep:
        """
        Advance the model by one time step (SIMULATION_STEP_MIN minutes).

        If cooling is active, temperature is maintained at initial_temp_c.
        If cooling is lost, Newton heat-ingress equation is applied.
        Door-open events add a heat pulse on top.
        """
        prev_temp = self._current_temp_c

        if cooling_active:
            # Cooling holds temperature stable
            new_temp = self.initial_temp_c
        else:
            # Newton's law of cooling (heat ingress from warmer ambient)
            delta = self.heat_ingress_rate * (
                self.ambient_temp_c - self._current_temp_c
            )
            new_temp = self._current_temp_c + delta * SIMULATION_STEP_MIN

        # Door-open heat pulse
        if door_opened:
            new_temp += self.door_open_pulse_c

        self._current_temp_c = new_temp
        self._time_elapsed_min += SIMULATION_STEP_MIN

        record = ThermalStep(
            time_min=self._time_elapsed_min,
            temperature_c=round(new_temp, 4),
            cooling_active=cooling_active,
            door_opened=door_opened,
            delta_c=round(new_temp - prev_temp, 4),
        )
        self._history.append(record)
        return record

    def simulate(
        self,
        duration_min: float,
        cooling_lost_at_min: float = 0.0,
        door_open_times_min: Optional[List[float]] = None,
    ) -> List[ThermalStep]:
        """
        Run a full simulation over `duration_min` minutes.

        Parameters
        ----------
        duration_min        : total simulation duration
        cooling_lost_at_min : when cooling is lost (0 = immediately)
        door_open_times_min : list of times at which door-open events occur

        Door events scheduled between minute boundaries are applied during
        the simulation step containing their scheduled time.
        """
        door_open_times = sorted(door_open_times_min or [])
        processed_door_events: set[int] = set()

        steps: List[ThermalStep] = []
        t = 0.0

        while t < duration_min:
            cooling_active = t < cooling_lost_at_min
            step_end = t + SIMULATION_STEP_MIN

            # Apply a door event during the step containing its scheduled time.
            # For example, an event at 12.5 minutes is applied during the
            # step beginning at minute 12. An event at 12.0 is also applied
            # during the step beginning at minute 12.
            door_opened = False

            for index, event_time in enumerate(door_open_times):
                if index in processed_door_events:
                    continue

                if t <= event_time < step_end:
                    door_opened = True
                    processed_door_events.add(index)

            record = self.step(
                cooling_active=cooling_active,
                door_opened=door_opened,
            )
            steps.append(record)
            t += SIMULATION_STEP_MIN

        return steps

    def minutes_to_exceed_safe_temp(self) -> Optional[float]:
        """
        Return the first time (min) temperature exceeded safe_temp_max_c,
        or None if it never did in the recorded history.
        """
        for step in self._history:
            if step.temperature_c > self.safe_temp_max_c:
                return step.time_min
        return None

    @property
    def current_temperature_c(self) -> float:
        return round(self._current_temp_c, 4)

    @property
    def history(self) -> List[ThermalStep]:
        return list(self._history)