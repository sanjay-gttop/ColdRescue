"""ColdRescue services package."""

from backend.services.thermal_risk import (
    DoorEvent,
    ThermalInput,
    ThermalPrediction,
    THERMAL_MODEL_VERSION,
    prediction_to_dict,
    simulate_thermal_risk,
    ThermalRiskService,
    ThermalRiskAssessment,
    ThermalRiskLevel,
)

from backend.services.route_provider import (
    RouteProvider,
    LocalHaversineRouteProvider,
    RouteEstimate,
    WaypointCoordinate,
)

from backend.services.allocation_greedy import (
    GreedyAllocationEngine,
    AllocationResult,
    AssignmentPlanItem,
)

from backend.services.allocation_global import (
    GlobalAllocationEngine,
)

from backend.services.allocation_service import (
    AllocationService,
    SingleIncidentRecoveryEvaluation,
    StrategyComparisonResult,
    CandidateEvaluation,
)

__all__ = [
    # Thermal simulation & assessment
    "DoorEvent",
    "ThermalInput",
    "ThermalPrediction",
    "THERMAL_MODEL_VERSION",
    "prediction_to_dict",
    "simulate_thermal_risk",
    "ThermalRiskService",
    "ThermalRiskAssessment",
    "ThermalRiskLevel",

    # Routing
    "RouteProvider",
    "LocalHaversineRouteProvider",
    "RouteEstimate",
    "WaypointCoordinate",

    # Allocation
    "GreedyAllocationEngine",
    "GlobalAllocationEngine",
    "AllocationResult",
    "AssignmentPlanItem",
    "AllocationService",
    "SingleIncidentRecoveryEvaluation",
    "StrategyComparisonResult",
    "CandidateEvaluation",
]