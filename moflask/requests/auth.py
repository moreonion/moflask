"""Auth middlewares for the requests library."""

import flask
import requests

from . import rest


class AuthAppClient(rest.Client):
    """A REST client for retrieving JWTs from the auth-app."""

    AUTH_API_VERSION = "v1"

    @classmethod
    def from_app(cls, app=None):
        """Create a new instance by reading the config from the Flask app config."""
        app = app or flask.current_app
        return cls(
            app.config["IMPACT_STACK_API_URL"] + "/auth/" + cls.AUTH_API_VERSION,
            app.config["IMPACT_STACK_API_KEY"],
        )

    def __init__(self, base_url, api_key):
        """Create a new client instance."""
        super().__init__(base_url)
        self.api_key = api_key

    def get_token(self):
        """Use the API token to get a new JWT."""
        response = self.post("token", json=self.api_key)
        return response.json()["token"]


class AuthAppMiddleware:
    """Middleware for authenticating using JWT tokens.

    The middleware transparently requests an API-token from the auth-app on-demand.
    """

    # pylint: disable=too-few-public-methods
    # For now the middleware is very simple, but in the future it should also take care of caching
    # the JWT and renew if needed.

    def __init__(self, client=None):
        """Create new auth-app requests auth middleware."""
        self.client = client or AuthAppClient.from_app()

    def __call__(self, request: requests.PreparedRequest):
        """Add the JWT token to the request."""
        request.headers["Authorization"] = "Bearer " + self.client.get_token()
        return request
