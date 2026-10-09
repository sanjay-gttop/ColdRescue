"""ColdRescue approval event schema."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field

from backend.schemas.common import EventEnvelope


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


class ApprovalEvent(EventEnvelope):
    """Event recording an operator approval/rejection of an assignment."""

    approval_id: str = Field(..., description="Unique approval record identifier")
    assignment_id: str = Field(..., description="Assignment being approved/rejected")
    decision: ApprovalDecision = Field(..., description="Operator decision")
    approved_by: str = Field(..., description="Operator identifier who made decision")
    reason: Optional[str] = Field(None, description="Justification for the decision")
    policy_rule_ids: list[str] = Field(
        default_factory=list,
        description="Policy rules that informed this decision",
    )
