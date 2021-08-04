"""Logging with some goodies.

Provide a enhanced logging infrastructure:
- Allow logging in JSON format (interesting for structured logging)
- Automatically enrich log entries with contextual information from Flask or
  Werkzeug such as the request IP, the response status code, ...
- The filters are extensible

You can select logging in JSON with the settings key `LOG_JSON`. You will
need to install `python-json-logger` for that.

If you do not use the JSON formatter the fallback formatter will be used
which allows you to log *arbitrary* values from the log records `extra`
attribute.

Currently the same formatter will be used for all configured handlers.
"""

import logging
import logging.handlers

import flask
from pythonjsonlogger import jsonlogger

# Ensure the `current_user` variable is set for the filter below.
try:
    from flask_login import current_user
except ImportError:
    current_user = None


def configure_logger(logger, config):
    """Configure a logger object with custom filters and handlers."""
    logger.addHandler(get_default_handler())

    # Add a file handler too if configured.
    file_handler = get_json_file_handler(config)
    if file_handler:
        logger.addHandler(file_handler)

    logger.setLevel(config.get("LOG_LEVEL", logging.INFO))


def add_request_context_data(record):
    """Add request data from the context to the log record if available."""
    if flask.has_request_context():
        record.request_remote_addr = flask.request.remote_addr
    return True


def add_app_context_data(record):
    """Add app data from the context to the log record if available."""
    if flask.has_app_context():
        record.app = flask.current_app.name
    return True


def add_user_data(record):
    """Add user data to the log record if available."""
    if current_user:
        if current_user.is_authenticated:
            record.user = repr(current_user)
        else:
            record.user = "<AnonymousUser>"
    return True


def add_request_data(record):
    """Add contextual information about a request to the log record.

    The filter looks for the attribute `_request` in the `record`,
    tries to retrieve specific information and sets or updates attributes
    on the log record. The request is expected to be of type `requests.Request`.

    `_request` can be added by log calls in the `extra` dict.
    """
    request = getattr(record, "_request", None)
    if request:
        record.request_url = request.url
        record.request_method = request.method
    return True


def add_response_data(record):
    """Add contextual information about a response to the log record.

    The filter looks for the attribute `_response` in the `record`,
    tries to retrieve specific information and sets or updates attributes
    on the log record. The response is expected to be of type `requests.Response`.

    `_response` can be added by log calls in the `extra` dict.
    """
    response = getattr(record, "_response", None)
    if response:
        record.response_status_code = response.status_code
        record.response_text = response.text
    return True


def get_formatter():
    """Get a string formatter."""
    return logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def get_json_formatter():
    """Get a JSON formatter."""
    include = [
        "message",
        "levelname",
        "name",
        "asctime",
        "created",
        "process",
        "processName",
        "thread",
        "threadName",
        "lineno",
        "module",
        "pathname",
    ]
    # Fields form the `extra` dict are automatically added by the JsonFormatter.
    return jsonlogger.JsonFormatter(" ".join(f"%({prop})" for prop in include))


def get_default_handler(filters=None, formatter=None):
    """Get a default stream handler with custom formatting."""
    handler = logging.StreamHandler()
    handler.setFormatter(formatter or get_formatter())
    for filter_ in filters or []:
        handler.addFilter(filter_)
    return handler


def get_json_file_handler(config, filters=None, formatter=None):
    """Get a file handler with custom JSON formatting and context data."""
    log_file = config.get("LOG_FILE", None)
    if log_file is None:
        return None
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.get("LOG_FILE_MAX_SIZE", 0),
        backupCount=config.get("LOG_FILE_COUNT", 0),
    )
    handler.setFormatter(formatter or get_json_formatter())
    default_filters = [
        add_app_context_data,
        add_request_context_data,
        add_request_data,
        add_response_data,
    ]
    if current_user:
        default_filters.append(add_user_data)
    for filter_ in default_filters + (filters or []):
        handler.addFilter(filter_)
    return handler
