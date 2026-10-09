"""ColdRescue health API endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from backend.common.utils import utc_now
from backend.config.settings import settings

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check() -> dict:
    """Liveness check — returns OK if the server is running."""
    return {
        "status": "ok",
        "timestamp": utc_now().isoformat(),
        "environment": settings.APP_ENV,
        "version": "0.2.0",
    }
