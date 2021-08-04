"""Test flask_security related loggging.

This needs some mocking of sys.modules, so isolate this in it's own test
file.
"""
# pylint: disable=no-member,protected-access

import logging

from flask import Flask
from flask_login import LoginManager

from ..logging import ContextFilter, UserContext


def test_user_context_filter():
    """Test UserContext enriches the LogRecord.

    Pulls information from a Flask-Security `currrent_user` object.
    """
    app = Flask(__name__)

    # Provide a minimal setup for `current_user` to work
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.user_loader(lambda user_id: None)

    context_filter = ContextFilter(UserContext())
    record = logging.makeLogRecord({})
    with app.test_request_context("/"):
        context_filter.filter(record)
    assert record.user
    assert record.user == "<AnonymousUser>"
