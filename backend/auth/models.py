"""
ColdRescue Authentication and Role-Based Access Control (RBAC) Models (Milestones 10 & 11).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    OPERATOR = "OPERATOR"
    APPROVER = "APPROVER"
    DRIVER = "DRIVER"
    RECEIVER = "RECEIVER"


class Permission(str, Enum):
    # Incident & Allocation Permissions
    CREATE_INCIDENT = "create_incident"
    INITIATE_RECOVERY = "initiate_recovery"
    VIEW_INCIDENT = "view_incident"
    REVIEW_ALLOCATION = "review_allocation"

    # Approval Permissions
    APPROVE_RECOVERY = "approve_recovery"
    REJECT_RECOVERY = "reject_recovery"

    # Driver & Transport Permissions
    ACKNOWLEDGE_ASSIGNMENT = "acknowledge_assignment"
    UPDATE_TRANSIT_PROGRESS = "update_transit_progress"

    # Receiver & Intake Permissions
    ACCEPT_DELIVERY = "accept_delivery"
    REJECT_DELIVERY = "reject_delivery"


# Comprehensive Role-Permission Matrix
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.OPERATOR: {
        Permission.CREATE_INCIDENT,
        Permission.INITIATE_RECOVERY,
        Permission.VIEW_INCIDENT,
        Permission.REVIEW_ALLOCATION,
    },
    UserRole.APPROVER: {
        Permission.VIEW_INCIDENT,
        Permission.REVIEW_ALLOCATION,
        Permission.APPROVE_RECOVERY,
        Permission.REJECT_RECOVERY,
    },
    UserRole.DRIVER: {
        Permission.VIEW_INCIDENT,
        Permission.ACKNOWLEDGE_ASSIGNMENT,
        Permission.UPDATE_TRANSIT_PROGRESS,
    },
    UserRole.RECEIVER: {
        Permission.VIEW_INCIDENT,
        Permission.ACCEPT_DELIVERY,
        Permission.REJECT_DELIVERY,
    },
}


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    role: UserRole
    name: Optional[str] = None
    claims: Dict[str, Any] = Field(default_factory=dict)

    def has_permission(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())


AuthenticatedUser.model_rebuild()
