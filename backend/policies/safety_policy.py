"""ColdRescue safety policy and assignment feasibility checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any

from pydantic import BaseModel, Field

POLICY_VERSION = "coldrescue-safety-v1.2.0"


class RuleSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HARD_BLOCK = "HARD_BLOCK"


@dataclass(frozen=True)
class AssignmentCandidate:
    incident_id: str
    receiver_id: str
    cargo_kg: float
    receiver_capacity_remaining_kg: float
    cooling_viable: bool
    receiver_backup_runtime_minutes: float
    route_minutes: float | None
    unloading_minutes: float
    thermal_deadline_minutes: float | None
    safety_margin_minutes: float
    required_safety_horizon_minutes: float | None = None
    route_provider: str = "unknown"
    route_is_simulated: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    incident_id: str
    receiver_id: str
    policy_version: str
    evaluated_at: str
    block_reasons: list[dict[str, str]]
    total_required_minutes: float | None
    route_provider: str
    route_is_simulated: bool


class RuleEvaluation(BaseModel):
    rule_name: str
    severity: RuleSeverity
    passed: bool
    message: str


class PolicyAssessment(BaseModel):
    incident_id: str
    receiver_id: str
    policy_version: str = POLICY_VERSION
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    is_safe: bool = False
    is_hard_blocked: bool = True
    hard_block_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rules: list[RuleEvaluation] = Field(default_factory=list)
    thermal_window_min: float | None = None
    route_provider: str = "unknown"
    route_is_simulated: bool = True

    @property
    def block_reasons(self) -> list[str]:
        return self.hard_block_reasons


def evaluate_assignment(candidate: AssignmentCandidate) -> PolicyDecision:
    """Evaluate a preconstructed assignment candidate."""
    reasons: list[dict[str, str]] = []

    def block(code: str, message: str) -> None:
        reasons.append({"code": code, "message": message})

    if candidate.cargo_kg <= 0:
        block("INVALID_CARGO_MASS", "Cargo mass must be positive.")

    if candidate.receiver_capacity_remaining_kg < 0:
        block(
            "INVALID_RECEIVER_CAPACITY",
            "Remaining capacity cannot be negative.",
        )
    elif candidate.cargo_kg > candidate.receiver_capacity_remaining_kg:
        block(
            "INSUFFICIENT_CAPACITY",
            f"Cargo requires {candidate.cargo_kg:g} kg, but only "
            f"{candidate.receiver_capacity_remaining_kg:g} kg is available.",
        )

    if not candidate.cooling_viable:
        block("NO_VIABLE_COOLING", "No verified viable cooling arrangement.")

    if candidate.receiver_backup_runtime_minutes < 0:
        block("INVALID_BACKUP_RUNTIME", "Backup runtime cannot be negative.")

    if candidate.route_minutes is None:
        block("ROUTE_UNAVAILABLE", "No usable route duration is available.")
    elif candidate.route_minutes < 0:
        block("INVALID_ROUTE_DURATION", "Route duration cannot be negative.")

    if candidate.unloading_minutes < 0:
        block("INVALID_UNLOADING_DURATION", "Unloading duration cannot be negative.")

    if candidate.safety_margin_minutes < 0:
        block("INVALID_SAFETY_MARGIN", "Safety margin cannot be negative.")

    if candidate.thermal_deadline_minutes is None:
        block(
            "THERMAL_DEADLINE_UNKNOWN",
            "No validated thermal deadline is available.",
        )
    elif candidate.thermal_deadline_minutes < 0:
        block("INVALID_THERMAL_DEADLINE", "Thermal deadline cannot be negative.")

    if (
        candidate.required_safety_horizon_minutes is not None
        and candidate.required_safety_horizon_minutes < 0
    ):
        block("INVALID_REQUIRED_HORIZON", "Required safety horizon cannot be negative.")

    required_minutes = None
    durations_valid = (
        candidate.route_minutes is not None
        and candidate.route_minutes >= 0
        and candidate.unloading_minutes >= 0
        and candidate.safety_margin_minutes >= 0
        and candidate.thermal_deadline_minutes is not None
        and candidate.thermal_deadline_minutes >= 0
    )

    if durations_valid:
        required_minutes = (
            candidate.route_minutes
            + candidate.unloading_minutes
            + candidate.safety_margin_minutes
        )

        if required_minutes > candidate.thermal_deadline_minutes:
            block(
                "THERMAL_DEADLINE_EXCEEDED",
                f"Required time is {required_minutes:g} minutes, but the "
                f"thermal deadline is {candidate.thermal_deadline_minutes:g} minutes.",
            )

        backup_horizon = (
            candidate.required_safety_horizon_minutes
            if candidate.required_safety_horizon_minutes is not None
            else required_minutes
        )

        if candidate.receiver_backup_runtime_minutes < backup_horizon:
            block(
                "INSUFFICIENT_BACKUP_RUNTIME",
                f"Receiver backup runtime is "
                f"{candidate.receiver_backup_runtime_minutes:g} minutes, below "
                f"the required {backup_horizon:g} minutes.",
            )

    return PolicyDecision(
        allowed=not reasons,
        incident_id=candidate.incident_id,
        receiver_id=candidate.receiver_id,
        policy_version=POLICY_VERSION,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
        block_reasons=reasons,
        total_required_minutes=required_minutes,
        route_provider=candidate.route_provider,
        route_is_simulated=candidate.route_is_simulated,
    )


def decision_to_dict(decision: PolicyDecision) -> dict[str, Any]:
    return asdict(decision)


class SafetyPolicyEngine:
    """Safety gate used by recovery and allocation services."""

    @staticmethod
    def evaluate_assignment(
        *,
        incident: Any,
        receiver: Any,
        travel_time_min: float | None,
        ambient_temperature_c: float = 25.0,
    ) -> PolicyAssessment:
        cargo = incident.cargo
        hard_blocks: list[str] = []
        warnings: list[str] = []
        rules: list[RuleEvaluation] = []

        def record(
            name: str,
            passed: bool,
            message: str,
            severity: RuleSeverity = RuleSeverity.HARD_BLOCK,
        ) -> None:
            rules.append(
                RuleEvaluation(
                    rule_name=name,
                    severity=severity,
                    passed=passed,
                    message=message,
                )
            )

            if not passed:
                if severity == RuleSeverity.HARD_BLOCK:
                    hard_blocks.append(message)
                elif severity == RuleSeverity.WARNING:
                    warnings.append(message)

        # 1. Receiver availability
        record(
            "receiver_available",
            bool(receiver.is_available),
            "Receiver is unavailable.",
        )

        # 2. Cargo mass and remaining capacity
        cargo_kg = float(cargo.cargo_kg)
        available_kg = float(receiver.available_capacity_kg)

        record(
            "capacity",
            cargo_kg > 0 and available_kg >= cargo_kg,
            f"Capacity Exceeded: Cargo requires {cargo_kg:g} kg; "
            f"receiver has {available_kg:g} kg available.",
        )

        # 3. The receiver and cargo temperature ranges must overlap.
        receiver_min = float(receiver.accepts_temperature_min_c)
        receiver_max = float(receiver.accepts_temperature_max_c)
        cargo_min = float(cargo.safe_temperature_min_c)
        cargo_max = float(cargo.safe_temperature_max_c)

        temperature_compatible = (
            receiver_max >= cargo_min
            and receiver_min <= cargo_max
        )

        record(
            "temperature_compatibility",
            temperature_compatible,
            f"Temperature Envelope Mismatch: Receiver range "
            f"[{receiver_min:g}, {receiver_max:g}] C does not overlap "
            f"cargo range [{cargo_min:g}, {cargo_max:g}] C.",
        )

        # 4. Cooling condition
        raw_cooling_status = getattr(
            receiver.cooling_status,
            "value",
            receiver.cooling_status,
        )
        cooling_status = str(raw_cooling_status).strip().lower()

        if cooling_status == "operational":
            record(
                "cooling_status",
                True,
                "Cooling is operational.",
            )
        elif cooling_status == "degraded":
            record(
                "cooling_status",
                False,
                "Receiver cooling is DEGRADED; verify the facility before dispatch.",
                RuleSeverity.WARNING,
            )
        elif cooling_status == "failed":
            record(
                "cooling_status",
                False,
                "Cooling Failure: Receiver cooling has failed.",
            )
        else:
            record(
                "cooling_status",
                False,
                "Cooling Failure: Receiver cooling status is unknown.",
            )

        # 5. Cargo category compatibility
        compatible_types = getattr(receiver, "compatible_cargo_types", []) or []
        cargo_type = str(
            getattr(cargo, "cargo_type", "general")
        ).strip().lower()

        normalized_types = {
            str(value).strip().lower()
            for value in compatible_types
        }

        type_compatible = (
            "*" in normalized_types
            or "all" in normalized_types
            or cargo_type in normalized_types
        )

        record(
            "cargo_type_compatibility",
            type_compatible,
            f"Incompatible Cargo Type: Receiver does not list "
            f"cargo type '{cargo_type}' as compatible.",
        )

        # 6. Calculate the thermal preservation window.
        # Invalid model input is not converted into a false safe estimate.
        from backend.services.thermal_risk import ThermalRiskService

        thermal = ThermalRiskService.evaluate_cargo_thermal_risk(
            cargo=cargo,
            ambient_temperature_c=ambient_temperature_c,
        )

        estimated = float(thermal.estimated_safe_window_min)

        thermal_window: float | None = (
            estimated
            if math.isfinite(estimated) and estimated >= 0
            else None
        )

        # Cargo backup runtime limits how long the cargo can wait for recovery.
        cargo_backup_runtime = getattr(cargo, "backup_runtime_min", None)

        if cargo_backup_runtime is not None:
            cargo_backup_runtime = float(cargo_backup_runtime)

            if (
                math.isfinite(cargo_backup_runtime)
                and cargo_backup_runtime >= 0
            ):
                thermal_window = (
                    cargo_backup_runtime
                    if thermal_window is None
                    else min(thermal_window, cargo_backup_runtime)
                )
            else:
                thermal_window = None

        # An explicit spoilage deadline further limits the window.
        deadline = getattr(cargo, "spoilage_deadline", None)
        reported_at = getattr(incident, "reported_at", None)

        if deadline is not None and reported_at is not None:
            try:
                deadline_minutes = (
                    deadline - reported_at
                ).total_seconds() / 60.0
                deadline_minutes = max(0.0, deadline_minutes)

                thermal_window = (
                    deadline_minutes
                    if thermal_window is None
                    else min(thermal_window, deadline_minutes)
                )
            except (TypeError, AttributeError):
                pass

        record(
            "thermal_window_available",
            thermal_window is not None,
            (
                "A validated thermal safety window is unavailable."
                if thermal_window is None
                else f"Estimated thermal safety window: {thermal_window:.1f} minutes."
            ),
        )

        # 7. Route, unloading and safety margin
        if travel_time_min is None:
            record(
                "route_duration",
                False,
                "Route duration is unavailable.",
            )
            route_minutes = None
        else:
            route_minutes = float(travel_time_min)

            if not math.isfinite(route_minutes) or route_minutes < 0:
                record(
                    "route_duration",
                    False,
                    "Route duration must be finite and nonnegative.",
                )
                route_minutes = None
            else:
                record(
                    "route_duration",
                    True,
                    f"Estimated route: {route_minutes:.1f} minutes.",
                )

        unloading_minutes = float(
            getattr(cargo, "unloading_duration_min", 0.0)
        )

        unloading_valid = (
            math.isfinite(unloading_minutes)
            and unloading_minutes >= 0
        )

        record(
            "unloading_duration",
            unloading_valid,
            "Unloading duration must be finite and nonnegative.",
        )

        required_minutes = (
            route_minutes + unloading_minutes + 5.0
            if route_minutes is not None and unloading_valid
            else None
        )

        if required_minutes is not None and thermal_window is not None:
            record(
                "thermal_deadline",
                required_minutes <= thermal_window,
                f"Thermal Deadline Infeasible: Route, unloading, and safety "
                f"margin require {required_minutes:.1f} minutes; thermal "
                f"window is {thermal_window:.1f} minutes.",
            )
        else:
            record(
                "thermal_deadline",
                False,
                "Thermal Deadline Infeasible: Cannot verify that transit "
                "and unloading finish within the thermal window.",
            )

        # 8. A failed cooling system is always blocked.
        # Degraded cooling generates a warning; backup information is recorded.
        receiver_backup_runtime = getattr(receiver, "backup_runtime_min", None)

        if cooling_status in {"failed", "degraded"}:
            try:
                backup_valid = (
                    receiver_backup_runtime is not None
                    and math.isfinite(float(receiver_backup_runtime))
                    and float(receiver_backup_runtime) > 0
                )
            except (TypeError, ValueError, OverflowError):
                backup_valid = False

            record(
                "receiver_backup_runtime",
                backup_valid,
                "Receiver backup runtime is missing or exhausted while "
                "cooling is not fully operational.",
                (
                    RuleSeverity.WARNING
                    if cooling_status == "degraded"
                    else RuleSeverity.HARD_BLOCK
                ),
            )
        else:
            record(
                "receiver_backup_runtime",
                True,
                "Receiver backup runtime is not required while cooling is operational.",
                RuleSeverity.INFO,
            )

        return PolicyAssessment(
            incident_id=str(incident.incident_id),
            receiver_id=str(receiver.receiver_id),
            policy_version=POLICY_VERSION,
            evaluated_at=datetime.now(timezone.utc),
            is_safe=not hard_blocks,
            is_hard_blocked=bool(hard_blocks),
            hard_block_reasons=hard_blocks,
            warnings=warnings,
            rules=rules,
            thermal_window_min=thermal_window,
            route_provider="local_haversine_fallback",
            route_is_simulated=True,
        )