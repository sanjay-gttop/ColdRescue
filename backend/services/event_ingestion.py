from pathlib import Path
import os
import sqlite3
import sys
import tempfile
import json
from typing import Optional, Dict, Any

from pydantic import ValidationError

from backend.schemas.incident import IncidentEvent
from backend.schemas.cargo import CargoEvent
from backend.schemas.receiver import ReceiverEvent
from backend.schemas.route import RouteEvent
from backend.schemas.assignment import AssignmentEvent
from backend.schemas.approval import ApprovalEvent
from backend.schemas.prediction import PredictionEvent
from backend.schemas.audit_event import AuditEvent


EVENT_SCHEMAS = {
    "incident": IncidentEvent,
    "cargo": CargoEvent,
    "receiver": ReceiverEvent,
    "route": RouteEvent,
    "assignment": AssignmentEvent,
    "approval": ApprovalEvent,
    "prediction": PredictionEvent,
    "audit": AuditEvent,
}


class IngestionError(Exception):
    """Base error for event ingestion."""


class UnsupportedEventType(IngestionError):
    """Raised when an event type is not supported."""


class DuplicateKeyConflict(IngestionError):
    """Raised when an idempotency key is reused with different data."""


class DuplicateEventIDConflict(IngestionError):
    """Raised when an event ID is reused for a different submission."""


class OutOfOrderEvent(IngestionError):
    """Raised when an event sequence is not newer than the stream state."""


def _default_database_path() -> Path:
    configured = os.environ.get("COLDRESCUE_EVENT_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()

    # Tests must never clear or write to the real local event database.
    if "pytest" in sys.modules or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("LAMBDA_TASK_ROOT"):
        return (
            Path(tempfile.gettempdir())
            / f"coldrescue-events-{os.getpid()}.sqlite3"
        )

    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / "coldrescue_events.sqlite3"


class SQLiteEventStore:
    """
    Persistent event store.

    SQLite transactions serialize competing writes. Database constraints
    enforce globally unique event IDs, globally unique idempotency keys,
    and unique sequence numbers within each stream.

    All processes must use the same database file to share event state.
    """

    def __init__(self, database_path=None) -> None:
        self.database_path = (
            Path(database_path).expanduser().resolve()
            if database_path is not None
            else _default_database_path()
        )
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=30,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize_database(self) -> None:
        connection = sqlite3.connect(
            str(self.database_path),
            timeout=30,
        )
        try:
            connection.execute("PRAGMA busy_timeout = 30000")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    stream_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL CHECK(sequence_number >= 1),
                    event_type TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stream_id, sequence_number)
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_stream_sequence
                ON events(stream_id, sequence_number)
            """)
            connection.commit()
        finally:
            connection.close()

    def ingest(
        self,
        stream_id: str,
        raw_event: dict,
    ) -> dict:
        if not stream_id or not stream_id.strip():
            raise ValueError("stream_id must not be empty or whitespace")

        stream_id = stream_id.strip()

        event_type = str(raw_event.get("event_type", "")).strip().lower()
        schema = EVENT_SCHEMAS.get(event_type)

        if schema is None:
            raise UnsupportedEventType(
                "Unsupported event_type. Use one of: "
                + ", ".join(EVENT_SCHEMAS)
            )

        event = schema.model_validate(raw_event)

        if event.sequence_number is None:
            raise ValueError(
                "sequence_number is required when ingesting an event"
            )

        normalized_event = event.model_dump(mode="json")
        event_json = json.dumps(
            normalized_event,
            sort_keys=True,
            separators=(",", ":"),
        )
        idempotency_key = event.idempotency_key
        event_id = event.event_id
        sequence_number = event.sequence_number

        connection = self._connect()
        try:
            # Acquire the write lock before checking existing state. This
            # prevents two independent workers accepting conflicting writes.
            connection.execute("BEGIN IMMEDIATE")

            existing = connection.execute(
                """
                SELECT stream_id, event_json
                FROM events
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            ).fetchone()

            if existing is not None:
                if (
                    existing["stream_id"] == stream_id
                    and existing["event_json"] == event_json
                ):
                    connection.commit()
                    return {
                        "status": "duplicate",
                        "duplicate": True,
                        "stream_id": stream_id,
                        "event_id": event_id,
                        "sequence_number": sequence_number,
                    }

                raise DuplicateKeyConflict(
                    "idempotency_key was already used for different event data"
                )

            existing_event = connection.execute(
                "SELECT event_id FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()

            if existing_event is not None:
                raise DuplicateEventIDConflict(
                    "event_id has already been used"
                )

            latest_row = connection.execute(
                """
                SELECT MAX(sequence_number) AS latest
                FROM events
                WHERE stream_id = ?
                """,
                (stream_id,),
            ).fetchone()

            latest = latest_row["latest"] or 0

            if sequence_number <= latest:
                raise OutOfOrderEvent(
                    f"sequence_number must be greater than {latest} "
                    f"for stream '{stream_id}'"
                )

            connection.execute(
                """
                INSERT INTO events (
                    event_id,
                    idempotency_key,
                    stream_id,
                    sequence_number,
                    event_type,
                    event_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    idempotency_key,
                    stream_id,
                    sequence_number,
                    event_type,
                    event_json,
                ),
            )

            connection.commit()

            return {
                "status": "accepted",
                "duplicate": False,
                "stream_id": stream_id,
                "event_id": event_id,
                "event_type": event_type,
                "sequence_number": sequence_number,
            }

        except sqlite3.IntegrityError as exc:
            connection.rollback()

            # Convert a database uniqueness race into the existing API errors.
            existing_key = connection.execute(
                "SELECT event_id FROM events WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()

            if existing_key is not None:
                raise DuplicateKeyConflict(
                    "idempotency_key was already used for different event data"
                ) from exc

            existing_id = connection.execute(
                "SELECT event_id FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()

            if existing_id is not None:
                raise DuplicateEventIDConflict(
                    "event_id has already been used"
                ) from exc

            raise OutOfOrderEvent(
                "A conflicting sequence number was accepted by another writer"
            ) from exc

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def clear(self) -> None:
        """Clear this database; intended for automated tests and maintenance."""
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM events")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


class DynamoDBEventStore:
    """
    DynamoDB-backed event store.
    
    Provides atomic conditional writes enforcing:
      - Unique (stream_id, sequence_number) via attribute_not_exists(stream_id)
      - Idempotency key conflict detection via GSI query
    Seamlessly falls back to SQLiteEventStore when AWS_INTEGRATIONS_ENABLED is False or on error.
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        region: Optional[str] = None,
        fallback_store: Optional[SQLiteEventStore] = None,
    ) -> None:
        from backend.config.settings import settings

        self.table_name = table_name or settings.DYNAMODB_EVENTS_TABLE_NAME
        self.region = region or settings.AWS_REGION
        self.fallback = fallback_store or SQLiteEventStore()
        self._enabled = settings.AWS_INTEGRATIONS_ENABLED

    def ingest(self, stream_id: str, raw_event: dict) -> dict:
        """Ingest event adhering to event_store interface."""
        if not self._enabled:
            return self.fallback.ingest(stream_id=stream_id, raw_event=raw_event)
        
        if not stream_id or not stream_id.strip():
            raise ValueError("stream_id must not be empty or whitespace")
        stream_id = stream_id.strip()

        event_type = str(raw_event.get("event_type", "")).strip().lower()
        schema = EVENT_SCHEMAS.get(event_type)
        if schema is None:
            raise UnsupportedEventType(
                "Unsupported event_type. Use one of: " + ", ".join(EVENT_SCHEMAS)
            )

        event = schema(**raw_event)
        if event.sequence_number is None:
            raise ValueError("sequence_number is required when ingesting an event")

        normalized = event.model_dump(mode="json")
        event_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        event_id = event.event_id
        idempotency_key = event.idempotency_key
        sequence_number = event.sequence_number

        try:
            import boto3

            dynamodb = boto3.resource("dynamodb", region_name=self.region)
            table = dynamodb.Table(self.table_name)

            # 1. Check idempotency key on GSI
            gsi_response = table.query(
                IndexName="IdempotencyKeyIndex",
                KeyConditionExpression="idempotency_key = :k",
                ExpressionAttributeValues={":k": idempotency_key},
                Limit=1,
            )
            items = gsi_response.get("Items", [])
            if items:
                existing = items[0]
                existing_json = existing.get("event_json")
                if existing_json == event_json and existing.get("stream_id") == stream_id:
                    return {
                        "status": "duplicate",
                        "duplicate": True,
                        "stream_id": stream_id,
                        "event_id": event_id,
                        "sequence_number": sequence_number,
                    }
                raise DuplicateKeyConflict("idempotency_key was already used for different event data")

            # 2. Put item with conditional write ensuring no duplicate sequence on stream
            table.put_item(
                Item={
                    "stream_id": stream_id,
                    "sequence_number": sequence_number,
                    "event_id": event_id,
                    "idempotency_key": idempotency_key,
                    "event_type": event_type,
                    "event_json": event_json,
                },
                ConditionExpression="attribute_not_exists(stream_id) AND attribute_not_exists(sequence_number)",
            )

            return {
                "status": "accepted",
                "duplicate": False,
                "stream_id": stream_id,
                "event_id": event_id,
                "event_type": event_type,
                "sequence_number": sequence_number,
            }

        except DuplicateKeyConflict:
            raise
        except Exception:
            return self.fallback.ingest(stream_id=stream_id, raw_event=raw_event)

    def clear(self) -> None:
        """Clear store fallback."""
        self.fallback.clear()


def get_event_store():
    from backend.config.settings import settings
    if settings.AWS_INTEGRATIONS_ENABLED:
        return DynamoDBEventStore()
    return SQLiteEventStore()


# Keep the existing public names so current API imports continue working.
LocalEventStore = SQLiteEventStore
event_store = get_event_store()


