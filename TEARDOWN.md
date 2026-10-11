# ColdRescue V7 — Teardown & Cost Containment Guide

This guide documents the exact commands to tear down or scale to zero all billable, active, and demonstration resources provisioned for ColdRescue V7 in AWS Region `ap-south-1`.

---

## 1. Single-Command Automated Teardown

Run the master teardown script from the project root:

```bash
python scripts/teardown_demo.py
```

Optional flags:
* `--dry-run`: Inspect resources that would be deleted without making modifications.
* `--region <region>`: Specify AWS region (defaults to `ap-south-1`).
* `--sagemaker-endpoint <name>`: Specify custom endpoint name (defaults to `coldrescue-thermal-serverless-v1`).

### What It Does:
1. **SageMaker AI**:
   - Deletes SageMaker Serverless Endpoint: `coldrescue-thermal-serverless-v1`
   - Deletes Endpoint Configuration: `coldrescue-thermal-serverless-config-v101`
   - Eliminates all serverless concurrency slots.
2. **ECS Fargate Simulator**:
   - Updates `ColdRescue-SimulatorService-dev` in cluster `ColdRescue-Cluster-dev` to `desiredCount: 0`.
   - Halts all container runtime tasks immediately, dropping compute cost to \$0.00.
3. **DynamoDB Streams Consumer**:
   - Verifies the state of `ColdRescue-StreamConsumer-dev` (read-only consumer, pure pay-per-request).

---

## 2. Manual Fallback Commands (AWS CLI)

If running commands directly in terminal or AWS CloudShell:

### A. SageMaker Endpoint & Config Deletion
```bash
aws sagemaker delete-endpoint \
  --endpoint-name coldrescue-thermal-serverless-v1 \
  --region ap-south-1

aws sagemaker delete-endpoint-config \
  --endpoint-config-name coldrescue-thermal-serverless-config-v101 \
  --region ap-south-1
```

### B. ECS Fargate Scale to 0
```bash
aws ecs update-service \
  --cluster ColdRescue-Cluster-dev \
  --service ColdRescue-SimulatorService-dev \
  --desired-count 0 \
  --region ap-south-1
```

---

## 3. Full CDK Stack Teardown (Optional Complete Purge)

To tear down all deployed CloudFormation stacks:

```bash
# Set PYTHONPATH for CDK app execution
export PYTHONPATH=.

# Destroy application stacks in reverse dependency order
npx cdk destroy ColdRescue-Monitoring-dev --app "python infrastructure/app.py" --force
npx cdk destroy ColdRescue-WebSocket-dev --app "python infrastructure/app.py" --force
npx cdk destroy ColdRescue-Simulator-dev --app "python infrastructure/app.py" --force
npx cdk destroy ColdRescue-EventPipeline-dev --app "python infrastructure/app.py" --force
npx cdk destroy ColdRescue-Orchestration-dev --app "python infrastructure/app.py" --force
npx cdk destroy ColdRescue-Auth-dev --app "python infrastructure/app.py" --force
npx cdk destroy ColdRescue-Foundation-dev --app "python infrastructure/app.py" --force
```

---

## 4. Spend Verification Check

Verify that month-to-date charges have stopped using AWS Cost Explorer:

```bash
python -c "
import boto3, datetime
ce = boto3.client('ce', region_name='us-east-1')
today = datetime.date.today()
resp = ce.get_cost_and_usage(
    TimePeriod={'Start': today.replace(day=1).isoformat(), 'End': (today + datetime.timedelta(days=1)).isoformat()},
    Granularity='MONTHLY',
    Metrics=['UnblendedCost']
)
print('MTD Spend:', resp['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'], 'USD')
"
```
