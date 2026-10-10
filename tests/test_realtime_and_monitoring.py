"""
Unit and integration tests for Milestones 14, 15, and 16:
- M14 ECS Fargate Telemetry Simulator Emitter
- M15 API Gateway WebSocket Real-Time Push & Connections
- M16 Observability: SNS Notifications, CloudWatch Dashboard & Alarms
"""
import json
import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template

from backend.handlers.websocket_handlers import (
    connect_handler,
    disconnect_handler,
    broadcast_message_handler,
)
from simulator.engine import run_simulation
from infrastructure.stacks.simulator_stack import ColdRescueSimulatorStack
from infrastructure.stacks.websocket_stack import ColdRescueWebSocketStack
from infrastructure.stacks.monitoring_stack import ColdRescueMonitoringStack


def test_websocket_connect_and_disconnect_handlers():
    # 1. Connect
    connect_event = {
        "requestContext": {"connectionId": "conn_test_001"},
        "queryStringParameters": {"role": "OPERATOR", "userId": "user_sanjay"},
    }
    res_conn = connect_handler(connect_event)
    assert res_conn["statusCode"] == 200
    assert res_conn["body"] == "Connected"

    # 2. Disconnect
    disconnect_event = {
        "requestContext": {"connectionId": "conn_test_001"},
    }
    res_disc = disconnect_handler(disconnect_event)
    assert res_disc["statusCode"] == 200
    assert res_disc["body"] == "Disconnected"


def test_websocket_broadcast_handler_local_fallback():
    event = {
        "body": json.dumps({
            "type": "INCIDENT_ALERT",
            "incident_id": "inc_ws_01",
            "cooling_status": "failed",
            "predicted_breach_min": 45.0,
        })
    }
    result = broadcast_message_handler(event)
    assert result["statusCode"] == 200
    assert result["sent_count"] >= 0


def test_simulator_engine_generates_fargate_telemetry_payload():
    result = run_simulation("REEFER_UNIT_FAILURE", seed=101)
    report = result.to_report()

    assert "simulation_report" in report
    assert "scenario_id" in report["simulation_report"]
    assert report["simulation_report"]["all_events_schema_valid"] is True
    assert len(result.thermal_steps) > 0
    assert result.final_temp_c is not None


def test_simulator_stack_synthesizes_ecs_cluster_and_fargate_task():
    app = cdk.App()
    target_env = cdk.Environment(account="494110627063", region="ap-south-1")
    stack = ColdRescueSimulatorStack(
        app,
        "Test-ColdRescue-Simulator-dev",
        environment_name="dev",
        env=target_env,
    )
    template = Template.from_stack(stack)

    # 1. ECS Cluster
    template.has_resource_properties(
        "AWS::ECS::Cluster",
        {"ClusterName": "ColdRescue-Cluster-dev"},
    )

    # 2. Fargate Task Definition (256 CPU, 512 RAM)
    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "RequiresCompatibilities": ["FARGATE"],
            "Cpu": "256",
            "Memory": "512",
        },
    )


def test_websocket_stack_synthesizes_api_and_connections_table():
    app = cdk.App()
    target_env = cdk.Environment(account="494110627063", region="ap-south-1")
    stack = ColdRescueWebSocketStack(
        app,
        "Test-ColdRescue-WebSocket-dev",
        environment_name="dev",
        env=target_env,
    )
    template = Template.from_stack(stack)

    # 1. DynamoDB Connections Table
    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "TableName": "ColdRescue-WebSocketConnections-dev",
            "KeySchema": [
                {"AttributeName": "connection_id", "KeyType": "HASH"},
            ],
        },
    )

    # 2. WebSocket API
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Api",
        {
            "Name": "ColdRescue-WebSocket-dev",
            "ProtocolType": "WEBSOCKET",
        },
    )


def test_monitoring_stack_synthesizes_sns_topic_dashboard_and_alarms():
    app = cdk.App()
    target_env = cdk.Environment(account="494110627063", region="ap-south-1")
    stack = ColdRescueMonitoringStack(
        app,
        "Test-ColdRescue-Monitoring-dev",
        environment_name="dev",
        env=target_env,
    )
    template = Template.from_stack(stack)

    # 1. SNS Alert Topic
    template.has_resource_properties(
        "AWS::SNS::Topic",
        {"TopicName": "ColdRescue-Alerts-dev"},
    )

    # 2. CloudWatch Dashboard
    template.has_resource_properties(
        "AWS::CloudWatch::Dashboard",
        {"DashboardName": "ColdRescue-Operations-dev"},
    )

    # 3. State Machine Failure Alarm
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "AlarmName": "ColdRescue-Workflow-Failures-dev",
            "Threshold": 1,
        },
    )
