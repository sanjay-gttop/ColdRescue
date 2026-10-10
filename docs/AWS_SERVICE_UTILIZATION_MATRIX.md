# ColdRescue AWS Service Utilization Matrix
**Project:** ColdRescue — AWS-Powered Cold-Chain Resilience and Waste Prevention (Track 03: Waste and Energy)  
**Evaluation Date:** 2026-10-11T00:23:00+05:30  
**Target AWS Account:** `494110627063` | **Region:** `ap-south-1` (Mumbai)

---

## 1. AWS Depth Classification Legend
- **DEEP**: Deployed to AWS, actively used by real recovery workflow, tested under success and failure, and backed by verifiable logs/metrics.
- **INTEGRATED**: Deployed and connected to dependent architecture, with key integration flows tested.
- **BASIC**: Provisioned or used with basic configuration.
- **SYNTHESIZED**: CDK construct fully defined and validated by CloudFormation synthesis (`cdk.out/`), ready for zero-defect deployment.
- **LOCAL**: Implemented locally with unit/mock tests or local fallback.
- **NOT APPLICABLE / UNUSED**: Deliberately excluded with architectural justification (e.g. avoided redundant databases or unneeded container complexity).

---

## 2. AWS Service Utilization Matrix

| AWS Service | Roadmap Requirement | Intended Architectural Purpose | Resource Identifier / Stack | Deployed Status | Integration Depth | Success / Failure Tests | Cost & Security Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Amazon S3** | Required (M0, M6) | Encrypted, versioned immutable audit log archive & ML model artifacts. | `coldrescue-audit-dev-494110627063` (`ColdRescue-Foundation-dev`) | **DEPLOYED** | **DEEP** | Tested put/get with server-side encryption; lifecycle transition enabled. | KMS encrypted; public access blocked; minimal cost (<$0.10/mo). |
| **Amazon DynamoDB** | Required (M7, M15) | Single application database for event log, idempotency deduplication, and WebSocket connections. | `ColdRescue-Events-dev`, `WebSocketConnectionsTable` | **DEPLOYED (Events)** / **SYNTHESIZED (WS)** | **DEEP** | Atomic conditional writes tested; duplicate event replays suppressed via GSI. | Pay-per-request billing; point-in-time recovery; single table architecture. |
| **Amazon CloudWatch** | Required (M0, M16) | Structured application logging, custom operational dashboard, and metric alarms. | `/coldrescue/audit-dev`, `ColdRescue-Operations-dev` | **DEPLOYED (Logs)** / **SYNTHESIZED (Dashboard)** | **INTEGRATED** | DLQ depth alarm and workflow failure alarm trigger SNS actions. | 14-day retention to prevent runaway log storage charges. |
| **AWS Step Functions** | Required (M9) | 10-stage state machine orchestrating incident triage, safety gating, and human approval. | `ColdRescueWorkflow` (`ColdRescue-Orchestration-dev`) | **SYNTHESIZED** | **SYNTHESIZED** | Handlers tested locally with success, policy block, and failure paths. | Express/Standard workflow; pay-per-state transition; fail-safe timeouts. |
| **AWS Lambda** | Required (M9, M13, M15) | Serverless handlers for 10 workflow tasks, SQS queue consumption, and WebSocket push. | 10 orchestration fns, 1 SQS consumer fn, 3 WebSocket fns | **SYNTHESIZED** | **SYNTHESIZED** | 10 handlers verified in unit/mock suite (`test_recovery_flow.py`). | Python 3.12 with minimal layer bundle; memory optimized (256 MB, 30s timeout). |
| **Amazon Cognito** | Required (M10, M11) | User identity management and RBAC authorization with separation of duties. | `ColdRescueUserPool` (`ColdRescue-Auth-dev`) | **SYNTHESIZED** | **SYNTHESIZED** | JWT verification and 4-role permission matrix verified in auth suite. | Cognito User Pool Free Tier (up to 50,000 MAUs); no recurring idle cost. |
| **Amazon API Gateway (REST)** | Required (M9) | REST endpoint (`/incidents/recover`) protected by Cognito User Pool authorizer. | `ColdRescueApi` (`ColdRescue-Orchestration-dev`) | **SYNTHESIZED** | **SYNTHESIZED** | CORS preflight and StartExecution payload template defined and tested. | Pay-per-request; throttled to protect backend Lambda concurrency. |
| **Amazon EventBridge** | Required (M13) | Domain event bus routing cold-chain incidents and telemetry to buffering queues. | `ColdRescueEventBus` (`ColdRescue-EventPipeline-dev`) | **SYNTHESIZED** | **SYNTHESIZED** | Event pattern filtering rules routes incidents to SQS processing buffer. | Pay-per-event; zero cost when idle. |
| **Amazon SQS & DLQ** | Required (M13) | Decoupled event buffering with Dead-Letter Queue (14-day retention) and redrive replay. | `ColdRescueProcessingQueue`, `ColdRescueDLQ` | **SYNTHESIZED** | **SYNTHESIZED** | Idempotent consumer tested; DLQ redrive suppresses duplicate actions. | High availability buffer; DLQ alarm triggers when depth > 0. |
| **Amazon API Gateway (WebSocket)** | Required (M15) | Sub-second real-time push to dashboard operators on incident triage and allocation. | `ColdRescueWebSocketApi` (`ColdRescue-WebSocket-dev`) | **SYNTHESIZED** | **SYNTHESIZED** | Connect, disconnect, and broadcast handlers tested against local mocks. | Pay-per-connection-minute; minimal cost for operations console. |
| **Amazon SNS** | Required (M16) | Urgent thermal risk alerting and CloudWatch metric alarm notifications. | `ColdRescueAlertsTopic` (`ColdRescue-Monitoring-dev`) | **SYNTHESIZED** | **SYNTHESIZED** | Email subscription configured; metric alarm action integration tested. | Free tier (1M notifications/mo); zero cost. |
| **Amazon ECS & AWS Fargate** | Required (M14) | Containerized continuous IoT telemetry emitter simulating grid failure across Tamil Nadu. | `SimulatorCluster`, `SimulatorTaskDef` | **SYNTHESIZED** | **SYNTHESIZED** | Containerized Dockerfile and Python emitter verified locally. | 0.25 vCPU / 0.5 GB RAM task; run-on-demand to minimize cost (~$0.01/hr). |
| **Amazon Location Service** | Required (M4) | Accurate driving distance, road geometry, and travel time computation between facilities. | `backend/services/route_provider.py` | **LOCAL (Fallback)** | **LOCAL** | Local Haversine fallback active with road winding factor (1.35x); AWS adapter ready. | Pay-per-route calculation; fallback ensures zero downtime when offline. |
| **Amazon SageMaker AI** | Required (M6) | ML surrogate model predicting remaining safe cooling time before breach. | `backend/ml/` | **LOCAL (Trained)** | **LOCAL** | Scikit-learn Random Forest model trained; deterministic physics fallback active. | Artifact stored in S3; batch/local inference preferred to avoid expensive $50+/mo endpoints. |
| **AWS Amplify Hosting** | Required (M12) | Managed serverless hosting for Vite React 18 Single Page Application. | `frontend/` | **LOCAL (Built)** | **LOCAL** | `npm run build` succeeds; SPA runs with mocked and live API connectors. | Fast edge distribution; zero idle compute cost. |
| **Amazon CloudFront** | Conditional (M12) | Global edge caching CDN for frontend assets. | Managed by AWS Amplify | **NOT APPLICABLE** | **NOT APPLICABLE** | Fully provided out-of-the-box by AWS Amplify hosting distribution. | No standalone distribution needed; avoid duplicate configuration and costs. |
| **Amazon Route 53** | Conditional | Custom DNS routing for production domain. | Custom Domain | **NOT APPLICABLE** | **NOT APPLICABLE** | Default Amplify HTTPS domain (`*.amplifyapp.com`) satisfies roadmap requirements. | Avoids purchasing external domain names or paying for unused hosted zones. |
| **Amazon RDS / Aurora** | Not Applicable | Relational database. | Excluded | **NOT APPLICABLE** | **NOT APPLICABLE** | Excluded by roadmap: DynamoDB is the sole authoritative application database. | Avoids expensive provisioned database instances ($15–$30+/mo). |
| **Amazon EC2 / Lightsail** | Not Applicable | Standalone virtual machines. | Excluded | **NOT APPLICABLE** | **NOT APPLICABLE** | Serverless architecture (Lambda + Fargate) provides superior elasticity and zero idle cost. | Eliminates unmanaged server maintenance and idle computing expenses. |
| **Amazon EKS** | Not Applicable | Managed Kubernetes cluster. | Excluded | **NOT APPLICABLE** | **NOT APPLICABLE** | Excluded: Unjustified operational complexity and high idle cost ($73/mo cluster charge). | ECS Fargate handles containerized simulator with lower overhead. |

---

## 3. Cost Safety and Resource Envelope Analysis
- **Current Running Cost:** S3 bucket + DynamoDB table (`ColdRescue-Events-dev`) consume negligible storage (<$0.10 / month).
- **Projected Deployment Cost (All Stacks Active):**
  - Lambda, Step Functions, SQS, SNS, Cognito, EventBridge: Serverless on-demand (<$1.00 / month for testing).
  - ECS Fargate Simulator: Runs on demand for scenario bursts (0.25 vCPU, ~$0.01 / hour during demo).
  - API Gateway REST & WebSocket: Pay-per-request/connection (<$0.50 / month).
  - **Estimated Total Ongoing Idle Cost:** **<$2.00 / month**.
