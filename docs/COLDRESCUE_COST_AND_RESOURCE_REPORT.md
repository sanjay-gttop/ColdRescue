# ColdRescue Cost and Resource Report
**Project:** ColdRescue — AWS-Powered Cold-Chain Resilience and Waste Prevention (Track 03: Waste and Energy)  
**Report Date:** 2026-10-11T00:50:00+05:30  
**Target AWS Account:** `<AWS_ACCOUNT_ID>` | **Region:** `ap-south-1` (Mumbai)

---

## 1. Actual Deployed AWS Resource Inventory (Live in ap-south-1)

| Resource Identifier | AWS Service | CloudFormation Stack | Current State | Monthly Cost Impact |
| :--- | :--- | :--- | :--- | :--- |
| `coldrescue-audit-dev-<AWS_ACCOUNT_ID>` | Amazon S3 | `ColdRescue-Foundation-dev` | Deployed (KMS encrypted) | <$0.05 / mo |
| `/coldrescue/audit-dev` | Amazon CloudWatch Logs | `ColdRescue-Foundation-dev` | Deployed (14d retention) | <$0.05 / mo |
| `ColdRescue-Events-dev` | Amazon DynamoDB | `ColdRescue-Events-dev` | Deployed (PAY_PER_REQUEST) | <$0.10 / mo |
| **Total Current Running Cost** | | | | **~$0.20 / month** |

---

## 2. Projected Incremental Cost for Full Deployment (All 6 Application Stacks)

| Resource / Stack | Service | Configuration / Sizing | Pricing Basis | Estimated Monthly Cost |
| :--- | :--- | :--- | :--- | :--- |
| `ColdRescue-Auth-dev` | Amazon Cognito | 1 User Pool, 1 App Client, 4 Groups | Free Tier (first 50,000 MAUs free) | **$0.00** |
| `ColdRescue-Orchestration-dev` | Step Functions & Lambda | 10 Lambda functions (256 MB, 30s timeout), 1 State Machine | Pay-per-execution / State transition | **<$0.50** |
| `ColdRescue-EventPipeline-dev` | EventBridge & SQS | 1 Custom Bus, 1 Queue, 1 DLQ (14-day retention) | Pay-per-event / SQS requests (1M free) | **<$0.10** |
| `ColdRescue-WebSocket-dev` | API Gateway V2 WebSocket | 1 WebSocket API, 1 DynamoDB Connections Table | $0.25 / million connection-minutes | **<$0.30** |
| `ColdRescue-Monitoring-dev` | CloudWatch & SNS | 1 Operations Dashboard, 2 Metric Alarms, 1 SNS Topic | 2 free alarms, $3/dashboard, 1M free SNS | **~$3.00** |
| `ColdRescue-Simulator-dev` | ECS / Fargate | 1 Task Def (0.25 vCPU, 0.5 GB RAM), VPC (2 public subnets) | Run on-demand ($0.012 / task-hour) | **<$0.50** (demo bursts) |
| **Total Projected Running Cost** | | | | **~$4.40 / month** |

---

## 3. Cost-Optimization & Safety Guardrails Implemented
1. **No Expensive Idle Provisioned Instances:**
   - Excluded Amazon RDS / Aurora instances (~$25–$50/mo minimum). DynamoDB is the sole application database.
   - Excluded Amazon EKS clusters ($73/mo cluster fee). ECS Fargate is used for serverless container execution on demand.
   - Excluded standalone EC2 virtual machines.
2. **NAT Gateway Avoidance:**
   - Simulator VPC uses public subnets with direct Internet Gateway rather than a NAT Gateway ($32.85/mo per AZ saved).
3. **Log Retention Limits:**
   - CloudWatch log groups are capped at 14 days retention to prevent indefinite accumulation of log storage charges.
4. **On-Demand Capacity:**
   - DynamoDB tables use `PAY_PER_REQUEST` billing mode, avoiding fixed provisioned read/write capacity charges.

---

## 4. Teardown Strategy
When testing or demonstrations are completed, all application stacks can be destroyed cleanly without affecting persistent audit records:
```powershell
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy ColdRescue-Simulator-dev ColdRescue-Monitoring-dev ColdRescue-WebSocket-dev ColdRescue-EventPipeline-dev ColdRescue-Orchestration-dev ColdRescue-Auth-dev --force
```
Persistent S3 audit buckets and DynamoDB event history remain protected against accidental deletion.
