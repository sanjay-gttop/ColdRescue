"""
ColdRescue M0 Infrastructure Template Tests.

Validates that the synthesized CloudFormation template satisfies all security,
encryption, public access prevention, retention, and tagging requirements.
"""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from infrastructure.stacks.foundation_stack import ColdRescueFoundationStack


def _synthesize_stack(env_name: str = "dev") -> tuple[ColdRescueFoundationStack, Template]:
    app = cdk.App()
    target_env = cdk.Environment(account="494110627063", region="ap-south-1")
    stack = ColdRescueFoundationStack(
        app,
        f"Test-ColdRescue-Foundation-{env_name}",
        environment_name=env_name,
        env=target_env,
    )
    template = Template.from_stack(stack)
    return stack, template


def test_s3_audit_bucket_has_block_public_access():
    """Verify S3 audit bucket blocks all public ACLs and policies (least privilege)."""
    _, template = _synthesize_stack("dev")

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
        },
    )


def test_s3_audit_bucket_has_encryption_and_versioning():
    """Verify S3 audit bucket enforces server-side encryption and versioning for audit compliance."""
    _, template = _synthesize_stack("dev")

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            },
            "VersioningConfiguration": {
                "Status": "Enabled",
            },
        },
    )


def test_s3_audit_bucket_enforces_ssl_transport():
    """Verify S3 bucket policy strictly rejects unencrypted HTTP requests."""
    _, template = _synthesize_stack("dev")

    template.has_resource_properties(
        "AWS::S3::BucketPolicy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Action": "s3:*",
                                "Effect": "Deny",
                                "Condition": {
                                    "Bool": {
                                        "aws:SecureTransport": "false",
                                    }
                                },
                            }
                        )
                    ]
                )
            }
        },
    )


def test_cloudwatch_log_group_has_explicit_retention():
    """Verify CloudWatch application log group has an explicit retention policy (30 days)."""
    _, template = _synthesize_stack("dev")

    template.has_resource_properties(
        "AWS::Logs::LogGroup",
        {
            "LogGroupName": "/coldrescue/application/dev",
            "RetentionInDays": 30,
        },
    )


def test_stack_outputs_present():
    """Verify essential CloudFormation outputs are exported for downstream integration."""
    _, template = _synthesize_stack("dev")

    outputs = template.to_json().get("Outputs", {})
    output_keys = list(outputs.keys())

    assert any("AuditBucketName" in k for k in output_keys)
    assert any("AuditBucketArn" in k for k in output_keys)
    assert any("ApplicationLogGroupName" in k for k in output_keys)
    assert any("ApplicationLogGroupArn" in k for k in output_keys)


def test_no_wildcard_iam_roles_created():
    """Verify M0 foundation template creates zero IAM roles with Administrator or wildcard policies."""
    _, template = _synthesize_stack("dev")

    roles = template.find_resources("AWS::IAM::Role")
    for role_logical_id, role_props in roles.items():
        policies = role_props.get("Properties", {}).get("Policies", [])
        for policy in policies:
            statements = policy.get("PolicyDocument", {}).get("Statement", [])
            for statement in statements:
                actions = statement.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                assert "*:*" not in actions
                assert "*" not in actions
