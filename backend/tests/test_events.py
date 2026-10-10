"""Tests for the ColdRescue event-ingestion API."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.event_ingestion import event_store


client = TestClient(app)


def make_incident_event(
    *,
    event_id: str = "evt_001",
    idempotency_key: str = "ikey_001",
    sequence_number: int = 1,
) -> dict:
    return {
        "event_id": event_id,
        "event_type": "incident",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0.0",
        "correlation_id": "corr_test_001",
        "idempotency_key": idempotency_key,
        "sequence_number": sequence_number,
        "incident_id": "inc_001",
        "incident_type": "REEFER_UNIT_FAILURE",
        "status": "OPEN",
        "location_id": "loc_001",
        "location_name": "Test Cold Storage",
        "reported_by": "test_sensor",
        "notes": "Test event",
    }


def setup_function() -> None:
    event_store.clear()


def test_ingest_accepts_valid_event():
    response = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-001",
            "event": make_incident_event(),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["sequence_number"] == 1


def test_ingest_returns_duplicate_for_identical_retry():
    payload = {
        "stream_id": "sensor-001",
        "event": make_incident_event(),
    }

    first = client.post("/api/v1/events/ingest", json=payload)
    second = client.post("/api/v1/events/ingest", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["status"] == "duplicate"


def test_ingest_rejects_reused_idempotency_key_with_different_event():
    first_event = make_incident_event()
    second_event = make_incident_event(
        event_id="evt_002",
        sequence_number=2,
    )

    first = client.post(
        "/api/v1/events/ingest",
        json={"stream_id": "sensor-001", "event": first_event},
    )
    second = client.post(
        "/api/v1/events/ingest",
        json={"stream_id": "sensor-001", "event": second_event},
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_ingest_rejects_out_of_order_sequence():
    first = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-001",
            "event": make_incident_event(sequence_number=2),
        },
    )
    older = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-001",
            "event": make_incident_event(
                event_id="evt_older",
                idempotency_key="ikey_older",
                sequence_number=1,
            ),
        },
    )

    assert first.status_code == 200
    assert older.status_code == 409


def test_ingest_rejects_missing_required_event_fields():
    response = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-001",
            "event": {
                "event_type": "incident",
                "sequence_number": 1,
            },
        },
    )

    assert response.status_code == 422


def test_ingest_rejects_missing_sequence_number():
    event = make_incident_event()
    event.pop("sequence_number")

    response = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-001",
            "event": event,
        },
    )

    assert response.status_code == 422


def test_ingest_rejects_unsupported_event_type():
    event = make_incident_event()
    event["event_type"] = "unknown_event"

    response = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-001",
            "event": event,
        },
    )

    assert response.status_code == 400


def test_sequence_numbers_are_independent_between_streams():
    first = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-A",
            "event": make_incident_event(
                event_id="evt_A",
                idempotency_key="ikey_A",
                sequence_number=5,
            ),
        },
    )
    second = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-B",
            "event": make_incident_event(
                event_id="evt_B",
                idempotency_key="ikey_B",
                sequence_number=1,
            ),
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200


def test_ingest_rejects_whitespace_only_stream_id():
    response = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "   ",
            "event": make_incident_event(),
        },
    )

    assert response.status_code == 422


def test_ingest_rejects_duplicate_event_id_with_new_idempotency_key():
    first_event = make_incident_event(
        event_id="evt_same",
        idempotency_key="ikey_first",
        sequence_number=1,
    )
    second_event = make_incident_event(
        event_id="evt_same",
        idempotency_key="ikey_second",
        sequence_number=2,
    )

    first = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-duplicate-id",
            "event": first_event,
        },
    )
    second = client.post(
        "/api/v1/events/ingest",
        json={
            "stream_id": "sensor-duplicate-id",
            "event": second_event,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 409