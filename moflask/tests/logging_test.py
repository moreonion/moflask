"""Tests for logging."""
# pylint: disable=no-member,protected-access

import logging

from flask import Flask
from pythonjsonlogger.jsonlogger import JsonFormatter

from ..logging import (
    AppContext,
    ContextFilter,
    OptionalExtraFormatter,
    RequestContext,
    configure_logger,
)


def test_configuring_default_logger():
    """Default formatter is OptionalExtraFormatter."""
    app = Flask("moflask")

    configure_logger(app.logger, {})

    assert app.logger.name == "moflask"
    assert isinstance(app.logger.handlers[0].formatter, OptionalExtraFormatter)


def test_configuring_with_json_logger():
    """Test configuring with JsonFormatter."""
    app = Flask("moflask")

    configure_logger(app.logger, {"LOG_JSON": True})

    assert app.logger.name == "moflask"
    assert isinstance(app.logger.handlers[0].formatter, JsonFormatter)


def test_app_context_filter():
    """AppContext enriches the LogRecord.

    Pulls information from a Flask `currrent_app` context.

    The information is available at the LogRecord and the `_extra` attribute.
    """
    app = Flask("app_context")

    context_filter = ContextFilter(AppContext())
    record = logging.makeLogRecord({})
    with app.app_context():
        context_filter.filter(record)
    assert record.app
    assert record.app == "app_context"
    assert "app" in record._extra
    assert record._extra["app"] == "app_context"


def test_request_context_filter():
    """RequestContext enriches the LogRecord.

    Pulls information from a Flask `request` context.

    The information is available at the LogRecord and the `_extra` attribute.
    """
    app = Flask(__name__)

    context_filter = ContextFilter(RequestContext())
    record = logging.makeLogRecord({})
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.1.2.3"}):
        context_filter.filter(record)
    assert record.request_remote_addr
    assert record.request_remote_addr == "127.1.2.3"
    assert "request_remote_addr" in record._extra
    assert record._extra["request_remote_addr"] == "127.1.2.3"
