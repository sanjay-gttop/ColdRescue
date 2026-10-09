"""
ColdRescue M0 event envelope — base class for all domain events.

Schema version: 1.0.0
All events MUST validate against this contract.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


SCHEMA_VERSION = "1.0.0"


class EventEnvelope(BaseModel):
    """
    Base class for every ColdRescue domain event.

    Required fields
    ---------------
    event_id        : unique event identifier (use make_event_id())
    event_type      : string tag identifying the event kind
    occurred_at     : timezone-aware UTC datetime of the event
    schema_version  : must equal "1.0.0"
    correlation_id  : request/trace correlation (use make_correlation_id())
    idempotency_key : client-supplied dedup key (use make_idempotency_key())

    Optional fields
    ---------------
    incident_id     : links the event to an active incident
    """

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type tag")
    occurred_at: datetime = Field(..., description="UTC datetime of occurrence")
    schema_version: str = Field(default=SCHEMA_VERSION, description="Schema version")
    incident_id: Optional[str] = Field(None, description="Associated incident ID")
    correlation_id: str = Field(..., description="Request correlation identifier")
    idempotency_key: str = Field(..., description="Idempotency / dedup key")

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware (use UTC)")
        return v

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if v != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be '{SCHEMA_VERSION}', got '{v}'")
        return v

    model_config = {"extra": "forbid"}
