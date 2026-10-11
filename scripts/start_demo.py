#!/usr/bin/env python3
"""
ColdRescue Demonstration Control: Start Fargate Telemetry Simulator.
Scales ColdRescue-SimulatorService-dev desired_count to 1 for live demo evaluations.
"""
import argparse
import boto3

def start_demo(region: str = "ap-south-1", count: int = 1):
    cluster = "ColdRescue-Cluster-dev"
    service = "ColdRescue-SimulatorService-dev"
    print(f"Scaling ECS Fargate service {service} in cluster {cluster} to desiredCount={count}...")
    ecs = boto3.client("ecs", region_name=region)
    resp = ecs.update_service(cluster=cluster, service=service, desiredCount=count)
    print(f"[+] Service updated. Current desiredCount: {resp['service']['desiredCount']}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start ColdRescue Demo Fargate Service")
    parser.add_argument("--region", default="ap-south-1", help="AWS region")
    parser.add_argument("--count", type=int, default=1, help="Desired task count (default: 1)")
    args = parser.parse_args()
    start_demo(region=args.region, count=args.count)
