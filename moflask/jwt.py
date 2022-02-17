"""JWT session handling.

This module provides the common code-base needed for consuming auth-app JWTs.

The JWT’s claims provide a user identifier, an organization and the current roles of the user.
"""

import functools
from typing import Iterable

import flask
import flask_jwt_extended
from flask_jwt_extended.exceptions import NoAuthorizationError

ctx_stack = flask._request_ctx_stack  # pylint: disable=protected-access
get_current_session = flask_jwt_extended.get_current_user


class Session:
    """Object that represents a user’s session for a specific organization."""

    @classmethod
    def from_raw_token(cls, token: dict):
        """Create a session from raw JWT token data."""
        claims = token["user_claims"]
        return cls(token["identity"], claims["org"], claims["roles"])

    def __init__(self, identity: str, org: str, roles: Iterable[str] = None):
        """Create a new session instance."""
        self.identity = identity
        self.org = org
        self.roles = set(roles or [])

    def push_to_context(self):
        """Set request context variables for the authenticated user.

        Some apps don’t need anything besides the raw session so this is just a stub per default.
        """

    def has_any_role_of(self, roles: Iterable[str]):
        """Check if the session has any of the given roles."""
        return any(role in self.roles for role in roles)

    def to_token_data(self):
        """Return the session object turned into the token data structure.

        This is the inverse of from_raw_token().
        """
        return {
            "identity": self.identity,
            "user_claims": {
                "org": self.org,
                "roles": list(self.roles),
            },
        }


class Manager(flask_jwt_extended.JWTManager):
    """A JWTManager subclass with a bit of custom behaviour."""

    session_cls = Session

    def init_app(self, app):
        """Initialize flask app configuration."""
        super().init_app(app)
        # Allow JWT support to be switched off (eg for testing)
        app.config.setdefault("JWT_ENABLED", True)
        # If JWT_ENABLED is off then this can be used to inject a session into the request context.
        app.config.setdefault("JWT_INJECT_SESSION", None)


manager = Manager()


@manager.user_lookup_loader
def create_session(_jwt_header, jwt_data):
    """Create a session object from token data.

    The session is made available in flask_jwt_extended.current_user and via
    flack_jwt_extended.get_current_user().
    """
    return manager.session_cls.from_raw_token(jwt_data)


@manager.additional_claims_loader
def session_to_token(session: Session):
    """Generate session into to JWT claims.

    Note: This is only needed for testing. In production this app is not supposed to create any
    tokens. The auth-app is responsible for that.
    """
    return session.to_token_data()


# Deactivate the default callback. session_to_token takes care of everything.
manager.user_identity_loader(lambda session: None)


def check_roles(session: Session, admitted_roles: Iterable[str]):
    """Check whether the session has any of the admitted roles."""
    if not session.has_any_role_of(admitted_roles):
        raise NoAuthorizationError("The session doesn’t have any of the required roles.")


def get_session():
    """Get a session for the current request."""
    flask_jwt_extended.verify_jwt_in_request()
    session = get_current_session()
    session.push_to_context()
    return session


def required(admitted_roles: Iterable[str] = None):
    """Require JWT authentication for a route.

    This decorator is a replacement for all of the flask_jwt_extended decorators.

    If you decorate an endpoint with this, it will ensure that the requester
    has a valid access token before allowing the endpoint to be called.

    The behaviour can be configured using the keyword parameters:
    - admitted_roles: Only allow session with any of these roles to access the route.
    """

    def wrap(wrapped_fn):
        @functools.wraps(wrapped_fn)
        def wrapper(*args, **kwargs):
            session = get_session()
            if session and admitted_roles is not None:
                check_roles(session, admitted_roles)
            return wrapped_fn(*args, **kwargs)

        return wrapper

    return wrap
