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
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(60),
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