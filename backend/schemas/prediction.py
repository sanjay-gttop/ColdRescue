"""ColdRescue prediction event schema."""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from backend.schemas.common import EventEnvelope


class PredictionEvent(EventEnvelope):
    model_config = {"protected_namespaces": (), "extra": "forbid"}

    """
    Event carrying a thermal or spoilage prediction.

    NOTE: All predictions are labelled estimates based on a simplified
    Newton-type linear model. They are NOT scientifically validated.
    """

    prediction_type: str = Field(
        ..., description="e.g. 'THERMAL_PROGRESSION' or 'SPOILAGE_RISK'"
    )
    predicted_temperature_c: Optional[float] = Field(
        None, description="Predicted temperature at forecast horizon (°C)"
    )
    time_to_spoilage_min: Optional[float] = Field(
        None, ge=0.0, description="Estimated minutes until cargo spoilage risk (>=0)"
    )
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Prediction confidence [0, 1]"
    )
    model_name: str = Field(
        default="newton_linear_v1",
        description="Model identifier (not a production ML model)",
    )
    assumptions: Optional[str] = Field(
        None, description="Documented assumptions used in this prediction"
    )
