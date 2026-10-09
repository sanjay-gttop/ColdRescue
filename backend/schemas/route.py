"""ColdRescue route event schema."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import Field

from backend.schemas.common import EventEnvelope


class RouteStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Waypoint(EventEnvelope.__base__):  # plain Pydantic BaseModel
    pass


from pydantic import BaseModel


class Waypoint(BaseModel):
    label: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    eta_min: Optional[float] = Field(None, ge=0.0, description="ETA from previous waypoint (min)")


class RouteEvent(EventEnvelope):
    """Event describing a planned or active delivery route."""

    route_id: str = Field(..., description="Unique route identifier")
    driver_id: str = Field(..., description="Assigned driver identifier")
    receiver_id: str = Field(..., description="Destination receiver identifier")
    status: RouteStatus = Field(default=RouteStatus.PLANNED)
    total_distance_km: float = Field(..., ge=0.0, description="Total route distance (km)")
    estimated_duration_min: float = Field(..., ge=0.0, description="Estimated travel time (min)")
    waypoints: List[Waypoint] = Field(default_factory=list)
    notes: Optional[str] = None
