"""
Unit and integration tests for Milestone 13: EventBridge, SQS, DLQ, and Event Recovery.
"""
import json
import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template

from backend.handlers.queue_consumer import sqs_event_consumer_handler, redrive_dlq_messages
from infrastructure.stacks.event_pipeline_stack import ColdRescueEventPipelineStack


def test_sqs_consumer_processes_valid_batch_idempotently():
    valid_event = {
        "event_id": "evt_sqs_001",
        "event_type": "incident",
        "occurred_at": "2026-10-10T12:00:00Z",
        "schema_version": "1.0.0",
        "correlation_id": "corr_sqs_001",
        "idempotency_key": "idem_sqs_001",
        "sequence_number": 1,
        "incident_type": "REEFER_UNIT_FAILURE",
        "status": "OPEN",
        "location_id": "loc_01",
        "location_name": "Warehouse A",
        "reported_by": "sqs_consumer",
    }
    sqs_event = {
        "Records": [
            {
                "messageId": "msg_001",
                "body": json.dumps(valid_event),
            }
        ]
    }
    result = sqs_event_consumer_handler(sqs_event)
    assert result["statusCode"] == 200
    assert result["processed_count"] == 1
    assert result["failed_count"] == 0
    assert len(result["batchItemFailures"]) == 0

    # Replay same message: must be handled idempotently without throwing error
    result_replay = sqs_event_consumer_handler(sqs_event)
    assert result_replay["statusCode"] == 200
    assert len(result_replay["batchItemFailures"]) == 0


def test_sqs_consumer_reports_controlled_failure_for_dlq_routing():
    failing_event = {
        "event_id": "evt_fail_002",
        "event_type": "incident",
        "occurred_at": "2026-10-10T12:00:00Z",
        "schema_version": "1.0.0",
        "correlation_id": "corr_fail_002",
        "idempotency_key": "idem_fail_002",
        "sequence_number": 1,
        "incident_type": "REEFER_UNIT_FAILURE",
        "simulate_failure": True,  # Injected controlled failure
    }
    sqs_event = {
        "Records": [
            {
                "messageId": "msg_failing_999",
                "body": json.dumps(failing_event),
            }
        ]
    }
    result = sqs_event_consumer_handler(sqs_event)
    assert result["statusCode"] == 200
    assert result["failed_count"] == 1
    assert len(result["batchItemFailures"]) == 1
    assert result["batchItemFailures"][0]["itemIdentifier"] == "msg_failing_999"


def test_controlled_dlq_redrive_prevents_duplicate_business_actions():
    sample_dlq_messages = [
        {
            "messageId": "dlq_msg_01",
            "body": {
                "detail": {
                    "event_id": "evt_redrive_01",
                    "event_type": "incident",
                    "occurred_at": "2026-10-10T12:00:00Z",
                    "schema_version": "1.0.0",
                    "correlation_id": "corr_redrive_01",
                    "idempotency_key": "idem_redrive_01",
                    "sequence_number": 1,
                    "incident_type": "REEFER_UNIT_FAILURE",
                    "status": "OPEN",
                    "location_id": "loc_01",
                    "location_name": "Hub Salem",
                    "reported_by": "redrive_worker",
                    "simulate_failure": True,
                }
            },
        }
    ]
    # First redrive pass
    res_1 = redrive_dlq_messages(sample_dlq_messages)
    assert res_1["status"] == "REDRIVED"
    assert res_1["replayed_count"] == 1
    assert res_1["duplicate_business_actions_prevented"] is True

    # Second redrive pass: must suppress duplicates
    res_2 = redrive_dlq_messages(sample_dlq_messages)
    assert res_2["duplicates_suppressed"] == 1


def test_event_pipeline_stack_synthesizes_all_resources():
    app = cdk.App()
    target_env = cdk.Environment(account="494110627063", region="ap-south-1")
    stack = ColdRescueEventPipelineStack(
        app,
        "Test-ColdRescue-EventPipeline-dev",
        environment_name="dev",
        env=target_env,
    )
    template = Template.from_stack(stack)

    # 1. Custom Event Bus
    template.has_resource_properties(
        "AWS::Events::EventBus",
        {"Name": "ColdRescue-Bus-dev"},
    )

    # 2. DLQ
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {
            "QueueName": "ColdRescue-DLQ-dev",
            "MessageRetentionPeriod": 1209600,  # 14 days
        },
    )

    # 3. Processing Queue with RedrivePolicy
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {
            "QueueName": "ColdRescue-ProcessingQueue-dev",
            "VisibilityTimeout": 120,
            "RedrivePolicy": {
                "maxReceiveCount": 3,
            },
        },
    )

    # 4. EventBridge Rules
    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "Description": "Route cold-chain power-failure and incident events to processing queue",
        },
    )

    # 5. DLQ CloudWatch Alarm
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmName": "ColdRescue-DLQ-Depth-dev",
            "Threshold": 1,
        },
    )
