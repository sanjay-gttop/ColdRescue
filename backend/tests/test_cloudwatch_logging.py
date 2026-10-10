"""Tests for the optional CloudWatch logging handler."""

import logging
from unittest.mock import Mock, patch

import pytest

from backend.config.settings import settings
from backend.services.cloudwatch_logging import (
    CloudWatchLogHandler,
    attach_cloudwatch_handler,
    create_cloudwatch_handler,
)


def make_record(message: str = "ColdRescue test message") -> logging.LogRecord:
    return logging.LogRecord(
        name="coldrescue.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_handler_sends_formatted_log_to_cloudwatch():
    client = Mock()
    handler = CloudWatchLogHandler(
        client=client,
        log_group="/coldrescue/application/test",
        log_stream="test-stream",
    )
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

    handler.emit(make_record())

    client.put_log_events.assert_called_once()
    call = client.put_log_events.call_args.kwargs

    assert call["logGroupName"] == "/coldrescue/application/test"
    assert call["logStreamName"] == "test-stream"
    assert len(call["logEvents"]) == 1
    assert call["logEvents"][0]["message"] == (
        "INFO:ColdRescue test message"
    )
    assert isinstance(call["logEvents"][0]["timestamp"], int)

    handler.close()


@pytest.mark.parametrize(
    ("log_group", "log_stream"),
    [
        ("", "test-stream"),
        ("   ", "test-stream"),
        ("/coldrescue/test", ""),
        ("/coldrescue/test", "   "),
    ],
)
def test_handler_rejects_empty_group_or_stream(log_group, log_stream):
    with pytest.raises(ValueError):
        CloudWatchLogHandler(
            client=Mock(),
            log_group=log_group,
            log_stream=log_stream,
        )


def test_cloudwatch_error_does_not_escape_handler():
    client = Mock()
    client.put_log_events.side_effect = RuntimeError(
        "Simulated AWS failure"
    )

    handler = CloudWatchLogHandler(
        client=client,
        log_group="/coldrescue/application/test",
        log_stream="test-stream",
    )

    with patch.object(handler, "handleError") as handle_error:
        handler.emit(make_record())

    handle_error.assert_called_once()
    handler.close()


def test_handler_does_not_call_aws_until_a_record_is_emitted():
    client = Mock()

    handler = CloudWatchLogHandler(
        client=client,
        log_group="/coldrescue/application/test",
        log_stream="test-stream",
    )

    client.put_log_events.assert_not_called()
    handler.close()


def test_cloudwatch_handler_is_disabled_by_default():
    assert settings.AWS_INTEGRATIONS_ENABLED is False

    with patch(
        "backend.services.cloudwatch_logging.boto3.client"
    ) as mock_client:
        handler = create_cloudwatch_handler()

    assert handler is None
    mock_client.assert_not_called()


def test_cloudwatch_handler_uses_configured_settings():
    with (
        patch(
            "backend.services.cloudwatch_logging.settings.AWS_INTEGRATIONS_ENABLED",
            True,
        ),
        patch(
            "backend.services.cloudwatch_logging.boto3.client"
        ) as mock_client,
    ):
        mock_client.return_value = Mock()

        handler = create_cloudwatch_handler()

    mock_client.assert_called_once_with(
        "logs",
        region_name=settings.AWS_REGION,
    )

    assert isinstance(handler, CloudWatchLogHandler)
    assert handler.log_group == settings.CLOUDWATCH_LOG_GROUP
    assert handler.log_stream == settings.CLOUDWATCH_LOG_STREAM
    assert handler.formatter is not None

    handler.close()


def test_attach_cloudwatch_handler_does_nothing_when_disabled():
    logger = logging.getLogger("coldrescue.test.disabled")

    with (
        patch(
            "backend.services.cloudwatch_logging.settings.AWS_INTEGRATIONS_ENABLED",
            False,
        ),
        patch(
            "backend.services.cloudwatch_logging.create_cloudwatch_handler"
        ) as mock_factory,
    ):
        result = attach_cloudwatch_handler(logger)

    assert result is False
    mock_factory.assert_not_called()


def test_attach_cloudwatch_handler_attaches_handler_when_enabled():
    logger = logging.getLogger("coldrescue.test.enabled")
    fake_handler = Mock(spec=CloudWatchLogHandler)

    with (
        patch(
            "backend.services.cloudwatch_logging.settings.AWS_INTEGRATIONS_ENABLED",
            True,
        ),
        patch(
            "backend.services.cloudwatch_logging.create_cloudwatch_handler",
            return_value=fake_handler,
        ) as mock_factory,
    ):
        result = attach_cloudwatch_handler(logger)

    try:
        assert result is True
        assert fake_handler in logger.handlers
        mock_factory.assert_called_once_with()
    finally:
        logger.removeHandler(fake_handler)


def test_attach_cloudwatch_handler_does_not_attach_duplicates():
    logger = logging.getLogger("coldrescue.test.duplicate")

    existing_handler = CloudWatchLogHandler(
        client=Mock(),
        log_group="/coldrescue/application/test",
        log_stream="test-stream",
    )
    logger.addHandler(existing_handler)

    try:
        with (
            patch(
                "backend.services.cloudwatch_logging.settings.AWS_INTEGRATIONS_ENABLED",
                True,
            ),
            patch(
                "backend.services.cloudwatch_logging.create_cloudwatch_handler"
            ) as mock_factory,
        ):
            result = attach_cloudwatch_handler(logger)

        assert result is True
        assert logger.handlers.count(existing_handler) == 1
        mock_factory.assert_not_called()
    finally:
        logger.removeHandler(existing_handler)
        existing_handler.close()