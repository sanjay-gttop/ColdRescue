# ColdRescue — Event Schemas

> Schema version: **1.0.0** — all events must carry `"schema_version": "1.0.0"`

---

## EventEnvelope (base)

Every domain event inherits from `EventEnvelope`. Fields below are required on all events.

| Field | Type | Description |
|---|---|---|
| `event_id` | `str` | Unique event identifier (`evt_…`) |
| `event_type` | `str` | String tag identifying the event kind |
| `occurred_at` | `datetime` | Timezone-aware UTC datetime |
| `schema_version` | `str` | Must be `"1.0.0"` |
| `incident_id` | `str?` | Optional — links event to an incident |
| `correlation_id` | `str` | Request/trace correlation identifier |
| `idempotency_key` | `str` | Deduplication key |

**Validators:**
- `occurred_at` rejects naive datetimes (no tzinfo)
- `schema_version` must equal `"1.0.0"` exactly
- Extra fields are forbidden (`extra="forbid"`)

---

## IncidentEvent

**event_type:** `incident.created` / `incident.updated`

| Field | Type | Values |
|---|---|---|
| `incident_type` | `IncidentType` | See enum below |
| `status` | `IncidentStatus` | `OPEN`, `ASSIGNED`, `RESOLVED`, `CANCELLED` |
| `location_id` | `str` | Facility / vehicle identifier |
| `location_name` | `str` | Human-readable name |
| `reported_by` | `str` | Operator or sensor |
| `notes` | `str?` | Optional operator notes |

### IncidentType Enum (5 values)

| Value | Description |
|---|---|
| `REEFER_UNIT_FAILURE` | Refrigeration unit mechanical/electrical failure |
| `COLD_ROOM_POWER_OUTAGE` | Walk-in cold room lost mains power |
| `WAREHOUSE_GRID_OUTAGE` | Facility-wide grid outage |
| `BACKUP_RUNTIME_LOW` | Backup power below critical threshold |
| `BACKUP_POWER_DEPLETED` | Backup power fully exhausted |

---

## CargoEvent

**event_type:** `cargo.profile`

| Field | Type | Constraint |
|---|---|---|
| `cargo_description` | `str` | — |
| `cargo_kg` | `float` | >= 0 |
| `safe_temperature_min_c` | `float` | <= `safe_temperature_max_c` |
| `safe_temperature_max_c` | `float` | >= `safe_temperature_min_c` |
| `current_temperature_c` | `float?` | Optional (None if no sensor) |
| `backup_runtime_min` | `float` | >= 0 |
| `available_capacity_kg` | `float` | >= 0 |
| `unloading_duration_min` | `float` | >= 0 |
| `time_sensitivity` | `CargoSensitivity` | `HIGH`, `MEDIUM`, `LOW` |

---

## ReceiverEvent

**event_type:** `receiver.profile`

| Field | Type | Constraint |
|---|---|---|
| `receiver_id` | `str` | — |
| `receiver_name` | `str` | — |
| `category` | `ReceiverCategory` | See enum below |
| `capacity_kg` | `float` | >= 0 |
| `current_load_kg` | `float` | >= 0 |
| `accepts_temperature_min_c` | `float` | — |
| `accepts_temperature_max_c` | `float` | — |
| `distance_km` | `float?` | >= 0 |
| `is_available` | `bool` | default `true` |

### ReceiverCategory Enum (4 values)

| Value | Description |
|---|---|
| `COLD_STORAGE_FACILITY` | Commercial refrigerated warehouse |
| `FOOD_BANK` | Charitable food distribution |
| `HOSPITAL_OR_CLINIC` | Medical facility with strict cold-chain |
| `COMMUNITY_COLD_ROOM` | Community shared refrigeration |

---

## PowerState Enum (5 values — Simulator)

| Value | Terminal? | Allowed Transitions |
|---|---|---|
| `GRID_STABLE` | No | GRID_UNSTABLE, BATTERY, SOLAR_BATTERY |
| `GRID_UNSTABLE` | No | GRID_STABLE, BATTERY, NO_COOLING |
| `BATTERY` | No | GRID_STABLE, SOLAR_BATTERY, NO_COOLING |
| `SOLAR_BATTERY` | No | GRID_STABLE, BATTERY, NO_COOLING |
| `NO_COOLING` | **Yes** | (none) |

---

## PredictionEvent

> **Disclaimer:** All predictions use a simplified Newton linear model and are **not validated for food-safety decisions**.

| Field | Type | Description |
|---|---|---|
| `prediction_type` | `str` | e.g. `THERMAL_PROGRESSION` |
| `predicted_temperature_c` | `float?` | Forecast temperature (°C) |
| `time_to_spoilage_min` | `float?` | Minutes until spoilage risk (>= 0) |
| `confidence` | `float?` | Confidence score [0, 1] |
| `model_name` | `str` | Default: `newton_linear_v1` |
| `assumptions` | `str?` | Documented model assumptions |

---

## Fixture Files

All fixtures are in `data/fixtures/` and serialised from live Pydantic schema instances.

| File | Schema |
|---|---|
| `incident.json` | `IncidentEvent` |
| `cargo.json` | `CargoEvent` |
| `receiver.json` | `ReceiverEvent` |
| `prediction.json` | `PredictionEvent` |
| `route.json` | `RouteEvent` |
| `assignment.json` | `AssignmentEvent` |
| `approval.json` | `ApprovalEvent` |
| `audit_event.json` | `AuditEvent` |
