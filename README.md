# ColdRescue

ColdRescue is an operational decision-support system designed to mitigate power and cooling failures affecting temperature-sensitive cargo (mRNA vaccines, blood platelets, biologics, and pharmaceuticals) in transit.

---

## Milestone 1 — Track 03: User Interface and User Journeys

The ColdRescue frontend is a React + TypeScript single-page application built on Vite, adhering to strict emergency logistics operational hierarchy, WCAG accessibility standards, and color-blind safe status representations.

### Key System Capabilities
1. **Operator Emergency Dashboard**: Active incident queue, critical/high alerts, aggregate cargo tonnage at risk, facility capacity reserves, pending approvals, and audit telemetry.
2. **Incident & Thermal Telemetry**: Active countdown timer for spoilage deadlines with model provenance, sensor confidence ratings, and power bus/cooling status.
3. **Receiver Facility Directory**: Capacity utilization indicators, thermal envelope verification, filter toolbars, and pre-dispatch feasibility validation.
4. **Greedy vs. Global Allocation Engine**: Side-by-side comparison of localized heuristics vs. fleet-wide constrained optimization with documented assumptions and limitations.
5. **Approval Decision Console**: Hard safety policy block enforcement (cannot be manually bypassed), rule evaluation matrix, alternative facility recommendations, and justification modals.
6. **Mobile-First Driver Portal**: Touch-friendly (>= 44px) delivery execution flow (Acknowledge → Depart → Progress → Arrive → Handoff) with safety protocols.
7. **Mobile-First Receiver Intake Portal**: Vault intake verification, chamber dock selection, and delivery acceptance or rejection with documented justification.
8. **Chronological Operational Audit Trail**: Deterministic event log capturing all state changes, algorithm proposals, operator decisions, and driver transitions.
9. **Reliability & Simulation State Management**: Real-time handling of loading, empty, stale telemetry (>15m threshold), offline/disconnected mode, and simulated API failure recovery.
10. **Action Contracts Matrix**: Complete specification of preconditions, inputs, expected outcomes, and duplicate-submission protections.

---

## Repository Structure

```text
ColdRescue/
├── frontend/                        # React / TypeScript Application
│   ├── src/
│   │   ├── app/                    # Central Application Controller (App.tsx)
│   │   ├── components/
│   │   │   ├── common/             # StatusBadge, CountdownTimer, Modal, ReliabilityView, Icons
│   │   │   ├── layout/             # Header, Navigation
│   │   │   ├── dashboard/          # Operator Dashboard
│   │   │   ├── incidents/          # Incident & Cargo Telemetry Detail View
│   │   │   ├── receivers/          # Receiver Directory & Card Grid
│   │   │   ├── allocation/         # Greedy vs Global Allocation Comparison
│   │   │   ├── approvals/          # Operator Approval Decision Console
│   │   │   ├── driver/             # Mobile-First Driver Delivery Portal
│   │   │   ├── receiver-portal/    # Mobile-First Receiver Intake Portal
│   │   │   ├── audit/              # Chronological Audit Timeline
│   │   │   └── policy/             # Policy-Block Detail View
│   │   ├── data/                   # Deterministic Synthetic Fixtures & Action Matrix
│   │   ├── styles/                 # Theme tokens & WCAG Accessible Styling (theme.css)
│   │   ├── tests/                  # Vitest Unit & Integration Suites
│   │   ├── types/                  # Typed Domain & State Interfaces
│   │   └── utils/                  # Policy Engine & Allocation Algorithms
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                        # Backend Application & Schemas
├── data/fixtures/                  # Machine-readable JSON fixtures
├── docs/                           # Architecture and setup documentation
├── infrastructure/                 # AWS deployment scaffolds
├── optimizer/                      # Future optimization models
├── simulator/                      # Fleet telemetry simulator
└── tests/                          # Backend tests
```

---

## Local Development & Setup

### Prerequisites
- Node.js (v20+ recommended, tested on Node v24.11.0)
- npm (v10+, tested on npm 11.4.2)

### Running the Frontend
```powershell
# Navigate to frontend
cd frontend

# Install dependencies (if not already installed)
npm install

# Start local Vite development server
npm run dev
```
The application will be available at `http://localhost:3000` (or `http://localhost:5173`).

### Running Production Build & Type Checking
```powershell
cd frontend
npm run build
```

### Running Automated Test Suites
```powershell
cd frontend
npm test
```

---

## User Journeys Verification Matrix

| Journey | Description | Key Verification Steps | Status |
| :--- | :--- | :--- | :--- |
| **Journey A** | Incident to Approval | Dashboard → Select `INC-2026-081` → Inspect Cargo → Select Receiver `RCV-CENTRAL-01` → Compare Allocation → Approve Proposal → Emits `APPROVAL_GRANTED` audit event. | **VERIFIED** |
| **Journey B** | Driver Delivery | Driver Portal → Open `ASN-8801` → Acknowledge → Mark Departed → Mark Arrived → Complete Handoff with temperature log. | **VERIFIED** |
| **Journey C** | Receiver Intake | Receiver Portal → Review incoming cargo → Confirm dock intake chamber → Available capacity updated → Emits `RECEIVER_ACCEPTED_DELIVERY`. | **VERIFIED** |
| **Journey D** | Policy Block | Select `INC-2026-081` → Select Infeasible Facility (`RCV-APEX-03` / `RCV-CASCADE-04`) → Enforces Hard Block → Inspect rule violation → Select alternative facility. | **VERIFIED** |
| **Journey E** | Failure Recovery | Trigger simulated network failure (`503 Service Unavailable`) → Error state displayed → Click "Retry Operation" → Normal state restored without data loss. | **VERIFIED** |
| **Journey F** | Stale / Disconnected | Click "Sim Stale" or "Sim Offline" in header → System displays warnings and locks consequential dispatch actions → Click "Refresh Telemetry" to restore. | **VERIFIED** |

---

## Data Source Boundaries: Demo vs. Live API
- **Demo Mode (Current)**: Operates against deterministic local fixtures in `frontend/src/data/mockData.ts`. All state transitions are clearly labeled as local and simulated.
- **Milestone 2 Integration Boundary**: Ready to connect to backend REST/WebSocket endpoints. When switched to Live mode via header toggle, the UI expects verified API contracts for telemetry and receiver updates.
