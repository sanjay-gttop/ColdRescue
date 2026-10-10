
"""ColdRescue event-ingestion API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator

from backend.services.event_ingestion import (
    DuplicateEventIDConflict,
    DuplicateKeyConflict,
    OutOfOrderEvent,
    UnsupportedEventType,
    event_store,
)

router = APIRouter(prefix="/events", tags=["events"])


class EventIngestRequest(BaseModel):
    stream_id: str = Field(..., min_length=1, max_length=200)
    event: dict[str, Any]

    @field_validator("stream_id")
    @classmethod
    def validate_stream_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("stream_id must not be empty or whitespace")
        return value.strip()

    model_config = {"extra": "forbid"}


@router.post("/ingest")
async def ingest_event(payload: EventIngestRequest) -> dict[str, Any]:
    try:
        return event_store.ingest(
            stream_id=payload.stream_id,
            raw_event=payload.event,
        )
    except UnsupportedEventType as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (
        DuplicateKeyConflict,
        DuplicateEventIDConflict,
        OutOfOrderEvent,
    ) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(include_url=False),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc