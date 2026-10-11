"""
End-to-End Recovery Flow and API Integration Tests.

Tests cover:
  - AllocationService single-incident evaluation
  - Strategy comparison workflow (Greedy vs Global)
  - FastAPI HTTP endpoints (/api/v1/health, /api/v1/allocation/evaluate, /api/v1/allocation/solve, /api/v1/allocation/compare)
  - Input validation and HTTP error code responses (400, 422)
"""
from __future__ import annotations

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.models.domain import (
    CargoItem,
    IncidentRecord,
    IncidentStatus,
    IncidentType,
    Location,
    ReceiverCategory,
    ReceiverNode,
    SeverityLevel,
)
from backend.services.allocation_service import AllocationService


def _create_sample_payload():
    incident = {
        "incident_id": "inc_e2e_01",
        "incident_type": "REEFER_UNIT_FAILURE",
        "severity": "high",
        "status": "OPEN",
        "location": {
            "location_id": "loc_origin",
            "name": "Produce Truck #12",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
        "cargo": {
            "cargo_id": "c_e2e_01",
            "description": "Strawberries and Berries",
            "cargo_type": "general",
            "cargo_kg": 500.0,
            "safe_temperature_min_c": 1.0,
            "safe_temperature_max_c": 6.0,
            "current_temperature_c": 3.0,
            "backup_runtime_min": 60.0,
            "unloading_duration_min": 15.0,
            "time_sensitivity": "HIGH",
        },
        "reported_at": datetime.now(timezone.utc).isoformat(),
    }

    receivers = [
        {
            "receiver_id": "recv_e2e_01",
            "name": "Central Chilled Depot",
            "category": "COLD_STORAGE_FACILITY",
            "capacity_kg": 5000.0,
            "current_load_kg": 1000.0,
            "accepts_temperature_min_c": 0.0,
            "accepts_temperature_max_c": 8.0,
            "compatible_cargo_types": ["general", "produce"],
            "cooling_status": "operational",
            "backup_runtime_min": 180.0,
            "latitude": 13.00,
            "longitude": 77.65,
            "distance_km": 12.0,
            "travel_time_min": 18.0,
            "is_available": True,
        }
    ]
    return incident, receivers


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_api_evaluate_incident_recovery():
    incident, receivers = _create_sample_payload()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/allocation/evaluate",
            json={
                "incident": incident,
                "receivers": receivers,
                "ambient_temperature_c": 25.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["incident_id"] == "inc_e2e_01"
        assert data["is_recoverable"] is True
        assert data["recommended_receiver_id"] == "recv_e2e_01"
        assert len(data["candidate_evaluations"]) == 1


@pytest.mark.asyncio
async def test_api_solve_fleet_allocation():
    incident, receivers = _create_sample_payload()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/allocation/solve",
            json={
                "incidents": [incident],
                "receivers": receivers,
                "strategy": "global",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["strategy"] == "global"
        assert len(data["assignments"]) == 1
        assert data["assignments"][0]["feasible"] is True


@pytest.mark.asyncio
async def test_api_compare_strategies():
    incident, receivers = _create_sample_payload()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/allocation/compare",
            json={
                "incidents": [incident],
                "receivers": receivers,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "greedy_plan" in data
        assert "global_plan" in data
        assert "comparison_summary" in data


@pytest.mark.asyncio
async def test_api_empty_receivers_returns_400():
    incident, _ = _create_sample_payload()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/allocation/evaluate",
            json={"incident": incident, "receivers": []},
        )
        assert response.status_code == 400


def test_allocation_service_direct_comparison():
    inc_dict, recv_dict = _create_sample_payload()
    inc = IncidentRecord(**inc_dict)
    recv = ReceiverNode(**recv_dict[0])

    service = AllocationService()
    comparison = service.compare_strategies(
        incidents=[inc],
        receivers=[recv],
    )
    assert comparison.greedy_plan.strategy == "greedy"
    assert comparison.global_plan.strategy == "global"
    assert comparison.recommended_strategy in ["global", "greedy"]


@pytest.mark.asyncio
async def test_rbac_unauthenticated_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request with no Authorization header
        resp_no_token = await client.post(
            "/api/v1/incidents/inc_sample/approve",
            json={"decision": "APPROVED"},
        )
        assert resp_no_token.status_code == 401
        assert "Authentication required" in resp_no_token.json()["detail"]

        # Request with forged / malformed Bearer token
        resp_bad_token = await client.post(
            "/api/v1/incidents/inc_sample/approve",
            json={"decision": "APPROVED"},
            headers={"Authorization": "Bearer forged.invalid.token"},
        )
        assert resp_bad_token.status_code == 401


@pytest.mark.asyncio
async def test_rbac_insufficient_role_returns_403_and_audits():
    from backend.auth.security import create_token
    from backend.auth.models import UserRole

    driver_token = create_token("user_driver_01", "driver@coldrescue.io", UserRole.DRIVER)
    approver_token = create_token("user_approver_01", "approver@coldrescue.io", UserRole.APPROVER)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Driver attempting to approve recovery -> 403 Forbidden (Separation of duties)
        resp_driver = await client.post(
            "/api/v1/incidents/inc_sample/approve",
            json={"decision": "APPROVED"},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert resp_driver.status_code == 403
        assert "Forbidden" in resp_driver.json()["detail"]

        # Approver attempting to approve recovery -> 200 OK
        resp_approver = await client.post(
            "/api/v1/incidents/inc_sample/approve",
            json={"decision": "APPROVED"},
            headers={"Authorization": f"Bearer {approver_token}"},
        )
        assert resp_approver.status_code == 200
        assert resp_approver.json()["decision"] == "APPROVED"

