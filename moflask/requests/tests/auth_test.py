"""Unit-tests for the auth middleware implementations."""
# pylint: disable=too-few-public-methods

from unittest import mock

import flask
import pytest
import requests_mock as rm

from .. import auth


@pytest.fixture(name="app", scope="class")
def fixture_app():
    """Define a test Flask app."""
    app = flask.Flask("test-app")
    app.config["IMPACT_STACK_AUTH_APP_URL"] = "https://auth.impact-stack.org/v1"
    app.config["IMPACT_STACK_AUTH_APP_KEY"] = "api-key"
    with app.app_context():
        yield app


@pytest.mark.usefixtures("app")
class AuthAppClientTest:
    """Test the auth-app client."""

    @staticmethod
    def test_get_token(requests_mock):
        """Test getting a token."""
        client = auth.AuthAppClient.from_config()
        requests_mock.post(rm.ANY, json={"token": "TOKEN.org1"})
        token = client.get_token("org1")
        assert token == "TOKEN.org1"


@pytest.mark.usefixtures("app")
class AuthAppMiddlewareTest:
    """Test the auth-app middleware."""

    @staticmethod
    def test_call_adds_header():
        """Test that the JWT token is added to the header."""
        client = mock.Mock(spec=auth.AuthAppClient)
        client.get_token.return_value = "TOKEN.org1"
        middleware = auth.AuthAppMiddleware(client, "org1")

        request = mock.Mock(headers={})
        middleware(request)
        assert client.method_calls == [mock.call.get_token("org1")]
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer TOKEN.org1"
