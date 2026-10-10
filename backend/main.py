"""
ColdRescue FastAPI application entry point.

Run locally:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from backend.api.health import router as health_router
from backend.api.allocation import router as allocation_router
from backend.api.events import router as events_router
from backend.config.logging import get_logger
from backend.config.settings import settings
from backend.middleware.errors import (
    generic_exception_handler,
    validation_exception_handler,
)
from backend.services.cloudwatch_logging import (
    attach_cloudwatch_handler,
)

logger = get_logger(__name__, settings.LOG_LEVEL)

app = FastAPI(
    title="ColdRescue API",
    description="Cold-chain rescue coordination platform",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

from backend.api.recovery_actions import router as recovery_actions_router

# Routers
app.include_router(health_router)
app.include_router(health_router, prefix="/api/v1")
app.include_router(allocation_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(recovery_actions_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup() -> None:
    # Attach CloudWatch only when explicitly enabled in configuration.
    # With AWS_INTEGRATIONS_ENABLED=False, no AWS client is created.
    cloudwatch_attached = attach_cloudwatch_handler(logger)

    logger.info(
        "ColdRescue backend starting",
        extra={
            "env": settings.APP_ENV,
            "debug": settings.APP_DEBUG,
            "cloudwatch_enabled": cloudwatch_attached,
        },
    )