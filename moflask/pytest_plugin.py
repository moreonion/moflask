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
    from . import jwt  # pylint: disable=unused-import

    JWT_INSTALLED = True
except ModuleNotFoundError:
    pass


if JWT_INSTALLED:
    import flask

    def _push_session_to_context(session, context):
        # pylint: disable=protected-access
        context._jwt_extended_jwt = session.to_token_data()
        context._jwt_extended_jwt_user = {"loaded_user": session}
        return None, context

    @pytest.fixture(name="jwt_inject_session")
    def fixture_inject_session():
        """Define a helper function to mock out JWT authentication checks."""

        @contextlib.contextmanager
        def inject_session(session):
            with mock.patch("flask_jwt_extended.verify_jwt_in_request") as mock_verify:
                mock_verify.side_effect = lambda *args, **kwargs: _push_session_to_context(
                    session, flask.g
                )
                yield

        return inject_session
