"""Standard API error envelope for ColdRescue."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    request_id: Optional[str] = None
