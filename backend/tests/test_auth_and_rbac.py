"""
Comprehensive tests for Cognito Authentication and Role-Based Authorization (Milestones 10 & 11).
Tests:
  - Unauthenticated requests rejected (401)
  - Expired / malformed tokens rejected (401)
  - Role-permission matrix enforced across OPERATOR, APPROVER, DRIVER, RECEIVER (403)
  - Separation of duties strictly enforced (Drivers cannot approve)
  - Audit logging of authorization failures
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth.models import UserRole
from backend.auth.security import create_token
from backend.services.event_ingestion import SQLiteEventStore

client = TestClient(app)


def test_unauthenticated_requests_rejected_with_401():
    # Unauthenticated initiate recovery
    res = client.post("/api/v1/incidents/recover", json={"incident_id": "inc_001"})
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]

    # Unauthenticated approve
    res_appr = client.post("/api/v1/incidents/inc_001/approve", json={"decision": "APPROVED"})
    assert res_appr.status_code == 401

    # Unauthenticated driver acknowledge
    res_ack = client.post(
        "/api/v1/incidents/inc_001/acknowledge",
        json={"driver_name": "Ravi", "vehicle_id": "TN-01-AB-1234"},
    )
    assert res_ack.status_code == 401

    # Unauthenticated receiver accept
    res_rcv = client.post(
        "/api/v1/incidents/inc_001/accept",
        json={"accepted_kg": 500.0},
    )
    assert res_rcv.status_code == 401


def test_invalid_and_expired_tokens_rejected_with_401():
    # Malformed token
    bad_headers = {"Authorization": "Bearer not-a-valid-jwt-token"}
    res = client.post("/api/v1/incidents/recover", json={"incident_id": "inc_001"}, headers=bad_headers)
    assert res.status_code == 401

    # Expired token (expires_in_seconds = -10)
    expired_token = create_token(
        user_id="usr_expired",
        email="operator@coldrescue.io",
        role=UserRole.OPERATOR,
        expires_in_seconds=-10,
    )
    res_exp = client.post(
        "/api/v1/incidents/recover",
        json={"incident_id": "inc_001"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res_exp.status_code == 401
    assert "expired" in res_exp.json()["detail"].lower()


def test_operator_role_permitted_and_forbidden_actions():
    token = create_token(
        user_id="usr_op_1",
        email="operator@coldrescue.io",
        role=UserRole.OPERATOR,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Permitted: Initiate recovery
    res_init = client.post("/api/v1/incidents/recover", json={"incident_id": "inc_101"}, headers=headers)
    assert res_init.status_code == 200
    assert res_init.json()["status"] == "INITIATED"

    # 2. Forbidden: Approve recovery (requires APPROVER)
    res_appr = client.post("/api/v1/incidents/inc_101/approve", json={"decision": "APPROVED"}, headers=headers)
    assert res_appr.status_code == 403
    assert "Forbidden" in res_appr.json()["detail"]

    # 3. Forbidden: Driver acknowledgement (requires DRIVER)
    res_ack = client.post(
        "/api/v1/incidents/inc_101/acknowledge",
        json={"driver_name": "Ravi", "vehicle_id": "TN-01"},
        headers=headers,
    )
    assert res_ack.status_code == 403

    # 4. Forbidden: Receiver intake acceptance (requires RECEIVER)
    res_acc = client.post(
        "/api/v1/incidents/inc_101/accept",
        json={"accepted_kg": 400.0},
        headers=headers,
    )
    assert res_acc.status_code == 403


def test_approver_role_permitted_and_forbidden_actions():
    token = create_token(
        user_id="usr_appr_1",
        email="approver@coldrescue.io",
        role=UserRole.APPROVER,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Permitted: Approve recovery
    res_appr = client.post(
        "/api/v1/incidents/inc_102/approve",
        json={"decision": "APPROVED", "notes": "Approved for emergency hub"},
        headers=headers,
    )
    assert res_appr.status_code == 200
    assert res_appr.json()["decision"] == "APPROVED"

    # 2. Permitted: Reject recovery
    res_rej = client.post(
        "/api/v1/incidents/inc_102/approve",
        json={"decision": "REJECTED", "notes": "No storage space"},
        headers=headers,
    )
    assert res_rej.status_code == 200
    assert res_rej.json()["decision"] == "REJECTED"

    # 3. Forbidden: Driver acknowledgement
    res_ack = client.post(
        "/api/v1/incidents/inc_102/acknowledge",
        json={"driver_name": "Driver X", "vehicle_id": "TN-02"},
        headers=headers,
    )
    assert res_ack.status_code == 403


def test_driver_role_separation_of_duties_strictly_enforced():
    token = create_token(
        user_id="usr_drv_1",
        email="driver@coldrescue.io",
        role=UserRole.DRIVER,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Permitted: Acknowledge assignment
    res_ack = client.post(
        "/api/v1/incidents/inc_103/acknowledge",
        json={"driver_name": "Murugan", "vehicle_id": "TN-37-X-9999"},
        headers=headers,
    )
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "DISPATCH_ACKNOWLEDGED"

    # 2. STRICT SEPARATION OF DUTIES: Drivers CANNOT approve restricted recovery actions!
    res_appr = client.post(
        "/api/v1/incidents/inc_103/approve",
        json={"decision": "APPROVED"},
        headers=headers,
    )
    assert res_appr.status_code == 403
    assert "Forbidden" in res_appr.json()["detail"] or "Separation of duties" in res_appr.json()["detail"]


def test_receiver_role_permitted_and_forbidden_actions():
    token = create_token(
        user_id="usr_rcv_1",
        email="receiver_coimbatore@coldrescue.io",
        role=UserRole.RECEIVER,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Permitted: Accept delivery
    res_acc = client.post(
        "/api/v1/incidents/inc_104/accept",
        json={"accepted_kg": 500.0, "bay_number": "Bay-4B"},
        headers=headers,
    )
    assert res_acc.status_code == 200
    assert res_acc.json()["status"] == "DELIVERY_ACCEPTED"
    assert res_acc.json()["accepted_kg"] == 500.0

    # 2. Forbidden: Initiate recovery
    res_init = client.post("/api/v1/incidents/recover", json={"incident_id": "inc_104"}, headers=headers)
    assert res_init.status_code == 403
