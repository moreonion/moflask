"""Pre-defined pytest fixtures to be used in tests of the dependent apps."""

import contextlib
from unittest import mock

import pytest


@pytest.fixture(name="jwt_inject_session")
def fixture_inject_session():
    """Define a helper function to mock out JWT authentication checks."""

    @contextlib.contextmanager
    def inject_session(session):
        with mock.patch("flask_jwt_extended.verify_jwt_in_request"):
            with mock.patch("moflask.jwt.get_current_session") as mock_current_session:
                mock_current_session.return_value = session
                yield

    return inject_session
