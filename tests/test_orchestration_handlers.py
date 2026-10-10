"""
Unit and integration tests for M9 Step Functions Lambda Orchestration Handlers.
Covers:
  - Event ingestion and schema validation
  - Thermal prediction
  - Route retrieval and ETA
  - Solver allocation (greedy vs global)
  - Deterministic safety policy evaluation (PASS and POLICY_BLOCKED paths)
  - Operator approval (APPROVED and REJECTED paths)
  - Driver acknowledgement
  - Receiver acceptance
  - Final audit logging and diverted waste accounting
  - Workflow failure handler (zero kg false recovery)
"""
import pytest
from backend.handlers.orchestration_handlers import (
    validate_and_ingest_handler,
    predict_thermal_risk_handler,
    retrieve_routes_handler,
    solve_allocation_handler,
    evaluate_safety_policy_handler,
    human_approval_handler,
    driver_acknowledgement_handler,
    receiver_acceptance_handler,
    finalize_audit_handler,
    handle_failure_handler,
)


@pytest.fixture
def sample_incident_event():
    return {
        "incident_id": "inc_test_001",
        "correlation_id": "corr_test_001",
        "incident": {
            "incident_id": "inc_test_001",
            "incident_type": "REEFER_UNIT_FAILURE",
            "location_id": "loc_origin",
            "location_name": "Coimbatore Cold Depot",
            "latitude": 11.0168,
            "longitude": 76.9558,
            "cooling_status": "failed",
            "cargo": {
                "cargo_id": "cargo_dairy_01",
                "description": "Grade A Raw Milk",
                "cargo_type": "dairy",
                "mass_kg": 500.0,
                "current_temperature_c": 4.0,
                "ambient_temperature_c": 28.0,
                "safe_temperature_min_c": 2.0,
                "safe_temperature_max_c": 8.0,
                "backup_runtime_min": 30.0,
            },
            "receivers": [
                {
                    "receiver_id": "recv_salem_01",
                    "name": "Salem Dairy Hub",
                    "category": "COLD_STORAGE_FACILITY",
                    "capacity_kg": 2000.0,
                    "accepts_temp_min_c": 0.0,
                    "accepts_temp_max_c": 8.0,
                    "distance_km": 5.0,
                    "cooling_status": "operational",
                    "backup_power_runtime_min": 180.0,
                    "latitude": 11.0300,
                    "longitude": 76.9700,
                    "compatible_cargo_types": ["dairy", "general"],
                }
            ],
        },
    }


def test_validate_and_ingest_handler(sample_incident_event):
    result = validate_and_ingest_handler(sample_incident_event)
    assert result["status"] == "INGESTED"
    assert result["incident_id"] == "inc_test_001"
    assert "stream_id" in result
    assert "correlation_id" in result


def test_predict_thermal_risk_handler(sample_incident_event):
    result = predict_thermal_risk_handler(sample_incident_event)
    assert result["status"] == "PREDICTED"
    assert result["predicted_breach_minutes"] is not None
    assert result["predicted_breach_minutes"] > 0
    assert result["is_breached"] is False


def test_retrieve_routes_handler(sample_incident_event):
    result = retrieve_routes_handler(sample_incident_event)
    assert result["status"] == "ROUTES_RETRIEVED"
    assert result["count"] == 1
    receiver = result["receivers"][0]
    assert "distance_km" in receiver
    assert "travel_time_min" in receiver
    assert receiver["travel_time_min"] > 0


def test_solve_allocation_handler(sample_incident_event):
    # Enrich with routes first
    route_res = retrieve_routes_handler(sample_incident_event)
    event = dict(sample_incident_event)
    event["route_result"] = route_res

    result = solve_allocation_handler(event)
    assert result["status"] == "ALLOCATED"
    assert result["is_feasible"] is True
    assert result["candidate_assignment"] is not None
    assert result["candidate_assignment"]["receiver_id"] == "recv_salem_01"


def test_evaluate_safety_policy_passing(sample_incident_event):
    route_res = retrieve_routes_handler(sample_incident_event)
    event = dict(sample_incident_event)
    event["route_result"] = route_res
    alloc_res = solve_allocation_handler(event)
    event["allocation_result"] = alloc_res

    policy_res = evaluate_safety_policy_handler(event)
    assert policy_res["policy_status"] == "POLICY_PASSED"
    assert policy_res["allowed"] is True
    assert len(policy_res["hard_block_reasons"]) == 0


def test_evaluate_safety_policy_hard_blocked_insufficient_capacity(sample_incident_event):
    # Set receiver capacity to 100 kg while cargo is 500 kg
    sample_incident_event["incident"]["receivers"][0]["capacity_kg"] = 100.0
    
    route_res = retrieve_routes_handler(sample_incident_event)
    event = dict(sample_incident_event)
    event["route_result"] = route_res
    alloc_res = solve_allocation_handler(event)
    event["allocation_result"] = alloc_res

    # Overwrite candidate assignment to point to this under-capacity receiver
    event["allocation_result"]["candidate_assignment"] = {
        "incident_id": "inc_test_001",
        "receiver_id": "recv_salem_01",
        "cargo_kg": 500.0,
        "route_distance_km": 15.0,
        "travel_time_min": 20.0,
    }

    policy_res = evaluate_safety_policy_handler(event)
    assert policy_res["policy_status"] == "POLICY_BLOCKED"
    assert policy_res["allowed"] is False
    assert any("Capacity" in r or "capacity" in r.lower() for r in policy_res["hard_block_reasons"])


def test_human_approval_approved_and_rejected():
    # Approved case
    event_approved = {"approval": {"approved": True, "approver_email": "chief_operator@coldrescue.io"}}
    res = human_approval_handler(event_approved)
    assert res["approval_status"] == "APPROVED"
    assert res["approver"] == "chief_operator@coldrescue.io"

    # Rejected case
    event_rejected = {"approval": {"approved": False, "reason": "No truck available"}}
    res_rej = human_approval_handler(event_rejected)
    assert res_rej["approval_status"] == "REJECTED"
    assert "No truck available" in res_rej["rejection_reason"]


def test_driver_and_receiver_handlers():
    res_drv = driver_acknowledgement_handler({"driver": {"driver_id": "driver_tamil_07"}})
    assert res_drv["driver_status"] == "ACKNOWLEDGED"
    assert res_drv["driver_id"] == "driver_tamil_07"

    res_recv = receiver_acceptance_handler({
        "allocation_result": {
            "candidate_assignment": {"receiver_id": "recv_hub_01", "cargo_kg": 750.0}
        }
    })
    assert res_recv["receiver_status"] == "ACCEPTED"
    assert res_recv["accepted_cargo_kg"] == 750.0


def test_finalize_audit_handler_success():
    event = {
        "correlation_id": "corr_success_123",
        "incident_id": "inc_001",
        "incident": {"cargo": {"mass_kg": 600.0}},
        "policy_result": {"policy_status": "POLICY_PASSED"},
        "approval_result": {"approval_status": "APPROVED", "approver": "op@coldrescue.io"},
        "receiver_result": {"receiver_status": "ACCEPTED", "accepted_cargo_kg": 600.0},
    }
    result = finalize_audit_handler(event)
    assert result["status"] == "FINALIZED"
    assert result["outcome"] == "RECOVERED_DIVERTED"
    assert result["cargo_diverted_kg"] == 600.0
    assert result["cargo_at_risk_kg"] == 0.0


def test_finalize_audit_handler_blocked_marks_zero_diverted():
    event = {
        "correlation_id": "corr_blocked_123",
        "incident_id": "inc_002",
        "incident": {"cargo": {"mass_kg": 600.0}},
        "policy_result": {"policy_status": "POLICY_BLOCKED"},
        "approval_result": {"approval_status": "APPROVED"},
        "receiver_result": {"receiver_status": "ACCEPTED"},
    }
    result = finalize_audit_handler(event)
    assert result["status"] == "FINALIZED"
    assert result["outcome"] == "BLOCKED_OR_REJECTED"
    # Never report blocked cargo as successfully diverted!
    assert result["cargo_diverted_kg"] == 0.0
    assert result["cargo_at_risk_kg"] == 600.0


def test_handle_failure_handler_marks_zero_diverted():
    event = {
        "correlation_id": "corr_fail_123",
        "incident_id": "inc_003",
        "incident": {"cargo": {"mass_kg": 850.0}},
    }
    result = handle_failure_handler(event)
    assert result["status"] == "FAILED"
    assert result["outcome"] == "EXECUTION_FAILED"
    assert result["cargo_diverted_kg"] == 0.0
    assert result["cargo_at_risk_kg"] == 850.0
