export type StatusLevel =
  | 'critical'
  | 'warning'
  | 'safe'
  | 'blocked'
  | 'pending'
  | 'unknown'
  | 'stale'
  | 'offline';

export type ReliabilityState =
  | 'idle'
  | 'loading'
  | 'success'
  | 'error'
  | 'stale'
  | 'offline'
  | 'empty';

export type DataSourceMode = 'demo' | 'live';

export interface Cargo {
  cargo_id: string;
  cargo_type: string;
  cargo_kg: number;
  current_temperature_c: number | null;
  safe_temperature_min: number;
  safe_temperature_max: number;
  spoilage_deadline: string | null; // ISO UTC
  estimate_source: string;
  estimate_confidence: 'high' | 'medium' | 'approximate' | 'unknown';
  physics_safe_window_min?: number;
  surrogate_safe_window_min?: number;
  effective_safe_window_min?: number;
  fallback_reason?: string;
}

export type PowerState = 'operational' | 'failed' | 'degraded' | 'unknown' | 'stale';
export type CoolingState = 'operational' | 'failed' | 'degraded' | 'unknown' | 'stale';

export interface Incident {
  incident_id: string;
  title: string;
  power_failure_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'active' | 'evaluating' | 'allocated' | 'en_route' | 'delivered' | 'resolved';
  detected_at: string; // ISO UTC
  location: string;
  power_state: PowerState;
  cooling_status: CoolingState;
  backup_power_source: string | null;
  backup_runtime_min: number | null;
  runtime_last_updated: string; // ISO UTC
  cargo: Cargo;
}

export interface Receiver {
  receiver_id: string;
  name: string;
  location: string;
  total_capacity_kg: number;
  available_capacity_kg: number;
  compatible_cargo_types: string[];
  temp_range_min: number;
  temp_range_max: number;
  power_source: string;
  backup_runtime_min: number | null;
  cooling_status: CoolingState;
  operational_availability: 'available' | 'at_capacity' | 'maintenance' | 'offline';
  unloading_duration_min: number;
  travel_time_min: number;
  distance_km: number;
  freshness_timestamp: string; // ISO UTC
}

export interface DecisionHistoryEntry {
  timestamp: string;
  actor: string;
  action: string;
  note?: string;
}

export type AssignmentStatus =
  | 'proposed'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'acknowledged'
  | 'declined'
  | 'en_route'
  | 'arrived'
  | 'handoff_submitted'
  | 'accepted'
  | 'completed';

export interface Assignment {
  assignment_id: string;
  incident_id: string;
  receiver_id: string;
  cargo_kg: number;
  status: AssignmentStatus;
  driver_id: string;
  driver_name: string;
  pickup_location: string;
  destination_location: string;
  estimated_arrival: string;
  safety_instructions: string[];
  contact_phone: string | null;
  decision_history: DecisionHistoryEntry[];
  rejection_reason?: string;
  decline_reason?: string;
  receiver_rejection_reason?: string;
  handoff_notes?: string;
  progress_stage?: 'assigned' | 'departed' | 'halfway' | 'arriving' | 'arrived';
}

export interface RuleEvaluation {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  severity: 'critical' | 'warning' | 'info';
  details: string;
  measured_value: string;
  required_threshold: string;
}

export interface PolicyAssessment {
  is_safe: boolean;
  is_hard_blocked: boolean;
  rule_evaluations: RuleEvaluation[];
  hard_block_reasons: string[];
  warnings: string[];
  alternative_receiver_ids: string[];
}

export interface ApprovalRequest {
  approval_id: string;
  assignment_id: string;
  incident_id: string;
  proposed_receiver_id: string;
  status: 'pending' | 'approved' | 'rejected' | 'reassessment_requested';
  policy_assessment: PolicyAssessment;
  requester: string;
  approver?: string;
  decided_at?: string;
  comments?: string;
}

export interface AllocationPlan {
  strategy: 'greedy' | 'global';
  scenario_name: string;
  assignments: Array<{
    incident_id: string;
    receiver_id: string;
    cargo_kg: number;
    feasible: boolean;
    rejection_reason?: string;
    travel_time_min: number;
    spoilage_margin_min: number;
  }>;
  unassigned_incidents: string[];
  capacity_utilization_pct: number;
  total_spoilage_risk_score: number; // 0-100 (lower is safer)
  average_travel_time_min: number;
  objective_value: string;
  explanation: string;
  assumptions: string[];
  limitations: string[];
}

export interface AuditEvent {
  event_id: string;
  event_type: string;
  occurred_at: string; // ISO UTC
  schema_version: string;
  incident_id?: string;
  correlation_id: string;
  idempotency_key: string;
  actor: string;
  action: string;
  entity_reference: string;
  description: string;
  source: 'simulated_local' | 'live_aws';
  outcome: 'success' | 'failure' | 'blocked';
  details?: Record<string, any>;
}

export interface ActionContract {
  action_name: string;
  screen: string;
  initiating_control: string;
  required_input: string;
  preconditions: string;
  expected_success: string;
  validation_failure: string;
  network_failure: string;
  duplicate_behavior: string;
  source_type: 'demo_local' | 'api_backed';
  audit_effect: string;
}
