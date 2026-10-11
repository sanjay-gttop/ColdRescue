"""ColdRescue Allocation & Recovery API endpoints."""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.models.domain import IncidentRecord, ReceiverNode
from backend.services.allocation_service import (
    AllocationService,
    SingleIncidentRecoveryEvaluation,
    StrategyComparisonResult,
    AllocationResult,
)

router = APIRouter(prefix="/allocation", tags=["allocation"])
service = AllocationService()


class EvaluateIncidentRequest(BaseModel):
    incident: IncidentRecord
    receivers: List[ReceiverNode]
    ambient_temperature_c: float = 25.0


class SolveAllocationRequest(BaseModel):
    incidents: List[IncidentRecord]
    receivers: List[ReceiverNode]
    strategy: str = Field(default="global", description="'greedy' or 'global'")
    scenario_name: str = "Live API Request"
    ambient_temperature_c: float = 25.0


class CompareStrategiesRequest(BaseModel):
    incidents: List[IncidentRecord]
    receivers: List[ReceiverNode]
    scenario_name: str = "Live Strategy Comparison"
    ambient_temperature_c: float = 25.0


@router.post("/evaluate", response_model=SingleIncidentRecoveryEvaluation)
async def evaluate_incident_recovery(payload: EvaluateIncidentRequest) -> SingleIncidentRecoveryEvaluation:
    """Evaluate thermal risk, routes, safety policy compliance, and best receiver for an incident."""
    if not payload.receivers:
        raise HTTPException(status_code=400, detail="At least one candidate receiver must be provided.")
    return service.evaluate_incident_recovery(
        incident=payload.incident,
        receivers=payload.receivers,
        ambient_temperature_c=payload.ambient_temperature_c,
    )


@router.post("/solve", response_model=AllocationResult)
async def solve_fleet_allocation(payload: SolveAllocationRequest) -> AllocationResult:
    """Solve multi-incident allocation across available receivers using greedy or global strategy."""
    if not payload.incidents:
        raise HTTPException(status_code=400, detail="At least one incident must be provided.")
    if not payload.receivers:
        raise HTTPException(status_code=400, detail="At least one receiver must be provided.")
    return service.solve_allocation(
        incidents=payload.incidents,
        receivers=payload.receivers,
        strategy=payload.strategy,
        scenario_name=payload.scenario_name,
        ambient_temperature_c=payload.ambient_temperature_c,
    )


@router.post("/compare", response_model=StrategyComparisonResult)
async def compare_allocation_strategies(payload: CompareStrategiesRequest) -> StrategyComparisonResult:
    """Execute both Greedy and Global solvers on the given fleet dataset and return comparison."""
    if not payload.incidents:
        raise HTTPException(status_code=400, detail="At least one incident must be provided.")
    if not payload.receivers:
        raise HTTPException(status_code=400, detail="At least one receiver must be provided.")
    return service.compare_strategies(
        incidents=payload.incidents,
        receivers=payload.receivers,
        scenario_name=payload.scenario_name,
        ambient_temperature_c=payload.ambient_temperature_c,
    )


class BenchmarkRequest(BaseModel):
    scenario_count: int = Field(default=50, ge=1, le=100)
    seed: int = Field(default=42)


@router.post("/benchmark")
async def execute_counterfactual_benchmark(payload: BenchmarkRequest = BenchmarkRequest()) -> Dict[str, Any]:
    """Execute 50 reproducible synthetic rescue scenarios comparing manual, greedy, and global solvers."""
    from scripts.run_stress_benchmark import generate_benchmark_scenarios, run_benchmark
    scenarios = generate_benchmark_scenarios(count=payload.scenario_count, seed=payload.seed)
    results = run_benchmark(scenarios)
    results["seed"] = payload.seed
    results["benchmark_version"] = "1.0.0"
    results["disclosure"] = "Illustrative estimate based on stated simulation assumptions, not measured real-world savings."
    return results

