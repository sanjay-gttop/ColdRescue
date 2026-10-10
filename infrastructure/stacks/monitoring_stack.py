"""ColdRescue M16 Monitoring Stack: SNS Notifications, CloudWatch Dashboard, and Alarms."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
)
from constructs import Construct


class ColdRescueMonitoringStack(Stack):
    """M16 Observability and Alerting Stack."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str = "dev",
        notification_email: str = "alerts@coldrescue.io",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. SNS Alert Topic
        self.alert_topic = sns.Topic(
            self,
            "ColdRescueAlertsTopic",
            topic_name=f"ColdRescue-Alerts-{environment_name}",
            display_name=f"ColdRescue Urgent Alerts ({environment_name})",
        )

        # Add email subscription
        self.alert_topic.add_subscription(
            subscriptions.EmailSubscription(notification_email)
        )

        # 2. CloudWatch Metric Alarms
        # Sustained Workflow Execution Failures Alarm
        self.workflow_failure_alarm = cw.Alarm(
            self,
            "WorkflowFailureAlarm",
            alarm_name=f"ColdRescue-Workflow-Failures-{environment_name}",
            alarm_description="Alert when ColdRescue incident recovery state machine executions fail",
            metric=cw.Metric(
                namespace="AWS/States",
                metric_name="ExecutionsFailed",
                dimensions_map={
                    "StateMachineArn": f"arn:aws:states:{self.region}:{self.account}:stateMachine:ColdRescue-IncidentRecovery-{environment_name}"
                },
                period=Duration.minutes(1),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        )

        # Attach SNS Notification Action to Alarm
        self.workflow_failure_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alert_topic)
        )

        # 3. Operational CloudWatch Dashboard
        self.dashboard = cw.Dashboard(
            self,
            "ColdRescueOperationsDashboard",
            dashboard_name=f"ColdRescue-Operations-{environment_name}",
        )

        self.dashboard.add_widgets(
            cw.TextWidget(
                markdown=(
                    "# ColdRescue Cold-Chain Operations Dashboard\n"
                    "Real-time monitoring of power outage detections, thermal risk predictions, "
                    "allocation solvers, SQS/DLQ buffering, and Step Functions workflows."
                ),
                width=24,
                height=2,
            ),
        )

        # Widget row: Step Functions Executions & DLQ Depth
        self.dashboard.add_widgets(
            cw.GraphWidget(
                title="Incident Recovery Workflows",
                left=[
                    cw.Metric(
                        namespace="AWS/States",
                        metric_name="ExecutionsSucceeded",
                        dimensions_map={
                            "StateMachineArn": f"arn:aws:states:{self.region}:{self.account}:stateMachine:ColdRescue-IncidentRecovery-{environment_name}"
                        },
                        statistic="Sum",
                        period=Duration.minutes(1),
                        color=cw.Color.GREEN,
                    ),
                    cw.Metric(
                        namespace="AWS/States",
                        metric_name="ExecutionsFailed",
                        dimensions_map={
                            "StateMachineArn": f"arn:aws:states:{self.region}:{self.account}:stateMachine:ColdRescue-IncidentRecovery-{environment_name}"
                        },
                        statistic="Sum",
                        period=Duration.minutes(1),
                        color=cw.Color.RED,
                    ),
                ],
                width=12,
                height=6,
            ),
            cw.GraphWidget(
                title="Event Buffer & Dead-Letter Queue Depth",
                left=[
                    cw.Metric(
                        namespace="AWS/SQS",
                        metric_name="ApproximateNumberOfMessagesVisible",
                        dimensions_map={"QueueName": f"ColdRescue-ProcessingQueue-{environment_name}"},
                        statistic="Maximum",
                        period=Duration.minutes(1),
                        color=cw.Color.BLUE,
                    ),
                    cw.Metric(
                        namespace="AWS/SQS",
                        metric_name="ApproximateNumberOfMessagesVisible",
                        dimensions_map={"QueueName": f"ColdRescue-DLQ-{environment_name}"},
                        statistic="Maximum",
                        period=Duration.minutes(1),
                        color=cw.Color.RED,
                    ),
                ],
                width=12,
                height=6,
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "AlertTopicArnOutput",
            value=self.alert_topic.topic_arn,
            description="ARN of ColdRescue SNS Alert Topic",
            export_name=f"ColdRescue-{environment_name}-AlertTopicArn",
        )
        CfnOutput(
            self,
            "DashboardNameOutput",
            value=self.dashboard.dashboard_name,
            description="Name of ColdRescue CloudWatch Operations Dashboard",
            export_name=f"ColdRescue-{environment_name}-DashboardName",
        )
