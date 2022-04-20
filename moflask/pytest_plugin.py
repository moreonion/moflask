"""Pre-defined pytest fixtures to be used in tests of the dependent apps.

This plugin is loaded automatically when this module is installed which makes the fixtures
available without further configuration.
"""

import contextlib
from unittest import mock

import pytest

# Check whether flask_jwt_extended (optional dependency) is installed.
JWT_INSTALLED = False
try:
    from . import jwt

    JWT_INSTALLED = True
except ModuleNotFoundError:
    pass


if JWT_INSTALLED:

    def _push_session_to_context(session):
        context = jwt.ctx_stack.top
        context.jwt = session.to_token_data()
        context.jwt_user = {"loaded_user": session}
        return None, context.jwt

    @pytest.fixture(name="jwt_inject_session")
    def fixture_inject_session():
        """Define a helper function to mock out JWT authentication checks."""

        @contextlib.contextmanager
        def inject_session(session):
            with mock.patch("flask_jwt_extended.verify_jwt_in_request") as mock_verify:
                mock_verify.side_effect = lambda *args, **kwargs: _push_session_to_context(session)
                yield

        return inject_session
