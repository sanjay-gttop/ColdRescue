"""
ColdRescue SQS Queue Consumer and DLQ Redrive Handler (Milestone 13).

Provides:
  - Idempotent SQS consumer for buffered domain events
  - Duplicate detection to prevent duplicate business actions
  - Failure reporting (partial batch item failure reporting)
  - Controlled DLQ redrive and message replay
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.services.event_ingestion import (
    DuplicateKeyConflict,
    get_event_store,
)


def sqs_event_consumer_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Process a batch of records from SQS with idempotency and batch failure reporting."""
    records = event.get("Records", [])
    batch_item_failures: List[Dict[str, str]] = []
    store = get_event_store()

    for record in records:
        message_id = record.get("messageId", "unknown_msg")
        body_raw = record.get("body", "{}")

        try:
            body = json.loads(body_raw)
            # Handle EventBridge envelope if message was routed via EventBridge
            detail = body.get("detail") if "detail" in body else body

            # Controlled processing failure simulation for DLQ verification
            if detail.get("simulate_failure") is True:
                raise RuntimeError(f"Controlled processing failure injected for message {message_id}")

            stream_id = detail.get("stream_id") or f"stream_{detail.get('incident_id', message_id)}"
            event_id = detail.get("event_id") or message_id

            # Ingest idempotently into event store
            store.ingest(stream_id=stream_id, raw_event=detail)

        except DuplicateKeyConflict:
            # Idempotency duplicate safely handled: do not fail or duplicate actions
            continue
        except Exception:
            # Report failure for this specific message to trigger SQS retry / DLQ routing
            batch_item_failures.append({"itemIdentifier": message_id})

    return {
        "statusCode": 200,
        "processed_count": len(records) - len(batch_item_failures),
        "failed_count": len(batch_item_failures),
        "batchItemFailures": batch_item_failures,
    }


def redrive_dlq_messages(dlq_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simulate or execute controlled redrive of DLQ messages back to processing."""
    replayed_count = 0
    duplicates_suppressed = 0
    store = get_event_store()

    for msg in dlq_messages:
        body = msg.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        detail = body.get("detail", body)

        # Clear simulated failure flag before redrive
        detail.pop("simulate_failure", None)

        stream_id = detail.get("stream_id", "stream_replayed")
        try:
            res = store.ingest(stream_id=stream_id, raw_event=detail)
            if res.get("duplicate") is True:
                duplicates_suppressed += 1
            else:
                replayed_count += 1
        except DuplicateKeyConflict:
            duplicates_suppressed += 1

    return {
        "status": "REDRIVED",
        "total_messages": len(dlq_messages),
        "replayed_count": replayed_count,
        "duplicates_suppressed": duplicates_suppressed,
        "duplicate_business_actions_prevented": True,
    }
