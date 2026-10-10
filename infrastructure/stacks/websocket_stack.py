"""ColdRescue M15 WebSocket Stack: API Gateway WebSocket API and DynamoDB Connections Table."""
from __future__ import annotations

import os
import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_int,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct


class ColdRescueWebSocketStack(Stack):
    """M15 WebSocket Real-Time Push Stack."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. DynamoDB Table for Active WebSocket Connections
        self.connections_table = dynamodb.Table(
            self,
            "WebSocketConnectionsTable",
            table_name=f"ColdRescue-WebSocketConnections-{environment_name}",
            partition_key=dynamodb.Attribute(
                name="connection_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl_timestamp",
            removal_policy=RemovalPolicy.DESTROY if environment_name == "dev" else RemovalPolicy.RETAIN,
        )

        # 2. Lambda Code Asset
        lambda_code = _lambda.Code.from_asset(
            ".",
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
        )

        layers = []
        layer_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layers", "runtime")
        if os.path.exists(layer_dir):
            runtime_layer = _lambda.LayerVersion(
                self,
                "WebSocketRuntimeLayer",
                code=_lambda.Code.from_asset(layer_dir),
                compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            )
            layers.append(runtime_layer)

        # Lambda Functions
        connect_fn = _lambda.Function(
            self,
            "WsConnectFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="backend.handlers.websocket_handlers.connect_handler",
            code=lambda_code,
            layers=layers,
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={
                "COLDRESCUE_ENV": environment_name,
                "AWS_INTEGRATIONS_ENABLED": "true",
            },
        )

        disconnect_fn = _lambda.Function(
            self,
            "WsDisconnectFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="backend.handlers.websocket_handlers.disconnect_handler",
            code=lambda_code,
            layers=layers,
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={
                "COLDRESCUE_ENV": environment_name,
                "AWS_INTEGRATIONS_ENABLED": "true",
            },
        )

        broadcast_fn = _lambda.Function(
            self,
            "WsBroadcastFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="backend.handlers.websocket_handlers.broadcast_message_handler",
            code=lambda_code,
            layers=layers,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "COLDRESCUE_ENV": environment_name,
                "AWS_INTEGRATIONS_ENABLED": "true",
            },
        )

        # Grant table read/write permissions
        self.connections_table.grant_read_write_data(connect_fn)
        self.connections_table.grant_read_write_data(disconnect_fn)
        self.connections_table.grant_read_write_data(broadcast_fn)

        # 3. WebSocket API Definition
        self.web_socket_api = apigwv2.WebSocketApi(
            self,
            "ColdRescueWebSocketApi",
            api_name=f"ColdRescue-WebSocket-{environment_name}",
            connect_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_int.WebSocketLambdaIntegration(
                    "ConnectIntegration",
                    connect_fn,
                )
            ),
            disconnect_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_int.WebSocketLambdaIntegration(
                    "DisconnectIntegration",
                    disconnect_fn,
                )
            ),
            default_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_int.WebSocketLambdaIntegration(
                    "DefaultIntegration",
                    broadcast_fn,
                )
            ),
        )

        # 4. WebSocket Stage
        self.stage = apigwv2.WebSocketStage(
            self,
            "WebSocketStage",
            web_socket_api=self.web_socket_api,
            stage_name=environment_name,
            auto_deploy=True,
        )

        # Grant broadcast Lambda permissions to post to connections
        api_arn = f"arn:aws:execute-api:{self.region}:{self.account}:{self.web_socket_api.api_id}/{environment_name}/POST/@connections/*"
        broadcast_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[api_arn],
            )
        )
        broadcast_fn.add_environment("WEBSOCKET_ENDPOINT_URL", self.stage.callback_url)

        # Outputs
        CfnOutput(
            self,
            "WebSocketUrlOutput",
            value=self.stage.url,
            description="WebSocket API Endpoint URL",
            export_name=f"ColdRescue-{environment_name}-WebSocketUrl",
        )
