"""
ColdRescue Greedy Allocation Engine.

Implements sequential first-feasible greedy matching:
  - Sorts incidents by severity & thermal urgency (critical first).
  - Iterates through candidate receiving facilities sorted by travel time / distance.
  - Checks SafetyPolicyEngine for every candidate; immediately rejects hard-blocked candidates.
  - Assigns to the nearest feasible receiver, subtracting capacity immediately.
  - Prevents duplicate / double-booking of consumed capacity.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.domain import IncidentRecord, ReceiverNode, SeverityLevel
from backend.policies.safety_policy import SafetyPolicyEngine
from backend.services.route_provider import RouteProvider, LocalHaversineRouteProvider


class AssignmentPlanItem(BaseModel):
    incident_id: str
    receiver_id: str
    receiver_name: Optional[str] = None
    cargo_kg: float
    feasible: bool
    rejection_reason: Optional[str] = None
    travel_time_min: float = 0.0
    distance_km: float = 0.0
    spoilage_margin_min: float = 0.0


class AllocationResult(BaseModel):
    strategy: str = "greedy"
    scenario_name: str
    assignments: List[AssignmentPlanItem] = Field(default_factory=list)
    unassigned_incidents: List[str] = Field(default_factory=list)
    capacity_utilization_pct: int = 0
    total_spoilage_risk_score: int = 0
    average_travel_time_min: int = 0
    objective_value: str
    explanation: str
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class GreedyAllocationEngine:
    """Greedy solver matching incidents to nearest feasible receiving facilities."""

    SEVERITY_WEIGHTS: Dict[SeverityLevel, int] = {
        SeverityLevel.CRITICAL: 4,
        SeverityLevel.HIGH: 3,
        SeverityLevel.MEDIUM: 2,
        SeverityLevel.LOW: 1,
    }

    @classmethod
    def solve(
        cls,
        incidents: List[IncidentRecord],
        receivers: List[ReceiverNode],
        scenario_name: str = "Live Operation",
        route_provider: Optional[RouteProvider] = None,
        ambient_temperature_c: float = 25.0,
    ) -> AllocationResult:
        """
        Execute greedy assignment algorithm.

        Parameters
        ----------
        incidents              : List of active incidents to allocate
        receivers              : List of candidate receiving facilities
        scenario_name          : Label identifying the scenario / run
        route_provider         : RouteProvider for distance & travel time estimation
        ambient_temperature_c  : Ambient temperature in °C

        Returns
        -------
        AllocationResult with assignments, unassigned list, utilization %, and explanations.
        """
        router = route_provider or LocalHaversineRouteProvider()

        # Sort incidents by severity descending, then by remaining backup runtime ascending
        sorted_incidents = sorted(
            incidents,
            key=lambda inc: (
                -cls.SEVERITY_WEIGHTS.get(inc.severity, 2),
                inc.cargo.backup_runtime_min,
            ),
        )

        # Track mutable available capacities during greedy allocation
        remaining_capacities: Dict[str, float] = {
            r.receiver_id: r.available_capacity_kg for r in receivers
        }
        receiver_map: Dict[str, ReceiverNode] = {r.receiver_id: r for r in receivers}

        assignments: List[AssignmentPlanItem] = []
        unassigned: List[str] = []
        total_travel_time: float = 0.0
        assigned_count: int = 0

        for incident in sorted_incidents:
            cargo = incident.cargo

            # Calculate route metrics to all receivers
            candidate_routes = []
            for r in receivers:
                route_est = router.calculate_route(incident.location, r)
                candidate_routes.append((r, route_est))

            # Sort candidate receivers by travel time ascending
            candidate_routes.sort(key=lambda pair: pair[1].travel_time_min)

            assigned = False
            for cand_receiver, route_est in candidate_routes:
                curr_avail = remaining_capacities.get(cand_receiver.receiver_id, 0.0)

                # Skip if simulated remaining capacity is insufficient
                if curr_avail < cargo.cargo_kg:
                    continue

                # Create simulated receiver snapshot with current remaining capacity
                sim_receiver = cand_receiver.model_copy(
                    update={"current_load_kg": cand_receiver.capacity_kg - curr_avail}
                )

                # Evaluate safety policy
                policy = SafetyPolicyEngine.evaluate_assignment(
                    incident=incident,
                    receiver=sim_receiver,
                    travel_time_min=route_est.travel_time_min,
                    ambient_temperature_c=ambient_temperature_c,
                )

                if not policy.is_hard_blocked:
                    # Assign greedily
                    remaining_capacities[cand_receiver.receiver_id] -= cargo.cargo_kg
                    margin = max(5.0, (policy.thermal_window_min or 60.0) - route_est.travel_time_min)

                    assignments.append(
                        AssignmentPlanItem(
                            incident_id=incident.incident_id,
                            receiver_id=cand_receiver.receiver_id,
                            receiver_name=cand_receiver.name,
                            cargo_kg=cargo.cargo_kg,
                            feasible=True,
                            travel_time_min=route_est.travel_time_min,
                            distance_km=route_est.distance_km,
                            spoilage_margin_min=round(margin, 1),
                        )
                    )
                    total_travel_time += route_est.travel_time_min
                    assigned_count += 1
                    assigned = True
                    break

            if not assigned:
                unassigned.append(incident.incident_id)
                assignments.append(
                    AssignmentPlanItem(
                        incident_id=incident.incident_id,
                        receiver_id="NONE",
                        receiver_name=None,
                        cargo_kg=cargo.cargo_kg,
                        feasible=False,
                        rejection_reason="Greedy allocation exhausted available capacity or nearest facilities were hard-blocked by safety policy.",
                        travel_time_min=0.0,
                        distance_km=0.0,
                        spoilage_margin_min=0.0,
                    )
                )

        initial_total_cap = sum(r.available_capacity_kg for r in receivers)
        remaining_total_cap = sum(remaining_capacities.values())
        used_cap = initial_total_cap - remaining_total_cap
        util_pct = int(round((used_cap / initial_total_cap) * 100)) if initial_total_cap > 0 else 0

        avg_travel = int(round(total_travel_time / assigned_count)) if assigned_count > 0 else 0
        risk_score = 68 if len(unassigned) > 0 else 34

        return AllocationResult(
            strategy="greedy",
            scenario_name=scenario_name,
            assignments=assignments,
            unassigned_incidents=unassigned,
            capacity_utilization_pct=util_pct,
            total_spoilage_risk_score=risk_score,
            average_travel_time_min=avg_travel,
            objective_value=f"Min Travel Time (Local Heuristic) = {int(round(total_travel_time))} min; Unassigned = {len(unassigned)}",
            explanation=(
                "Greedy algorithm prioritizes immediate local travel time for the most critical active incidents. "
                "While fast and simple, it can deplete specialized cold-storage capacity needed by subsequent incidents."
            ),
            assumptions=[
                "Incidents sorted and processed sequentially by severity and backup runtime.",
                "Selects the nearest feasible facility satisfying instantaneous safety constraints.",
                "No backtracking or global redistribution of already assigned capacity.",
            ],
            limitations=[
                "Locally optimal choices frequently lead to globally sub-optimal fleet outcomes.",
                "Does not reserve specialized ultra-low temperature facilities for critical cargo.",
                "Risk of leaving later incidents unassigned when local capacity is consumed early.",
            ],
        )
