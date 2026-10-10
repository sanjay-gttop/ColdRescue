"""
ColdRescue Simulator — domain models.

Pydantic models for:
  - CargoProfile      : mass, temperature limits, time sensitivity
  - ReceiverProfile   : category, capacity, temperature acceptance
  - SimulatedIncident : links cargo + receivers + power state
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from simulator.enums import IncidentType, PowerState, ReceiverCategory


class CargoProfile(BaseModel):
    """
    Configurable cargo profile for simulation.

    Validation rules:
      mass_kg >= 0
      backup_runtime_min >= 0
      safe_temp_min_c <= safe_temp_max_c
    """

    cargo_id: str = Field(..., description="Unique identifier for this cargo lot")
    description: str = Field(..., description="Human-readable cargo description")
    mass_kg: float = Field(..., ge=0.0, description="Total cargo mass (kg, >=0)")
    safe_temp_min_c: float = Field(..., description="Minimum safe storage temperature (°C)")
    safe_temp_max_c: float = Field(..., description="Maximum safe storage temperature (°C)")
    initial_temp_c: float = Field(..., description="Temperature at incident start (°C)")
    backup_runtime_min: float = Field(
        ..., ge=0.0, description="Remaining backup power at incident start (min, >=0)"
    )
    time_sensitivity_hours: float = Field(
        ..., gt=0.0, description="Hours until spoilage risk becomes critical (>0)"
    )
    unloading_duration_min: float = Field(
        ..., ge=0.0, description="Estimated unloading time (min, >=0)"
    )
    thermal_resistance: float = Field(
        default=1.0, gt=0.0, description="Thermal insulation resistance factor (higher = slower warming)"
    )
    heat_ingress_rate: float = Field(
        default=0.005, gt=0.0, description="Base heat ingress rate constant (1/min)"
    )

    @model_validator(mode="after")
    def validate_temp_range(self) -> "CargoProfile":
        if self.safe_temp_min_c > self.safe_temp_max_c:
            raise ValueError(
                f"safe_temp_min_c ({self.safe_temp_min_c}) must not exceed "
                f"safe_temp_max_c ({self.safe_temp_max_c})"
            )
        return self

    @model_validator(mode="after")
    def validate_initial_temp_in_range(self) -> "CargoProfile":
        if not (self.safe_temp_min_c <= self.initial_temp_c <= self.safe_temp_max_c):
            # Initial temp out of range is a warning, not an error — cargo may
            # already be warming. We allow it but log it.
            pass
        return self


class ReceiverProfile(BaseModel):
    """
    Configurable receiver profile for simulation.

    Validation rules:
      capacity_kg >= 0
      current_load_kg >= 0
      current_load_kg <= capacity_kg
    """

    receiver_id: str = Field(..., description="Unique receiver identifier")
    name: str = Field(..., description="Organisation name")
    category: ReceiverCategory = Field(..., description="Receiver category")
    capacity_kg: float = Field(..., ge=0.0, description="Total cold-storage capacity (kg)")
    current_load_kg: float = Field(..., ge=0.0, description="Currently stored mass (kg)")
    accepts_temp_min_c: float = Field(
        ..., description="Minimum temperature this receiver can maintain (°C)"
    )
    accepts_temp_max_c: float = Field(
        ..., description="Maximum temperature this receiver will accept (°C)"
    )
    distance_km: float = Field(..., ge=0.0, description="Distance from incident location (km)")
    is_available: bool = Field(default=True)

    @model_validator(mode="after")
    def load_does_not_exceed_capacity(self) -> "ReceiverProfile":
        if self.current_load_kg > self.capacity_kg:
            raise ValueError(
                f"current_load_kg ({self.current_load_kg}) exceeds "
                f"capacity_kg ({self.capacity_kg})"
            )
        return self

    @property
    def available_capacity_kg(self) -> float:
        return max(0.0, self.capacity_kg - self.current_load_kg)

    def can_accept_cargo(self, cargo: CargoProfile) -> bool:
        """Return True if this receiver can store the cargo (temp + capacity)."""
        temp_ok = (
            self.accepts_temp_min_c <= cargo.safe_temp_min_c
            and cargo.safe_temp_max_c <= self.accepts_temp_max_c
        )
        capacity_ok = self.available_capacity_kg >= cargo.mass_kg
        return self.is_available and temp_ok and capacity_ok


class SimulatedIncident(BaseModel):
    """Root model for one complete simulation scenario."""

    incident_id: str = Field(..., description="Unique incident identifier")
    scenario_id: str = Field(..., description="Named scenario used to generate this incident")
    random_seed: int = Field(..., description="Seed for reproducibility")
    incident_type: IncidentType = Field(..., description="M2 incident type")
    location_id: str = Field(..., description="Facility / vehicle ID")
    location_name: str = Field(..., description="Human-readable location name")
    cargo: CargoProfile = Field(..., description="Cargo profile at incident start")
    receivers: List[ReceiverProfile] = Field(
        ..., min_length=1, description="Available receivers (at least one required)"
    )
    initial_power_state: PowerState = Field(..., description="Power state at incident start")
