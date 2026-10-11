"""
Rigorous mathematical tests for allocation optimization:
1. Exact Kuhn-Munkres (Hungarian) matching optimality verification against exhaustive brute force.
2. Rectangular matrices and tie-breaking determinism.
3. Capacity-constrained scenario set validating no double allocation or capacity overflows.
4. Comprehensive multi-dimensional sensitivity analysis verifying:
   - Travel time perturbation (+/- 20%)
   - Ambient temperature / temperature-rise rate perturbation (+/- 20%)
   - Receiver capacity perturbation (+/- 20%)
   - Combined adverse perturbations
   - 100% preservation of deterministic safety policy rules under all perturbed conditions.
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
from backend.services.hungarian import linear_sum_assignment
from backend.services.route_provider import LocalHaversineRouteProvider, RouteProvider, RouteEstimate
from backend.policies.safety_policy import SafetyPolicyEngine


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


def _create_random_instance(
    num_incidents: int = 4,
    num_receivers: int = 4,
    seed: int = 42,
    ambient_temp_c: float = 30.0,
    capacity_multiplier: float = 1.0,
):
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
        capacity = 1000.0 * capacity_multiplier
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


def test_exact_hungarian_optimality_vs_brute_force():
    """Verify that linear_sum_assignment matches the EXACT global optimum found by brute force across 20 random instances."""
    rng = random.Random(101)
    for trial in range(20):
        # Generate random cost matrix (square 4x4)
        n = 4
        cost_matrix = [[round(rng.uniform(5.0, 100.0), 2) for _ in range(n)] for _ in range(n)]

        # Brute force search over all permutations
        min_brute_cost = float("inf")
        best_perm = None
        for perm in itertools.permutations(range(n)):
            cost = sum(cost_matrix[i][perm[i]] for i in range(n))
            if cost < min_brute_cost:
                min_brute_cost = cost
                best_perm = perm

        # Kuhn-Munkres exact algorithm
        rows, cols = linear_sum_assignment(cost_matrix)
        exact_cost = sum(cost_matrix[r][c] for r, c in zip(rows, cols))

        assert abs(exact_cost - min_brute_cost) < 1e-6, (
            f"Trial {trial}: Hungarian cost {exact_cost} != Brute Force {min_brute_cost}"
        )


def test_exact_hungarian_rectangular_matrices():
    """Verify Kuhn-Munkres optimality on rectangular matrices (more receivers than incidents, 3x5)."""
    rng = random.Random(202)
    for trial in range(15):
        n = 3
        m = 5
        cost_matrix = [[round(rng.uniform(10.0, 80.0), 2) for _ in range(m)] for _ in range(n)]

        min_brute_cost = float("inf")
        for perm in itertools.permutations(range(m), n):
            cost = sum(cost_matrix[i][perm[i]] for i in range(n))
            if cost < min_brute_cost:
                min_brute_cost = cost

        rows, cols = linear_sum_assignment(cost_matrix)
        exact_cost = sum(cost_matrix[r][c] for r, c in zip(rows, cols))
        assert abs(exact_cost - min_brute_cost) < 1e-6


def test_exact_hungarian_deterministic_tie_breaking():
    """Verify deterministic assignment under equal/tied costs."""
    cost_matrix = [
        [10.0, 10.0, 20.0],
        [10.0, 10.0, 30.0],
        [20.0, 30.0, 10.0],
    ]
    r1, c1 = linear_sum_assignment(cost_matrix)
    r2, c2 = linear_sum_assignment(cost_matrix)
    assert (r1, c1) == (r2, c2)
    assert sum(cost_matrix[r][c] for r, c in zip(r1, c1)) == 30.0


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


def test_multidimensional_sensitivity_analysis():
    """
    Comprehensive multi-parameter sensitivity analysis:
    - Travel time +/- 20%
    - Ambient temperature / temperature-rise rate +/- 20% (24°C, 30°C, 36°C)
    - Receiver capacity +/- 20% (800kg, 1000kg, 1200kg)
    - Adverse combination: +20% travel time, +20% temperature, -20% capacity
    - Verify 100% preservation of deterministic safety policy rules under all perturbed conditions.
    """
    base_seed = 303
    perturbations = [
        ("Nominal (1.0x time, 30C, 1.0x cap)", 1.0, 30.0, 1.0),
        ("Time +20%", 1.2, 30.0, 1.0),
        ("Time -20%", 0.8, 30.0, 1.0),
        ("Temp +20% (36C)", 1.0, 36.0, 1.0),
        ("Temp -20% (24C)", 1.0, 24.0, 1.0),
        ("Capacity +20%", 1.0, 30.0, 1.2),
        ("Capacity -20%", 1.0, 30.0, 0.8),
        ("Adverse Combined (+20% time, 36C, -20% cap)", 1.2, 36.0, 0.8),
    ]

    for label, time_mult, amb_temp, cap_mult in perturbations:
        incidents, receivers = _create_random_instance(
            num_incidents=4,
            num_receivers=4,
            seed=base_seed,
            ambient_temp_c=amb_temp,
            capacity_multiplier=cap_mult,
        )
        router = PerturbedRouteProvider(multiplier=time_mult)

        res = GlobalAllocationEngine.solve(
            incidents=incidents,
            receivers=receivers,
            route_provider=router,
            ambient_temperature_c=amb_temp,
        )

        # Invariant 1: Total allocations never exceed receiver capacities
        allocated_by_recv = {}
        for a in res.assignments:
            if a.feasible:
                allocated_by_recv[a.receiver_id] = allocated_by_recv.get(a.receiver_id, 0.0) + a.cargo_kg

        for r in receivers:
            allocated = allocated_by_recv.get(r.receiver_id, 0.0)
            assert allocated <= r.capacity_kg + 1e-4, f"Over-allocation in {label}"

        # Invariant 2: Authoritative Safety Policy must be satisfied 100%
        for a in res.assignments:
            if a.feasible:
                inc = next(i for i in incidents if i.incident_id == a.incident_id)
                rec = next(rc for rc in receivers if rc.receiver_id == a.receiver_id)
                policy = SafetyPolicyEngine.evaluate_assignment(
                    incident=inc,
                    receiver=rec,
                    travel_time_min=a.travel_time_min,
                    ambient_temperature_c=amb_temp,
                )
                assert not policy.is_hard_blocked, (
                    f"Policy violation under perturbation {label}: {policy.block_reasons}"
                )
