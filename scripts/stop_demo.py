#!/usr/bin/env python3
"""
ColdRescue Demonstration Control: Stop Fargate Telemetry Simulator.
Scales ColdRescue-SimulatorService-dev desired_count back to 0 to prevent background costs.
"""
import argparse
import boto3

def stop_demo(region: str = "ap-south-1"):
    cluster = "ColdRescue-Cluster-dev"
    service = "ColdRescue-SimulatorService-dev"
    print(f"Scaling ECS Fargate service {service} in cluster {cluster} to desiredCount=0...")
    ecs = boto3.client("ecs", region_name=region)
    resp = ecs.update_service(cluster=cluster, service=service, desiredCount=0)
    print(f"[+] Service updated. Current desiredCount: {resp['service']['desiredCount']} (ZERO running cost).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stop ColdRescue Demo Fargate Service")
    parser.add_argument("--region", default="ap-south-1", help="AWS region")
    args = parser.parse_args()
    stop_demo(region=args.region)
