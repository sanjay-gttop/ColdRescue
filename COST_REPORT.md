# ColdRescue V7 — AWS Spend & Cost Architecture Report

**Billing Period:** October 1, 2026 – Present  
**AWS Account ID:** `494110627063` | **Primary Region:** `ap-south-1` (Mumbai)  
**Cost Explorer Verification Date:** October 11, 2026, 19:32 IST  
**MTD Spend (AWS Cost Explorer):** **\$0.00** (`0.0000000003 USD`)

> [!NOTE]
> **AWS Cost Explorer Latency Notice:** AWS Cost Explorer data typically lags real-time usage by 24 to 48 hours. The values below include live measured resource metrics alongside calculated run-rate cost estimates based on official AWS pricing formulas.

---

## 1. Budget Guardrails & Cost Defense Architecture

- **AWS Budget Name:** `ColdRescue-Demo-Budget`
- **Hard Ceiling:** **\$25.00 / month**
- **Proactive Alert Threshold:** **\$20.00 (80%)** via Amazon SNS (`ColdRescue-Alerts-dev`)
- **Total Extra AWS Budget Spent in Development:** **\$0.00** (Strict adherence to Free Tier and zero-idle serverless patterns)

---

## 2. Service-by-Service Architecture & Spend Breakdown

| AWS Service | Architecture Pattern | Deployment Configuration | Measured Live Usage | Est. Unit Cost | Actual Spend |
|---|---|---|---|---|---|
| **Amazon SageMaker AI** | Serverless Inference | 1,024 MB RAM, concurrency 5, `coldrescue-thermal-serverless-v1` | 14 test invocations, ~108 ms warm execution | \$0.000020 / sec | **\$0.00** (< \$0.01) |
| **Amazon ECS Fargate** | Telemetry Fleet Simulator | 0.25 vCPU, 512 MiB RAM, public subnet, **0 NAT Gateways** | `desired_count=0` default (scaled to 1 only during live demo) | \$0.0125 / task-hr | **\$0.00** (\$0.00 idle) |
| **AWS Step Functions** | Distributed Recovery State Machine | Express / Standard workflows (`ColdRescue-IncidentRecovery-dev`) | ~25 state machine executions | 4,000 free / mo | **\$0.00** (Free tier) |
| **AWS Lambda** | Kuhn-Munkres, Ingestion, Safety Authority | 12 functions, 256–512 MB, ARM64/x86 Python 3.12 | ~350 invocations | 1M free / mo | **\$0.00** (Free tier) |
| **Amazon DynamoDB & Streams** | Audit & Idempotency Store | On-Demand (PAY_PER_REQUEST), Stream batch size 10 | ~80 writes, 25 reads | 25 GB free / mo | **\$0.00** (Free tier) |
| **Amazon SQS & DLQ** | Decoupled Ingestion & Poison Isolation | Standard Queues (`ProcessingQueue-dev`, `DLQ-dev`) | ~120 messages buffered & redriven | 1M free / mo | **\$0.00** (Free tier) |
| **AWS IoT Core** | Vehicle Telemetry Ingestion Broker | Topic Rule `ColdRescue_Telemetry_Rule_dev` | ~50 MQTT messages forwarded | 2.25M free / mo | **\$0.00** (Free tier) |
| **Amazon Location Service** | Esri Routing & Truck ETA Calculator | Route Calculator `ColdRescue-RouteCalculator-dev` | ~30 CalculateRoute calls | 10k free / mo | **\$0.00** (Free tier) |
| **Amazon S3 & Glacier IR** | Immutable Audit Log Vault | Transition to `GLACIER_IR` after 30 days | < 50 MB audit logs & model tarballs | 5 GB free / mo | **\$0.00** (Free tier) |
| **AWS X-Ray** | End-to-End Tracing | Active tracing across Lambda, API GW, Step Functions | 19 segments captured per trace, ~250 traces total | 100k free / mo | **\$0.00** (Free tier) |
| **Amazon CloudWatch** | Operations Dashboard & Metric Alarms | 1 dashboard (`ColdRescue-Operations-dev`), 7 custom metrics | Metrics: `ColdRescue/Thermal`, `ColdRescue/Policy`, `ColdRescue/Events` | 10 metrics free | **\$0.00** (Free tier) |
| **AWS Amplify Hosting** | Operator Web Application | App `ColdRescue-Frontend-dev` (`d1pwxznhg8jq0u`) | 18 automated deployments, 93 kB gzip bundle | 1,000 build min free | **\$0.00** (Free tier) |
| **Total Incurred Spend** | | | | | **\$0.00** |

---

## 3. High-Risk Cost Traps Eliminated

1. **NAT Gateway Elimination (\$32/month trap):**  
   Common pitfall in ECS Fargate architectures is provisioning NAT Gateways in private subnets, incurring \$0.045/hour (~ \$32.40/month minimum per AZ) regardless of traffic. ColdRescue provisions Fargate strictly in public subnets with `assign_public_ip=True` and `nat_gateways=0`, achieving **zero hourly networking charges**.
2. **Dedicated SageMaker Instance Trap (\$50–\$150/month trap):**  
   Provisioned real-time endpoints (e.g. `ml.m5.large`) bill continuously 24/7. ColdRescue provisions **Serverless Inference** (`ServerlessConfig` with 1,024 MB and max concurrency 5), billing strictly per millisecond of compute. Idle cost is mathematically **\$0.00**.
3. **Continuous Fargate Worker Run Trap (\$9/month trap):**  
   The simulator stack defaults to `desired_count=0`. Operators scale the fleet to 1 only during live judge demonstrations using `python scripts/start_demo.py` and immediately return to 0 with `python scripts/stop_demo.py` or `python scripts/teardown_demo.py`.
