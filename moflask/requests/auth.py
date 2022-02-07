"""Auth middlewares for the requests library."""

import urllib.parse

import flask
import requests

from . import rest


class AuthAppClient(rest.Client):
    """A REST client for retrieving JWTs from the auth-app."""

    @classmethod
    def from_app(cls, app=None):
        """Create a new instance by reading the config from the Flask app config."""
        app = app or flask.current_app
        return cls(
            app.config["IMPACT_STACK_AUTH_APP_URL"],
            app.config["IMPACT_STACK_AUTH_APP_KEY"],
        )

    def __init__(self, base_url, api_key):
        """Create a new client instance."""
        super().__init__(base_url)
        self.api_key = api_key

    def get_token(self, organization):
        """Get a JWT token for a sub-organization."""
        organization = urllib.parse.quote_plus(organization)
        response = self.post("token", organization, json=self.api_key)
        return response.json()["token"]


class AuthAppMiddleware:
    """Middleware for authenticating using JWT tokens.

    The middleware transparently requests an API-token from the auth-app on-demand.
    """

    def __init__(self, organization, client=None):
        """Create new auth-app requests auth middleware."""
        self.client = client or AuthAppClient.from_app()
        self.organization = organization

    def get_token(self):
        """Get a JWT token from the auth-app."""
        return self.client.get_token(self.organization)

    def __call__(self, request: requests.PreparedRequest):
        """Add the JWT token to the request."""
        request.headers["Authorization"] = "Bearer " + self.get_token()
        return request
