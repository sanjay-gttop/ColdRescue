# COLDRESCUE V7 — FINAL EVIDENCE RECONCILIATION & READ-ONLY AUDIT REPORT
**Target Commit:** `bcaececd6bdbca890a573f66a5d234fc6672c206` (`bcaecec`)  
**Audit Mode:** Read-Only Verification (No mutations, deployments, or resource deletions performed)  
**Execution Timestamp:** 2026-10-11T10:28:00+05:30  
**Target AWS Region:** `ap-south-1` (Mumbai)  
**Verified Caller Identity:** `arn:aws:iam::<AWS_ACCOUNT_ID>:user/<REDACTED_IAM_USER>`  

---

## 1. Section 1 — Model Safety & Surrogate Reconciliation

### 1.1 Direct Recomputation of Held-Out Evaluation Metrics
Evaluated directly from all 250 test rows in `ml/evaluation/test_dataset.csv` against `ml/training/model.json` using `ThermalMLPredictor`:

| Metric | Recorded in Evidence Report | Independently Recomputed from Samples | Delta | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Sample Count ($N$)** | 250 | 250 | 0 | **VERIFIED** |
| **Evaluation Split Seed** | 999 | 999 | 0 | **VERIFIED** |
| **MAE** | 71.70 min | 71.70 min | 0.00 min | **VERIFIED** |
| **RMSE** | 93.49 min | 93.49 min | 0.00 min | **VERIFIED** |
| **Median Absolute Error** | 52.30 min | 52.30 min | 0.00 min | **VERIFIED** |
| **95th-Percentile Absolute Error** | 188.10 min | 188.10 min | 0.00 min | **VERIFIED** |
| **Signed Mean Bias** | +3.54 min | +3.54 min | 0.00 min | **VERIFIED** |
| **False-Safe Count ($>15$ min optimism)** | 87 | 87 | 0 | **VERIFIED** |
| **False-Safe Rate ($>15$ min optimism)** | 34.80% | 34.80% | 0.00% | **VERIFIED** |
| **False-Safe Count ($>0$ min optimism)** | N/A (unreported) | 101 | — | **VERIFIED** (40.40% unconstrained) |

#### Top 3 Worst-Case Errors (Directly Recomputed):
1. **Sample 1 (Dairy):** Ambient 33.26°C, Active Cooling, Physics Reference = 139.0 min, Predicted = 510.1 min, Error = **+371.1 min** (Optimistic).
2. **Sample 2 (Dairy):** Ambient 40.09°C, Active Cooling, Physics Reference = 223.0 min, Predicted = 483.5 min, Error = **+260.5 min** (Optimistic).
3. **Sample 3 (Perishable Food):** Ambient 37.32°C, Active Cooling, Physics Reference = 222.0 min, Predicted = 445.7 min, Error = **+223.7 min** (Optimistic).

### 1.2 Split Independence and Label Provenance
- **Dataset Generation:** `ml/evaluation/test_dataset.csv` is generated with `seed=999`, distinct from the training set seed (`seed=42`).
- **Label Provenance:** All ground-truth labels (`breach_minutes`) originate from simulated Newton cooling numerical integration in `simulate_thermal_risk`.
- **Validation Distinction:** The evaluation measures **agreement with the synthetic physics simulation**, **NOT** measured biochemical food/medicine degradation in physical transport.

### 1.3 Decision Path Trace: 440-Minute Surrogate vs. 47-Minute Physics Example
- **Input Scenario:** Degraded cooling, high ambient (35.0°C), current temp 4.0°C, max limit 8.0°C.
- **Surrogate Prediction:** Live SageMaker serverless inference or mock returns $440.0\text{ min}$.
- **Physics Reference:** Deterministic numerical integration calculates breach at $47.0\text{ min}$.
- **Reconciliation Rule (`backend/services/thermal_risk.py` lines 431–434):**
  $$\text{safe\_window} = \min(\text{raw\_physics\_window}, \text{raw\_surrogate\_window}) = \min(47.0, 440.0) = \mathbf{47.0\text{ min}}$$
- **Operational Risk Classification:** $47.0\text{ min} < 90\text{ min} \implies \mathbf{HIGH\text{ RISK}}$ (avoiding the catastrophic `LOW RISK` misclassification that $440\text{ min}$ would have caused).
- **False-Safe Rate Verification:** The claimed 0.0% operational false-safe rate is **ONLY VALID** because of the hard code constraint $\min(\text{physics}, \text{surrogate})$. Without this deterministic rule, the ML surrogate has an intrinsic false-safe rate of **34.80%** ($>15$ min) and **40.40%** ($>0$ min).

### 1.4 Hard Guards & Boundary Condition Verification
- **Hard Temperature/Time Limits:** In `backend/services/thermal_risk.py`, current temperature $> \text{safe\_max}$ immediately returns `risk_level: CRITICAL`, `estimated_safe_window_min: 0.0`, and `spoilage_breached: True` before invoking ML or physics simulations.
- **Invalid / Non-Finite Telemetry:** `math.isfinite()` validation raises `ValueError` for `NaN`, `Inf`, or ambient temps outside $[-80^\circ\text{C}, +80^\circ\text{C}]$, preventing garbage inputs.
- **Endpoint Timeouts & Fallback:** Checked via `test_surrogate_endpoint_failure_falls_back_to_physics`. Any `ClientError`, `BotoCoreError`, or timeout cleanly catches exceptions, populates `fallback_reason: "SageMaker unavailable (ResourceNotFoundException); deterministic physics fallback armed."`, sets `prediction_source: "physics_fallback"`, and executes deterministic physics.
- **UI Surface:** `ThermalRiskAssessment` returns `raw_physics_window_min`, `raw_surrogate_window_min`, `estimated_safe_window_min`, `prediction_source`, `model_version`, `is_fallback`, and `fallback_reason`.

---

## 2. Section 2 — Benchmark Suite & Mathematical Allocation Verification

### 2.1 File Hashes & Data Integrity
- `evidence/benchmark/live_counterfactual_benchmark_evidence.json`:  
  **SHA256:** `A1BECD770E16E2B21142D38765A6004BC6ED0936F063B841F3387533DEACAC6D`
- `evidence/benchmark/high_contention_benchmark_evidence.json`:  
  **SHA256:** `801E3212C275548CFEFBF975280C09BEA6A499E6EE8E3A61C5FEF398F1CC208B`

### 2.2 Independent Recomputation of Benchmark Metrics

| Metric | Baseline Suite (`seed=42`) | High Contention Suite (`seed=77`) | Status |
| :--- | :---: | :---: | :---: |
| **Total Scenarios** | 50 (Recorded: 50) | 50 (Recorded: 50) | **MATCH** |
| **Total Cargo Evaluated** | 139,081.1 kg (Recorded: 139,081.1 kg) | 245,902.7 kg (Recorded: 245,902.7 kg) | **MATCH** |
| **Greedy Cargo Diverted** | 75,449.3 kg (Recorded: 75,449.3 kg) | 5,704.8 kg (Recorded: 5,704.8 kg) | **MATCH** |
| **Global Cargo Diverted** | 75,763.6 kg (Recorded: 75,763.6 kg) | 6,180.6 kg (Recorded: 6,180.6 kg) | **MATCH** |
| **Net Global Lift (kg)** | **+314.3 kg** (Recorded: +314.3 kg) | **+475.8 kg** (Recorded: +475.8 kg) | **MATCH** |
| **Net Global Lift (%)** | **+0.42%** ($\frac{314.3}{75,449.3} \times 100$) | **+8.34%** ($\frac{475.8}{5,704.8} \times 100$) | **MATCH** |
| **Outcome Counts** | 1 Global Win, 48 Ties, 1 Greedy Win | 1 Global Win, 49 Ties, 0 Greedy Wins | **MATCH** |
| **Policy Invariant Violations**| 0 (0.0%) | 0 (0.0%) | **MATCH** |
| **Avg Greedy Latency** | 98.57 ms | 71.97 ms | **MATCH** |
| **Avg Global Latency** | 147.86 ms | 107.95 ms | **MATCH** |

### 2.3 Isolation of the +475.8 kg Divergence in Seed 77
Across all 50 scenarios in Seed 77, exactly **one scenario** accounts for the entire 475.8 kg lift:
- **Scenario ID:** `contention_035`
  - Incidents: 6 concurrent trucks (produce 1,750.7 kg, produce 1,698.8 kg, produce 1,656.0 kg, vaccine 1,791.8 kg, produce 548.3 kg, dairy 1,024.1 kg)
  - Receivers: 3 scarce hubs (Capacities: 1,249.6 kg, 1,766.4 kg, 1,407.1 kg; Total capacity = 4,423.1 kg vs. Total cargo = 8,469.7 kg)
  - **Greedy Assignment:** Greedy greedily grabs incident 5 (548.3 kg produce), blocking the hub and stranding incident 6. Result: **548.3 kg** diverted.
  - **Global Solver Assignment:** Kuhn-Munkres global optimization assigns the hub to incident 6 (1,024.1 kg dairy). Result: **1,024.1 kg** diverted.
  - **Net Difference:** $1,024.1 - 548.3 = \mathbf{+475.8\text{ kg}}$ ($+86.78\%$ lift on this scenario).
  - The remaining 49 scenarios were exact ties (mostly 0 kg diverted due to tight capacity/spoilage cutoffs or identical selections).

### 2.4 Structural Contention Properties Verified
- **Scarce-Capacity:** 48 of 50 scenarios ($96.0\%$) had total receiver capacity $< 75\%$ of total incident cargo mass.
- **Rectangular Matrices:** 44 of 50 scenarios ($88.0\%$) had unequal incident/receiver dimensions (unassigned cargo by mathematical necessity).
- **UI State Disclosures:** In `AllocationComparisonView.tsx`, the benchmark results displayed in the UI modal are currently **pre-recorded constants** derived from the recorded runs (seed 42 and seed 77). The UI does not execute a live REST call to backend benchmark scripts dynamically on button click.

---

## 3. Section 3 — Live Trace Verification & Chronological Correlation

### 3.1 Trace Event Correlation
Inspected `frontend/src/components/audit/AwsLiveTraceView.tsx` against recorded live execution records (`data/evidence/live/orchestration_verification.json` and `live_alarm_evidence.json`):
- **Core Execution ID:** `TRUCK-104-LIVE-1791662747` (Timestamp: 2026-10-11T03:03:07Z to 03:03:11Z)
- **Hops Traced:**
  1. *AWS IoT Core:* MQTT message `iot-msg-1791668587` on topic `coldrescue/telemetry/truck_104` (**Observed in telemetry script logs**)
  2. *AWS IoT Rules Engine:* Topic Rule `ColdRescue_Telemetry_Rule_dev` forwarding to SQS (**Observed CloudFormation & SQS buffer**)
  3. *Amazon SQS Queue:* Message ID `msg-c1ff12f0-fb8a-4690-94d1-5944a7c5c40e` in `ColdRescue-ProcessingQueue-dev` (**Observed queue attributes**)
  4. *ML Surrogate:* `s3://.../models/thermal-surrogate-v1.0.0/model.tar.gz` (**Observed in S3 bucket**)
  5. *Amazon Location Service:* Route calculation on `ColdRescue-RouteCalculator-dev` (**Observed live ARN, 13.27 km, 33.3 min**)
  6. *Kuhn-Munkres Allocation:* Solver executed in Lambda `ColdRescue-Orchestration-SolveAllocationFn` (**Observed test & log data**)
  7. *Deterministic Safety Policy:* Hard gate in `EvaluatePolicyFn` (**Observed in Step Functions execution history**)
  8. *AWS Step Functions:* Execution `TRUCK-104-LIVE-1791662747` on state machine `ColdRescue-IncidentRecovery-dev` (**Observed execution history JSON**)
  9. *Amazon DynamoDB:* Event persist `stream_truck_104_1791662747#1` in `ColdRescue-Events-dev` (**Observed table scan**)

### 3.2 Observed vs. Inferred/Static Classification
- **Genuinely Observed on AWS:** Step Functions execution `TRUCK-104-LIVE-1791662747`, DynamoDB event persistence, SQS Processing Queue, SQS DLQ depth (3 msgs), CloudWatch alarm transition, RouteCalculator calculation, and SageMaker serverless endpoint `InService`.
- **Pre-recorded in UI:** The array `LIVE_RESCUE_STEPS` in `AwsLiveTraceView.tsx` is a **static frontend representation** of the real captured run `TRUCK-104-LIVE-1791662747`. It does not poll live Step Functions APIs in real-time from the browser (due to browser CORS and unauthenticated guest visitor boundaries).

---

## 4. Section 4 — AWS Cost & Resource State (Read-Only Inspection)

### 4.1 Live Resource Configuration
- **SageMaker Endpoint Name:** `coldrescue-thermal-serverless-v1`
- **Endpoint Status:** `InService`
- **Current Instance Count:** `0` (Serverless Architecture)
- **Serverless Config:** `MemorySizeInMB: 1024`, `MaxConcurrency: 5`
- **Deployed Container:** `763104351884.dkr.ecr.ap-south-1.amazonaws.com/pytorch-inference:2.1.0-cpu-py310`
- **Model S3 Path:** `s3://coldrescue-foundation-dev-auditlogsbucket963995a4-m5yvkigbfg3t/models/thermal-surrogate-v1.0.1/model.tar.gz`

### 4.2 Budget & Cost Audit
- **AWS Budget Name:** `ColdRescue-Development-Budget`
- **Budget Limit:** \$25.00 USD / month
- **Calculated Actual Spend (Oct 1 to Oct 11, 2026):** **\$0.014 USD**
- **Budget Health Status:** `HEALTHY` (Last updated 2026-10-11T09:20:02+05:30)
- **Audit Limitation Note:** The actual spend reflects AWS Cost and Usage reporting latency (typically 8–24 hours). While SageMaker Serverless compute billing drops to zero when concurrency is zero, S3 storage and CloudWatch metrics incur tiny continuous fractions of a cent (hence \$0.014 spend to date).

---

## 5. Section 5 — Security & Release Verification

### 5.1 RBAC Separation of Duties (401 vs. 403)
- **401 Unauthorized Gate:** Verified on API Gateway (`https://l4bpu3mf2f.execute-api.ap-south-1.amazonaws.com/dev/incidents/recover`). Unauthenticated requests and forged JWT tokens return HTTP `401 Unauthorized`.
- **403 Forbidden Gate:** Evaluated at the Lambda policy enforcement layer. As recorded in `evidence/rbac/live_api_auth_evidence.json`, API Gateway allows bearer tokens from the Cognito User Pool through to Lambda; however, `DRIVER` roles are blocked from initiating reassignment overrides within the business logic.

### 5.2 Redaction Scan Audit
- **Tracked Markdown Documentation:** Fully clean. Zero instances of account ID `494110627063` or username `Death` found in any `.md` file in the root or `docs/`.
- **Remaining Unredacted Occurrences in Code / Fixtures:**
  1. `frontend/src/components/audit/AwsLiveTraceView.tsx` line 148: hardcoded display string `'arn:aws:iam::494110627063:user/Death'` in the trace health bar.
  2. `.env.example`, `infrastructure/app.py`, and infrastructure unit tests (`tests/test_infrastructure.py`): contains static fallback account `494110627063` for CDK synthesis testing.
  3. JSON evidence files in `evidence/` and `data/evidence/live/`: contain verbatim ARNs from AWS CLI execution outputs.

### 5.3 Amplify Deployment & Mobile Verification
- **Amplify App ID:** `d1pwxznhg8jq0u`
- **Branch:** `dev`
- **Deployment Job ID:** **8** (`SUCCEED`)
- **Git Commit Alignment:** Built from commit `bcaecec` `dist/` bundle.
- **Mobile Responsive Screenshots:** Amplify automated verification generated 4 device screenshots in job 8:
  - `ipadair2` (768x1024)
  - `iphone7plus` (414x736)
  - `iphone8` (357x667)
  - `samsungs7` (360x640)
- **Physical Device Limitation:** Verified through Amplify headless device emulation (Puppeteer/Chrome); **no physical real-world smartphone hardware testing** was conducted.

---

## 6. Section 6 — Report Consistency & Roadmap V7 Reconciliation

### 6.1 Reconciliation of Score Claims
The phrasing in prior draft reports contained conflicting language:
- *"All 20 gates verified"* **contradicts** *"18/20 Gates Full, 2 Provisional"* and *"90% deployed / 92% implemented"*.
- **Authoritative Resolution:** The project has **18 VERIFIED gates** and **2 PARTIALLY VERIFIED / PROVISIONALLY SCORED gates** (M6 and M18) due to synthetic training provenance, lack of physical hardware telemetry, and pre-recorded UI simulation cards.

### 6.2 Milestone-by-Milestone Traceability Matrix (M0–M19)

| Milestone | Scope Summary | Implementation Status | AWS Deployed Status | Final Audited Status | Exact Empirical Basis |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **M0** | Foundations, Schemas, S3 Audit Bucket | 10 / 10 | 10 / 10 | **VERIFIED** | KMS-encrypted S3 bucket active; Pydantic schemas validated. |
| **M1** | React 18 UI & 4 Journeys | 10 / 10 | 10 / 10 | **VERIFIED** | 14 Vitest tests passing; live Amplify hosting. |
| **M2** | Newton Cooling Simulator | 10 / 10 | 10 / 10 | **VERIFIED** | Verified numerical physics model; Fargate task exit 0. |
| **M3** | Deterministic Safety Policy | 10 / 10 | 10 / 10 | **VERIFIED** | 6-rule hard block policy gate authoritative in code and SFN. |
| **M4** | Amazon Location Service Routing | 10 / 10 | 10 / 10 | **VERIFIED** | `ColdRescue-RouteCalculator-dev` live; 13.27 km calculated route. |
| **M5** | Kuhn-Munkres Allocation | 10 / 10 | 10 / 10 | **VERIFIED** | 0.0% gap vs brute force across 35 instances; pure Python. |
| **M6** | ML Surrogate Predictor | 8.8 / 10 | 9.0 / 10 | **PARTIALLY VERIFIED** | SageMaker serverless endpoint live, but trained on synthetic simulation labels; fallback and precedence enforced. |
| **M7** | DynamoDB Event Persistence | 10 / 10 | 10 / 10 | **VERIFIED** | Table `ColdRescue-Events-dev` active; conditional writes verified. |
| **M8** | Vertical Recovery Slice | 10 / 10 | 10 / 10 | **VERIFIED** | End-to-end slice executed on AWS Step Functions. |
| **M9** | Step Functions Orchestration | 10 / 10 | 10 / 10 | **VERIFIED** | 10 Lambdas and state machine active in `ap-south-1`. |
| **M10** | Cognito Authentication | 10 / 10 | 10 / 10 | **VERIFIED** | User pool and client active; 401 gate verified live. |
| **M11** | RBAC Separation of Duties | 10 / 10 | 10 / 10 | **VERIFIED** | 4 roles active; driver override blocks enforced. |
| **M12** | Production Frontend Single-Page App | 10 / 10 | 10 / 10 | **VERIFIED** | Live Amplify HTTPS hosting (HTTP 200 OK verified). |
| **M13** | EventBridge & SQS DLQ | 10 / 10 | 10 / 10 | **VERIFIED** | DLQ captured 3 messages upon retry exhaustion; redrive tested. |
| **M14** | ECS Fargate Simulator | 10 / 10 | 10 / 10 | **VERIFIED** | Task run on `ColdRescue-Cluster-dev` with zero standing idle tasks. |
| **M15** | WebSocket Real-Time Push | 10 / 10 | 10 / 10 | **VERIFIED** | API Gateway WebSocket API active with connection store. |
| **M16** | CloudWatch & SNS Alerts | 10 / 10 | 10 / 10 | **VERIFIED** | Alarm transitioned to `ALARM` state, triggered SNS, reset to `OK`. |
| **M17** | End-to-End System Integration | 10 / 10 | 10 / 10 | **VERIFIED** | 181 backend tests passing; full cloud pipeline verified. |
| **M18** | Stress Benchmark & Scenarios | 9.0 / 10 | 9.0 / 10 | **PARTIALLY VERIFIED** | 50 baseline and 50 high-contention scenarios verified in Python; UI displays pre-recorded run cards rather than live REST triggers. |
| **M19** | Documentation & Runbooks | 10 / 10 | N/A | **VERIFIED** | Complete runbooks, architecture diagrams, and matrices. |

---

## 7. Short List of Highest-Priority Fixes (For a Future Authorized Pass)

1. **Redact IAM Account & User in `AwsLiveTraceView.tsx`:** Line 148 of `AwsLiveTraceView.tsx` still renders `'arn:aws:iam::494110627063:user/Death'`. Update to render a dynamic or sanitized string (`'arn:aws:iam::<AWS_ACCOUNT_ID>:user/<REDACTED_IAM_USER>'`).
2. **Dynamic UI Benchmark Trigger:** Wire the "Run Counterfactual Benchmark" button in `AllocationComparisonView.tsx` to invoke a backend API endpoint (`POST /benchmark/run`) rather than returning a `setTimeout` with hardcoded constant results.
3. **Explicit UI Latency & Source Badges in Trace:** Add badges in `AwsLiveTraceView.tsx` clearly distinguishing "Captured AWS Execution Trace" from live WebSocket subscriptions to eliminate judge confusion.
4. **Cognito Token Dynamic Scopes for 403 API Gateway Rejection:** Move the 403 RBAC check from the Lambda application level directly to an API Gateway Cognito Authorizer scope/resource-policy mapping so unauthorized roles receive an immediate HTTP 403 at the gateway edge.
