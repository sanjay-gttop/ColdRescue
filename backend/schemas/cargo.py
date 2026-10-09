"""
ColdRescue cargo event schema — M2 cargo profile with thermal constraints.

Validation rules:
  cargo_kg >= 0
  backup_runtime_min >= 0
  available_capacity_kg >= 0
  unloading_duration_min >= 0
  safe_temperature_min_c <= safe_temperature_max_c
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from backend.schemas.common import EventEnvelope


class CargoSensitivity(str, Enum):
    """Time sensitivity classification for cargo."""
    HIGH = "HIGH"      # < 2 hours before spoilage risk
    MEDIUM = "MEDIUM"  # 2–6 hours
    LOW = "LOW"        # > 6 hours


class CargoEvent(EventEnvelope):
    """Event carrying cargo profile and thermal state."""

    cargo_description: str = Field(..., description="Human-readable cargo description")
    cargo_kg: float = Field(..., ge=0.0, description="Cargo mass in kilograms (>=0)")
    safe_temperature_min_c: float = Field(
        ..., description="Lower bound of safe temperature range (°C)"
    )
    safe_temperature_max_c: float = Field(
        ..., description="Upper bound of safe temperature range (°C)"
    )
    current_temperature_c: Optional[float] = Field(
        None, description="Current measured temperature (°C); None if sensor unavailable"
    )
    backup_runtime_min: float = Field(
        ..., ge=0.0, description="Remaining backup power runtime (minutes, >=0)"
    )
    available_capacity_kg: float = Field(
        ..., ge=0.0, description="Available receiving capacity (kg, >=0)"
    )
    unloading_duration_min: float = Field(
        ..., ge=0.0, description="Estimated unloading time (minutes, >=0)"
    )
    time_sensitivity: CargoSensitivity = Field(
        default=CargoSensitivity.MEDIUM,
        description="How urgently this cargo must be transferred",
    )

    @model_validator(mode="after")
    def temp_range_valid(self) -> "CargoEvent":
        if self.safe_temperature_min_c > self.safe_temperature_max_c:
            raise ValueError(
                "safe_temperature_min_c must not exceed safe_temperature_max_c"
            )
        return self
