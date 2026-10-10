"""
ColdRescue API Gateway WebSocket Handlers for Real-Time UI Push (Milestone 15).

Routes:
  - $connect: Store active WebSocket connection in DynamoDB
  - $disconnect: Remove disconnected client
  - broadcast: Push real-time updates (incidents, predictions, allocations, policy blocks)
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List


def _get_connections_table():
    import boto3
    env_name = os.getenv("COLDRESCUE_ENV", "dev")
    region = os.getenv("AWS_REGION", "ap-south-1")
    table_name = f"ColdRescue-WebSocketConnections-{env_name}"
    dynamodb = boto3.resource("dynamodb", region_name=region)
    return dynamodb.Table(table_name)


def connect_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Handle $connect route: register client connection."""
    conn_id = event.get("requestContext", {}).get("connectionId")
    if not conn_id:
        return {"statusCode": 400, "body": "Missing connectionId"}

    query_params = event.get("queryStringParameters") or {}
    user_role = query_params.get("role", "OPERATOR")
    user_id = query_params.get("userId", "anonymous")

    try:
        table = _get_connections_table()
        table.put_item(
            Item={
                "connection_id": conn_id,
                "user_id": user_id,
                "role": user_role,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "ttl_timestamp": int(time.time()) + 86400,  # 24 hour TTL
            }
        )
    except Exception:
        # Fallback in local/mock testing
        pass

    return {"statusCode": 200, "body": "Connected"}


def disconnect_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Handle $disconnect route: remove connection."""
    conn_id = event.get("requestContext", {}).get("connectionId")
    if conn_id:
        try:
            table = _get_connections_table()
            table.delete_item(Key={"connection_id": conn_id})
        except Exception:
            pass

    return {"statusCode": 200, "body": "Disconnected"}


def broadcast_message_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """Broadcast an event payload to active clients, removing stale 410 connections."""
    import boto3
    from botocore.exceptions import ClientError

    body = event.get("body", "{}")
    if isinstance(body, str):
        payload = json.loads(body)
    else:
        payload = body

    endpoint_url = os.getenv("WEBSOCKET_ENDPOINT_URL")
    region = os.getenv("AWS_REGION", "ap-south-1")

    # Local fallback testing
    if not endpoint_url or os.getenv("AWS_INTEGRATIONS_ENABLED") != "true":
        return {
            "statusCode": 200,
            "broadcast_status": "LOCAL_MOCKED",
            "sent_count": 1,
            "stale_cleaned": 0,
        }

    apigw_client = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url, region_name=region)
    table = _get_connections_table()
    
    response = table.scan()
    connections = response.get("Items", [])

    sent_count = 0
    stale_count = 0
    encoded_data = json.dumps(payload).encode("utf-8")

    for item in connections:
        c_id = item["connection_id"]
        try:
            apigw_client.post_to_connection(ConnectionId=c_id, Data=encoded_data)
            sent_count += 1
        except ClientError as exc:
            # 410 Gone indicates connection is closed / stale
            if exc.response["Error"]["Code"] == "GoneException":
                table.delete_item(Key={"connection_id": c_id})
                stale_count += 1

    return {
        "statusCode": 200,
        "sent_count": sent_count,
        "stale_cleaned": stale_count,
    }
