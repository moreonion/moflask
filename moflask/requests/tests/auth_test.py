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
    app.config["IMPACT_STACK_API_URL"] = "https://impact-stack.net/api"
    app.config["IMPACT_STACK_API_KEY"] = "api-key"
    with app.app_context():
        yield app


@pytest.mark.usefixtures("app")
class AuthAppClientTest:
    """Test the auth-app client."""

    def test_get_token(self, requests_mock):
        """Test getting a token."""
        client = auth.AuthAppClient.from_app()
        requests_mock.post(rm.ANY, json={"token": "TOKEN.org1"})
        token = client.get_token()
        assert token == "TOKEN.org1"
        assert len(requests_mock.request_history) == 1
        assert requests_mock.request_history[0].url == "https://impact-stack.net/api/auth/v1/token"
        assert requests_mock.request_history[0].json() == "api-key"


@pytest.mark.usefixtures("app")
class AuthAppMiddlewareTest:
    """Test the auth-app middleware."""

    def test_default_client_from_app_config(self):
        """Test that instantiating without a client uses client configured from the app config."""
        middleware = auth.AuthAppMiddleware()
        assert isinstance(middleware.client, auth.AuthAppClient)

    def test_call_adds_header(self):
        """Test that the JWT token is added to the header."""
        client = mock.Mock(spec=auth.AuthAppClient)
        client.get_token.return_value = "TOKEN.org1"
        middleware = auth.AuthAppMiddleware(client)

        request = mock.Mock(headers={})
        middleware(request)
        assert client.method_calls == [mock.call.get_token()]
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer TOKEN.org1"
