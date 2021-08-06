"""Test flask_security related loggging.

This needs some mocking of sys.modules, so isolate this in it's own test
file.
"""
# pylint: disable=no-member,protected-access

import logging as _logging

from flask import Flask
from flask_login import LoginManager

from moflask import logging


def test_user_context_filter():
    """Test UserContext enriches the LogRecord.

    Pulls information from a Flask-Security `currrent_user` object.
    """
    app = Flask(__name__)

    # Provide a minimal setup for `current_user` to work
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.user_loader(lambda user_id: None)

    context_filter = logging.add_user_data
    record = _logging.makeLogRecord({})
    with app.test_request_context("/"):
        context_filter(record)
    assert record.user
    assert record.user == "<AnonymousUser>"
