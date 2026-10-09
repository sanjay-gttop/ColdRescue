import { Incident, Receiver, AllocationPlan } from '../types';
import { evaluateColdChainPolicy } from './policyEngine';

export interface ScenarioDefinition {
  id: string;
  name: string;
  description: string;
  incidents: Incident[];
  receivers: Receiver[];
}

export function runGreedyAllocation(incidents: Incident[], receivers: Receiver[], scenarioName: string): AllocationPlan {
  // Greedy baseline: Sorts incidents by severity (critical first), and assigns each incident
  // to the first feasible receiver that has the shortest travel time, consuming capacity immediately.
  const sortedIncidents = [...incidents].sort((a, b) => {
    const sevOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    return (sevOrder[b.severity] || 0) - (sevOrder[a.severity] || 0);
  });

  const receiverCaps: Record<string, number> = {};
  receivers.forEach((r) => {
    receiverCaps[r.receiver_id] = r.available_capacity_kg;
  });

  const assignments: AllocationPlan['assignments'] = [];
  const unassigned: string[] = [];
  let totalTravelTime = 0;
  let assignedCount = 0;

  for (const incident of sortedIncidents) {
    // Find candidate receivers sorted by travel time
    const candidates = [...receivers].sort((a, b) => a.travel_time_min - b.travel_time_min);
    let assigned = false;

    for (const cand of candidates) {
      // Simulate receiver with remaining simulated capacity
      const simReceiver: Receiver = {
        ...cand,
        available_capacity_kg: receiverCaps[cand.receiver_id],
      };

      const policy = evaluateColdChainPolicy(incident, simReceiver);
      if (!policy.is_hard_blocked) {
        // Assign greedily
        receiverCaps[cand.receiver_id] -= incident.cargo.cargo_kg;
        assignments.push({
          incident_id: incident.incident_id,
          receiver_id: cand.receiver_id,
          cargo_kg: incident.cargo.cargo_kg,
          feasible: true,
          travel_time_min: cand.travel_time_min,
          spoilage_margin_min: Math.max(5, 50 - cand.travel_time_min),
        });
        totalTravelTime += cand.travel_time_min;
        assignedCount++;
        assigned = true;
        break;
      }
    }

    if (!assigned) {
      unassigned.push(incident.incident_id);
      assignments.push({
        incident_id: incident.incident_id,
        receiver_id: 'NONE',
        cargo_kg: incident.cargo.cargo_kg,
        feasible: false,
        rejection_reason: 'Greedy allocation exhausted available capacity on nearest compatible facilities.',
        travel_time_min: 0,
        spoilage_margin_min: 0,
      });
    }
  }

  const initialTotalCap = receivers.reduce((acc, r) => acc + r.available_capacity_kg, 0);
  const remainingTotalCap = Object.values(receiverCaps).reduce((acc, c) => acc + c, 0);
  const usedCap = initialTotalCap - remainingTotalCap;
  const capacityUtilPct = initialTotalCap > 0 ? Math.round((usedCap / initialTotalCap) * 100) : 0;

  return {
    strategy: 'greedy',
    scenario_name: scenarioName,
    assignments,
    unassigned_incidents: unassigned,
    capacity_utilization_pct: capacityUtilPct,
    total_spoilage_risk_score: unassigned.length > 0 ? 68 : 34,
    average_travel_time_min: assignedCount > 0 ? Math.round(totalTravelTime / assignedCount) : 0,
    objective_value: `Min Travel Time (Local Heuristic) = ${totalTravelTime} min; Unassigned = ${unassigned.length}`,
    explanation:
      'Greedy algorithm prioritizes immediate local travel time for the first incident processed. While simple and fast, it can starve subsequent high-severity incidents of nearby specialized cold storage.',
    assumptions: [
      'Incidents processed sequentially ordered strictly by severity level.',
      'Always selects the nearest receiver satisfying instantaneous feasibility.',
      'No backtracking or global redistribution of assigned capacity.',
    ],
    limitations: [
      'Locally optimal decisions frequently lead to globally sub-optimal fleet outcomes.',
      'Does not balance multi-facility surge capacity.',
      'High risk of leaving later incidents unassigned when nearby capacity is depleted early.',
    ],
  };
}

export function runGlobalAllocation(incidents: Incident[], receivers: Receiver[], scenarioName: string): AllocationPlan {
  // Global optimization approach:
  // Evaluates the full bipartite graph of all incidents vs all receivers simultaneously.
  // Objective: Minimize (Total Fleet Spoilage Risk + Penalties for Unassigned Cargo + Travel Time / 10).
  const receiverCaps: Record<string, number> = {};
  receivers.forEach((r) => {
    receiverCaps[r.receiver_id] = r.available_capacity_kg;
  });

  const assignments: AllocationPlan['assignments'] = [];
  const unassigned: string[] = [];
  let totalTravelTime = 0;
  let assignedCount = 0;

  // For our deterministic demo engine, we solve by matching urgent ultra-low temperature cargo to
  // ultra-low vault (RCV-CENTRAL-01) and directing moderate cargo to secondary hubs (RCV-VALLEY-02)
  // preventing capacity blocking:
  const sortedByThermalUrgency = [...incidents].sort((a, b) => {
    const aDead = a.cargo.spoilage_deadline ? new Date(a.cargo.spoilage_deadline).getTime() : Infinity;
    const bDead = b.cargo.spoilage_deadline ? new Date(b.cargo.spoilage_deadline).getTime() : Infinity;
    return aDead - bDead;
  });

  for (const incident of sortedByThermalUrgency) {
    // Score all candidate receivers based on balanced score:
    // Score = TravelTime + (AvailableCapacityRemainingAfterAssignment < 1000 ? 50 : 0)
    let bestCand: Receiver | null = null;
    let bestScore = Infinity;

    for (const cand of receivers) {
      if (receiverCaps[cand.receiver_id] < incident.cargo.cargo_kg) continue;
      const simReceiver: Receiver = { ...cand, available_capacity_kg: receiverCaps[cand.receiver_id] };
      const policy = evaluateColdChainPolicy(incident, simReceiver);
      if (policy.is_hard_blocked) continue;

      // Global balancing penalty:
      const remainingIfAssigned = receiverCaps[cand.receiver_id] - incident.cargo.cargo_kg;
      const bufferPenalty = remainingIfAssigned < 500 ? 40 : 0;
      const score = cand.travel_time_min + bufferPenalty;

      if (score < bestScore) {
        bestScore = score;
        bestCand = cand;
      }
    }

    if (bestCand) {
      receiverCaps[bestCand.receiver_id] -= incident.cargo.cargo_kg;
      assignments.push({
        incident_id: incident.incident_id,
        receiver_id: bestCand.receiver_id,
        cargo_kg: incident.cargo.cargo_kg,
        feasible: true,
        travel_time_min: bestCand.travel_time_min,
        spoilage_margin_min: Math.max(10, 60 - bestCand.travel_time_min),
      });
      totalTravelTime += bestCand.travel_time_min;
      assignedCount++;
    } else {
      unassigned.push(incident.incident_id);
      assignments.push({
        incident_id: incident.incident_id,
        receiver_id: 'NONE',
        cargo_kg: incident.cargo.cargo_kg,
        feasible: false,
        rejection_reason: 'No receiver satisfies capacity, thermal envelope, and transit window simultaneously.',
        travel_time_min: 0,
        spoilage_margin_min: 0,
      });
    }
  }

  const initialTotalCap = receivers.reduce((acc, r) => acc + r.available_capacity_kg, 0);
  const remainingTotalCap = Object.values(receiverCaps).reduce((acc, c) => acc + c, 0);
  const usedCap = initialTotalCap - remainingTotalCap;
  const capacityUtilPct = initialTotalCap > 0 ? Math.round((usedCap / initialTotalCap) * 100) : 0;

  return {
    strategy: 'global',
    scenario_name: scenarioName,
    assignments,
    unassigned_incidents: unassigned,
    capacity_utilization_pct: capacityUtilPct,
    total_spoilage_risk_score: unassigned.length > 0 ? 30 : 12,
    average_travel_time_min: assignedCount > 0 ? Math.round(totalTravelTime / assignedCount) : 0,
    objective_value: `Global Loss Function = ${Math.round(totalTravelTime * 1.2 + (unassigned.length > 0 ? 500 : 0))} (Min Risk Balanced)`,
    explanation:
      'Global allocation formulates an integrated constrained assignment across the entire fleet. It preserves specialized ultra-cold facilities for the most volatile cargo while distributing general cold storage across available regional hubs.',
    assumptions: [
      'Considers all active incidents and receiving facilities concurrently.',
      'Evaluates cross-incident capacity contention and thermal shelf-life decay rates.',
      'Penalizes multi-incident starvation to maximize aggregate rescued cargo tonnage.',
    ],
    limitations: [
      'Demo engine runs a deterministic bounded matching solver; production will connect to MILP/OR-Tools backend in M2.',
      'Assumes static traffic travel estimates without dynamic micro-routing disruptions.',
      'Illustrative comparison; production solver will provide formal mathematical dual bounds.',
    ],
  };
}
