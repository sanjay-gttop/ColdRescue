"""ColdRescue M0 Foundation Infrastructure Stack.

Establishes core foundational cloud primitives:
  1. Secure S3 Bucket for audit logs, telemetry archives, and incident receipts.
     - Strict Block Public Access (all 4 public access blocks)
     - SSL/TLS In-Transit Encryption Enforced
     - S3-Managed Server-Side Encryption (SSE-S3)
     - Object Versioning for compliance and audit trail immutability
     - Lifecycle management to optimize storage costs
  2. Central CloudWatch Log Group for structured backend application logging.
     - Explicit 30-day retention policy to prevent unbounded cost accumulation
  3. Standardized Resource Tagging & Structured CloudFormation Outputs.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_logs as logs,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_sources,
    aws_lambda_destinations as lambda_destinations,
    aws_sqs as sqs,
    aws_iam as iam,
)
from constructs import Construct


class ColdRescueFoundationStack(Stack):
    """M0 Foundation CloudFormation Stack for ColdRescue."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_name = environment_name
        is_production = environment_name.lower() in {"prod", "production"}

        # ── 1. Secure Audit & Artifact S3 Bucket ─────────────────────────────
        self.audit_bucket = s3.Bucket(
            self,
            "AuditLogsBucket",
            bucket_name=None,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,

            event_bridge_enabled=True,

            # Preserve audit data if the CloudFormation stack is deleted.
            # No automatic deletion of bucket objects is configured.
            removal_policy=RemovalPolicy.RETAIN,

            lifecycle_rules=[
                s3.LifecycleRule(
                    id="AuditLogArchivalPolicy",
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(90),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER_INSTANT_RETRIEVAL,
                            transition_after=Duration.days(30),
                        )
                    ],
                )
            ],
        )

        # ── 2. CloudWatch Log Group ──────────────────────────────────────────
        self.application_log_group = logs.LogGroup(
            self,
            "ApplicationLogGroup",
            log_group_name=f"/coldrescue/application/{environment_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=(
                RemovalPolicy.RETAIN
                if is_production
                else RemovalPolicy.DESTROY
            ),
        )

        # ── 3. DynamoDB Event Store Table ────────────────────────────────────
        self.events_table = dynamodb.Table(
            self,
            "EventsTable",
            table_name=f"ColdRescue-Events-{environment_name}",
            partition_key=dynamodb.Attribute(
                name="stream_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="sequence_number",
                type=dynamodb.AttributeType.NUMBER,
            ),
            stream=dynamodb.StreamViewType.NEW_IMAGE,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=(
                RemovalPolicy.RETAIN
                if is_production
                else RemovalPolicy.DESTROY
            ),
        )

        # GSI: Query by idempotency_key for conflict detection
        self.events_table.add_global_secondary_index(
            index_name="IdempotencyKeyIndex",
            partition_key=dynamodb.Attribute(
                name="idempotency_key",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # ── 4. DynamoDB Streams Read-Only Observability Consumer ──────────────
        self.stream_dlq = sqs.Queue(
            self,
            "StreamConsumerDLQ",
            queue_name=f"ColdRescue-Stream-DLQ-{environment_name}",
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if not is_production else RemovalPolicy.RETAIN,
        )

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

        self.stream_consumer = _lambda.Function(
            self,
            "StreamConsumerFn",
            function_name=f"ColdRescue-StreamConsumer-{environment_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="backend.handlers.stream_consumer.dynamodb_stream_consumer_handler",
            code=lambda_code,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            environment={
                "COLDRESCUE_ENV": environment_name,
                "AWS_INTEGRATIONS_ENABLED": "true",
            },
        )

        self.stream_consumer.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "ColdRescue/Events",
                    }
                },
            )
        )

        self.stream_consumer.add_event_source(
            lambda_sources.DynamoEventSource(
                self.events_table,
                starting_position=_lambda.StartingPosition.LATEST,
                batch_size=10,
                bisect_batch_on_error=True,
                retry_attempts=3,
                on_failure=lambda_destinations.SqsDestination(self.stream_dlq),
            )
        )

        # ── 3. CloudFormation Outputs ────────────────────────────────────────
        CfnOutput(
            self,
            "AuditBucketNameOutput",
            value=self.audit_bucket.bucket_name,
            description=(
                "Name of the secure S3 bucket for audit logs and incident receipts"
            ),
            export_name=f"ColdRescue-{environment_name}-AuditBucketName",
        )

        CfnOutput(
            self,
            "AuditBucketArnOutput",
            value=self.audit_bucket.bucket_arn,
            description=(
                "ARN of the secure S3 bucket for audit logs and incident receipts"
            ),
            export_name=f"ColdRescue-{environment_name}-AuditBucketArn",
        )

        CfnOutput(
            self,
            "ApplicationLogGroupNameOutput",
            value=self.application_log_group.log_group_name,
            description=(
                "Name of the CloudWatch Log Group for ColdRescue backend application logs"
            ),
            export_name=f"ColdRescue-{environment_name}-LogGroupName",
        )

        CfnOutput(
            self,
            "ApplicationLogGroupArnOutput",
            value=self.application_log_group.log_group_arn,
            description=(
                "ARN of the CloudWatch Log Group for ColdRescue backend application logs"
            ),
            export_name=f"ColdRescue-{environment_name}-LogGroupArn",
        )

        CfnOutput(
            self,
            "EventsTableNameOutput",
            value=self.events_table.table_name,
            description="Name of the DynamoDB table for event ingestion and persistence",
            export_name=f"ColdRescue-{environment_name}-EventsTableName",
        )

        CfnOutput(
            self,
            "EventsTableArnOutput",
            value=self.events_table.table_arn,
            description="ARN of the DynamoDB table for event ingestion and persistence",
            export_name=f"ColdRescue-{environment_name}-EventsTableArn",
        )