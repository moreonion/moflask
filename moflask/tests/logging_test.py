"""Tests for logging."""
# pylint: disable=no-member,protected-access

import logging as _logging

import requests
from flask import Flask
from pythonjsonlogger.jsonlogger import JsonFormatter

from moflask import logging


def test_configuring_default_logger():
    """Test Default formatter is used."""
    app = Flask("moflask")

    logging.init_logger(app)

    assert app.logger.name == "moflask"
    assert isinstance(app.logger.handlers[-1].formatter, _logging.Formatter)


def test_configuring_file_logger():
    """Test JsonFormatter is used for log file."""
    app = Flask("moflask")
    app.config["LOG_FILE"] = "/tmp/moflask.logging_test.log"

    logging.init_logger(app)

    assert app.logger.name == "moflask"
    assert isinstance(app.logger.handlers[-1].formatter, JsonFormatter)
    assert app.logger.handlers[-1].baseFilename == "/tmp/moflask.logging_test.log"


def test_handlers_are_added_once():
    """Test that existing handlers are not added again."""
    app = Flask("moflask")
    app.config["LOG_FILE"] = "/tmp/moflask.logging_test.log"

    logging.init_logger(app)
    assert len(app.logger.handlers) == 2
    handlers1 = app.logger.handlers.copy()

    logging.init_logger(app)
    assert len(app.logger.handlers) == 2
    assert app.logger.handlers == handlers1


def test_adding_extra_filters():
    """Test extra filters are added to the handlers."""

    def extra_filter(record):
        record.test = "test"
        return True

    app = Flask("moflask")
    app.config["LOG_FILE"] = "/tmp/moflask.logging_test.log"

    logging.init_logger(app, [extra_filter])
    for handler in app.logger.handlers:
        assert extra_filter in handler.filters


def test_app_context_filter():
    """Test app context enriches the LogRecord.

    Pulls information from a Flask `currrent_app` context.
    """
    app = Flask("app_context")

    context_filter = logging.add_app_context_data
    record = _logging.makeLogRecord({})
    with app.app_context():
        context_filter(record)
    assert record.app
    assert record.app == "app_context"


def test_request_context_filter():
    """Test request context enriches the LogRecord.

    Pulls information from a Flask `request` context.
    """
    app = Flask(__name__)

    context_filter = logging.add_request_context_data
    record = _logging.makeLogRecord({})
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.1.2.3"}):
        context_filter(record)
    assert record.request_remote_addr
    assert record.request_remote_addr == "127.1.2.3"


def test_request_filter():
    """Test _request in extra enriches the LogRecord."""
    record = _logging.makeLogRecord({"_request": requests.Request("POST", "https://mo.flask")})
    logging.add_request_data(record)
    assert record.request_method
    assert record.request_method == "POST"
    assert record.request_url
    assert record.request_url == "https://mo.flask"


def test_response_filter():
    """Test _response in extra enriches the LogRecord."""
    response = requests.Response()
    response.status_code = 200
    # pylint: disable=protected-access
    response._content = "Hello".encode("utf-8")
    record = _logging.makeLogRecord({"_response": response})
    logging.add_response_data(record)
    assert record.response_status_code
    assert record.response_status_code == 200
    assert record.response_body
    assert record.response_body == "Hello"


def test_response_filter_with_json():
    """Test the added response body is JSON if the response was JSON."""
    response = requests.Response()
    response.status_code = 200
    # pylint: disable=protected-access
    response._content = '{"test": 1}'.encode("utf-8")
    record = _logging.makeLogRecord({"_response": response})
    logging.add_response_data(record)
    assert record.response_status_code
    assert record.response_status_code == 200
    assert record.response_body
    assert "test" in record.response_body
    assert record.response_body["test"] == 1
