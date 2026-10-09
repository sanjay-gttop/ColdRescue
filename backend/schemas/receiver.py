"""
ColdRescue receiver event schema — M2 receiver profile categories.

Receiver categories (exact):
  COLD_STORAGE_FACILITY — commercial refrigerated warehouse
  FOOD_BANK             — charitable food distribution
  HOSPITAL_OR_CLINIC    — medical facility with strict cold-chain
  COMMUNITY_COLD_ROOM   — community shared refrigeration
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from backend.schemas.common import EventEnvelope


class ReceiverCategory(str, Enum):
    COLD_STORAGE_FACILITY = "COLD_STORAGE_FACILITY"
    FOOD_BANK = "FOOD_BANK"
    HOSPITAL_OR_CLINIC = "HOSPITAL_OR_CLINIC"
    COMMUNITY_COLD_ROOM = "COMMUNITY_COLD_ROOM"


class ReceiverEvent(EventEnvelope):
    """Event carrying receiver profile and current availability."""

    receiver_id: str = Field(..., description="Unique receiver identifier")
    receiver_name: str = Field(..., description="Organisation / facility name")
    category: ReceiverCategory = Field(..., description="Receiver category")
    capacity_kg: float = Field(..., ge=0.0, description="Total cold-storage capacity (kg)")
    current_load_kg: float = Field(..., ge=0.0, description="Current stored mass (kg)")
    accepts_temperature_min_c: float = Field(
        ..., description="Lowest temperature the receiver can maintain (°C)"
    )
    accepts_temperature_max_c: float = Field(
        ..., description="Highest temperature the receiver will accept (°C)"
    )
    distance_km: Optional[float] = Field(
        None, ge=0.0, description="Distance from incident location (km)"
    )
    contact_name: Optional[str] = Field(None, description="Primary contact")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    is_available: bool = Field(default=True, description="Whether receiver is currently accepting")

    @property
    def available_capacity_kg(self) -> float:
        """Remaining capacity not yet occupied."""
        return max(0.0, self.capacity_kg - self.current_load_kg)
