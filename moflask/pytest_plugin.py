"""Pre-defined pytest fixtures to be used in tests of the dependent apps."""

import contextlib
from unittest import mock

import pytest

from . import jwt


def _push_session_to_context(session):
    context = jwt.ctx_stack.top
    context.jwt = session.to_token_data()
    context.jwt_user = {"loaded_user": session}


@pytest.fixture(name="jwt_inject_session")
def fixture_inject_session():
    """Define a helper function to mock out JWT authentication checks."""

    @contextlib.contextmanager
    def inject_session(session):
        with mock.patch("flask_jwt_extended.verify_jwt_in_request") as mock_verify:
            mock_verify.side_effect = lambda: _push_session_to_context(session)
            yield

    return inject_session
