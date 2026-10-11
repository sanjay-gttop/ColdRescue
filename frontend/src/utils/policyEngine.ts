import { Incident, Receiver, PolicyAssessment, RuleEvaluation } from '../types';

export function evaluateColdChainPolicy(incident: Incident, receiver: Receiver): PolicyAssessment {
  const evaluations: RuleEvaluation[] = [];
  const hardBlockReasons: string[] = [];
  const warnings: string[] = [];

  const cargo = incident.cargo;

  // 1. Capacity Check
  const hasCapacity = receiver.available_capacity_kg >= cargo.cargo_kg;
  evaluations.push({
    rule_id: 'POL-CAP-001',
    rule_name: 'Available Capacity Feasibility',
    passed: hasCapacity,
    severity: 'critical',
    details: hasCapacity
      ? `Receiver has ${receiver.available_capacity_kg} kg available, which satisfies ${cargo.cargo_kg} kg requirement.`
      : `Insufficient capacity: Cargo requires ${cargo.cargo_kg} kg, but facility only has ${receiver.available_capacity_kg} kg available.`,
    measured_value: `${receiver.available_capacity_kg} kg available`,
    required_threshold: `>= ${cargo.cargo_kg} kg`,
  });
  if (!hasCapacity) {
    hardBlockReasons.push(`Capacity Exceeded: Cargo mass (${cargo.cargo_kg} kg) exceeds receiver available space (${receiver.available_capacity_kg} kg).`);
  }

  // 2. Cargo Type Compatibility
  const isTypeCompatible = receiver.compatible_cargo_types.includes(cargo.cargo_type);
  evaluations.push({
    rule_id: 'POL-COMPAT-002',
    rule_name: 'Cargo Category Compatibility',
    passed: isTypeCompatible,
    severity: 'critical',
    details: isTypeCompatible
      ? `Facility is certified for handling ${cargo.cargo_type}.`
      : `Cargo type '${cargo.cargo_type}' is NOT among certified categories for this facility: [${receiver.compatible_cargo_types.join(', ')}].`,
    measured_value: cargo.cargo_type,
    required_threshold: receiver.compatible_cargo_types.join(', '),
  });
  if (!isTypeCompatible) {
    hardBlockReasons.push(`Incompatible Cargo Type: Facility cannot handle '${cargo.cargo_type}'.`);
  }

  // 3. Thermal Envelope Match
  const tempMatches =
    receiver.temp_range_min <= cargo.safe_temperature_min &&
    receiver.temp_range_max >= cargo.safe_temperature_max;
  evaluations.push({
    rule_id: 'POL-TEMP-003',
    rule_name: 'Temperature Envelope Match',
    passed: tempMatches,
    severity: 'critical',
    details: tempMatches
      ? `Facility envelope (${receiver.temp_range_min}°C to ${receiver.temp_range_max}°C) encloses cargo safe range (${cargo.safe_temperature_min}°C to ${cargo.safe_temperature_max}°C).`
      : `Thermal mismatch: Facility range (${receiver.temp_range_min}°C to ${receiver.temp_range_max}°C) cannot safely maintain cargo range (${cargo.safe_temperature_min}°C to ${cargo.safe_temperature_max}°C).`,
    measured_value: `${receiver.temp_range_min}°C to ${receiver.temp_range_max}°C`,
    required_threshold: `${cargo.safe_temperature_min}°C to ${cargo.safe_temperature_max}°C`,
  });
  if (!tempMatches) {
    hardBlockReasons.push(`Temperature Envelope Mismatch: Receiver capabilities do not cover cargo required safe thermal limits.`);
  }

  // 4. Receiver Cooling and Power Operational Status
  const isCoolingOperational = receiver.cooling_status === 'operational';
  const isCoolingDegraded = receiver.cooling_status === 'degraded';
  const coolingPassed = isCoolingOperational || isCoolingDegraded;
  evaluations.push({
    rule_id: 'POL-COOL-004',
    rule_name: 'Receiver Cooling Plant Status',
    passed: coolingPassed,
    severity: isCoolingDegraded ? 'warning' : 'critical',
    details: isCoolingOperational
      ? 'Facility cooling infrastructure is confirmed 100% operational.'
      : isCoolingDegraded
      ? 'Facility cooling status is DEGRADED. Operational warning issued.'
      : `CRITICAL: Facility cooling has FAILED (${receiver.cooling_status}). Inflow of sensitive cargo is strictly prohibited.`,
    measured_value: `Cooling: ${receiver.cooling_status.toUpperCase()}`,
    required_threshold: 'OPERATIONAL',
  });
  if (!coolingPassed) {
    hardBlockReasons.push(`Cooling Failure: Target receiver cooling is ${receiver.cooling_status.toUpperCase()}. Cannot safely accept temperature-critical cargo.`);
  } else if (isCoolingDegraded) {
    warnings.push(`Receiver cooling is degraded. Monitor facility status closely.`);
  }

  // 5. Travel Time vs Spoilage Deadline
  let transitMarginSafe = true;
  if (cargo.spoilage_deadline) {
    const deadlineMs = new Date(cargo.spoilage_deadline).getTime();
    const remainingMs = Math.max(0, deadlineMs - Date.now());
    const remainingMin = Math.round(remainingMs / 60000);
    const requiredMin = receiver.travel_time_min + 15; // 15 min safety buffer

    transitMarginSafe = remainingMin > requiredMin;
    evaluations.push({
      rule_id: 'POL-TIME-005',
      rule_name: 'Transit Time vs Thermal Deadline',
      passed: transitMarginSafe,
      severity: 'critical',
      details: transitMarginSafe
        ? `Estimated transit (${receiver.travel_time_min} min + 15 min buffer) is within remaining safe window (${remainingMin} min).`
        : `Deadline violation: Estimated travel (${receiver.travel_time_min} min) exceeds or cuts too close to safe window (${remainingMin} min). Risk of in-transit spoilage.`,
      measured_value: `${receiver.travel_time_min}m travel (window: ${remainingMin}m)`,
      required_threshold: `< ${remainingMin - 15}m`,
    });
    if (!transitMarginSafe) {
      hardBlockReasons.push(`Thermal Deadline Infeasible: Travel time (${receiver.travel_time_min} min) exceeds allowable thermal preservation window.`);
    }
  }

  // 6. Backup Power Runtime
  const minBackupThreshold = receiver.travel_time_min + 45; // Transit + 45 min margin
  const backupPassed = (receiver.backup_runtime_min ?? 0) >= minBackupThreshold;
  evaluations.push({
    rule_id: 'POL-PWR-006',
    rule_name: 'Receiver Backup Power Reserve',
    passed: backupPassed,
    severity: 'warning',
    details: backupPassed
      ? `Facility backup runtime (${receiver.backup_runtime_min} min) exceeds recommended threshold (${minBackupThreshold} min).`
      : `Low backup reserve: Facility has ${receiver.backup_runtime_min ?? 'UNKNOWN'} min backup power, below recommended ${minBackupThreshold} min margin.`,
    measured_value: `${receiver.backup_runtime_min ?? 'N/A'} min`,
    required_threshold: `>= ${minBackupThreshold} min`,
  });
  if (!backupPassed && receiver.backup_runtime_min !== null && receiver.backup_runtime_min < 30) {
    warnings.push(`Severe backup power deficiency: only ${receiver.backup_runtime_min} minutes remaining.`);
  }

  const isHardBlocked = hardBlockReasons.length > 0;
  const isSafe = !isHardBlocked && evaluations.every((e) => e.passed || e.severity !== 'critical');

  return {
    is_safe: isSafe,
    is_hard_blocked: isHardBlocked,
    rule_evaluations: evaluations,
    hard_block_reasons: hardBlockReasons,
    warnings,
    alternative_receiver_ids: [],
  };
}
