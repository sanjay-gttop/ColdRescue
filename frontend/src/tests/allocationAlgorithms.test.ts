import { describe, it, expect } from 'vitest';
import { runGreedyAllocation, runGlobalAllocation } from '../utils/allocationAlgorithms';
import { INITIAL_INCIDENTS, INITIAL_RECEIVERS } from '../data/mockData';

describe('Greedy vs. Global Allocation Algorithms', () => {
  it('runs greedy allocation deterministically and produces metrics and explanations', () => {
    const plan = runGreedyAllocation(INITIAL_INCIDENTS, INITIAL_RECEIVERS, 'Test Scenario');
    expect(plan.strategy).toBe('greedy');
    expect(plan.assignments.length).toBe(INITIAL_INCIDENTS.length);
    expect(plan.capacity_utilization_pct).toBeGreaterThan(0);
    expect(plan.explanation).toBeDefined();
    expect(plan.limitations.length).toBeGreaterThan(0);
  });

  it('runs global allocation and minimizes aggregate thermal risk score compared to greedy', () => {
    const greedyPlan = runGreedyAllocation(INITIAL_INCIDENTS, INITIAL_RECEIVERS, 'Test Scenario');
    const globalPlan = runGlobalAllocation(INITIAL_INCIDENTS, INITIAL_RECEIVERS, 'Test Scenario');

    expect(globalPlan.strategy).toBe('global');
    expect(globalPlan.assignments.length).toBe(INITIAL_INCIDENTS.length);
    // Global risk score should be strictly equal or lower due to multi-facility balancing
    expect(globalPlan.total_spoilage_risk_score).toBeLessThanOrEqual(greedyPlan.total_spoilage_risk_score);
    expect(globalPlan.assumptions).toBeDefined();
  });

  it('handles infeasible assignments properly when capacities are exhausted', () => {
    const tinyReceivers = INITIAL_RECEIVERS.map((r) => ({
      ...r,
      available_capacity_kg: 100, // Tiny capacity, cannot fit any cargo
    }));

    const greedyPlan = runGreedyAllocation(INITIAL_INCIDENTS, tinyReceivers, 'Exhaustion Scenario');
    expect(greedyPlan.unassigned_incidents.length).toBe(INITIAL_INCIDENTS.length);
    expect(greedyPlan.assignments.every((a) => !a.feasible)).toBe(true);
  });
});
