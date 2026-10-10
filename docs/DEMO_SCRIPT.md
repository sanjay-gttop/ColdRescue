# ColdRescue 4-Beat Final Demonstration Script
**Track 03: Waste and Energy**  
**Title:** Keep the cold chain powered. Keep food and medicine out of the bin.  
**Corridor:** Tamil Nadu Dairy Logistics Corridor (Salem – Erode – Tiruppur – Coimbatore)

---

## Beat 1: The Outage & Spoilage Deadline (Failure Ingestion)
- **What is happening:**
  - An insulated reefer truck carrying $1,200\text{ kg}$ of fresh pasteurized milk suffers a total alternator failure on NH-544 near Bhavani.
  - Ambient temperature is $38.5^\circ\text{C}$ in the afternoon heat. Internal temperature starts at $4.0^\circ\text{C}$. Critical spoilage threshold is $8.0^\circ\text{C}$.
- **What to show on screen:**
  - Telemetry event arrives via IoT ingestion into EventBridge / SQS.
  - The Thermal Trajectory chart displays the exponential Newton cooling curve.
  - Remaining Safe-Cooling Time (RST) is calculated: **breach deadline in exactly $74\text{ minutes}$**.

---

## Beat 2: Greedy Failure vs Global Solver Triumph (Allocation Comparison)
- **What is happening:**
  - Multiple simultaneous outages occur along the corridor.
  - A simple **Greedy / Nearest-Viable** algorithm routes Truck 1 to the nearest depot in Erode, completely filling its $1,000\text{ kg}$ intake capacity. When Truck 2 arrives with high-value cargo, it is rejected and spoils.
  - ColdRescue's **Global Optimization Solver** runs an $O(N \cdot M)$ Hungarian matching algorithm considering travel ETA, receiver capacity, backup generator status, and grid stability.
- **What to show on screen:**
  - The Allocation Comparison table shows Global Solver achieves $+314.3\text{ kg}$ more cargo saved.
  - The system selects Tiruppur Cold Hub ($56.2\text{ km}$, $48\text{ min}$ drive) with $100\%$ grid viability and verified $4\text{ hours}$ backup runtime.

---

## Beat 3: Authoritative Safety Policy & Human-in-the-Loop Approval (Governance)
- **What is happening:**
  - The Deterministic Safety Policy Engine evaluates 6 non-negotiable safety rules.
  - Safety margin check: Travel ETA ($48\text{ min}$) is less than Safe-Cooling Time ($74\text{ min}$) minus safety margin ($15\text{ min}$) $\rightarrow$ **PASS**.
  - Operator Console displays the candidate plan for review.
- **What to show on screen:**
  - Operator clicks **Approve Recovery Assignment**.
  - Separation of duties: Drivers cannot approve their own assignments.
  - Step Functions state machine transitions from `TaskHumanApproval` to `TaskDriverAcknowledgement`.

---

## Beat 4: Handshake, Delivery Acceptance & Verified Impact (Audit & Metrics)
- **What is happening:**
  - Driver acknowledges diversion route on mobile interface.
  - Truck arrives at Tiruppur facility. Receiver scans barcode and inspects core temperature ($6.2^\circ\text{C}$, safely below $8.0^\circ\text{C}$).
  - Receiver accepts intake.
- **What to show on screen:**
  - Immutable audit event recorded in DynamoDB (`ColdRescue-Events-dev`) and archived to S3.
  - Real-time impact metric increments: **$1,200\text{ kg}$ cargo diverted from waste risk**.
  - Avoided embedded emissions calculated: **$2,880\text{ kg CO2e}$ avoided** ($2.4\text{ kg CO2e / kg milk}$).
  - CloudWatch operations dashboard reflects zero workflow failures and zero unaccepted cargo.
