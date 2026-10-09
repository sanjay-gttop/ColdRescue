"""ColdRescue assignment event schema."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from backend.schemas.common import EventEnvelope


class AssignmentStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class AssignmentEvent(EventEnvelope):
    """Event when cargo is assigned to a receiver and driver."""

    assignment_id: str = Field(..., description="Unique assignment identifier")
    receiver_id: str = Field(..., description="Target receiver identifier")
    driver_id: str = Field(..., description="Assigned driver identifier")
    cargo_kg: float = Field(..., ge=0.0, description="Cargo mass being assigned (kg)")
    status: AssignmentStatus = Field(default=AssignmentStatus.PENDING)
    algorithm_used: Optional[str] = Field(None, description="Allocation algorithm name")
    score: Optional[float] = Field(None, description="Optimisation score (higher = better)")
    notes: Optional[str] = None
