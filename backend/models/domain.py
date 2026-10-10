"""ColdRescue domain models package."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

from backend.schemas.incident import IncidentType, IncidentStatus
from backend.schemas.receiver import ReceiverCategory
from backend.schemas.cargo import CargoSensitivity


class CoolingStatus(str, Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Location(BaseModel):
    location_id: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None


class CargoItem(BaseModel):
    cargo_id: str
    description: str
    cargo_type: str = "general"
    cargo_kg: float = Field(..., ge=0.0)
    safe_temperature_min_c: float
    safe_temperature_max_c: float
    current_temperature_c: Optional[float] = None
    backup_runtime_min: float = Field(0.0, ge=0.0)
    unloading_duration_min: float = Field(0.0, ge=0.0)
    time_sensitivity: CargoSensitivity = CargoSensitivity.MEDIUM
    spoilage_deadline: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_temps(self) -> "CargoItem":
        if self.safe_temperature_min_c > self.safe_temperature_max_c:
            raise ValueError(
                f"safe_temperature_min_c ({self.safe_temperature_min_c}) cannot exceed "
                f"safe_temperature_max_c ({self.safe_temperature_max_c})"
            )
        return self


class ReceiverNode(BaseModel):
    receiver_id: str
    name: str
    category: ReceiverCategory
    capacity_kg: float = Field(..., ge=0.0)
    current_load_kg: float = Field(0.0, ge=0.0)
    accepts_temperature_min_c: float
    accepts_temperature_max_c: float
    compatible_cargo_types: List[str] = Field(default_factory=lambda: ["general"])
    cooling_status: CoolingStatus = CoolingStatus.OPERATIONAL
    backup_runtime_min: Optional[float] = Field(None, ge=0.0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = Field(None, ge=0.0)
    travel_time_min: Optional[float] = Field(None, ge=0.0)
    is_available: bool = True

    @property
    def available_capacity_kg(self) -> float:
        return max(0.0, self.capacity_kg - self.current_load_kg)

    @model_validator(mode="after")
    def validate_capacity(self) -> "ReceiverNode":
        if self.current_load_kg > self.capacity_kg:
            raise ValueError(
                f"current_load_kg ({self.current_load_kg}) cannot exceed capacity_kg ({self.capacity_kg})"
            )
        if self.accepts_temperature_min_c > self.accepts_temperature_max_c:
            raise ValueError(
                f"accepts_temperature_min_c ({self.accepts_temperature_min_c}) cannot exceed "
                f"accepts_temperature_max_c ({self.accepts_temperature_max_c})"
            )
        return self


class IncidentRecord(BaseModel):
    incident_id: str
    incident_type: IncidentType
    severity: SeverityLevel = SeverityLevel.HIGH
    status: IncidentStatus = IncidentStatus.OPEN
    location: Location
    cargo: CargoItem
    reported_at: datetime
    notes: Optional[str] = None
