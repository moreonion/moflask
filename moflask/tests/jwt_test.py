"""Tests for the JWT auth-app utilities."""

import flask
import flask_jwt_extended
import pytest

from .. import jwt


class SessionTest:
    """Unit-tests for the Session class."""

    @staticmethod
    def test_init_generates_session_id():
        """Test that creating a new session automatically generates a unique session id."""
        session1 = jwt.Session("user-id", "org", [])
        session2 = jwt.Session("user-id", "org", [])
        assert session1.session_id
        assert session2.session_id
        assert session1.session_id != session2.session_id

    @staticmethod
    def test_custom_uuid_init():
        """Test passing a custom session uuid in the constructor."""
        uuid = "24861915-4617-4dc9-ac0e-2326c7538abc"
        session = jwt.Session("user-id", "org", [], uuid)
        data = session.to_token_data()
        assert data["user_claims"]["session_id"] == uuid

    @staticmethod
    def test_create_session_from_token():
        """Test creating a session from a token."""
        token = {
            "identity": "7fd8ecf2-c1fa-43fa-8661-3eafaec457b0",
            "user_claims": {
                "org": "org1",
                "roles": ["admin"],
                "session_id": "24861915-4617-4dc9-ac0e-2326c7538abc",
            },
        }
        session = jwt.Session.from_raw_token(token)
        assert session.to_token_data() == token


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

    @app.route("/optional")
    @jwt.required(optional=True)
    def dump_session2():
        session = jwt.get_current_session()
        return flask.jsonify(session.to_token_data())

    return app


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
    assert response.json["user_claims"]["session_id"]


def test_getting_injected_session_data(protected_app, jwt_inject_session):
    """Inject session using the settings."""
    session = jwt.Session("user-id", "organization", ["app"])

    with jwt_inject_session(session):
        with protected_app.test_client() as client:
            response = client.get("/")

    assert response.status_code == 200
    assert response.json["identity"] == "user-id"
    assert response.json["user_claims"]["org"] == "organization"
    assert response.json["user_claims"]["roles"] == ["app"]


def test_denying_access_without_an_admitted_role(protected_app, jwt_inject_session):
    """Test the error response given when the JWT doesn’t have any of the admitted roles."""
    session = jwt.Session("user-id", "organization", ["not-app"])

    with jwt_inject_session(session):
        with protected_app.test_client() as client:
            response = client.get("/")

    assert response.status_code == 403
    assert "The user has none of the admitted roles" in response.data.decode()


def test_anonymous_session_with_optional(protected_app):
    """Test that a session is created on-the-fly for anonymous users."""
    with protected_app.test_client() as client:
        response = client.get("/optional")
    assert response.status_code == 200
    assert response.json["identity"] is None
    assert response.json["user_claims"]["org"] is None
    assert response.json["user_claims"]["roles"] == []


def test_anonymous_session_with_organization(protected_app):
    """Test that sessions for anonymous requests read the x-ist-org header."""
    with protected_app.test_client() as client:
        # Showcase that the header name is not case-sensitive.
        response = client.get("/optional", headers={"X-IsT-OrG": "test-org"})
    assert response.status_code == 200
    assert response.json["identity"] is None
    assert response.json["user_claims"]["org"] == "test-org"
    assert response.json["user_claims"]["roles"] == []
