"""
ColdRescue incident event schema — M2 incident types.

Incident types (exact):
  REEFER_UNIT_FAILURE      — refrigeration unit mechanical/electrical failure
  COLD_ROOM_POWER_OUTAGE   — walk-in cold room lost mains power
  WAREHOUSE_GRID_OUTAGE    — facility-wide grid outage
  BACKUP_RUNTIME_LOW       — backup power below threshold (configurable)
  BACKUP_POWER_DEPLETED    — backup power exhausted
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from backend.schemas.common import EventEnvelope


class IncidentType(str, Enum):
    REEFER_UNIT_FAILURE = "REEFER_UNIT_FAILURE"
    COLD_ROOM_POWER_OUTAGE = "COLD_ROOM_POWER_OUTAGE"
    WAREHOUSE_GRID_OUTAGE = "WAREHOUSE_GRID_OUTAGE"
    BACKUP_RUNTIME_LOW = "BACKUP_RUNTIME_LOW"
    BACKUP_POWER_DEPLETED = "BACKUP_POWER_DEPLETED"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class IncidentEvent(EventEnvelope):
    """Event emitted when an incident is created or updated."""

    incident_type: IncidentType = Field(..., description="Classified incident type")
    status: IncidentStatus = Field(default=IncidentStatus.OPEN)
    location_id: str = Field(..., description="Facility / vehicle location identifier")
    location_name: str = Field(..., description="Human-readable location name")
    reported_by: str = Field(..., description="Operator or sensor that reported the incident")
    notes: Optional[str] = Field(None, description="Free-text notes from operator")
