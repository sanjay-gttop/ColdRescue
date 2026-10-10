"""Persistence and cross-process tests for the SQLite event store."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from backend.services.event_ingestion import SQLiteEventStore


def make_event(event_id="evt_persist_001", idempotency_key="ikey_persist_001", sequence_number=1):
    return {
        "event_id": event_id,
        "event_type": "incident",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0.0",
        "correlation_id": "corr_persist_test",
        "idempotency_key": idempotency_key,
        "sequence_number": sequence_number,
        "incident_id": "inc_persist_test",
        "incident_type": "REEFER_UNIT_FAILURE",
        "status": "OPEN",
        "location_id": "loc_persist_test",
        "location_name": "Persistence Test Cold Storage",
        "reported_by": "test_sensor",
        "notes": "SQLite persistence test",
    }


def test_events_persist_across_store_instances(tmp_path):
    database = tmp_path / "events.sqlite3"
    first_store = SQLiteEventStore(database)
    event = make_event()

    result = first_store.ingest("sensor-persist", event)
    assert result["status"] == "accepted"

    restarted_store = SQLiteEventStore(database)
    duplicate = restarted_store.ingest("sensor-persist", event)

    assert duplicate["status"] == "duplicate"
    assert duplicate["duplicate"] is True


def test_database_is_shared_with_a_separate_python_process(tmp_path):
    database = tmp_path / "shared-events.sqlite3"
    parent_store = SQLiteEventStore(database)

    first_event = make_event()
    assert parent_store.ingest("sensor-shared", first_event)["status"] == "accepted"

    second_event = make_event(
        event_id="evt_persist_002",
        idempotency_key="ikey_persist_002",
        sequence_number=2,
    )

    child_code = r'''
import json
import sys
from backend.services.event_ingestion import SQLiteEventStore

db_path = sys.argv[1]
payload = json.load(sys.stdin)
store = SQLiteEventStore(db_path)
print(json.dumps(store.ingest(payload["stream_id"], payload["event"])))
'''

    child = subprocess.run(
        [sys.executable, "-c", child_code, str(database)],
        input=json.dumps({
            "stream_id": "sensor-shared",
            "event": second_event,
        }),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert child.returncode == 0, child.stderr
    child_result = json.loads(child.stdout.strip())
    assert child_result["status"] == "accepted"

    # The parent process must immediately see the event written by the child.
    another_store = SQLiteEventStore(database)
    retry = another_store.ingest("sensor-shared", second_event)

    assert retry["status"] == "duplicate"
    assert retry["duplicate"] is True
