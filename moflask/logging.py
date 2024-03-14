"""Logging with some goodies.

Provide a enhanced logging infrastructure:
- A default handler with a custom format (settings key `LOG_FORMAT`)
- A file log handler in JSON format (interesting for structured logging)
- Filters to enrich log entries with contextual information from Flask or
  Werkzeug or requests such as the request IP, the response status code,…

Settings options:
- LOG_LEVEL: log level for the logger
- LOG_FORMAT: string format for the default formatter
- LOG_DATE_FORMAT: date format for the default formatter
- LOG_FILE: path to the log file – if not set the file handler is disabled
- LOG_FILE_INCLUDE: record fields to include in the JSON output
- LOG_FILE_MAX_SIZE: maximum size of the logfile before a new file is started
- LOG_FILE_COUNT: number of old log files to keep (if 0 the max size will be exceeded)

"""

import datetime
import json
import logging
import logging.handlers
import os

import flask
from pythonjsonlogger import jsonlogger


class ISOTimeFormatterMixin:  # pylint: disable=too-few-public-methods
    """Mixin for formatting the logging time as ISO8601.

    Formats with TZ offset and milliseconds.
    This is not achievable with the default formatter options alone.

    Caveats:
    - The datefmt option is hardcoded.
    - Formatter.converter is ignored, localtime is used
    """

    def formatTime(self, record, *_args, **_kwargs):  # pylint: disable=invalid-name
        """Format time as ISO8601 timestamps with milliseconds."""
        created = datetime.datetime.fromtimestamp(record.created)
        return created.astimezone().isoformat(timespec="milliseconds")


class Formatter(ISOTimeFormatterMixin, logging.Formatter):
    """Extended logging formatter."""


class JsonFormatter(ISOTimeFormatterMixin, jsonlogger.JsonFormatter):
    """Extended JSON logging formatter."""


def init_logger(app, extra_filters=None):
    """Configure the app’s logger with custom filters and handlers."""
    logger = logging.getLogger(app.name)
    logger.setLevel(app.config.get("LOG_LEVEL", logging.DEBUG if app.debug else logging.INFO))

    # Configure a handler before accessing the logger via app.logger.
    logger.addHandler(get_default_handler(app.config, extra_filters))

    # Add a file handler too if configured.
    file_handler = get_json_file_handler(app.config, logger, extra_filters)
    if file_handler:
        logger.addHandler(file_handler)


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
        record.response_body_text = response.text
        try:
            record.response_body_json = response.json()
        except json.decoder.JSONDecodeError:
            pass
    return True


def get_formatter(config):
    """Get a string formatter."""
    fmt = config.get("LOG_FORMAT", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    datefmt = config.get("LOG_DATE_FORMAT", None)
    return Formatter(fmt, datefmt)


def get_json_formatter(config):
    """Get a JSON formatter."""
    default_include = [
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
    include = config.get("LOG_FILE_INCLUDE", default_include)
    # Fields form the `extra` dict are automatically added by the JsonFormatter.
    return JsonFormatter(" ".join(f"%({prop})" for prop in include))


def get_default_handler(config, filters=None):
    """Get a default stream handler with custom formatting."""
    handler = flask.logging.default_handler
    handler.setFormatter(get_formatter(config))
    for filter_ in filters or []:
        handler.addFilter(filter_)
    return handler


def get_json_file_handler(config, logger=None, filters=None):
    """Get a file handler with custom JSON formatting and context data."""
    log_file = config.get("LOG_FILE", os.environ.get("LOG_FILE", None))
    if log_file is None:
        return None
    # Check for existing handler before adding a new one.
    handler = next(
        filter(
            lambda h: getattr(h, "baseFilename", None) == log_file,
            logger.handlers if logger else [],
        ),
        logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.get("LOG_FILE_MAX_SIZE", 0),
            backupCount=config.get("LOG_FILE_COUNT", 0),
        ),
    )
    handler.setFormatter(get_json_formatter(config))
    default_filters = [
        add_app_context_data,
        add_request_context_data,
        add_request_data,
        add_response_data,
    ]
    for filter_ in default_filters + (filters or []):
        handler.addFilter(filter_)
    return handler
