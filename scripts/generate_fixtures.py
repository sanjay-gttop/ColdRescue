"""Generate all fixture JSON files for data/fixtures/."""
import json
import sys

sys.path.insert(0, ".")

from datetime import datetime, timezone

from backend.schemas.approval import ApprovalDecision, ApprovalEvent
from backend.schemas.assignment import AssignmentEvent
from backend.schemas.audit_event import AuditAction, AuditEvent
from backend.schemas.cargo import CargoEvent, CargoSensitivity
from backend.schemas.incident import IncidentEvent, IncidentType
from backend.schemas.prediction import PredictionEvent
from backend.schemas.receiver import ReceiverCategory, ReceiverEvent
from backend.schemas.route import RouteEvent

ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
base = dict(
    event_id="evt_fix_001",
    occurred_at=ts,
    schema_version="1.0.0",
    correlation_id="corr_fix_001",
    idempotency_key="ikey_fix_001",
)

# incident
inc = IncidentEvent(
    **base,
    event_type="incident.created",
    incident_id="inc_fix_001",
    incident_type=IncidentType.REEFER_UNIT_FAILURE,
    location_id="truck_09",
    location_name="Delivery Truck 09",
    reported_by="operator_01",
)
with open("data/fixtures/incident.json", "w") as f:
    f.write(inc.model_dump_json(indent=2))

# cargo
cargo = CargoEvent(
    **{**base, "event_id": "evt_fix_002", "idempotency_key": "ikey_fix_002"},
    event_type="cargo.profile",
    incident_id="inc_fix_001",
    cargo_description="Mixed dairy produce",
    cargo_kg=500.0,
    safe_temperature_min_c=2.0,
    safe_temperature_max_c=8.0,
    backup_runtime_min=90.0,
    available_capacity_kg=1000.0,
    unloading_duration_min=30.0,
    time_sensitivity=CargoSensitivity.HIGH,
)
with open("data/fixtures/cargo.json", "w") as f:
    f.write(cargo.model_dump_json(indent=2))

# receiver
rcv = ReceiverEvent(
    **{**base, "event_id": "evt_fix_003", "idempotency_key": "ikey_fix_003"},
    event_type="receiver.profile",
    receiver_id="recv_01",
    receiver_name="Arctic Cold Logistics Hub",
    category=ReceiverCategory.COLD_STORAGE_FACILITY,
    capacity_kg=5000.0,
    current_load_kg=1000.0,
    accepts_temperature_min_c=-25.0,
    accepts_temperature_max_c=8.0,
)
with open("data/fixtures/receiver.json", "w") as f:
    f.write(rcv.model_dump_json(indent=2))

# prediction
pred = PredictionEvent(
    **{**base, "event_id": "evt_fix_004", "idempotency_key": "ikey_fix_004"},
    event_type="prediction.thermal_progression",
    incident_id="inc_fix_001",
    prediction_type="THERMAL_PROGRESSION",
    predicted_temperature_c=12.0,
    time_to_spoilage_min=43.0,
    confidence=0.6,
    assumptions="ESTIMATE ONLY - not validated for food-safety decisions.",
)
with open("data/fixtures/prediction.json", "w") as f:
    f.write(pred.model_dump_json(indent=2))

# route
route = RouteEvent(
    **{**base, "event_id": "evt_fix_005", "idempotency_key": "ikey_fix_005"},
    event_type="route.planned",
    incident_id="inc_fix_001",
    route_id="route_01",
    driver_id="driver_01",
    receiver_id="recv_01",
    total_distance_km=15.0,
    estimated_duration_min=25.0,
)
with open("data/fixtures/route.json", "w") as f:
    f.write(route.model_dump_json(indent=2))

# assignment
assign = AssignmentEvent(
    **{**base, "event_id": "evt_fix_006", "idempotency_key": "ikey_fix_006"},
    event_type="assignment.created",
    incident_id="inc_fix_001",
    assignment_id="assign_01",
    receiver_id="recv_01",
    driver_id="driver_01",
    cargo_kg=500.0,
)
with open("data/fixtures/assignment.json", "w") as f:
    f.write(assign.model_dump_json(indent=2))

# approval
appr = ApprovalEvent(
    **{**base, "event_id": "evt_fix_007", "idempotency_key": "ikey_fix_007"},
    event_type="approval.granted",
    incident_id="inc_fix_001",
    approval_id="appr_01",
    assignment_id="assign_01",
    decision=ApprovalDecision.APPROVED,
    approved_by="operator_jane",
)
with open("data/fixtures/approval.json", "w") as f:
    f.write(appr.model_dump_json(indent=2))

# audit
audit = AuditEvent(
    **{**base, "event_id": "evt_fix_008", "idempotency_key": "ikey_fix_008"},
    event_type="audit.simulation_started",
    action=AuditAction.SIMULATION_STARTED,
    actor="simulator.engine",
    details={"scenario_id": "REEFER_UNIT_FAILURE", "seed": 42},
)
with open("data/fixtures/audit_event.json", "w") as f:
    f.write(audit.model_dump_json(indent=2))

print("All 8 fixture files written successfully.")
