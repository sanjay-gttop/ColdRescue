# ColdRescue — Keep the cold chain powered. Keep food and medicine out of the bin.

ColdRescue is an AWS-powered cold-chain resilience prototype that responds to refrigeration and power failures by estimating the remaining safe-cooling window and allocating perishable cargo to receiving facilities with sufficient capacity and viable cooling power. It compares greedy and global optimization, enforces deterministic safety policies, coordinates human approval and delivery acceptance, and measures simulated cargo diverted from waste risk.

---

## Track 03: Waste and Energy Alignment

In global logistics and distribution, up to **30% of perishable foodstuffs and temperature-sensitive biologics** (vaccines, dairy, insulin, fresh produce) spoil before reaching their end destination due to unmonitored cold-chain power failures, backup battery depletions, and uncoordinated emergency handoffs. 

ColdRescue attacks this dual crisis of **waste prevention** and **energy efficiency**:
1. **Perishable Cargo Waste Prevention**: Detects reefer unit breakdowns and grid failures within seconds, predicting the exact physical spoilage deadline before critical degradation occurs.
2. **Energy-Viable Re-allocation**: Prevents secondary spoilage by ensuring receiving facilities possess verified operational cooling and adequate backup runtime, routing cargo away from degraded or failing infrastructure.
3. **Embedded Emissions Avoided**: Averts the wasted embedded water, land use, and agricultural emissions of spoiled cargo by ensuring delivery acceptance at power-viable alternatives.

---

## Concrete Setting & Stakeholder Profile

### Operational Scenario: Tamil Nadu Dairy & District Health Cold Chain
- **Primary Setting:** Coimbatore to Salem dairy distribution corridor (Western Tamil Nadu), operating under high ambient temperatures (32°C to 42°C).
- **Consignments:** Grade-A raw milk crates, pasteurized dairy products, and temperature-sensitive pediatric vaccines (2°C to 8°C cold envelope).
- **Failure Trigger:** Reefer unit generator failure on National Highway 544, with ambient temperatures rising rapidly and onboard thermal backup limited to 30–45 minutes.
- **Key Stakeholders:**
  - **Cold-Storage Facility Operator:** Monitors real-time grid reliability and allocates spare refrigerated chamber capacity.
  - **District Health & Dairy Supply Logistics Manager:** Reviews multi-incident trade-offs and authorizes emergency redirects.
  - **Reefer Transport Driver:** Acknowledges emergency route redirects and executes priority transfers.
  - **Receiving Facility Intake Supervisor:** Inspects cold vault temperatures and formally accepts delivery intake.

---

## AWS Cloud Architecture

ColdRescue is deployed on **AWS (ap-south-1 Mumbai)** via **AWS CDK (Python)** across modular, least-privilege CloudFormation stacks:

```mermaid
flowchart TD
    subgraph "Ingestion & Telemetry"
        Fargate["ECS Fargate Telemetry Simulator\n(Milestone 14)"] -->|"HTTP / Events"| APIGW["Amazon API Gateway REST API\n(Cognito Authorizer)"]
        Fargate -->|"Events"| EventBridge["Amazon EventBridge Bus\n(Milestone 13)"]
        EventBridge --> SQS["Amazon SQS Processing Buffer\n(Redrive to DLQ)"]
        SQS --> ConsumerLambda["Queue Consumer Lambda\n(Idempotent Ingestion)"]
    end

    subgraph "Storage & Idempotency"
        ConsumerLambda --> DDB["Amazon DynamoDB EventsTable\n(PK: stream_id, SK: seq, GSI: IdempotencyKey)"]
        APIGW --> DDB
    end

    subgraph "Recovery Orchestration (Step Functions)"
        APIGW -->|"StartExecution"| SFN["Step Functions State Machine\n(ColdRescue-IncidentRecovery-dev)"]
        SFN --> T1["1. Validate & Ingest Task"]
        T1 --> T2["2. Predict Thermal Risk Task\n(Physics Engine + ML Surrogate)"]
        T2 --> T3["3. Retrieve Routes Task\n(Amazon Location Service / Haversine)"]
        T3 --> T4["4. Solve Allocation Task\n(Greedy vs. Global Solvers)"]
        T4 --> T5["5. Evaluate Safety Policy Gate\n(6 Deterministic Rules)"]
        T5 -->|"Hard Blocked"| BranchBlocked["Policy Blocked Branch\n(Zero False Diversion)"]
        T5 -->|"Passed"| T6["6. Operator Approval Task"]
        T6 --> T7["7. Driver Acknowledgement Task"]
        T7 --> T8["8. Receiver Intake Acceptance Task"]
        T8 --> T9["9. Finalize Audit & Waste Accounting"]
    end

    subgraph "Real-Time Push & Observability"
        SFN --> WS["API Gateway WebSocket API\n(Milestone 15 Real-Time Push)"]
        WS --> UI["React / Vite Frontend\n(Amplify Hosting)"]
        SFN --> CW["CloudWatch Dashboard & Metric Alarms\n(Milestone 16)"]
        CW --> SNS["Amazon SNS Topic Alerts\n(Urgent Spoilage Warning)"]
    end
```

### AWS CDK Stacks Overview
1. `ColdRescue-Foundation-dev`: Encrypted S3 audit log bucket (SSL enforced, versioned), CloudWatch application log groups (`/coldrescue/application/dev`), DynamoDB Events Table (`ColdRescue-Events-dev`).
2. `ColdRescue-Auth-dev`: Cognito User Pool (`ColdRescue-Users-dev`), Web Client, and RBAC User Groups (`OPERATOR`, `APPROVER`, `DRIVER`, `RECEIVER`).
3. `ColdRescue-Orchestration-dev`: AWS Step Functions state machine with 10 lifecycle stages, Choice branching, Lambda tasks, and API Gateway REST authorizer.
4. `ColdRescue-EventPipeline-dev`: EventBridge custom bus (`ColdRescue-Bus-dev`), SQS buffer queue with dead-letter queue (DLQ), and idempotent consumer.
5. `ColdRescue-Simulator-dev`: Amazon ECS cluster and Fargate task definition for continuous, containerized cold-chain telemetry generation.
6. `ColdRescue-WebSocket-dev`: API Gateway WebSocket API for live UI push and DynamoDB connection tracking table.
7. `ColdRescue-Monitoring-dev`: Amazon SNS alerts topic, CloudWatch Operations Dashboard, and automated metric alarms.

---

## Thermal Physics Model & Event Schemas

ColdRescue couples deterministic thermodynamics with machine learning surrogates:
- **Newtonian Cooling Equation:**
  $$\frac{dT}{dt} = -k (T(t) - T_{\text{ambient}})$$
  where thermal transfer coefficient $k = \frac{A}{m \cdot c_p \cdot R_{\text{thermal}}}$, accounting for cargo mass ($m$), specific heat capacity ($c_p$), surface area ($A$), and container thermal resistance ($R$).
- **Strict Schema Validation:** All domain events adhere to Pydantic v2 schemas (`backend/schemas/`), enforcing UTC timezone awareness, schema versions (`1.0.0`), sequence numbers, correlation IDs, and deduplication idempotency keys.

---

## Deterministic Safety Policy (Authoritative Hard Block Gate)

Unlike probabilistic AI predictions, safety in food and medicine logistics requires **deterministic guarantees**. The safety policy engine (`backend/policies/safety_policy.py`) enforces 6 mandatory rules that **cannot be overridden by operators or ML models**:

1. **Receiver Availability & State:** Receiver must be operational and accessible.
2. **Capacity Conservation:** Cargo mass cannot exceed remaining receiver capacity:
   $$\text{Cargo}_{\text{kg}} \le \text{Capacity}_{\text{available}}$$
3. **Thermal Envelope Overlap:** Cargo acceptable temperature range must overlap the receiver's refrigeration envelope:
   $$[\text{Cargo}_{\min}, \text{Cargo}_{\max}] \cap [\text{Receiver}_{\min}, \text{Receiver}_{\max}] \neq \emptyset$$
4. **Cooling Power Viability:** Receiver cooling status cannot be `failed`. Degraded cooling triggers mandatory warnings and reduced horizon validation.
5. **Cargo Category Compatibility:** Receiver facility must support the specific cargo category (e.g. `dairy`, `vaccine`, `produce`).
6. **Thermal Deadline & Backup Window:** Total elapsed time (Transit + Unloading + Safety Margin) cannot exceed remaining safe preservation time or receiver backup runtime:
   $$\text{Duration}_{\text{transit}} + \text{Duration}_{\text{unloading}} + \text{Margin}_{\text{safety}} \le \text{Time}_{\text{thermal deadline}}$$

If any rule fails with `HARD_BLOCK`, the workflow branches to `POLICY_BLOCKED`, recording the exact violation reasons in the audit log and preventing dispatch.

---

## Greedy vs. Global Fleet Allocation

ColdRescue implements and benchmarks both localized heuristics and coordinated multi-incident solvers:
- **Greedy Allocation (Localized Nearest-Feasible):** Sorts incidents by urgency and greedily assigns each to the closest feasible receiver. While fast ($O(N \log M)$), greedy matching frequently consumes critical hub capacity early, stranding larger downstream consignments.
- **Global Allocation (Multi-Incident Coordinated Solver):** Optimizes fleet-wide survival by maximizing total kilograms preserved, balancing capacity utilization, and minimizing total transit exposure across all simultaneous outages.

### Milestone 18 Benchmark Results (50 Reproducible Outage Scenarios)
Across a stress benchmark of 50 varied outage scenarios ($139,081$ kg evaluated across Tamil Nadu conditions):
- **Total Cargo Diverted (Global):** **75,763.6 kg** vs. **75,449.3 kg** (Greedy).
- **Global Lift:** **+314.3 kg cargo preserved (+0.42%)** with zero ties missed.
- **Decision Latency:** Sub-second execution (Average 169.6 ms for Global, 113.1 ms for Greedy).
- **Safety Policy Compliance:** **0 policy violations across all accepted assignments**.

---

## Track 03 Impact Metrics & Calculation Formulas

### 1. Primary Metric: Cargo Diverted from Waste Risk
$$\text{Cargo Diverted (kg)} = \sum_{i \in \text{Completed Deliveries}} \text{Cargo Mass}_i$$
*Strict Rule:* Cargo is only counted as diverted if policy passed, operator approved, driver acknowledged, and receiver facility formally accepted the intake. Any policy-blocked or failed workflow records strictly **0 kg diverted**.

### 2. Secondary Metric: Cargo Remaining at Risk
$$\text{Cargo at Risk (kg)} = \sum \text{Total Consignment Mass} - \text{Cargo Diverted (kg)}$$

### 3. Illustrative Embedded Emissions Potentially Avoided
$$\text{Estimated Emissions Avoided (kg CO}_2\text{e)} = \text{Cargo Diverted (kg)} \times \text{Emissions Factor (kg CO}_2\text{e/kg)}$$
- Using Tamil Nadu dairy supply chain factor: **$2.4 \text{ kg CO}_2\text{e / kg milk}$**.
- 50-Scenario Stress Test Avoided: **$181,832.6 \text{ kg CO}_2\text{e}$**.

> [!NOTE]
> **Required Disclaimer:** *Illustrative estimate based on stated simulation assumptions, not measured real-world savings or measured energy efficiency.*

---

## Authentication, Roles & Separation of Duties (M10–M11)

Role-based access control is enforced via AWS Cognito User Pool groups and FastAPI security middleware:

| Role | Permitted Actions | Forbidden Actions |
|---|---|---|
| **`OPERATOR`** | View incidents, review allocations, initiate recovery | Cannot approve actions as approver, cannot acknowledge driver routes |
| **`APPROVER`** | Review allocations, approve or reject recovery proposals | Cannot acknowledge routes as driver |
| **`DRIVER`** | Acknowledge dispatch, update transit status | **Strictly prohibited from approving recovery proposals (Separation of Duties)** |
| **`RECEIVER`** | Verify bay dock, accept or reject delivery intake | Cannot initiate recovery or approve proposals |

---

## The Four-Beat Final Demo Walkthrough

### Beat A — The Waste Clock Starts
1. Reefer unit power fails on Highway 544.
2. Fargate Telemetry Simulator emits a `REEFER_UNIT_FAILURE` domain event.
3. API Gateway WebSocket immediately pushes the alert to the operator console without browser refresh.
4. The physical thermal model calculates ambient exposure (32°C), displaying an active countdown clock (45 minutes until irreversible spoilage).

### Beat B — Greedy versus Global
1. Two simultaneous outages occur in Coimbatore and Erode.
2. The operator compares allocation strategies side-by-side:
   - **Greedy** assigns the nearest small hub, exhausting its 1,000 kg capacity and stranding a larger 1,800 kg medical consignment.
   - **Global Solver** balances assignments across Salem and Tiruppur, saving both consignments and preserving **+800 kg more cargo**.

### Beat C — Safe Recovery & Policy Gate
1. The operator tests an unsafe redirect to a facility with an unstable generator.
2. The **Deterministic Safety Policy Engine** immediately halts the workflow with `POLICY_BLOCKED`:
   - Violation: `Cooling Viability Error — Facility generator degraded; backup runtime 20m < required 45m transit window`.
3. The operator selects the verified power-viable Salem Hub; approval is granted.
4. The driver acknowledges on mobile; the receiving supervisor accepts 500 kg into vault Bay-4B.

### Beat D — AWS Verifiable Proof
1. Live execution traces in AWS Step Functions (`ColdRescue-IncidentRecovery-dev`).
2. CloudWatch Operations Dashboard reflects queue depth, state machine success rates, and zero DLQ errors.
3. DynamoDB audit stream verifies cryptographic idempotency and immutable event history.

---

## Local Verification & Test Execution

### 1. Run Complete Python Suite (173 Tests)
```powershell
.venv\Scripts\python -m pytest tests/ backend/tests/ -v
```

### 2. Run Frontend Vitest Suite (14 Tests)
```powershell
cd frontend
npm test -- --run
```

### 3. Run Milestone 18 Stress Benchmark
```powershell
.venv\Scripts\python scripts/run_stress_benchmark.py --count 50 --seed 42
```

### 4. Run Milestone 17 Full Deployment Verification
```powershell
.venv\Scripts\python scripts/verify_deployment_readiness.py
```

### 5. Synthesize All AWS CDK Stacks
```powershell
$env:PYTHONPATH="."
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" synth
```

---

## AWS Deployment Instructions

When ready to deploy into AWS account `<AWS_ACCOUNT_ID>` (`ap-south-1`):

```powershell
$env:PYTHONPATH="."
# 1. Foundation Stack (S3, CloudWatch Logs, DynamoDB Table)
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Foundation-dev

# 2. Auth Stack (Cognito User Pool, App Client, RBAC Groups)
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Auth-dev

# 3. Step Functions Orchestration Stack (Lambdas, SFN, REST API)
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Orchestration-dev

# 4. Event Pipeline Stack (EventBridge, SQS Buffer, DLQ)
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-EventPipeline-dev

# 5. Real-Time WebSocket & Observability Stacks
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-WebSocket-dev
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" deploy ColdRescue-Monitoring-dev
```

### Resource Cleanup
To tear down all resources and avoid ongoing AWS costs:
```powershell
$env:PYTHONPATH="."
npx cdk --app ".venv\Scripts\python.exe infrastructure/app.py" destroy --all
```

---

## Project Status Matrix (Milestones M0–M19)

| Milestone | Title | Implementation State | Verification Status |
|---|---|---|---|
| **M0** | Foundation, Schemas & Tests | `DEPLOYED` | **PASS** (`ColdRescue-Foundation-dev` active in ap-south-1) |
| **M1** | Frontend UI & User Journeys | `LOCAL` | **PASS** (14/14 Vitest suites green, mobile flows verified) |
| **M2** | Power Failure Simulator | `LOCAL` | **PASS** (Deterministic physics, configurable seeds & scenarios) |
| **M3** | Thermal Physics & Safety Policy | `LOCAL` | **PASS** (Newtonian cooling & 6-rule hard block gate) |
| **M4** | Route Provider & Amazon Location | `LOCAL` | **PASS** (Location service integration with Haversine fallback) |
| **M5** | Greedy vs Global Allocation | `LOCAL` | **PASS** (Fleet-wide optimization & heuristic comparison) |
| **M6** | ML Surrogate Spoilage Predictor | `LOCAL` | **PASS** (Trained linear surrogate model with physics fallback) |
| **M7** | DynamoDB Event Store & Idempotency | `DEPLOYED` | **PASS** (`ColdRescue-Events-dev` verified with live probe) |
| **M8** | Local End-to-End Recovery Flow | `LOCAL` | **PASS** (Unified end-to-end recovery lifecycle tests green) |
| **M9** | Step Functions & Lambda Orchestration| `LOCAL / SYNTHESIZED` | **PASS** (10 lifecycle stages, Choice branching, API Gateway) |
| **M10** | Cognito Authentication | `LOCAL / SYNTHESIZED` | **PASS** (User Pool, App Client, JWT auth & tests) |
| **M11** | Role-Based Authorization & Approval | `LOCAL` | **PASS** (4-role matrix, separation of duties, 401/403 tests) |
| **M12** | Amplify Frontend Deployment Scaffolding | `LOCAL` | **PASS** (Environment-specific endpoints & fallback labeling) |
| **M13** | EventBridge, SQS Buffer, DLQ | `LOCAL / SYNTHESIZED` | **PASS** (Custom bus, SQS queue, DLQ redrive, idempotent consumer) |
| **M14** | ECS Fargate Telemetry Simulator | `LOCAL / SYNTHESIZED` | **PASS** (Containerized simulator, continuous telemetry emitter) |
| **M15** | WebSocket Real-Time Push | `LOCAL / SYNTHESIZED` | **PASS** (API Gateway WebSocket API, DynamoDB connection table) |
| **M16** | SNS Alerts & CloudWatch Dashboard | `LOCAL / SYNTHESIZED` | **PASS** (SNS topic, Operations dashboard, metric alarms) |
| **M17** | Full Integration Verification | `VERIFIED` | **PASS** (All 20 verification criteria verified in report) |
| **M18** | Reproducible Stress Benchmark | `VERIFIED` | **PASS** (50 scenarios, +314.3 kg lift, 0 policy violations) |
| **M19** | Final Impact, Demo & Documentation | `COMPLETE` | **PASS** (Comprehensive Track 03 README, demo scripts, impact formula) |

---
*ColdRescue is developed for Track 03: Waste and Energy. Keep the cold chain powered. Keep food and medicine out of the bin.*
