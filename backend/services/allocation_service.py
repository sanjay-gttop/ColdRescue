"""
ColdRescue Master Allocation and Recovery Orchestration Service.

Integrates:
  - ThermalRiskService (safe window and breach prediction)
  - RouteProvider (Haversine distance and transit estimation)
  - SafetyPolicyEngine (mandatory 6-rule compliance verification)
  - GreedyAllocationEngine (fast sequential first-feasible matching)
  - GlobalAllocationEngine (multi-incident coordinated balanced solver)
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.domain import IncidentRecord, ReceiverNode
from backend.policies.safety_policy import PolicyAssessment, SafetyPolicyEngine
from backend.services.allocation_global import GlobalAllocationEngine
from backend.services.allocation_greedy import AllocationResult, GreedyAllocationEngine
from backend.services.route_provider import LocalHaversineRouteProvider, RouteEstimate, RouteProvider
from backend.services.thermal_risk import ThermalRiskAssessment, ThermalRiskService


class CandidateEvaluation(BaseModel):
    receiver_id: str
    receiver_name: str
    route_estimate: RouteEstimate
    policy_assessment: PolicyAssessment
    overall_feasible: bool
    score: float


class SingleIncidentRecoveryEvaluation(BaseModel):
    incident_id: str
    thermal_risk: ThermalRiskAssessment
    candidate_evaluations: List[CandidateEvaluation]
    recommended_receiver_id: Optional[str] = None
    recommended_receiver_name: Optional[str] = None
    is_recoverable: bool = False
    explanation: str


class StrategyComparisonResult(BaseModel):
    scenario_name: str
    greedy_plan: AllocationResult
    global_plan: AllocationResult
    comparison_summary: str
    recommended_strategy: str


class AllocationService:
    """Coordinating service orchestrating rescue assessments and fleet allocations."""

    def __init__(self, route_provider: Optional[RouteProvider] = None) -> None:
        self.route_provider = route_provider or LocalHaversineRouteProvider()

    def evaluate_incident_recovery(
        self,
        incident: IncidentRecord,
        receivers: List[ReceiverNode],
        ambient_temperature_c: float = 25.0,
    ) -> SingleIncidentRecoveryEvaluation:
        """
        Perform a comprehensive recovery evaluation for a single incident.

        Assesses:
          1. Thermal risk & safe window
          2. Routes to all receivers
          3. Safety policy compliance for each candidate
          4. Recommended destination
        """
        # 1. Thermal risk assessment
        thermal_risk = ThermalRiskService.evaluate_cargo_thermal_risk(
            cargo=incident.cargo,
            ambient_temperature_c=ambient_temperature_c,
        )

        candidate_evals: List[CandidateEvaluation] = []
        best_receiver: Optional[ReceiverNode] = None
        best_score = float("inf")

        for r in receivers:
            route = self.route_provider.calculate_route(incident.location, r)
            policy = SafetyPolicyEngine.evaluate_assignment(
                incident=incident,
                receiver=r,
                travel_time_min=route.travel_time_min,
                ambient_temperature_c=ambient_temperature_c,
            )

            is_feasible = policy.is_safe and (r.available_capacity_kg >= incident.cargo.cargo_kg)
            score = route.travel_time_min if is_feasible else float("inf")

            candidate_evals.append(
                CandidateEvaluation(
                    receiver_id=r.receiver_id,
                    receiver_name=r.name,
                    route_estimate=route,
                    policy_assessment=policy,
                    overall_feasible=is_feasible,
                    score=score,
                )
            )

            if is_feasible and score < best_score:
                best_score = score
                best_receiver = r

        is_recoverable = best_receiver is not None
        if is_recoverable and best_receiver:
            explanation = (
                f"Incident '{incident.incident_id}' is safely recoverable. "
                f"Recommended destination is '{best_receiver.name}' ({best_receiver.receiver_id}) "
                f"with estimated travel time of {best_score:.1f} min within safe window of {thermal_risk.estimated_safe_window_min:.1f} min."
            )
        else:
            explanation = (
                f"Incident '{incident.incident_id}' has NO feasible receiving facility satisfying "
                f"capacity, temperature envelope, and travel deadline simultaneously."
            )

        return SingleIncidentRecoveryEvaluation(
            incident_id=incident.incident_id,
            thermal_risk=thermal_risk,
            candidate_evaluations=candidate_evals,
            recommended_receiver_id=best_receiver.receiver_id if best_receiver else None,
            recommended_receiver_name=best_receiver.name if best_receiver else None,
            is_recoverable=is_recoverable,
            explanation=explanation,
        )

    def solve_allocation(
        self,
        incidents: List[IncidentRecord],
        receivers: List[ReceiverNode],
        strategy: str = "global",
        scenario_name: str = "Active Fleet Coordination",
        ambient_temperature_c: float = 25.0,
    ) -> AllocationResult:
        """Execute either greedy or global multi-incident allocation."""
        if strategy.lower() == "greedy":
            return GreedyAllocationEngine.solve(
                incidents=incidents,
                receivers=receivers,
                scenario_name=scenario_name,
                route_provider=self.route_provider,
                ambient_temperature_c=ambient_temperature_c,
            )
        else:
            return GlobalAllocationEngine.solve(
                incidents=incidents,
                receivers=receivers,
                scenario_name=scenario_name,
                route_provider=self.route_provider,
                ambient_temperature_c=ambient_temperature_c,
            )

    def compare_strategies(
        self,
        incidents: List[IncidentRecord],
        receivers: List[ReceiverNode],
        scenario_name: str = "Strategy Comparison",
        ambient_temperature_c: float = 25.0,
    ) -> StrategyComparisonResult:
        """Run both Greedy and Global solvers side-by-side and return comparative analysis."""
        greedy_plan = GreedyAllocationEngine.solve(
            incidents=incidents,
            receivers=receivers,
            scenario_name=scenario_name,
            route_provider=self.route_provider,
            ambient_temperature_c=ambient_temperature_c,
        )
        global_plan = GlobalAllocationEngine.solve(
            incidents=incidents,
            receivers=receivers,
            scenario_name=scenario_name,
            route_provider=self.route_provider,
            ambient_temperature_c=ambient_temperature_c,
        )

        unassigned_diff = len(greedy_plan.unassigned_incidents) - len(global_plan.unassigned_incidents)
        if unassigned_diff > 0:
            summary = (
                f"Global strategy successfully allocates {unassigned_diff} more incident(s) than Greedy by "
                f"intelligently reserving specialized cold vaults and balancing regional capacity."
            )
            recommended = "global"
        else:
            summary = (
                f"Both strategies allocated all incidents. Global achieved spoilage risk score of {global_plan.total_spoilage_risk_score} "
                f"vs Greedy score of {greedy_plan.total_spoilage_risk_score}."
            )
            recommended = "global" if global_plan.total_spoilage_risk_score <= greedy_plan.total_spoilage_risk_score else "greedy"

        return StrategyComparisonResult(
            scenario_name=scenario_name,
            greedy_plan=greedy_plan,
            global_plan=global_plan,
            comparison_summary=summary,
            recommended_strategy=recommended,
        )
