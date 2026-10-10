#!/usr/bin/env python3
"""ColdRescue AWS CDK Application Entry Point."""

from __future__ import annotations

import os
import aws_cdk as cdk
from aws_cdk import Tags

from infrastructure.stacks.foundation_stack import ColdRescueFoundationStack


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

    # Instantiate M0 Foundation Stack
    stack_name = f"ColdRescue-Foundation-{env_name}"
    foundation_stack = ColdRescueFoundationStack(
        app,
        stack_name,
        environment_name=env_name,
        env=target_env,
        description="ColdRescue M0 Foundation: Secure S3 Audit Archive and CloudWatch Application Logging.",
    )

    # Standardized Resource Tagging across all stack resources
    Tags.of(foundation_stack).add("Project", "ColdRescue")
    Tags.of(foundation_stack).add("Environment", env_name)
    Tags.of(foundation_stack).add("ManagedBy", "AWS-CDK")
    Tags.of(foundation_stack).add("Milestone", "M0")

    app.synth()


if __name__ == "__main__":
    main()
