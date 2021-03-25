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

from flask import current_app, has_app_context, has_request_context, request
from flask.logging import default_handler

# Ensure the `current_user` variable is set for the filter below.
try:
    from flask_security import current_user
except ImportError:
    current_user = None


def configure_logger(logger, config):
    """Configure a logger object with custom filters and handlers.

    If `LOG_JSON=True` then the logs are formatted using a JSON formatter.

    Otherwise a custom formatter, which also prints (any not-consumed)
    `_extra` fields is used. These fields get populated by the filters from
    this module.

    If `LOG_HANDLERS` is not configured, the Flask `default_handler` is used.
    """
    if config.get("LOG_JSON", False):
        from pythonjsonlogger import jsonlogger

        # extra fields are taken care of by the JsonFormatter
        formatter = jsonlogger.JsonFormatter(
            (
                "%(message) %(levelname) %(name) %(asctime) %(created) "
                "%(process) %(processName) %(thread) %(threadName) "
                "%(lineno) %(module) %(pathname)"
            )
        )
    else:
        formatter = OptionalExtraFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    logger.setLevel(config.get("LOG_LEVEL", logging.INFO))

    for handler in config.get("LOG_HANDLERS", [default_handler]):
        logger.addHandler(handler)

    # configure registered handlers
    for handler in logger.handlers:
        handler.setFormatter(formatter)

    # add any relevant filters to the logger
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

        record._extra = data  # pylint: disable=protected-access
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


class OptionalExtraFormatter(logging.Formatter):
    """
    Formatter which outputs structured extra information to a log msg string.

    It allows you to savely try to output a `extra` template variable as this
    Formatter only tries to use it when the information is available in the
    log record.

    The information in the `extra` attribute get's serialized as `str()`. You can
    change this with the `extrafmt` argument.

    You can combine this with e.g. a LoggingAdapter which ensures an `_extra`
    attribute on the logrecord. Otherwise the default logging modules behaviour
    would be to copy the `extra`s fields onto the logrecord using the
    respective keys, the `extra` dict is not available as dict on the logrecord
    by default.
    """

    def __init__(self, fmt=None, datefmt=None, extrafmt="%(message)s %(extra)s"):
        """Create formatter."""
        super().__init__(fmt, datefmt)
        self._extrafmt = extrafmt

    def format(self, record):
        """Format a record."""
        # pylint: disable=protected-access
        if hasattr(record, "_extra") and record._extra:
            msg = logging.Formatter.format(self, record)
            msg = self._extrafmt % {"message": msg, "extra": record._extra}
        else:
            msg = logging.Formatter.format(self, record)

        return msg
