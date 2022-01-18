"""Auth middlewares for the requests library."""

import urllib.parse

import flask
import requests

from . import rest


class AuthAppClient(rest.Client):
    """Client for the impact-stack auth app."""

    @classmethod
    def from_app_config(cls):
        """Create a new auth-app client instance from the app config."""
        return cls(flask.current_app.config.get("IMPACT_STACK_AUTH_APP_URL"))

    def get_token(self, organization):
        """Get a JWT token for a sub-organization."""
        api_key = flask.current_app.config.get("IMPACT_STACK_AUTH_APP_KEY")
        organization = urllib.parse.quote_plus(organization)
        response = self.post("token", organization, json=api_key)
        return response.json()["token"]


class AuthAppMiddleware:
    """Middleware for authenticating using JWT tokens.

    The middleware transparently requests an API-token from the auth-app on-demand.
    """

    def __init__(self, organization, client=None):
        """Create new auth-app requests auth middleware."""
        self.client = client or AuthAppClient.from_app_config()
        self.organization = organization

    def get_token(self):
        """Get a JWT token from the auth-app."""
        return self.client.get_token(self.organization)

    def __call__(self, request: requests.PreparedRequest):
        """Add the JWT token to the request."""
        request.headers["Authorization"] = "Bearer " + self.get_token()
        return request
