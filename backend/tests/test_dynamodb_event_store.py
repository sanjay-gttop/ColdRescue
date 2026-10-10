import json
from unittest.mock import MagicMock, patch
import pytest

from backend.services.event_ingestion import (
    DynamoDBEventStore,
    DuplicateKeyConflict,
    EVENT_SCHEMAS,
)


def test_dynamodb_event_store_fallback_when_disabled():
    store = DynamoDBEventStore()
    assert store._enabled is False

    valid_event = {
        "event_id": "evt_test_001",
        "event_type": "incident",
        "occurred_at": "2026-10-10T12:00:00Z",
        "schema_version": "1.0.0",
        "correlation_id": "corr_001",
        "idempotency_key": "idem_001",
        "sequence_number": 1,
        "incident_type": "REEFER_UNIT_FAILURE",
        "status": "OPEN",
        "location_id": "loc_01",
        "location_name": "Warehouse A",
        "reported_by": "operator",
    }
    result = store.ingest(stream_id="stream_test", raw_event=valid_event)
    assert result["status"] == "accepted"
    assert result["event_id"] == "evt_test_001"


def test_dynamodb_event_store_mocked_live_operations():
    with patch("backend.config.settings.settings.AWS_INTEGRATIONS_ENABLED", True):
        with patch("boto3.resource") as mock_boto:
            mock_table = MagicMock()
            mock_boto.return_value.Table.return_value = mock_table
            
            # 1. New event append
            mock_table.query.return_value = {"Items": []}
            store = DynamoDBEventStore()
            store._enabled = True

            valid_event = {
                "event_id": "evt_test_002",
                "event_type": "incident",
                "occurred_at": "2026-10-10T12:00:00Z",
                "schema_version": "1.0.0",
                "correlation_id": "corr_002",
                "idempotency_key": "idem_002",
                "sequence_number": 1,
                "incident_type": "REEFER_UNIT_FAILURE",
                "status": "OPEN",
                "location_id": "loc_01",
                "location_name": "Warehouse A",
                "reported_by": "operator",
            }
            res = store.ingest("stream_002", valid_event)
            assert res["status"] == "accepted"
            assert res["duplicate"] is False
            assert mock_table.put_item.called

            # 2. Duplicate detection on GSI
            schema = EVENT_SCHEMAS["incident"]
            event_obj = schema(**valid_event)
            event_json = json.dumps(
                event_obj.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            )
            mock_table.query.return_value = {
                "Items": [
                    {
                        "stream_id": "stream_002",
                        "event_json": event_json,
                    }
                ]
            }
            dup_res = store.ingest("stream_002", valid_event)
            assert dup_res["status"] == "duplicate"
            assert dup_res["duplicate"] is True
