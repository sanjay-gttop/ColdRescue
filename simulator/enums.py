"""
ColdRescue Simulator — domain enumerations.

These enums are the single source of truth for M2 domain constants.
They are re-exported from backend.schemas.* for schema validation.
"""
from __future__ import annotations

from enum import Enum


# ── Incident Types ─────────────────────────────────────────────────────────────
class IncidentType(str, Enum):
    """Exactly 5 incident types as specified in M2."""
    REEFER_UNIT_FAILURE = "REEFER_UNIT_FAILURE"
    COLD_ROOM_POWER_OUTAGE = "COLD_ROOM_POWER_OUTAGE"
    WAREHOUSE_GRID_OUTAGE = "WAREHOUSE_GRID_OUTAGE"
    BACKUP_RUNTIME_LOW = "BACKUP_RUNTIME_LOW"
    BACKUP_POWER_DEPLETED = "BACKUP_POWER_DEPLETED"


# ── Power States ───────────────────────────────────────────────────────────────
class PowerState(str, Enum):
    """
    Exactly 5 power states as specified in M2.

    Transition rules (enforced by state_machine.py):
      GRID_STABLE    -> GRID_UNSTABLE | BATTERY | SOLAR_BATTERY
      GRID_UNSTABLE  -> GRID_STABLE | BATTERY | NO_COOLING
      BATTERY        -> GRID_STABLE | SOLAR_BATTERY | NO_COOLING
      SOLAR_BATTERY  -> GRID_STABLE | BATTERY | NO_COOLING
      NO_COOLING     -> (terminal — cannot transition automatically)
    """
    GRID_STABLE = "GRID_STABLE"
    GRID_UNSTABLE = "GRID_UNSTABLE"
    BATTERY = "BATTERY"
    SOLAR_BATTERY = "SOLAR_BATTERY"
    NO_COOLING = "NO_COOLING"


# ── Receiver Categories ────────────────────────────────────────────────────────
class ReceiverCategory(str, Enum):
    """Exactly 4 receiver categories as specified in M2."""
    COLD_STORAGE_FACILITY = "COLD_STORAGE_FACILITY"
    FOOD_BANK = "FOOD_BANK"
    HOSPITAL_OR_CLINIC = "HOSPITAL_OR_CLINIC"
    COMMUNITY_COLD_ROOM = "COMMUNITY_COLD_ROOM"


# ── Allowed Power State Transitions ───────────────────────────────────────────
ALLOWED_TRANSITIONS: dict[PowerState, set[PowerState]] = {
    PowerState.GRID_STABLE: {
        PowerState.GRID_UNSTABLE,
        PowerState.BATTERY,
        PowerState.SOLAR_BATTERY,
    },
    PowerState.GRID_UNSTABLE: {
        PowerState.GRID_STABLE,
        PowerState.BATTERY,
        PowerState.NO_COOLING,
    },
    PowerState.BATTERY: {
        PowerState.GRID_STABLE,
        PowerState.SOLAR_BATTERY,
        PowerState.NO_COOLING,
    },
    PowerState.SOLAR_BATTERY: {
        PowerState.GRID_STABLE,
        PowerState.BATTERY,
        PowerState.NO_COOLING,
    },
    PowerState.NO_COOLING: set(),  # terminal state
}
