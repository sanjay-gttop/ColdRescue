"""ColdRescue M10 Auth Stack: AWS Cognito User Pool, Client, and RBAC Groups."""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_cognito as cognito,
)
from constructs import Construct


class ColdRescueAuthStack(Stack):
    """M10 Cognito User Pool and Client Stack."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            "ColdRescueUserPool",
            user_pool_name=f"ColdRescue-Users-{environment_name}",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True, username=False),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                fullname=cognito.StandardAttribute(required=False, mutable=True),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
                temp_password_validity=Duration.days(7),
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY if environment_name == "dev" else RemovalPolicy.RETAIN,
        )

        # 2. Cognito User Pool Application Client (Public Web Client, no client secret)
        self.user_pool_client = self.user_pool.add_client(
            "ColdRescueWebClient",
            user_pool_client_name=f"ColdRescue-WebClient-{environment_name}",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True,
            ),
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            prevent_user_existence_errors=True,
        )

        # 3. RBAC Groups (Milestone 11 Roles: OPERATOR, APPROVER, DRIVER, RECEIVER)
        self.operator_group = cognito.CfnUserPoolGroup(
            self,
            "OperatorGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="OPERATOR",
            description="ColdRescue Operators: incident creation, recovery initiation, and allocation review",
            precedence=10,
        )

        self.approver_group = cognito.CfnUserPoolGroup(
            self,
            "ApproverGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="APPROVER",
            description="ColdRescue Approvers: incident recovery approval and policy override decisions",
            precedence=20,
        )

        self.driver_group = cognito.CfnUserPoolGroup(
            self,
            "DriverGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="DRIVER",
            description="ColdRescue Drivers: route dispatch acknowledgement and transit updates",
            precedence=30,
        )

        self.receiver_group = cognito.CfnUserPoolGroup(
            self,
            "ReceiverGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="RECEIVER",
            description="ColdRescue Receivers: facility intake verification and delivery acceptance",
            precedence=40,
        )

        # 4. Outputs
        CfnOutput(
            self,
            "UserPoolIdOutput",
            value=self.user_pool.user_pool_id,
            description="ID of the ColdRescue Cognito User Pool",
            export_name=f"ColdRescue-{environment_name}-UserPoolId",
        )
        CfnOutput(
            self,
            "UserPoolArnOutput",
            value=self.user_pool.user_pool_arn,
            description="ARN of the ColdRescue Cognito User Pool",
            export_name=f"ColdRescue-{environment_name}-UserPoolArn",
        )
        CfnOutput(
            self,
            "UserPoolClientIdOutput",
            value=self.user_pool_client.user_pool_client_id,
            description="ID of the ColdRescue Cognito User Pool Client",
            export_name=f"ColdRescue-{environment_name}-UserPoolClientId",
        )
