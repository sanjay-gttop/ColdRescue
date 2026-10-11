#!/usr/bin/env python3
"""
ColdRescue Master Teardown Script.
Safely tears down or scales down all billable/demonstration cloud resources:
  1. SageMaker Serverless Endpoint and EndpointConfig (coldrescue-thermal-serverless-*)
  2. ECS Fargate Telemetry Simulator Service (scale desired_count to 0)
  3. Validates DynamoDB Streams consumer state
Idempotent: safe to run multiple times.
"""
from __future__ import annotations

import argparse
import sys
import boto3
from botocore.exceptions import ClientError


def teardown_sagemaker(region: str = "ap-south-1", endpoint_name: str = "coldrescue-thermal-serverless-v1") -> None:
    print(f"\n[1/3] SageMaker Teardown in {region}...")
    sm = boto3.client("sagemaker", region_name=region)

    # 1. Delete Endpoint
    try:
        print(f"  Checking endpoint: {endpoint_name}...")
        sm.describe_endpoint(EndpointName=endpoint_name)
        print(f"  Deleting SageMaker endpoint: {endpoint_name}...")
        sm.delete_endpoint(EndpointName=endpoint_name)
        print(f"  [+] Endpoint {endpoint_name} deleted successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ResourceNotFound", "ValidationException"):
            print(f"  [i] Endpoint {endpoint_name} does not exist (already deleted).")
        else:
            print(f"  [-] Error deleting endpoint: {e}")

    # 2. Delete Endpoint Config
    config_name = "coldrescue-thermal-serverless-config-v101"
    try:
        print(f"  Checking endpoint config: {config_name}...")
        sm.describe_endpoint_config(EndpointConfigName=config_name)
        print(f"  Deleting endpoint config: {config_name}...")
        sm.delete_endpoint_config(EndpointConfigName=config_name)
        print(f"  [+] Endpoint config {config_name} deleted successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ResourceNotFound", "ValidationException"):
            print(f"  [i] Endpoint config {config_name} does not exist (already deleted).")
        else:
            print(f"  [-] Error deleting endpoint config: {e}")


def teardown_fargate(region: str = "ap-south-1", cluster_name: str = "ColdRescue-Cluster-dev", service_name: str = "ColdRescue-SimulatorService-dev") -> None:
    print(f"\n[2/3] ECS Fargate Teardown in {region}...")
    ecs = boto3.client("ecs", region_name=region)

    try:
        print(f"  Checking ECS cluster: {cluster_name} and service: {service_name}...")
        services = ecs.describe_services(cluster=cluster_name, services=[service_name])
        active_services = [s for s in services.get("services", []) if s.get("status") == "ACTIVE"]
        if active_services:
            current_count = active_services[0].get("desiredCount", 0)
            print(f"  Current desired task count: {current_count}. Scaling to 0...")
            ecs.update_service(cluster=cluster_name, service=service_name, desiredCount=0)
            print(f"  [+] Scaled {service_name} to desiredCount=0.")
        else:
            print(f"  [i] Fargate service {service_name} not active or not yet deployed.")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("ClusterNotFoundException", "ServiceNotFoundException"):
            print(f"  [i] ECS cluster or service does not exist (no active charges).")
        else:
            print(f"  [-] Note on ECS check: {e}")


def teardown_stream_consumer(region: str = "ap-south-1", function_name: str = "ColdRescue-StreamConsumer-dev") -> None:
    print(f"\n[3/3] DynamoDB Stream Consumer in {region}...")
    lmb = boto3.client("lambda", region_name=region)

    try:
        resp = lmb.get_function(FunctionName=function_name)
        print(f"  [+] Stream consumer Lambda {function_name} is managed via CDK foundation stack.")
        print(f"      To fully remove stream consumer, run: npx cdk destroy ColdRescue-Foundation-dev")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"  [i] Function {function_name} does not exist.")
        else:
            print(f"  [-] Note on Lambda check: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ColdRescue Demo Teardown Utility")
    parser.add_argument("--region", default="ap-south-1", help="AWS Region (default: ap-south-1)")
    parser.add_argument("--sagemaker-endpoint", default="coldrescue-thermal-serverless-v1", help="SageMaker endpoint name")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without deleting")
    parser.add_argument(
        "--full-teardown",
        action="store_true",
        help="Perform permanent deletion of SageMaker serverless endpoint after judging is completed. Without this flag, endpoint is preserved.",
    )
    args = parser.parse_args()

    print("=======================================================")
    print("      ColdRescue V7 — Demonstration Teardown           ")
    print("=======================================================")
    print(f"Region: {args.region}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Full Teardown Mode: {args.full_teardown}")

    if args.dry_run:
        if args.full_teardown:
            print("\n[DRY RUN] Would delete SageMaker endpoint & scale ECS Fargate service to 0.")
        else:
            print("\n[DRY RUN] Would scale ECS Fargate to 0 and PRESERVE SageMaker serverless endpoint for live judging ($0 idle cost).")
        return

    # In default mode, scale down ECS Fargate to 0 to eliminate container runtime charges,
    # and preserve SageMaker serverless endpoint for live judge evaluations.
    if args.full_teardown:
        teardown_sagemaker(region=args.region, endpoint_name=args.sagemaker_endpoint)
    else:
        print("\n[PRESERVED] SageMaker serverless endpoint kept intact for judging ($0 idle cost). Use --full-teardown to delete.")

    teardown_fargate(region=args.region)
    teardown_stream_consumer(region=args.region)

    print("\n[+] Teardown operation complete. ECS Fargate is at desiredCount=0.")


if __name__ == "__main__":
    main()

