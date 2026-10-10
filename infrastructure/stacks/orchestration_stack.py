"""ColdRescue M9 Orchestration Stack: AWS Step Functions, Lambda Tasks, and API Gateway."""
from __future__ import annotations

import os
import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_logs as logs,
    aws_apigateway as apigw,
    aws_iam as iam,
)
from constructs import Construct


class ColdRescueOrchestrationStack(Stack):
    """M9 Step Functions Workflow Orchestrator Stack with Deterministic Safety Policy Branching."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment_name: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Asset exclusions for Lambda code bundle
        lambda_code = _lambda.Code.from_asset(
            ".",
            exclude=[
                ".venv",
                ".venv/**",
                "venv",
                "venv/**",
                "frontend",
                "frontend/**",
                "node_modules",
                "node_modules/**",
                ".git",
                ".git/**",
                "cdk.out",
                "cdk.out/**",
                "__pycache__",
                "**/__pycache__",
                "**/*.pyc",
                ".pytest_cache",
                "**/.pytest_cache/**",
                "tests",
                "tests/**",
                "docs",
                "docs/**",
                "data",
                "data/**",
                "infrastructure/layers",
                "infrastructure/layers/**",
            ],
        )

        # Optional Lambda Runtime Dependencies Layer (if layers directory exists)
        layers = []
        layer_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layers", "runtime")
        if os.path.exists(layer_dir):
            runtime_layer = _lambda.LayerVersion(
                self,
                "RuntimeDependenciesLayer",
                code=_lambda.Code.from_asset(layer_dir),
                compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
                description="ColdRescue Python 3.12 Runtime Dependencies (Pydantic)",
            )
            layers.append(runtime_layer)

        # Helper to create Lambda functions with standard configuration
        def create_handler(fn_id: str, handler_name: str, timeout_sec: int = 30, memory_mb: int = 256) -> _lambda.Function:
            return _lambda.Function(
                self,
                fn_id,
                runtime=_lambda.Runtime.PYTHON_3_12,
                handler=f"backend.handlers.orchestration_handlers.{handler_name}",
                code=lambda_code,
                layers=layers,
                timeout=Duration.seconds(timeout_sec),
                memory_size=memory_mb,
                environment={
                    "COLDRESCUE_ENV": environment_name,
                    "AWS_INTEGRATIONS_ENABLED": "true",
                },
            )

        # 1. Lambda Functions for all M9 lifecycle stages
        ingest_fn = create_handler("IngestValidateFn", "validate_and_ingest_handler", 30, 256)
        predict_fn = create_handler("PredictRiskFn", "predict_thermal_risk_handler", 30, 256)
        routes_fn = create_handler("RetrieveRoutesFn", "retrieve_routes_handler", 30, 256)
        alloc_fn = create_handler("SolveAllocationFn", "solve_allocation_handler", 60, 512)
        policy_fn = create_handler("EvaluatePolicyFn", "evaluate_safety_policy_handler", 30, 256)
        approval_fn = create_handler("HumanApprovalFn", "human_approval_handler", 30, 256)
        driver_fn = create_handler("DriverAckFn", "driver_acknowledgement_handler", 30, 256)
        receiver_fn = create_handler("ReceiverAcceptanceFn", "receiver_acceptance_handler", 30, 256)
        audit_fn = create_handler("FinalizeAuditFn", "finalize_audit_handler", 30, 256)
        failure_fn = create_handler("HandleFailureFn", "handle_failure_handler", 30, 256)

        # Grant DynamoDB permissions for event ingestion and audit finalization
        events_table_arn = f"arn:aws:dynamodb:{self.region}:{self.account}:table/ColdRescue-Events-{environment_name}"
        events_table_policy = iam.PolicyStatement(
            actions=["dynamodb:PutItem", "dynamodb:Query", "dynamodb:GetItem"],
            resources=[events_table_arn, f"{events_table_arn}/index/*"],
        )
        ingest_fn.add_to_role_policy(events_table_policy)
        audit_fn.add_to_role_policy(events_table_policy)
        failure_fn.add_to_role_policy(events_table_policy)

        # Retry policy for transient Lambda execution errors
        lambda_retry_props = {
            "errors": [
                "Lambda.ClientExecutionTimeoutException",
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException",
            ],
            "interval": Duration.seconds(2),
            "max_attempts": 3,
            "backoff_rate": 2.0,
        }

        # 2. Step Functions Task Definitions
        t_ingest = tasks.LambdaInvoke(
            self, "TaskIngestAndValidate",
            lambda_function=ingest_fn,
            result_path="$.ingest_result",
            payload_response_only=True,
        )
        t_ingest.add_retry(**lambda_retry_props)

        t_predict = tasks.LambdaInvoke(
            self, "TaskPredictThermalRisk",
            lambda_function=predict_fn,
            result_path="$.prediction_result",
            payload_response_only=True,
        )
        t_predict.add_retry(**lambda_retry_props)

        t_routes = tasks.LambdaInvoke(
            self, "TaskRetrieveRoutes",
            lambda_function=routes_fn,
            result_path="$.route_result",
            payload_response_only=True,
        )
        t_routes.add_retry(**lambda_retry_props)

        t_alloc = tasks.LambdaInvoke(
            self, "TaskSolveAllocation",
            lambda_function=alloc_fn,
            result_path="$.allocation_result",
            payload_response_only=True,
        )
        t_alloc.add_retry(**lambda_retry_props)

        t_policy = tasks.LambdaInvoke(
            self, "TaskEvaluateSafetyPolicy",
            lambda_function=policy_fn,
            result_path="$.policy_result",
            payload_response_only=True,
        )
        t_policy.add_retry(**lambda_retry_props)

        t_approval = tasks.LambdaInvoke(
            self, "TaskHumanApproval",
            lambda_function=approval_fn,
            result_path="$.approval_result",
            payload_response_only=True,
        )

        t_driver = tasks.LambdaInvoke(
            self, "TaskDriverAcknowledgement",
            lambda_function=driver_fn,
            result_path="$.driver_result",
            payload_response_only=True,
        )

        t_receiver = tasks.LambdaInvoke(
            self, "TaskReceiverAcceptance",
            lambda_function=receiver_fn,
            result_path="$.receiver_result",
            payload_response_only=True,
        )

        t_audit_success = tasks.LambdaInvoke(
            self, "TaskFinalizeAuditSuccess",
            lambda_function=audit_fn,
            result_path="$.audit_result",
            payload_response_only=True,
        )

        t_audit_blocked = tasks.LambdaInvoke(
            self, "TaskFinalizeAuditBlocked",
            lambda_function=audit_fn,
            result_path="$.audit_result",
            payload_response_only=True,
        )

        t_handle_failure = tasks.LambdaInvoke(
            self, "TaskHandleWorkflowFailure",
            lambda_function=failure_fn,
            result_path="$.failure_result",
            payload_response_only=True,
        )

        workflow_failed = sfn.Fail(
            self, "WorkflowFailedState",
            cause="ColdRescue workflow encountered an unrecoverable error or timeout",
            error="WorkflowExecutionFailed",
        )
        t_handle_failure.next(workflow_failed)

        # Catch all task failures to route to failure handler
        for task_item in [t_ingest, t_predict, t_routes, t_alloc, t_policy, t_approval, t_driver, t_receiver, t_audit_success]:
            task_item.add_catch(
                t_handle_failure,
                errors=["States.ALL"],
                result_path="$.workflow_error",
            )

        # 3. State Machine Flow Definition
        # Hard safety policy branch
        policy_blocked_fail = sfn.Fail(
            self, "SafetyPolicyBlockedState",
            cause="Deterministic Safety Policy detected hard safety violation",
            error="POLICY_BLOCKED",
        )
        t_audit_blocked.next(policy_blocked_fail)

        choice_policy = sfn.Choice(self, "ChoicePolicyEvaluation")
        is_blocked = sfn.Condition.string_equals("$.policy_result.policy_status", "POLICY_BLOCKED")
        
        # Approval decision branch
        choice_approval = sfn.Choice(self, "ChoiceApprovalDecision")
        is_approved = sfn.Condition.string_equals("$.approval_result.approval_status", "APPROVED")

        # Wire successful completion chain
        t_receiver.next(t_audit_success)
        t_driver.next(t_receiver)

        choice_approval.when(
            is_approved,
            t_driver,
        ).otherwise(
            t_audit_blocked  # If rejected, finalize audit as blocked/rejected
        )

        t_approval.next(choice_approval)

        choice_policy.when(
            is_blocked,
            t_audit_blocked,
        ).otherwise(
            t_approval
        )

        definition = (
            t_ingest
            .next(t_predict)
            .next(t_routes)
            .next(t_alloc)
            .next(t_policy)
            .next(choice_policy)
        )

        log_group = logs.LogGroup(
            self,
            "StateMachineLogGroup",
            log_group_name=f"/coldrescue/statemachine/{environment_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.state_machine = sfn.StateMachine(
            self,
            "ColdRescueWorkflow",
            state_machine_name=f"ColdRescue-IncidentRecovery-{environment_name}",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.minutes(10),
            logs=sfn.LogOptions(
                destination=log_group,
                level=sfn.LogLevel.ALL,
            ),
        )

        # 4. API Gateway Integration for M9 REST API Entry Point
        api = apigw.RestApi(
            self,
            "ColdRescueApi",
            rest_api_name=f"ColdRescue-API-{environment_name}",
            description="ColdRescue Incident Recovery Orchestration API",
            deploy_options=apigw.StageOptions(stage_name=environment_name),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["*"],
            ),
        )

        # API Gateway execution role to start Step Functions executions
        sfn_exec_role = iam.Role(
            self,
            "ApiGatewayStepFunctionsRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
        )
        self.state_machine.grant_start_execution(sfn_exec_role)
        self.state_machine.grant_read(sfn_exec_role)

        # POST /incidents/recover -> StartExecution integration
        sfn_integration = apigw.AwsIntegration(
            service="states",
            action="StartExecution",
            integration_http_method="POST",
            options=apigw.IntegrationOptions(
                credentials_role=sfn_exec_role,
                request_templates={
                    "application/json": f'{{"stateMachineArn": "{self.state_machine.state_machine_arn}", "input": "$util.escapeJavaScript($input.json(\'$\'))"}}'
                },
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"executionArn": "$util.parseJson($input.json(\'$\')).executionArn", "startDate": "$util.parseJson($input.json(\'$\')).startDate"}'
                        },
                    )
                ],
            ),
        )

        incidents_resource = api.root.add_resource("incidents")
        recover_resource = incidents_resource.add_resource("recover")
        recover_resource.add_method(
            "POST",
            sfn_integration,
            method_responses=[apigw.MethodResponse(status_code="200")],
        )

        # Outputs
        CfnOutput(
            self,
            "StateMachineArnOutput",
            value=self.state_machine.state_machine_arn,
            description="ARN of the ColdRescue Incident Recovery State Machine",
            export_name=f"ColdRescue-{environment_name}-StateMachineArn",
        )
        CfnOutput(
            self,
            "ApiUrlOutput",
            value=api.url,
            description="Base URL of ColdRescue REST API",
            export_name=f"ColdRescue-{environment_name}-ApiUrl",
        )
