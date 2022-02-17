"""Tests for the JWT auth-app utilities."""

import contextlib
from unittest import mock

import flask
import flask_jwt_extended
import pytest

from .. import jwt


@pytest.fixture(name="protected_app")
def fixture_protected_app():
    """Create an app with one JWT protected route."""
    app = flask.Flask("test")
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    jwt.manager.init_app(app)

    @app.route("/")
    @jwt.required(admitted_roles=["app"])
    def dump_session():
        session = jwt.get_current_session()
        return flask.jsonify(session.to_token_data())

    return app


@pytest.fixture(name="inject_session")
def fixture_inject_session():
    """Define a helper function to mock out JWT authentication checks."""

    @contextlib.contextmanager
    def inject_session(session):
        with mock.patch("flask_jwt_extended.verify_jwt_in_request"):
            with mock.patch.object(jwt, "get_current_session") as mock_current_session:
                mock_current_session.return_value = session
                yield

    return inject_session


def test_getting_session_data_in_authorized_request(protected_app):
    """Send an authorized request to the endpoint."""
    session = jwt.Session("user-id", "organization", ["app"])
    with protected_app.app_context():
        token = flask_jwt_extended.create_access_token(session)

    with protected_app.test_client() as client:
        response = client.get("/", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json["identity"] == "user-id"
    assert response.json["user_claims"]["org"] == "organization"
    assert response.json["user_claims"]["roles"] == ["app"]


def test_getting_injected_session_data(protected_app, inject_session):
    """Inject session using the settings."""
    session = jwt.Session("user-id", "organization", ["app"])

    with inject_session(session):
        with protected_app.test_client() as client:
            response = client.get("/")

    assert response.status_code == 200
    assert response.json["identity"] == "user-id"
    assert response.json["user_claims"]["org"] == "organization"
    assert response.json["user_claims"]["roles"] == ["app"]
