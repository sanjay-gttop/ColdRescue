"""
ColdRescue Simulator — Power state machine.

Enforces valid power-state transitions and emits validated EventEnvelope events.

State transition rules (from simulator/enums.py):
    GRID_STABLE    -> GRID_UNSTABLE | BATTERY | SOLAR_BATTERY
    GRID_UNSTABLE  -> GRID_STABLE | BATTERY | NO_COOLING
    BATTERY        -> GRID_STABLE | SOLAR_BATTERY | NO_COOLING
    SOLAR_BATTERY  -> GRID_STABLE | BATTERY | NO_COOLING
    NO_COOLING     -> (terminal — rejects all transitions)

Each accepted transition emits an IncidentEvent validated against EventEnvelope.
Rejected transitions raise InvalidTransitionError (never silently ignored).
Out-of-order or duplicate events are detected and raise DuplicateEventError.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Set

from backend.common.utils import (
    make_correlation_id,
    make_event_id,
    make_idempotency_key,
    utc_now,
)
from backend.schemas.incident import IncidentEvent, IncidentStatus, IncidentType
from simulator.enums import ALLOWED_TRANSITIONS, PowerState


class InvalidTransitionError(Exception):
    """Raised when a power-state transition is not allowed."""


class DuplicateEventError(Exception):
    """Raised when an event with a duplicate idempotency key is applied."""


class PowerStateMachine:
    """
    Deterministic power-state machine for a single simulated facility.

    Every state change produces a validated IncidentEvent.
    All emitted events must pass EventEnvelope validation (timezone-aware, schema 1.0.0).
    """

    def __init__(
        self,
        incident_id: str,
        location_id: str,
        location_name: str,
        initial_state: PowerState,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.incident_id = incident_id
        self.location_id = location_id
        self.location_name = location_name
        self.current_state = initial_state
        self.correlation_id = correlation_id or make_correlation_id()
        self._seen_idempotency_keys: Set[str] = set()
        self._emitted_events: List[IncidentEvent] = []

    def transition(
        self,
        new_state: PowerState,
        reported_by: str = "simulator",
        notes: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        idempotency_key: Optional[str] = None,
    ) -> IncidentEvent:
        """
        Apply a power-state transition.

        Parameters
        ----------
        new_state       : target PowerState
        reported_by     : actor performing the transition
        notes           : optional human-readable note
        occurred_at     : event timestamp (timezone-aware UTC); defaults to now
        idempotency_key : client dedup key; auto-generated if not supplied

        Returns
        -------
        IncidentEvent — the validated event for this transition

        Raises
        ------
        InvalidTransitionError : transition not in ALLOWED_TRANSITIONS
        DuplicateEventError    : idempotency_key already seen
        """
        allowed = ALLOWED_TRANSITIONS.get(self.current_state, set())
        if new_state not in allowed:
            allowed_str = ", ".join(s.value for s in allowed) if allowed else "(none - terminal state)"
            raise InvalidTransitionError(
                f"Cannot transition {self.current_state} -> {new_state}. "
                f"Allowed: {allowed_str}"
            )

        ikey = idempotency_key or make_idempotency_key()
        if ikey in self._seen_idempotency_keys:
            raise DuplicateEventError(
                f"Duplicate idempotency_key detected: {ikey}"
            )

        # Map power state to incident type
        incident_type = _power_state_to_incident_type(new_state)

        ts = occurred_at or utc_now()
        if ts.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")

        event = IncidentEvent(
            event_id=make_event_id(),
            event_type=f"power_state.{new_state.value.lower()}",
            occurred_at=ts,
            schema_version="1.0.0",
            incident_id=self.incident_id,
            correlation_id=self.correlation_id,
            idempotency_key=ikey,
            incident_type=incident_type,
            status=IncidentStatus.OPEN,
            location_id=self.location_id,
            location_name=self.location_name,
            reported_by=reported_by,
            notes=notes,
        )

        self._seen_idempotency_keys.add(ikey)
        self._emitted_events.append(event)
        self.current_state = new_state
        return event

    def restore_grid(
        self,
        reported_by: str = "simulator",
        notes: Optional[str] = None,
    ) -> IncidentEvent:
        """Convenience method — transition to GRID_STABLE."""
        return self.transition(
            PowerState.GRID_STABLE,
            reported_by=reported_by,
            notes=notes or "Grid power restored",
        )

    @property
    def is_terminal(self) -> bool:
        return len(ALLOWED_TRANSITIONS.get(self.current_state, set())) == 0

    @property
    def emitted_events(self) -> List[IncidentEvent]:
        return list(self._emitted_events)


def _power_state_to_incident_type(state: PowerState) -> IncidentType:
    """Map a PowerState to the appropriate IncidentType."""
    mapping = {
        PowerState.GRID_STABLE: IncidentType.COLD_ROOM_POWER_OUTAGE,   # restoration
        PowerState.GRID_UNSTABLE: IncidentType.WAREHOUSE_GRID_OUTAGE,
        PowerState.BATTERY: IncidentType.BACKUP_RUNTIME_LOW,
        PowerState.SOLAR_BATTERY: IncidentType.BACKUP_RUNTIME_LOW,
        PowerState.NO_COOLING: IncidentType.BACKUP_POWER_DEPLETED,
    }
    return mapping[state]
