"""ColdRescue audit event schema."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import Field

from backend.schemas.common import EventEnvelope


class AuditAction(str, Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_UPDATED = "INCIDENT_UPDATED"
    ASSIGNMENT_CREATED = "ASSIGNMENT_CREATED"
    ASSIGNMENT_APPROVED = "ASSIGNMENT_APPROVED"
    ASSIGNMENT_REJECTED = "ASSIGNMENT_REJECTED"
    ROUTE_CREATED = "ROUTE_CREATED"
    ROUTE_COMPLETED = "ROUTE_COMPLETED"
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SIMULATION_STARTED = "SIMULATION_STARTED"
    SIMULATION_COMPLETED = "SIMULATION_COMPLETED"


class AuditEvent(EventEnvelope):
    """Immutable audit trail entry for compliance and debugging."""

    action: AuditAction = Field(..., description="The action being audited")
    actor: str = Field(..., description="User, service, or component that performed the action")
    target_id: Optional[str] = Field(None, description="ID of the entity acted upon")
    target_type: Optional[str] = Field(None, description="Type of the entity acted upon")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Structured details about the action"
    )
    ip_address: Optional[str] = Field(None, description="Client IP if from HTTP request")
