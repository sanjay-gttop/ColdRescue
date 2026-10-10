"""
Role-protected endpoints for incident recovery, human approval, driver acknowledgement, and receiver intake (Milestone 11).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.models import AuthenticatedUser, Permission, UserRole
from backend.auth.security import require_permission, require_role, record_auth_failure_audit
from backend.services.event_ingestion import get_event_store

router = APIRouter(prefix="/incidents", tags=["recovery-actions"])


class ApprovalRequest(BaseModel):
    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    notes: Optional[str] = None
    override_reason: Optional[str] = None


class DriverAcknowledgementRequest(BaseModel):
    driver_name: str
    vehicle_id: str
    estimated_departure_time: Optional[str] = None


class ReceiverAcceptanceRequest(BaseModel):
    accepted_kg: float = Field(..., ge=0.0)
    bay_number: Optional[str] = None
    notes: Optional[str] = None


@router.post("/recover")
async def initiate_recovery(
    payload: Dict[str, Any],
    user: AuthenticatedUser = Depends(require_permission(Permission.INITIATE_RECOVERY)),
) -> Dict[str, Any]:
    """Initiate incident recovery workflow (Requires OPERATOR role)."""
    incident_id = payload.get("incident_id") or "inc_sample"
    return {
        "status": "INITIATED",
        "incident_id": incident_id,
        "initiated_by": user.email,
        "initiated_at": datetime.now(timezone.utc).isoformat(),
        "role": user.role.value,
    }


@router.post("/{incident_id}/approve")
async def approve_recovery(
    incident_id: str,
    req: ApprovalRequest,
    user: AuthenticatedUser = Depends(require_permission(Permission.APPROVE_RECOVERY)),
) -> Dict[str, Any]:
    """Approve or reject proposed recovery allocation (Requires APPROVER role)."""
    # Strict separation of duties: Drivers cannot approve restricted recovery actions
    if user.role == UserRole.DRIVER:
        record_auth_failure_audit(
            user=user,
            action="APPROVE_RECOVERY",
            reason="Separation of duties violation: DRIVER cannot approve recovery actions",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Separation of duties: DRIVER is strictly prohibited from approving recovery actions",
        )

    decision_norm = req.decision.strip().upper()
    if decision_norm not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'APPROVED' or 'REJECTED'",
        )

    return {
        "incident_id": incident_id,
        "decision": decision_norm,
        "approver_id": user.user_id,
        "approver_email": user.email,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "notes": req.notes,
    }


@router.post("/{incident_id}/acknowledge")
async def acknowledge_assignment(
    incident_id: str,
    req: DriverAcknowledgementRequest,
    user: AuthenticatedUser = Depends(require_permission(Permission.ACKNOWLEDGE_ASSIGNMENT)),
) -> Dict[str, Any]:
    """Acknowledge route and assignment dispatch (Requires DRIVER role)."""
    return {
        "incident_id": incident_id,
        "status": "DISPATCH_ACKNOWLEDGED",
        "driver_id": user.user_id,
        "driver_email": user.email,
        "vehicle_id": req.vehicle_id,
        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{incident_id}/accept")
async def accept_delivery(
    incident_id: str,
    req: ReceiverAcceptanceRequest,
    user: AuthenticatedUser = Depends(require_permission(Permission.ACCEPT_DELIVERY)),
) -> Dict[str, Any]:
    """Accept incoming cargo delivery at receiving facility (Requires RECEIVER role)."""
    return {
        "incident_id": incident_id,
        "status": "DELIVERY_ACCEPTED",
        "receiver_id": user.user_id,
        "receiver_email": user.email,
        "accepted_kg": req.accepted_kg,
        "bay_number": req.bay_number,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
    }
