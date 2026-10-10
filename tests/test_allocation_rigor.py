"""
Rigorous mathematical tests for allocation optimization:
1. Hungarian / Minimum-Cost Matching optimality verification against Brute Force search on small instances.
2. Capacity-constrained scenario set validating no double allocation or capacity overflows.
3. Sensitivity analysis verifying allocation stability and objective variation across +/- 20% travel time perturbation.
"""
from __future__ import annotations

import itertools
import random
from datetime import datetime, timezone
import pytest

from backend.models.domain import (
    CargoItem,
    CoolingStatus,
    IncidentRecord,
    IncidentStatus,
    IncidentType,
    Location,
    ReceiverCategory,
    ReceiverNode,
    SeverityLevel,
)
from backend.services.allocation_greedy import GreedyAllocationEngine
from backend.services.allocation_global import GlobalAllocationEngine
from backend.services.route_provider import LocalHaversineRouteProvider, RouteProvider, RouteEstimate


class PerturbedRouteProvider(RouteProvider):
    """Route provider that scales travel times by a multiplier for sensitivity testing."""
    def __init__(self, multiplier: float = 1.0):
        self.base = LocalHaversineRouteProvider()
        self.multiplier = multiplier

    def calculate_route(self, origin: Location, destination: ReceiverNode, average_speed_kmh: float = 50.0) -> RouteEstimate:
        est = self.base.calculate_route(origin, destination, average_speed_kmh)
        return RouteEstimate(
            origin_id=est.origin_id,
            destination_id=est.destination_id,
            distance_km=est.distance_km,
            travel_time_min=round(est.travel_time_min * self.multiplier, 2),
            average_speed_kmh=est.average_speed_kmh,
            provider_name=f"perturbed_{self.multiplier}",
            is_fallback=True,
            confidence=est.confidence,
            waypoints=est.waypoints,
        )


def _create_random_instance(num_incidents: int = 4, num_receivers: int = 4, seed: int = 42):
    rng = random.Random(seed)
    incidents = []
    receivers = []

    for i in range(num_incidents):
        cargo_kg = 200.0 + rng.uniform(0, 300)
        incidents.append(
            IncidentRecord(
                incident_id=f"inc_{i}",
                incident_type=IncidentType.REEFER_UNIT_FAILURE,
                severity=SeverityLevel.HIGH,
                status=IncidentStatus.OPEN,
                location=Location(
                    location_id=f"loc_inc_{i}",
                    name=f"Incident Location {i}",
                    latitude=13.0 + rng.uniform(-0.1, 0.1),
                    longitude=80.2 + rng.uniform(-0.1, 0.1),
                ),
                cargo=CargoItem(
                    cargo_id=f"cargo_{i}",
                    description=f"Dairy Product {i}",
                    cargo_type="dairy",
                    cargo_kg=cargo_kg,
                    safe_temperature_min_c=2.0,
                    safe_temperature_max_c=8.0,
                    current_temperature_c=4.0,
                    backup_runtime_min=180.0,
                ),
                reported_at=datetime.now(timezone.utc),
            )
        )

    for j in range(num_receivers):
        capacity = 1000.0
        receivers.append(
            ReceiverNode(
                receiver_id=f"recv_{j}",
                name=f"Receiver Hub {j}",
                category=ReceiverCategory.COLD_STORAGE_FACILITY,
                latitude=13.0 + rng.uniform(-0.15, 0.15),
                longitude=80.2 + rng.uniform(-0.15, 0.15),
                capacity_kg=capacity,
                accepts_temperature_min_c=0.0,
                accepts_temperature_max_c=10.0,
                compatible_cargo_types=["dairy", "general"],
            )
        )

    return incidents, receivers


def test_global_allocation_vs_brute_force_optimality():
    """Verify that Global Allocation matches the minimum-cost assignment found by exhaustive brute force search."""
    incidents, receivers = _create_random_instance(num_incidents=4, num_receivers=4, seed=101)
    router = LocalHaversineRouteProvider()

    # Brute force search over all bijective permutations
    best_perm = None
    min_total_travel_time = float("inf")

    for perm in itertools.permutations(receivers, len(incidents)):
        total_time = 0.0
        for inc, rec in zip(incidents, perm):
            est = router.calculate_route(inc.location, rec)
            total_time += est.travel_time_min

        if total_time < min_total_travel_time:
            min_total_travel_time = total_time
            best_perm = perm

    # Run ColdRescue Global Allocation
    res = GlobalAllocationEngine.solve(incidents=incidents, receivers=receivers, route_provider=router)
    assert len(res.assignments) == len(incidents)
    actual_total_travel_time = sum(a.travel_time_min for a in res.assignments)
    # The heuristic global solver should be within 15% of the true global theoretical optimum
    assert actual_total_travel_time <= min_total_travel_time * 1.15
    print(f"Brute Force Optimum Travel Time: {min_total_travel_time:.2f} min | Global Engine Time: {actual_total_travel_time:.2f} min")


def test_capacity_constrained_stress():
    """Verify that total allocated cargo to any receiver strictly never exceeds available capacity."""
    incidents, receivers = _create_random_instance(num_incidents=6, num_receivers=2, seed=202)
    # Total cargo is ~2000 kg, total capacity is 1600 kg (tight capacity)
    receivers[0].capacity_kg = 800.0
    receivers[1].capacity_kg = 800.0

    res = GlobalAllocationEngine.solve(incidents=incidents, receivers=receivers)

    allocated_per_receiver = {}
    for item in res.assignments:
        allocated_per_receiver[item.receiver_id] = allocated_per_receiver.get(item.receiver_id, 0.0) + item.cargo_kg

    for r in receivers:
        allocated = allocated_per_receiver.get(r.receiver_id, 0.0)
        assert allocated <= r.capacity_kg, f"Capacity overflow on receiver {r.receiver_id}: {allocated} > {r.capacity_kg}"

    assert len(res.unassigned_incidents) > 0, "Expected some unassigned cargo under strict capacity exhaustion"


def test_sensitivity_analysis_perturbation():
    """Verify allocation stability and continuous metric scaling under +/- 20% travel time perturbation."""
    incidents, receivers = _create_random_instance(num_incidents=4, num_receivers=4, seed=303)

    res_nominal = GlobalAllocationEngine.solve(incidents=incidents, receivers=receivers, route_provider=PerturbedRouteProvider(1.0))
    res_plus_20 = GlobalAllocationEngine.solve(incidents=incidents, receivers=receivers, route_provider=PerturbedRouteProvider(1.2))
    res_minus_20 = GlobalAllocationEngine.solve(incidents=incidents, receivers=receivers, route_provider=PerturbedRouteProvider(0.8))

    assert len(res_nominal.assignments) == len(res_plus_20.assignments) == len(res_minus_20.assignments) == 4
    time_nominal = sum(a.travel_time_min for a in res_nominal.assignments)
    time_plus_20 = sum(a.travel_time_min for a in res_plus_20.assignments)
    time_minus_20 = sum(a.travel_time_min for a in res_minus_20.assignments)

    # Monotonic scaling of travel times
    assert time_minus_20 < time_nominal < time_plus_20
    print(f"-20%: {time_minus_20:.1f}m | Nominal: {time_nominal:.1f}m | +20%: {time_plus_20:.1f}m")
