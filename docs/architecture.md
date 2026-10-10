# ColdRescue — System Architecture

## 1. Overview
ColdRescue is an intelligent cold-chain rescue coordination platform designed to prevent catastrophic food, dairy, and medical supplies spoilage during refrigeration failures, grid outages, and transportation breakdowns.

The platform continuously models thermal decay, enforces strict safety policies, computes transit durations, and solves multi-incident capacity allocation across regional receiving facilities (cold storage warehouses, food banks, hospital pharmacies, and community cold rooms).

---

## 2. Architectural Layers

```
+-----------------------------------------------------------------------------+
|                                USER INTERFACE                               |
|          React 18 + TypeScript + Vite (Operator, Driver, Receiver)          |
+-----------------------------------------------------------------------------+
                                       |
                                       v [REST / HTTP]
+-----------------------------------------------------------------------------+
|                          FASTAPI BACKEND SERVICES                           |
|                                                                             |
|  +-------------------+  +--------------------+  +------------------------+  |
|  | Event Ingestion   |  | Safety Policy      |  | Thermal Risk           |  |
|  | Stream Store &    |  | Engine             |  | Evaluation             |  |
|  | Sequence Dedup    |  | (Safety Rules & Validation)|  | (Newton Cooling Model) |  |
|  +-------------------+  +--------------------+  +------------------------+  |
|                                  |                                          |
|  +-----------------------------------------------------------------------+  |
|  | Allocation & Recovery Orchestration Service                           |  |
|  |   - Greedy First-Feasible Solver                                      |  |
|  |   - Global Multi-Incident Balanced Solver                             |  |
|  |   - Local Haversine Route Provider & Road Circuity (1.3x)             |  |
|  +-----------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                          AWS CLOUD INFRASTRUCTURE                           |
|                                                                             |
|  [M0 Foundation Stack]                                                      |
|    - Secure S3 Audit Bucket (SSE-S3, Versioning, Block Public Access, SSL)  |
|    - CloudWatch Log Group (/coldrescue/application/dev, 30-day retention)   |
|                                                                             |
|  [Future Milestones Roadmap]                                                |
|    - Amazon EventBridge Event Bus (Domain Event Routing)                    |
|    - Amazon DynamoDB (Durable Multi-Facility State & Idempotency)           |
|    - AWS ECS / Fargate Container Service & Application Load Balancer        |
+-----------------------------------------------------------------------------+
```

---

## 3. Domain Event Schemas (M0 Foundation)
All platform state changes are modeled as immutable domain events inheriting from `EventEnvelope` (`schema_version: "1.0.0"`):
- `IncidentEvent`: Incident classification (`REEFER_UNIT_FAILURE`, `COLD_ROOM_POWER_OUTAGE`, `WAREHOUSE_GRID_OUTAGE`, `BACKUP_RUNTIME_LOW`, `BACKUP_POWER_DEPLETED`).
- `CargoEvent`: Mass, thermal envelope constraints, current temperature, and remaining backup runtime.
- `ReceiverEvent`: Facility capacity, current load, temperature acceptance window, and categories.
- `RouteEvent`: Waypoints, distance, and transit ETAs.
- `AssignmentEvent`: Driver, receiver, and cargo allocation linkage.
- `ApprovalEvent`: Operator review decisions and policy compliance audit trail.
- `PredictionEvent`: Thermal progression and estimated time-to-breach.
- `AuditEvent`: System audit trail entries.

---

## 4. Security & Compliance Architecture
1. **Zero Public Storage Exposure**: S3 buckets configure `BlockPublicAccess.BLOCK_ALL` with explicit bucket policies denying unencrypted (`aws:SecureTransport: false`) traffic.
2. **Encryption In-Transit & At-Rest**: All S3 objects are encrypted at rest with server-side encryption (`AES256`).
3. **Audit Trail Immutability**: S3 versioning ensures historical audit records cannot be overwritten.
4. **Controlled Cloud Costs**: CloudWatch log groups enforce finite retention policies (30 days in development).
5. **Least Privilege IAM**: Stack synthesis strictly avoids wildcard `*:*` administrative roles and excessive permissions.
