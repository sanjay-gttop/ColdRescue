from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import math
import os
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SAGEMAKER_ENDPOINT_NAME = os.environ.get("COLDRESCUE_SAGEMAKER_ENDPOINT", "coldrescue-thermal-serverless-v1")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")


THERMAL_MODEL_VERSION = "thermal-simulation-v1.2.0"
DEFAULT_SIMULATION_HORIZON_MINUTES = 10080  # 7 days


@dataclass(frozen=True)
class DoorEvent:
    start_minute: int
    duration_minutes: int


@dataclass(frozen=True)
class ThermalInput:
    cargo_type: str
    current_temperature_c: float
    ambient_temperature_c: float
    safe_temperature_limit_c: float
    cooling_status: str
    backup_runtime_minutes: float
    simulation_horizon_minutes: int = 720
    cooling_restoration_minute: int | None = None
    door_events: tuple[DoorEvent, ...] = ()
    initial_input_timestamp: str | None = None


@dataclass(frozen=True)
class ThermalPrediction:
    model_version: str
    input_timestamp: str
    predicted_breach_minutes: float | None
    predicted_breach_temperature_c: float | None
    initial_temperature_c: float
    safe_temperature_limit_c: float
    simulated_temperature_trajectory: list[dict[str, float]]
    assumptions: list[str]
    provenance: str
    status: str


# Illustrative coefficients only. They are not field-calibrated.
CARGO_WARMING_RATES_C_PER_MIN = {
    "dairy": 0.12,
    "perishable_food": 0.10,
    "temperature_sensitive_supplies": 0.08,
    "default": 0.10,
}

COOLING_RATES_C_PER_MIN = {
    "dairy": 0.08,
    "perishable_food": 0.07,
    "temperature_sensitive_supplies": 0.05,
    "default": 0.06,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate(data: ThermalInput) -> None:
    numbers = (
        data.current_temperature_c,
        data.ambient_temperature_c,
        data.safe_temperature_limit_c,
        data.backup_runtime_minutes,
    )

    if not all(math.isfinite(value) for value in numbers):
        raise ValueError("Thermal inputs must be finite numbers.")

    if not -80.0 <= data.ambient_temperature_c <= 80.0:
        raise ValueError(
            "Ambient temperature is outside plausible operating limits."
        )

    if not -100.0 <= data.current_temperature_c <= 150.0:
        raise ValueError("Current cargo temperature is outside plausible limits.")

    if data.backup_runtime_minutes < 0:
        raise ValueError("Backup runtime cannot be negative.")

    if data.simulation_horizon_minutes <= 0:
        raise ValueError("Simulation horizon must be positive.")

    if data.cooling_status not in {
        "operational",
        "backup",
        "failed",
        "unknown",
    }:
        raise ValueError("Unsupported cooling status.")

    if data.cooling_restoration_minute is not None:
        if data.cooling_restoration_minute < 0:
            raise ValueError("Restoration minute cannot be negative.")

    for event in data.door_events:
        if event.start_minute < 0 or event.duration_minutes < 0:
            raise ValueError("Door-event timing cannot be negative.")


def simulate_thermal_risk(data: ThermalInput) -> ThermalPrediction:
    _validate(data)

    cargo = data.cargo_type.lower()
    cooling_rate = COOLING_RATES_C_PER_MIN.get(
        cargo, COOLING_RATES_C_PER_MIN["default"]
    )

    temperature = data.current_temperature_c
    breach_minute: float | None = None
    trajectory = [{"minute": 0.0, "temperature_c": temperature}]

    for minute in range(1, data.simulation_horizon_minutes + 1):
        restored = (
            data.cooling_restoration_minute is not None
            and minute >= data.cooling_restoration_minute
        )

        backup_active = (
            data.cooling_status == "backup"
            and minute <= data.backup_runtime_minutes
        )

        cooling_active = (
            data.cooling_status == "operational"
            or backup_active
            or restored
        )

        door_open = any(
            event.start_minute <= minute
            < event.start_minute + event.duration_minutes
            for event in data.door_events
        )

        if cooling_active:
            # Simplified active-cooling model.
            temperature -= cooling_rate
        else:
            # Without active cooling, temperature moves gradually toward
            # ambient temperature. It cannot drift beyond ambient solely
            # because of this passive-exchange calculation.
            temperature += (
                data.ambient_temperature_c - temperature
            ) * 0.01

        if door_open:
            temperature += 0.05

        trajectory.append(
            {
                "minute": float(minute),
                "temperature_c": round(temperature, 4),
            }
        )

        if (
            breach_minute is None
            and temperature > data.safe_temperature_limit_c
        ):
            breach_minute = float(minute)

    if data.cooling_status == "unknown":
        status = "UNKNOWN_COOLING_STATE"
    elif breach_minute is not None:
        status = "BREACH_PREDICTED"
    else:
        status = "NO_BREACH_WITHIN_SIMULATION_HORIZON"

    breach_temperature = (
        trajectory[int(breach_minute)]["temperature_c"]
        if breach_minute is not None
        else None
    )

    assumptions = [
        "Simulation coefficients are illustrative, not field-calibrated.",
        "Temperature is modelled at one-minute time steps.",
        "Without active cooling, cargo temperature gradually approaches ambient.",
        "Active cooling uses simplified cargo-category coefficients.",
        "Door-open events add a simplified thermal disturbance.",
        "Cooling restoration is assumed effective from its configured minute.",
        "Backup runtime is a configured duration, not a measured battery test.",
        "No breach within the simulation horizon is not a guarantee of food safety.",
    ]

    return ThermalPrediction(
        model_version=THERMAL_MODEL_VERSION,
        input_timestamp=data.initial_input_timestamp or _utc_now(),
        predicted_breach_minutes=breach_minute,
        predicted_breach_temperature_c=breach_temperature,
        initial_temperature_c=data.current_temperature_c,
        safe_temperature_limit_c=data.safe_temperature_limit_c,
        simulated_temperature_trajectory=trajectory,
        assumptions=assumptions,
        provenance="SIMULATED_NOT_FIELD_CALIBRATED",
        status=status,
    )


def prediction_to_dict(prediction: ThermalPrediction) -> dict[str, Any]:
    return asdict(prediction)


class ThermalRiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ThermalRiskAssessment(BaseModel):
    model_config = {"protected_namespaces": ()}

    cargo_id: str
    risk_level: ThermalRiskLevel
    current_temperature_c: Optional[float] = None
    safe_temperature_max_c: float
    ambient_temperature_c: float
    active_cooling: bool
    remaining_backup_runtime_min: float
    estimated_safe_window_min: float
    predicted_temperature_after_transit_c: Optional[float] = None
    spoilage_breached: bool = False
    prediction_source: str = "physics_fallback"
    model_version: str = THERMAL_MODEL_VERSION
    is_fallback: bool = True
    fallback_reason: Optional[str] = None
    explanation: str
    assumptions: str
    disclaimer: str = (
        "Thermal predictions are simplified, illustrative approximations for "
        "operational guidance only. They are not validated for regulatory "
        "food-safety certification."
    )


class ThermalRiskService:
    """Evaluate cargo thermal risk using the simplified simulation model."""

    DEFAULT_AMBIENT_TEMP_C = 25.0

    @classmethod
    def evaluate_cargo_thermal_risk(
        cls,
        cargo: Any,
        ambient_temperature_c: Optional[float] = None,
        cooling_status: Any = "operational",
        transit_duration_min: Optional[float] = None,
        heat_ingress_rate_k: Optional[float] = None,
    ) -> ThermalRiskAssessment:
        ambient = (
            cls.DEFAULT_AMBIENT_TEMP_C
            if ambient_temperature_c is None
            else float(ambient_temperature_c)
        )

        if not math.isfinite(ambient) or not -80.0 <= ambient <= 80.0:
            raise ValueError(
                "Ambient temperature is outside plausible operating limits."
            )

        cargo_id = getattr(cargo, "cargo_id", "cargo_unknown")
        cargo_type = str(getattr(cargo, "cargo_type", "general"))

        safe_max_value = getattr(cargo, "safe_temperature_max_c", None)
        if safe_max_value is None:
            safe_max_value = getattr(cargo, "safe_temp_max_c", 8.0)

        safe_min_value = getattr(cargo, "safe_temperature_min_c", None)
        if safe_min_value is None:
            safe_min_value = getattr(cargo, "safe_temp_min_c", 0.0)

        safe_max = float(safe_max_value)
        safe_min = float(safe_min_value)

        if not math.isfinite(safe_min) or not math.isfinite(safe_max):
            raise ValueError("Cargo temperature limits must be finite.")

        if safe_min > safe_max:
            raise ValueError("Cargo minimum temperature exceeds its maximum.")

        current_temp = getattr(cargo, "current_temperature_c", None)
        if current_temp is None:
            current_temp = getattr(cargo, "initial_temp_c", None)

        if current_temp is None:
            current_temp = (safe_min + safe_max) / 2.0
            explanation_prefix = (
                "Current temperature unmeasured; using the permitted "
                "temperature-range midpoint. "
            )
        else:
            current_temp = float(current_temp)
            explanation_prefix = ""

        if not math.isfinite(current_temp):
            raise ValueError("Current cargo temperature must be finite.")

        backup_runtime = getattr(cargo, "backup_runtime_min", 0.0)
        backup_runtime = float(backup_runtime or 0.0)

        if not math.isfinite(backup_runtime) or backup_runtime < 0:
            raise ValueError("Backup runtime must be finite and nonnegative.")

        raw_status = (
            str(cooling_status.value).lower()
            if hasattr(cooling_status, "value")
            else str(cooling_status).lower()
        )

        if current_temp > safe_max:
            return ThermalRiskAssessment(
                cargo_id=cargo_id,
                risk_level=ThermalRiskLevel.CRITICAL,
                current_temperature_c=current_temp,
                safe_temperature_max_c=safe_max,
                ambient_temperature_c=ambient,
                active_cooling=(raw_status == "operational"),
                remaining_backup_runtime_min=backup_runtime,
                estimated_safe_window_min=0.0,
                predicted_temperature_after_transit_c=current_temp,
                spoilage_breached=True,
                explanation=(
                    f"{explanation_prefix}CRITICAL: Cargo temperature "
                    f"({current_temp:.1f} C) already exceeds the safe "
                    f"upper limit ({safe_max:.1f} C)."
                ),
                assumptions="Immediate thermal limit breach detected.",
            )

        if raw_status == "operational":
            sim_cooling = "operational"
        elif raw_status in {"backup", "failed", "unknown"}:
            sim_cooling = raw_status
        elif raw_status == "degraded":
            sim_cooling = "backup"
            backup_runtime *= 0.5
        else:
            raise ValueError(f"Unsupported cooling status: {raw_status}")

        # Baseline deterministic physics simulation (always run for fallback and trajectory)
        prediction = simulate_thermal_risk(
            ThermalInput(
                cargo_type=cargo_type,
                current_temperature_c=current_temp,
                ambient_temperature_c=ambient,
                safe_temperature_limit_c=safe_max,
                cooling_status=sim_cooling,
                backup_runtime_minutes=backup_runtime,
                simulation_horizon_minutes=DEFAULT_SIMULATION_HORIZON_MINUTES,
            )
        )

        if prediction.predicted_breach_minutes is not None:
            physics_safe_window = prediction.predicted_breach_minutes
        elif prediction.status == "UNKNOWN_COOLING_STATE":
            physics_safe_window = 0.0
        else:
            physics_safe_window = float(DEFAULT_SIMULATION_HORIZON_MINUTES)

        # Attempt real SageMaker Serverless Inference when enabled
        safe_window = physics_safe_window
        prediction_source = "physics_fallback"
        model_version = THERMAL_MODEL_VERSION
        is_fallback = True
        fallback_reason = None

        if os.environ.get("ENABLE_SAGEMAKER_INFERENCE", "false").lower() in ("true", "1", "yes"):
            try:
                sm_runtime = boto3.client("sagemaker-runtime", region_name=AWS_REGION)
                cargo_kg = float(getattr(cargo, "cargo_kg", 500.0) or 500.0)
                payload_dict = {
                    "cargo_type": cargo_type,
                    "current_temp_c": current_temp,
                    "ambient_temp_c": ambient,
                    "safe_limit_c": safe_max,
                    "cooling_status": sim_cooling,
                    "backup_runtime_min": backup_runtime,
                    "mass_kg": cargo_kg,
                    "thermal_resistance": 1.0,
                }
                response = sm_runtime.invoke_endpoint(
                    EndpointName=SAGEMAKER_ENDPOINT_NAME,
                    ContentType="application/json",
                    Body=json.dumps(payload_dict),
                )
                resp_body = json.loads(response["Body"].read().decode("utf-8"))
                if "predicted_breach_minutes" in resp_body:
                    safe_window = float(resp_body["predicted_breach_minutes"])
                    prediction_source = "sagemaker_serverless"
                    model_version = resp_body.get("model_version", "1.0.0")
                    is_fallback = False
                    fallback_reason = None
            except (ClientError, BotoCoreError, Exception) as sm_err:
                fallback_reason = f"SageMaker unavailable ({type(sm_err).__name__}); deterministic physics fallback armed."
                logger.warning("SageMaker endpoint invocation fell back to physics: %s", sm_err)
                safe_window = physics_safe_window
                prediction_source = "physics_fallback"
                is_fallback = True

        predicted_arrival_temp = current_temp

        if transit_duration_min is not None:
            transit_duration_min = float(transit_duration_min)

            if (
                not math.isfinite(transit_duration_min)
                or transit_duration_min < 0
            ):
                raise ValueError(
                    "Transit duration must be finite and nonnegative."
                )

            index = min(
                len(prediction.simulated_temperature_trajectory) - 1,
                int(round(transit_duration_min)),
            )
            predicted_arrival_temp = prediction.simulated_temperature_trajectory[
                index
            ]["temperature_c"]

        if prediction.status == "UNKNOWN_COOLING_STATE":
            risk_level = ThermalRiskLevel.UNKNOWN
        elif safe_window < 30.0:
            risk_level = ThermalRiskLevel.CRITICAL
        elif safe_window < 90.0:
            risk_level = ThermalRiskLevel.HIGH
        elif safe_window < 240.0:
            risk_level = ThermalRiskLevel.MEDIUM
        else:
            risk_level = ThermalRiskLevel.LOW

        return ThermalRiskAssessment(
            cargo_id=cargo_id,
            risk_level=risk_level,
            current_temperature_c=current_temp,
            safe_temperature_max_c=safe_max,
            ambient_temperature_c=ambient,
            active_cooling=(
                raw_status == "operational"
                or (raw_status == "backup" and backup_runtime > 0)
            ),
            remaining_backup_runtime_min=backup_runtime,
            estimated_safe_window_min=round(safe_window, 1),
            predicted_temperature_after_transit_c=(
                round(predicted_arrival_temp, 2)
                if transit_duration_min is not None
                else None
            ),
            spoilage_breached=False,
            prediction_source=prediction_source,
            model_version=model_version,
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            explanation=(
                f"{explanation_prefix}Estimated safe preservation window is "
                f"{safe_window:.1f} minutes via {prediction_source}. Cooling status: {raw_status.upper()}."
            ),
            assumptions=(
                f"Model {model_version}; ambient={ambient:.1f} C, "
                f"safe_max={safe_max:.1f} C. Coefficients are illustrative."
            ),
        )