#!/usr/bin/env python3
"""
Verify live AWS CloudWatch Monitoring & SNS Notifications for Milestone 16.
Validates:
1. SNS Alert Topic: arn:aws:sns:ap-south-1:494110627063:ColdRescue-Alerts-dev
2. CloudWatch Metric Alarm: ColdRescue-Workflow-Failures-dev
3. Publishing test notification to SNS topic
4. Verifying Alarm configuration and state
5. CloudWatch Operations Dashboard existence and configuration
6. Captures real AWS response timestamps, alarm ARNs, and SNS message IDs into data/evidence/live/monitoring_verification.json
"""

import json
import os
import sys
import time
import boto3

REGION = "ap-south-1"
TOPIC_ARN = "arn:aws:sns:ap-south-1:494110627063:ColdRescue-Alerts-dev"
ALARM_NAME = "ColdRescue-Workflow-Failures-dev"
DASHBOARD_NAME = "ColdRescue-Operations-dev"

def run_verification():
    sns_client = boto3.client("sns", region_name=REGION)
    cw_client = boto3.client("cloudwatch", region_name=REGION)

    print(f"Checking SNS Alert Topic: {TOPIC_ARN}...")
    topic_attrs = sns_client.get_topic_attributes(TopicArn=TOPIC_ARN)
    print(f"Topic attributes retrieved successfully: {topic_attrs['Attributes'].get('TopicArn')}")

    # List subscriptions
    subs = sns_client.list_subscriptions_by_topic(TopicArn=TOPIC_ARN)
    sub_list = subs.get("Subscriptions", [])
    print(f"Subscriptions on topic: {len(sub_list)}")
    for s in sub_list:
        print(f" - Subscription: Protocol={s.get('Protocol')}, Endpoint={s.get('Endpoint')}")

    # Publish an operational alert message to verify topic delivery
    alert_msg = {
        "event": "CRITICAL_ALERT",
        "service": "ColdRescue-Monitoring",
        "severity": "HIGH",
        "description": "Live verification of ColdRescue SNS Alert Notification channel",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    print("Publishing operational alert to SNS topic...")
    pub_resp = sns_client.publish(
        TopicArn=TOPIC_ARN,
        Subject="ColdRescue Live Test: System Alert Notification",
        Message=json.dumps(alert_msg, indent=2),
    )
    msg_id = pub_resp.get("MessageId")
    print(f"SNS message published successfully. MessageId: {msg_id}")

    # Verify CloudWatch Metric Alarm
    print(f"\nChecking CloudWatch Alarm: {ALARM_NAME}...")
    alarms_resp = cw_client.describe_alarms(AlarmNames=[ALARM_NAME])
    metric_alarms = alarms_resp.get("MetricAlarms", [])
    assert len(metric_alarms) > 0, f"Alarm {ALARM_NAME} not found"
    alarm = metric_alarms[0]
    print(f"Alarm ARN: {alarm.get('AlarmArn')}")
    print(f"Alarm State: {alarm.get('StateValue')}")
    print(f"Alarm Metric: {alarm.get('MetricName')} in {alarm.get('Namespace')}")
    print(f"Alarm Actions: {alarm.get('AlarmActions')}")
    assert TOPIC_ARN in alarm.get("AlarmActions", []), "SNS Topic is not wired to AlarmActions"

    # Verify CloudWatch Dashboard
    print(f"\nChecking CloudWatch Dashboard: {DASHBOARD_NAME}...")
    dash_resp = cw_client.get_dashboard(DashboardName=DASHBOARD_NAME)
    dashboard_body = json.loads(dash_resp.get("DashboardBody", "{}"))
    widgets_count = len(dashboard_body.get("widgets", []))
    print(f"Dashboard ARN: {dash_resp.get('DashboardArn')}")
    print(f"Dashboard contains {widgets_count} widgets")

    # Save live verification evidence
    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "aws_region": REGION,
        "sns_alert_topic": {
            "arn": TOPIC_ARN,
            "test_message_id": msg_id,
            "subscription_count": len(sub_list),
            "status": "ACTIVE"
        },
        "cloudwatch_alarm": {
            "name": ALARM_NAME,
            "arn": alarm.get("AlarmArn"),
            "state": alarm.get("StateValue"),
            "metric": alarm.get("MetricName"),
            "namespace": alarm.get("Namespace"),
            "alarm_action_wired": TOPIC_ARN in alarm.get("AlarmActions", [])
        },
        "cloudwatch_dashboard": {
            "name": DASHBOARD_NAME,
            "arn": dash_resp.get("DashboardArn"),
            "widget_count": widgets_count
        },
        "overall_status": "VERIFIED_LIVE"
    }

    os.makedirs("data/evidence/live", exist_ok=True)
    evidence_path = "data/evidence/live/monitoring_verification.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print(f"\nLive monitoring verification completed successfully! Evidence saved to {evidence_path}")

if __name__ == "__main__":
    run_verification()
