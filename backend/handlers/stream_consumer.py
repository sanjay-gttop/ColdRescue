"""
ColdRescue DynamoDB Streams Event Consumer (Milestone 13 / Phase 1 Step 2).

Strict architectural invariants:
  1. Read-only observability consumer.
  2. Emits custom CloudWatch metric 'EventsPersistedCount' under namespace 'ColdRescue/Events'.
  3. Strict one-way telemetry: NEVER writes back to ColdRescue-Events-dev DynamoDB table
     (guarantees mathematical impossibility of recursive invocation loops).
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict

import boto3

logger = logging.getLogger(__name__)

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
COLDRESCUE_ENV = os.environ.get("COLDRESCUE_ENV", "dev")


def dynamodb_stream_consumer_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Consume DynamoDB stream records and emit persisted count metric to CloudWatch."""
    records = event.get("Records", [])
    record_count = len(records)
    if not record_count:
        logger.info("No records present in DynamoDB stream invocation batch.")
        return {"status": "NO_RECORDS", "events_persisted": 0}

    logger.info("DynamoDB Stream consumer received %d records", record_count)

    # Emit CloudWatch custom metric under ColdRescue/Events namespace
    try:
        cw = boto3.client("cloudwatch", region_name=AWS_REGION)
        cw.put_metric_data(
            Namespace="ColdRescue/Events",
            MetricData=[
                {
                    "MetricName": "EventsPersistedCount",
                    "Value": float(record_count),
                    "Unit": "Count",
                    "Dimensions": [
                        {"Name": "Environment", "Value": COLDRESCUE_ENV}
                    ],
                    "Timestamp": datetime.now(timezone.utc),
                }
            ],
        )
        logger.info("Emitted EventsPersistedCount=%d to ColdRescue/Events", record_count)
    except Exception as exc:
        logger.warning("Failed to emit EventsPersistedCount metric to CloudWatch: %s", exc)

    return {
        "status": "PROCESSED",
        "events_persisted": record_count,
        "environment": COLDRESCUE_ENV,
    }
