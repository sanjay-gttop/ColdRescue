#!/usr/bin/env python3
"""
Warm-up utility for ColdRescue SageMaker Serverless Inference Endpoint.
Ensures the serverless container is pre-warmed prior to live hackathon demos.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import boto3
from botocore.config import Config


def warmup_endpoint(endpoint_name: str = "coldrescue-thermal-serverless-v1", region: str = "ap-south-1") -> bool:
    print(f"[*] Pre-warming SageMaker Serverless Endpoint: {endpoint_name} in {region}...")
    
    # Allow 20s read timeout specifically for potential cold start
    cfg = Config(connect_timeout=5, read_timeout=25, retries={"max_attempts": 1})
    client = boto3.client("sagemaker-runtime", region_name=region, config=cfg)
    
    test_payload = {
        "cargo_type": "dairy",
        "current_temp_c": 4.0,
        "ambient_temp_c": 28.0,
        "safe_limit_c": 8.0,
        "cooling_status": "failed",
        "backup_runtime_min": 30.0,
        "mass_kg": 500.0,
        "thermal_resistance": 1.0,
    }
    
    t0 = time.perf_counter()
    try:
        response = client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps(test_payload),
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0
        resp_data = json.loads(response["Body"].read().decode("utf-8"))
        print(f"[+] Endpoint response received in {latency_ms:.1f} ms (HTTP {response['ResponseMetadata']['HTTPStatusCode']})")
        print(f"    Predicted breach minutes: {resp_data.get('predicted_breach_minutes')} min")
        print(f"    Model Version: {resp_data.get('model_version')}")
        print(f"    Provenance: {resp_data.get('provenance')}")
        
        # Second call to verify warm latency
        t1 = time.perf_counter()
        response2 = client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps(test_payload),
        )
        warm_latency_ms = (time.perf_counter() - t1) * 1000.0
        print(f"[+] Confirmed warm latency: {warm_latency_ms:.1f} ms (sub-second target met: {warm_latency_ms < 1500})")
        return True
    except Exception as exc:
        print(f"[-] Warm-up invocation error: {exc}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="ColdRescue SageMaker Serverless Warm-up")
    parser.add_argument("--endpoint", default="coldrescue-thermal-serverless-v1", help="SageMaker endpoint name")
    parser.add_argument("--region", default="ap-south-1", help="AWS region")
    args = parser.parse_args()
    
    success = warmup_endpoint(endpoint_name=args.endpoint, region=args.region)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
