import { describe, it, expect } from 'vitest';
import { evaluateColdChainPolicy } from '../utils/policyEngine';
import { Incident, Receiver } from '../types';
import { INITIAL_INCIDENTS, INITIAL_RECEIVERS } from '../data/mockData';

describe('ColdChain Policy Engine', () => {
  const baseIncident: Incident = INITIAL_INCIDENTS.find((i) => i.incident_id === 'INC-2026-081') || INITIAL_INCIDENTS[0]; // mRNA Vaccines, 2400kg, -80 to -60C
  const validReceiver: Receiver = INITIAL_RECEIVERS[0]; // St Jude, 8500kg avail, -85 to 10C, active cooling

  it('passes all critical safety checks when receiver is compatible and has sufficient capacity', () => {
    const assessment = evaluateColdChainPolicy(baseIncident, validReceiver);
    expect(assessment.is_safe).toBe(true);
    expect(assessment.is_hard_blocked).toBe(false);
    expect(assessment.hard_block_reasons).toHaveLength(0);
  });

  it('triggers a hard block when receiver capacity is insufficient for cargo mass', () => {
    const smallReceiver: Receiver = {
      ...validReceiver,
      available_capacity_kg: 500, // Cargo requires 2400kg
    };
    const assessment = evaluateColdChainPolicy(baseIncident, smallReceiver);
    expect(assessment.is_safe).toBe(false);
    expect(assessment.is_hard_blocked).toBe(true);
    expect(assessment.hard_block_reasons.some((r) => r.includes('Capacity Exceeded'))).toBe(true);
  });

  it('triggers a hard block when cargo type is not certified by receiver', () => {
    const incompatibleReceiver: Receiver = {
      ...validReceiver,
      compatible_cargo_types: ['Fresh Produce', 'Frozen Seafood'],
    };
    const assessment = evaluateColdChainPolicy(baseIncident, incompatibleReceiver);
    expect(assessment.is_hard_blocked).toBe(true);
    expect(assessment.hard_block_reasons.some((r) => r.includes('Incompatible Cargo Type'))).toBe(true);
  });

  it('triggers a hard block when receiver temperature envelope does not cover required limits', () => {
    const warmReceiver: Receiver = {
      ...validReceiver,
      temp_range_min: -20.0, // Cargo requires -80C min
      temp_range_max: 5.0,
    };
    const assessment = evaluateColdChainPolicy(baseIncident, warmReceiver);
    expect(assessment.is_hard_blocked).toBe(true);
    expect(assessment.hard_block_reasons.some((r) => r.includes('Temperature Envelope Mismatch'))).toBe(true);
  });

  it('triggers a hard block when receiver cooling plant has failed', () => {
    const failedCoolingReceiver: Receiver = {
      ...validReceiver,
      cooling_status: 'failed',
    };
    const assessment = evaluateColdChainPolicy(baseIncident, failedCoolingReceiver);
    expect(assessment.is_hard_blocked).toBe(true);
    expect(assessment.hard_block_reasons.some((r) => r.includes('Cooling Failure'))).toBe(true);
  });

  it('enforces travel time buffer against spoilage deadline', () => {
    const farReceiver: Receiver = {
      ...validReceiver,
      travel_time_min: 60, // Exceeds remaining safe margin (45 min)
    };
    const assessment = evaluateColdChainPolicy(baseIncident, farReceiver);
    expect(assessment.is_hard_blocked).toBe(true);
    expect(assessment.hard_block_reasons.some((r) => r.includes('Thermal Deadline Infeasible'))).toBe(true);
  });
});
