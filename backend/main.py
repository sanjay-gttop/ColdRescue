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
from backend.config.logging import get_logger
from backend.config.settings import settings
from backend.middleware.errors import (
    generic_exception_handler,
    validation_exception_handler,
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

# Routers
app.include_router(health_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "ColdRescue backend starting",
        extra={"env": settings.APP_ENV, "debug": settings.APP_DEBUG},
    )
