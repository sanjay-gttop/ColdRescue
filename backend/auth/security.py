"""
ColdRescue JWT Security and RBAC Authorization Guards (Milestones 10 & 11).
"""
from __future__ import annotations

import base64
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.models import AuthenticatedUser, Permission, ROLE_PERMISSIONS, UserRole
from backend.services.event_ingestion import get_event_store

# HTTP Bearer scheme
security_scheme = HTTPBearer(auto_error=False)

# Test/Mock secret key for HMAC validation
DEFAULT_SECRET = "coldrescue-jwt-secret-dev-2026"


def create_token(
    user_id: str,
    email: str,
    role: UserRole,
    expires_in_seconds: int = 3600,
    name: Optional[str] = None,
) -> str:
    """Create a standardized JWT-like token for testing and local authentication."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "name": name or email.split("@")[0],
        "role": role.value,
        "cognito:groups": [role.value],
        "iat": now,
        "exp": now + expires_in_seconds,
        "jti": str(uuid.uuid4()),
    }
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(f"{encoded_header}.{encoded_payload}.mock_sig".encode()).decode().rstrip("=")
    return f"{encoded_header}.{encoded_payload}.{signature}"


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate token expiration and structure."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT token structure")

    payload_b64 = parts[1]
    # Add padding if needed
    rem = len(payload_b64) % 4
    if rem > 0:
        payload_b64 += "=" * (4 - rem)

    try:
        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode("utf-8")
        payload = json.loads(payload_json)
    except Exception as exc:
        raise ValueError(f"Failed to decode JWT payload: {exc}") from exc

    # Check expiration
    exp = payload.get("exp")
    if exp and time.time() > exp:
        raise ValueError("JWT token has expired")

    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> AuthenticatedUser:
    """Extract and validate authenticated user from Authorization Bearer header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Missing or empty Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("user_id")
    email = payload.get("email")
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Missing subject or email claims in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Determine role from 'role' or 'cognito:groups' claim
    role_str = payload.get("role")
    if not role_str and "cognito:groups" in payload:
        groups = payload["cognito:groups"]
        if groups and isinstance(groups, list):
            role_str = groups[0]

    try:
        role = UserRole(str(role_str).upper())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: User has invalid or unassigned role '{role_str}'",
        )

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        role=role,
        name=payload.get("name"),
        claims=payload,
    )


def record_auth_failure_audit(user: Optional[AuthenticatedUser], action: str, reason: str) -> None:
    """Record authorization failure in the persistent event/audit store."""
    try:
        store = get_event_store()
        corr_id = f"corr_auth_fail_{uuid.uuid4().hex[:8]}"
        audit_payload = {
            "event_id": f"evt_auth_{uuid.uuid4().hex[:8]}",
            "event_type": "audit_event",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
            "correlation_id": corr_id,
            "idempotency_key": f"idem_auth_{uuid.uuid4().hex[:8]}",
            "sequence_number": 1,
            "action": f"AUTHORIZATION_DENIED: {action}",
            "actor": user.email if user else "anonymous",
            "entity_type": "user_role",
            "entity_id": user.user_id if user else "unknown",
            "diverted_kg": 0.0,
            "at_risk_kg": 0.0,
            "outcome": f"DENIED: {reason}",
        }
        store.ingest(stream_id=f"audit_{corr_id}", raw_event=audit_payload)
    except Exception:
        pass


def require_role(allowed_roles: List[UserRole]) -> Callable:
    """Dependency enforcing that the authenticated user possesses one of the allowed roles."""
    async def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in allowed_roles:
            record_auth_failure_audit(
                user=user,
                action="ROLE_CHECK",
                reason=f"Role '{user.role.value}' not in {[r.value for r in allowed_roles]}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of {[r.value for r in allowed_roles]}, but user has role '{user.role.value}'",
            )
        return user

    return role_checker


def require_permission(permission: Permission) -> Callable:
    """Dependency enforcing that the authenticated user possesses the specific permission."""
    async def permission_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.has_permission(permission):
            record_auth_failure_audit(
                user=user,
                action=permission.value,
                reason=f"Role '{user.role.value}' lacks permission '{permission.value}'",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Role '{user.role.value}' lacks required permission '{permission.value}'",
            )
        return user

    return permission_checker
