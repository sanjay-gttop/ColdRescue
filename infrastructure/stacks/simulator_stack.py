"""ColdRescue M14 Simulator Stack: ECS Fargate Cold-Chain Telemetry Simulator."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_iam as iam,
)
from constructs import Construct


class ColdRescueSimulatorStack(Stack):
    """M14 ECS Fargate Simulator Stack for Continuous Telemetry Generation."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str = "dev",
        api_url: str = "http://localhost:8000",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Cost-conscious VPC for Fargate (isolated subnets or lightweight public-only)
        self.vpc = ec2.Vpc(
            self,
            "SimulatorVpc",
            max_azs=2,
            nat_gateways=0,  # 0 NAT Gateways to minimize costs
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
        )

        # 2. ECS Cluster
        self.cluster = ecs.Cluster(
            self,
            "SimulatorCluster",
            cluster_name=f"ColdRescue-Cluster-{environment_name}",
            vpc=self.vpc,
        )

        # 3. CloudWatch Log Group for Simulator
        self.log_group = logs.LogGroup(
            self,
            "SimulatorLogGroup",
            log_group_name=f"/ecs/coldrescue-simulator/{environment_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # 4. Fargate Task Definition (Minimal 0.25 vCPU, 512 MiB RAM)
        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "SimulatorTaskDef",
            cpu=256,
            memory_limit_mib=512,
        )

        # Grant permissions to write logs, metrics, and publish to EventBridge
        self.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[self.log_group.log_group_arn, f"{self.log_group.log_group_arn}:*"],
            )
        )
        self.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "ColdRescue/Simulator"
                    }
                },
            )
        )
        self.task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[f"arn:aws:events:{self.region}:{self.account}:event-bus/ColdRescue-Bus-{environment_name}"],
            )
        )

        # 5. Container Definition
        self.container = self.task_definition.add_container(
            "TelemetryEmitterContainer",
            image=ecs.ContainerImage.from_asset(
                ".",
                file="simulator/Dockerfile",
                exclude=[
                    ".venv",
                    "venv",
                    "frontend",
                    "node_modules",
                    ".git",
                    "cdk.out",
                    "__pycache__",
                    "tests",
                    "docs",
                    "data",
                    "infrastructure/layers",
                ],
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="telemetry",
                log_group=self.log_group,
            ),
            environment={
                "COLDRESCUE_API_URL": api_url,
                "COLDRESCUE_ENV": environment_name,
                "SCENARIO_NAME": "WAREHOUSE_GRID_OUTAGE",
            },
        )

        # Outputs
        CfnOutput(
            self,
            "ClusterNameOutput",
            value=self.cluster.cluster_name,
            description="ECS Cluster Name for ColdRescue Simulator",
            export_name=f"ColdRescue-{environment_name}-ClusterName",
        )
        CfnOutput(
            self,
            "TaskDefinitionArnOutput",
            value=self.task_definition.task_definition_arn,
            description="Fargate Task Definition ARN",
            export_name=f"ColdRescue-{environment_name}-TaskDefinitionArn",
        )
