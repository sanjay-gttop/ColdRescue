"""ColdRescue common utilities."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def make_event_id() -> str:
    """Generate a unique event ID."""
    return f"evt_{uuid.uuid4().hex}"


def make_incident_id() -> str:
    """Generate a unique incident ID."""
    return f"inc_{uuid.uuid4().hex}"


def make_correlation_id() -> str:
    """Generate a correlation ID for request tracing."""
    return f"corr_{uuid.uuid4().hex}"


def make_idempotency_key() -> str:
    """Generate an idempotency key."""
    return uuid.uuid4().hex


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)
