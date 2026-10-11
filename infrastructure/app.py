#!/usr/bin/env python3
"""ColdRescue AWS CDK Application Entry Point."""

from __future__ import annotations

import os
import aws_cdk as cdk
from aws_cdk import Tags

from infrastructure.stacks.foundation_stack import ColdRescueFoundationStack
from infrastructure.stacks.auth_stack import ColdRescueAuthStack
from infrastructure.stacks.orchestration_stack import ColdRescueOrchestrationStack
from infrastructure.stacks.event_pipeline_stack import ColdRescueEventPipelineStack
from infrastructure.stacks.simulator_stack import ColdRescueSimulatorStack
from infrastructure.stacks.websocket_stack import ColdRescueWebSocketStack
from infrastructure.stacks.monitoring_stack import ColdRescueMonitoringStack


def main() -> None:
    app = cdk.App()

    # Determine environment context and target AWS Account & Region
    env_name = app.node.try_get_context("environment") or os.getenv("APP_ENV", "dev")
    account = (
        os.getenv("CDK_DEFAULT_ACCOUNT")
        or os.getenv("AWS_ACCOUNT_ID")
        or app.node.try_get_context("defaultAccount")
        or "494110627063"
    )
    region = (
        os.getenv("CDK_DEFAULT_REGION")
        or os.getenv("AWS_REGION")
        or app.node.try_get_context("defaultRegion")
        or "ap-south-1"
    )

    target_env = cdk.Environment(account=account, region=region)

    # 1. Instantiate M0 Foundation Stack
    stack_name = f"ColdRescue-Foundation-{env_name}"
    foundation_stack = ColdRescueFoundationStack(
        app,
        stack_name,
        environment_name=env_name,
        env=target_env,
        description="ColdRescue M0 Foundation: Secure S3 Audit Archive and CloudWatch Application Logging.",
    )

    # 2. Instantiate M10 Auth Stack (Cognito User Pool, App Client, RBAC Groups)
    auth_stack_name = f"ColdRescue-Auth-{env_name}"
    auth_stack = ColdRescueAuthStack(
        app,
        auth_stack_name,
        environment_name=env_name,
        env=target_env,
        description="ColdRescue M10: Cognito User Pool, Client, and RBAC Groups.",
    )

    # 3. Instantiate M9 Orchestration Stack
    orch_stack_name = f"ColdRescue-Orchestration-{env_name}"
    orchestration_stack = ColdRescueOrchestrationStack(
        app,
        orch_stack_name,
        environment_name=env_name,
        user_pool=auth_stack.user_pool,
        env=target_env,
        description="ColdRescue M9: Step Functions Incident Recovery Orchestration and Lambda Tasks.",
    )

    # 4. Instantiate M13 Event Pipeline Stack (EventBridge, SQS, DLQ, Idempotent Consumer)
    pipeline_stack_name = f"ColdRescue-EventPipeline-{env_name}"
    event_pipeline_stack = ColdRescueEventPipelineStack(
        app,
        pipeline_stack_name,
        environment_name=env_name,
        env=target_env,
        description="ColdRescue M13: EventBridge Routing, SQS Buffering, DLQ, and Idempotent Consumer.",
    )

    # 5. Instantiate M14 ECS Fargate Simulator Stack
    simulator_stack_name = f"ColdRescue-Simulator-{env_name}"
    simulator_stack = ColdRescueSimulatorStack(
        app,
        simulator_stack_name,
        environment_name=env_name,
        env=target_env,
        description="ColdRescue M14: ECS Fargate Cold-Chain Telemetry Simulator.",
    )

    # 6. Instantiate M15 WebSocket Real-Time Push Stack
    websocket_stack_name = f"ColdRescue-WebSocket-{env_name}"
    websocket_stack = ColdRescueWebSocketStack(
        app,
        websocket_stack_name,
        environment_name=env_name,
        env=target_env,
        description="ColdRescue M15: API Gateway WebSocket Real-Time Push and DynamoDB Connections.",
    )

    # 7. Instantiate M16 Observability Stack (SNS Notifications, CloudWatch Dashboard & Alarms)
    monitoring_stack_name = f"ColdRescue-Monitoring-{env_name}"
    monitoring_stack = ColdRescueMonitoringStack(
        app,
        monitoring_stack_name,
        environment_name=env_name,
        env=target_env,
        description="ColdRescue M16: SNS Notifications, CloudWatch Operations Dashboard, and Alarms.",
    )

    # Standardized Resource Tagging across all stack resources
    all_stacks = [
        (foundation_stack, "M0"),
        (auth_stack, "M10"),
        (orchestration_stack, "M9"),
        (event_pipeline_stack, "M13"),
        (simulator_stack, "M14"),
        (websocket_stack, "M15"),
        (monitoring_stack, "M16"),
    ]
    for s, m in all_stacks:
        Tags.of(s).add("project", "coldrescue")
        Tags.of(s).add("Environment", env_name)
        Tags.of(s).add("ManagedBy", "AWS-CDK")
        Tags.of(s).add("Milestone", m)

    app.synth()


if __name__ == "__main__":
    main()
