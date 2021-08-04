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

# pylint: disable=too-few-public-methods

import logging
import logging.handlers

from flask import current_app, has_app_context, has_request_context, request
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

    # Add any relevant filters to the logger.
    logger.addFilter(ContextFilter(AppContext(), RequestContext()))
    if current_user:
        logger.addFilter(ContextFilter(UserContext()))
    logger.addFilter(RequestResponseContextFilter())


class RequestContext:
    """
    Return information about the current request if available.

    This information can be used to enrich log calls by merging this information
    into the `extra` dict.
    """

    def __call__(self):
        """Get request context information."""
        if has_request_context():
            return {"request_remote_addr": request.remote_addr}
        return {}


class AppContext:
    """
    Return information about the app if available.

    This information can be used to enrich log calls by merging this information
    into the `extra` dict.
    """

    def __call__(self):
        """Get app context information."""
        if has_app_context():
            return {"app": current_app.name}
        return {}


class UserContext:
    """
    Return information about the logged in user if available.

    This information can be used to enrich log calls by merging this information
    into the `extra` dict.
    """

    def __call__(self):
        """Get user context information."""
        if current_user:
            if current_user.is_authenticated:
                return {"user": repr(current_user)}
            return {"user": "<AnonymousUser>"}
        return {}


class ContextFilter(logging.Filter):
    """Set contextual information about the app, request and user."""

    def __init__(self, *args):
        """Create a new filter by passing the context callables."""
        super().__init__()
        self.contexts = args

    def filter(self, record):
        """Add custom attributes as specified by the context objects."""
        data = {}
        for callback in self.contexts:
            data.update(callback())

        for key, value in data.items():
            setattr(record, key, value)

        return True


class RequestResponseContextFilter(logging.Filter):
    """
    Set contextual information about a response or request in the logrecord.

    The filter looks for the attribute `_response` or `_request` in the `record`,
    tries to retrieve whitelisted information and sets or updates attribures on
    the logrecord.

    * `_response.status_code` --> `response_status_code`
    * `_response.text` --> `response_text`
    * `_request.url` --> `request_url`
    * `_request.method` --> `request_method`

    If an attribute is not set the value `<attr not found>` get's logged.

    `_response`/`_request` can be added by log calls in the `extra` dict.
    """

    def filter(self, record):
        """Add custom attributes as specified by the context objects."""
        if hasattr(record, "_response"):
            resp = getattr(record, "_response", None)
            record.response_status_code = getattr(resp, "status_code", "<attr not found>")
            record.response_text = getattr(resp, "text", "<attr not found>")

        if hasattr(record, "_request"):
            req = getattr(record, "_request", None)
            record.request_url = getattr(req, "url", "<attr not found>")
            record.request_method = getattr(req, "method", "<attr not found>")

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
    for filter_ in filters or []:
        handler.addFilter(filter_)
    return handler
