# ColdRescue Deployment & Resource Cleanup Runbook
**Target Environment:** AWS Account `494110627063` | Region `ap-south-1` (Mumbai)  
**CDK App Root:** `c:\Users\SANJAY M.S\OneDrive\Documents\ColdRescue`

---

## 1. Prerequisites & Environment Setup

Ensure the active AWS identity has deployment permissions in `ap-south-1`:
```powershell
# Verify AWS credentials
aws sts get-caller-identity
aws configure get region

# Set environment variables for CDK
$env:PYTHONPATH="."
```

---

## 2. Sequential Stack Deployment Procedure

Deploy the stacks strictly in order of their CloudFormation export/import dependencies:

### Step 1: Deploy Auth Stack (`ColdRescue-Auth-dev`)
Provisions Cognito User Pool, App Client, and RBAC groups (`OPERATOR`, `APPROVER`, `DRIVER`, `RECEIVER`):
```powershell
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Auth-dev
```

### Step 2: Deploy Orchestration Stack (`ColdRescue-Orchestration-dev`)
Provisions 10 Lambda functions, Step Functions State Machine, and REST API Gateway:
```powershell
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Orchestration-dev
```

### Step 3: Deploy Event Pipeline Stack (`ColdRescue-EventPipeline-dev`)
Provisions EventBridge custom bus, SQS processing buffer, Dead-Letter Queue (DLQ), and idempotent consumer:
```powershell
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-EventPipeline-dev
```

### Step 4: Deploy WebSocket Real-Time Push Stack (`ColdRescue-WebSocket-dev`)
Provisions API Gateway V2 WebSocket, DynamoDB connection table, and broadcast handlers:
```powershell
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-WebSocket-dev
```

### Step 5: Deploy Monitoring & Operations Stack (`ColdRescue-Monitoring-dev`)
Provisions SNS alert topic, CloudWatch operations dashboard, and metric alarms:
```powershell
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Monitoring-dev
```

### Step 6: Deploy Telemetry Simulator Stack (`ColdRescue-Simulator-dev`)
Provisions ECS Cluster, VPC, and Fargate task definition for continuous Tamil Nadu corridor IoT simulation:
```powershell
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Simulator-dev
```

---

## 3. Post-Deployment Live Verification

After deployment, run the end-to-end cloud probe script:
```powershell
& .venv\Scripts\python.exe scripts/verify_deployment_readiness.py
```

---

## 4. Teardown & Resource Cleanup Runbook

To prevent recurring charges, decommission deployed resources in reverse dependency order:

```powershell
# 1. Terminate running ECS Fargate tasks
aws ecs list-tasks --cluster ColdRescue-Simulator-dev-Cluster --region ap-south-1

# 2. Destroy application stacks in reverse order
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy ColdRescue-Simulator-dev --force
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy ColdRescue-Monitoring-dev --force
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy ColdRescue-WebSocket-dev --force
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy ColdRescue-EventPipeline-dev --force
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy ColdRescue-Orchestration-dev --force
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy ColdRescue-Auth-dev --force

# Note: ColdRescue-Foundation-dev and ColdRescue-Events-dev retain persistent audit logs and data tables.
```
