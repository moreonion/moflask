"""Tests for logging."""
# pylint: disable=no-member,protected-access

import logging

from flask import Flask
from pythonjsonlogger.jsonlogger import JsonFormatter

from ..logging import AppContext, ContextFilter, RequestContext, configure_logger


def test_configuring_default_logger():
    """Test Default formatter is used."""
    app = Flask("moflask")

    configure_logger(app.logger, {})

    assert app.logger.name == "moflask"
    assert isinstance(app.logger.handlers[-1].formatter, logging.Formatter)


def test_configuring_file_logger():
    """Test JsonFormatter is used for log file."""
    app = Flask("moflask")

    configure_logger(app.logger, {"LOG_FILE": "/tmp/moflask.logging_test.log"})

    assert app.logger.name == "moflask"
    assert isinstance(app.logger.handlers[-1].formatter, JsonFormatter)
    assert app.logger.handlers[-1].baseFilename == "/tmp/moflask.logging_test.log"


def test_app_context_filter():
    """Test AppContext enriches the LogRecord.

    Pulls information from a Flask `currrent_app` context.
    """
    app = Flask("app_context")

    context_filter = ContextFilter(AppContext())
    record = logging.makeLogRecord({})
    with app.app_context():
        context_filter.filter(record)
    assert record.app
    assert record.app == "app_context"


def test_request_context_filter():
    """Test RequestContext enriches the LogRecord.

    Pulls information from a Flask `request` context.
    """
    app = Flask(__name__)

    context_filter = ContextFilter(RequestContext())
    record = logging.makeLogRecord({})
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.1.2.3"}):
        context_filter.filter(record)
    assert record.request_remote_addr
    assert record.request_remote_addr == "127.1.2.3"
