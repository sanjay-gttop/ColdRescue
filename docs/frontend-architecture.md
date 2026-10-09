# ColdRescue Frontend Architecture & Action Contracts Matrix

This document specifies the user interface architecture, state machines, and action contracts implemented in **Milestone 1 — Track 03**.

## 1. Core Design Philosophy
- **Operational Density without Clutter**: High contrast, dark-slate emergency operations palette with clear typographic hierarchy.
- **Color-Blind Safe Palette**: Status conventions use combined text labels, icons, borders, and high-contrast color tokens (`Critical`, `Warning`, `Safe`, `Blocked`, `Pending`, `Unknown`, `Stale`, `Offline`).
- **Data Integrity**: Never infer safety from absence of data. Missing sensors or uncalibrated models are surfaced as `UNKNOWN` or `DATA MISSING`.
- **Zero-Bypass Policy Hard Blocks**: When physical constraints (capacity, temperature boundaries, cooling failure, transit timeout) are violated, the system disallows operator authorization.

## 2. Consequential Action Contracts Matrix

| Action Name | Initiating Control | Required Inputs | Preconditions | Success Outcome | Failure State / Protection | Audit Impact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Open Incident** | Incident Table Row / Button | `incident_id` | Incident exists in queue | Displays Incident & Cargo details | Error card if ID not found | None (read) |
| **Filter Receivers** | Dropdowns / Slider | Filter criteria | None | Reactive filtered card list | Reset button restores view | None |
| **Compare Allocation** | "Re-evaluate Optimization" | Scenario ID | >=1 incident, >=1 receiver | Computes Greedy vs Global plans side-by-side | Graceful empty notification | `ALLOCATION_EVALUATED` |
| **Select Receiver Proposal** | "Propose Receiver" Button | `receiver_id` | Incident active | If safe -> Approval screen; If unsafe -> Policy Block screen | Hard block triggers rejection route | `PROPOSAL_DRAFTED` |
| **Approve Proposal** | "Authorize Dispatch" Modal | Operator name | Policy passed, status `pending` | Transitions to `approved`, dispatches Driver | Locked button if hard blocked | `APPROVAL_GRANTED` |
| **Reject Proposal** | "Reject Proposal" Modal | Rejection reason (>= 5 chars) | Status `pending` | Transitions to `rejected`, logs reason | Reason required before submit | `APPROVAL_REJECTED` |
| **Driver Acknowledge** | "Acknowledge & Accept" | `assignment_id` | Status `approved` | Status becomes `acknowledged` | Blocked if already declined | `DRIVER_ACKNOWLEDGED` |
| **Driver Decline** | "Decline Assignment" Modal | Decline reason (>= 5 chars) | Status `approved` or `acknowledged` | Status becomes `declined` | Reason required before submit | `DRIVER_DECLINED` |
| **Update Progress** | "Mark Departed" / "Arrived" | `assignment_id`, stage | Strict progression | Updates transit stage and ETA | Invalid stage jumps rejected | `DELIVERY_PROGRESS_UPDATED` |
| **Submit Handoff** | "Complete Handoff" Modal | Arrival temp, notes | Driver arrived | Status becomes `handoff_submitted` | Arrival required first | `HANDOFF_SUBMITTED` |
| **Receiver Accept** | "Accept & Confirm Intake" | Dock ID, notes | Handoff submitted, capacity available | Status `completed`, capacity decremented | Inoperable if cooling failed | `RECEIVER_ACCEPTED_DELIVERY` |
| **Receiver Reject** | "Reject Intake" Modal | Rejection reason (>= 5 chars) | Intake pending | Status `rejected`, emergency re-routing | Reason required | `RECEIVER_REJECTED_DELIVERY` |
| **Refresh Stale Data** | "Refresh" Header Button | None | None | Revalidates cache, clears stale banner | Network error banner if offline | `TELEMETRY_REFRESHED` |

## 3. Policy Rules Implemented
1. **Capacity Feasibility (`POL-CAP-001`)**: `receiver.available_capacity_kg >= cargo.cargo_kg`. Hard block if violated.
2. **Cargo Category Compatibility (`POL-COMPAT-002`)**: `cargo.cargo_type in receiver.compatible_cargo_types`. Hard block if violated.
3. **Thermal Envelope Match (`POL-TEMP-003`)**: `receiver.temp_range_min <= cargo.safe_temperature_min` AND `receiver.temp_range_max >= cargo.safe_temperature_max`. Hard block if violated.
4. **Receiver Cooling Status (`POL-COOL-004`)**: Cooling must be `operational` or `degraded`. Hard block if `failed` or `offline`.
5. **Transit Window vs Spoilage Deadline (`POL-TIME-005`)**: Transit duration + 15 min buffer must be `<` remaining spoilage time. Hard block if violated.
6. **Backup Power Reserve (`POL-PWR-006`)**: Facility backup power runtime must exceed transit time + 45 min margin. Warning issued if lower.
