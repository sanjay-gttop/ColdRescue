"""Optional CloudWatch Logs integration for ColdRescue."""
from __future__ import annotations

import logging
import time
from typing import Any

import boto3

from backend.config.settings import settings


class CloudWatchLogHandler(logging.Handler):
    """Send formatted log records to an existing CloudWatch log stream."""

    def __init__(
        self,
        client: Any,
        log_group: str,
        log_stream: str,
    ) -> None:
        super().__init__()

        if not log_group.strip():
            raise ValueError("log_group must not be empty")
        if not log_stream.strip():
            raise ValueError("log_stream must not be empty")

        self.client = client
        self.log_group = log_group
        self.log_stream = log_stream

    def emit(self, record: logging.LogRecord) -> None:
        """Send one record without propagating AWS errors to the application."""
        try:
            message = self.format(record)

            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        "timestamp": int(time.time() * 1000),
                        "message": message,
                    }
                ],
            )
        except Exception:
            self.handleError(record)


def create_cloudwatch_handler() -> CloudWatchLogHandler | None:
    """Create a handler only when AWS integration is explicitly enabled.

    This function does not create log groups or log streams.
    """
    if not settings.AWS_INTEGRATIONS_ENABLED:
        return None

    client = boto3.client(
        "logs",
        region_name=settings.AWS_REGION,
    )

    handler = CloudWatchLogHandler(
        client=client,
        log_group=settings.CLOUDWATCH_LOG_GROUP,
        log_stream=settings.CLOUDWATCH_LOG_STREAM,
    )

    from backend.config.logging import JsonFormatter

    handler.setFormatter(JsonFormatter())
    return handler


def attach_cloudwatch_handler(logger: logging.Logger) -> bool:
    """Attach CloudWatch logging when enabled; otherwise do nothing."""
    if not settings.AWS_INTEGRATIONS_ENABLED:
        return False

    # Avoid attaching duplicate CloudWatch handlers.
    if any(
        isinstance(handler, CloudWatchLogHandler)
        for handler in logger.handlers
    ):
        return True

    handler = create_cloudwatch_handler()
    if handler is None:
        return False

    logger.addHandler(handler)
    return True