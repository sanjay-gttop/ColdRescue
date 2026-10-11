"""ColdRescue M13 Event Pipeline Stack: EventBridge, SQS, DLQ, and Consumer."""
from __future__ import annotations

import os
import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_cloudwatch as cw,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_sources,
    aws_sqs as sqs,
)
from constructs import Construct


class ColdRescueEventPipelineStack(Stack):
    """M13 Resilient Event Processing Stack with EventBridge, SQS Buffer, and DLQ."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Custom EventBridge Event Bus
        self.event_bus = events.EventBus(
            self,
            "ColdRescueEventBus",
            event_bus_name=f"ColdRescue-Bus-{environment_name}",
        )

        # 2. Dead-Letter Queue (DLQ)
        self.dlq = sqs.Queue(
            self,
            "ColdRescueDLQ",
            queue_name=f"ColdRescue-DLQ-{environment_name}",
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if environment_name == "dev" else RemovalPolicy.RETAIN,
        )

        # 3. Main SQS Buffer Queue with Redrive Policy
        self.processing_queue = sqs.Queue(
            self,
            "ColdRescueProcessingQueue",
            queue_name=f"ColdRescue-ProcessingQueue-{environment_name}",
            visibility_timeout=Duration.seconds(120),
            retention_period=Duration.days(4),
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.dlq,
            ),
            removal_policy=RemovalPolicy.DESTROY if environment_name == "dev" else RemovalPolicy.RETAIN,
        )

        # 4. EventBridge Rules routing events to SQS Buffer
        self.incident_rule = events.Rule(
            self,
            "IncidentEventsRule",
            event_bus=self.event_bus,
            description="Route cold-chain power-failure and incident events to processing queue",
            event_pattern=events.EventPattern(
                source=["coldrescue.incident", "coldrescue.telemetry"],
                detail_type=["IncidentDetected", "PowerFailureAlert", "RefrigerationAlarm"],
            ),
            targets=[targets.SqsQueue(self.processing_queue)],
        )

        self.orchestration_rule = events.Rule(
            self,
            "OrchestrationEventsRule",
            event_bus=self.event_bus,
            description="Route workflow decisions and recovery finalization events",
            event_pattern=events.EventPattern(
                source=["coldrescue.orchestration"],
                detail_type=["PolicyBlocked", "RecoveryApproved", "DeliveryAccepted"],
            ),
            targets=[targets.SqsQueue(self.processing_queue)],
        )

        # 5. Idempotent SQS Consumer Lambda Function
        lambda_code = _lambda.Code.from_asset(
            ".",
            exclude=[
                ".venv",
                ".venv/**",
                "venv",
                "venv/**",
                "frontend",
                "frontend/**",
                "node_modules",
                "node_modules/**",
                ".git",
                ".git/**",
                "cdk.out",
                "cdk.out/**",
                "__pycache__",
                "**/__pycache__",
                "**/*.pyc",
                ".pytest_cache",
                "**/.pytest_cache/**",
                "tests",
                "tests/**",
                "docs",
                "docs/**",
                "data",
                "data/**",
                "infrastructure/layers",
                "infrastructure/layers/**",
            ],
        )

        layers = []
        layer_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layers", "runtime")
        if os.path.exists(layer_dir):
            runtime_layer = _lambda.LayerVersion(
                self,
                "PipelineRuntimeLayer",
                code=_lambda.Code.from_asset(layer_dir),
                compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            )
            layers.append(runtime_layer)

        self.consumer_lambda = _lambda.Function(
            self,
            "QueueConsumerFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="backend.handlers.queue_consumer.sqs_event_consumer_handler",
            code=lambda_code,
            layers=layers,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "COLDRESCUE_ENV": environment_name,
                "AWS_INTEGRATIONS_ENABLED": "true",
            },
        )

        # Add SQS event source with batch failure reporting
        self.consumer_lambda.add_event_source(
            lambda_sources.SqsEventSource(
                self.processing_queue,
                batch_size=10,
                max_batching_window=Duration.seconds(5),
                report_batch_item_failures=True,
            )
        )

        # DynamoDB permissions for idempotency verification
        events_table_arn = f"arn:aws:dynamodb:{self.region}:{self.account}:table/ColdRescue-Events-{environment_name}"
        events_table_policy = iam.PolicyStatement(
            actions=["dynamodb:PutItem", "dynamodb:Query", "dynamodb:GetItem"],
            resources=[events_table_arn, f"{events_table_arn}/index/*"],
        )
        self.consumer_lambda.add_to_role_policy(events_table_policy)

        # 6. CloudWatch Metric & Alarm for DLQ depth
        self.dlq_depth_alarm = cw.Alarm(
            self,
            "DLQDepthAlarm",
            alarm_name=f"ColdRescue-DLQ-Depth-{environment_name}",
            alarm_description="Alert when messages enter the Dead-Letter Queue due to processing failures",
            metric=self.dlq.metric_approximate_number_of_messages_visible(
                period=Duration.minutes(1),
                statistic="Maximum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        )

        # 7. Outputs
        CfnOutput(
            self,
            "EventBusArnOutput",
            value=self.event_bus.event_bus_arn,
            description="ARN of ColdRescue EventBridge Event Bus",
            export_name=f"ColdRescue-{environment_name}-EventBusArn",
        )
        CfnOutput(
            self,
            "ProcessingQueueUrlOutput",
            value=self.processing_queue.queue_url,
            description="URL of ColdRescue SQS Processing Buffer Queue",
            export_name=f"ColdRescue-{environment_name}-ProcessingQueueUrl",
        )
        CfnOutput(
            self,
            "DLQUrlOutput",
            value=self.dlq.queue_url,
            description="URL of ColdRescue SQS Dead-Letter Queue",
            export_name=f"ColdRescue-{environment_name}-DLQUrl",
        )
