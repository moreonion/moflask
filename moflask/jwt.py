"""JWT session handling.

This module provides the common code-base needed for consuming auth-app JWTs.

The JWT’s claims provide a user identifier, an organization and the current roles of the user.
"""

import functools
import uuid
from typing import Iterable

import flask
import flask_jwt_extended
import werkzeug.exceptions

get_current_session = flask_jwt_extended.get_current_user


class Session:
    """Object that represents a user’s session for a specific organization."""

    @classmethod
    def from_raw_token(cls, token: dict):
        """Create a session from raw JWT token data."""
        claims = token["user_claims"]
        return cls(token["identity"], claims["org"], claims["roles"], claims["session_id"])

    @classmethod
    def create_anonymous_session(cls):
        """Create an anonymous session from the request headers."""
        org = flask.request.headers.get("x-ist-org", None)
        return cls(None, org, [])

    def __init__(
        self, identity: str, org: str, roles: Iterable[str] = None, custom_uuid: str = None
    ):
        """Create a new session instance."""
        self.identity = identity
        self.org = org
        self.roles = set(roles or [])
        self.session_id = custom_uuid or str(uuid.uuid4())

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
                "session_id": self.session_id,
                "org": self.org,
                "roles": list(self.roles),
            },
        }


class Manager(flask_jwt_extended.JWTManager):
    """A JWTManager subclass with a bit of custom behaviour."""

    @staticmethod
    def _push_context_callback(session: Session, context):  # pylint: disable=method-hidden
        """Implement a default push context callback doing nothing."""

    def push_context(self, session):
        """Push data to the request context."""
        self._push_context_callback(session, flask.g)

    def push_context_callback(self, callback):
        """Register a callback for pushing data to the request context.

        Most commonly this callback would load a user or organization object from the database to be
        used later in the request. The callback can throw werkzeug.exceptions to interrupt the
        request handling.
        """
        self._push_context_callback = callback


manager = Manager()


@manager.user_lookup_loader
def create_session(_jwt_header, jwt_data):
    """Create a session object from token data.

    The session is made available in either of:
    - flask_jwt_extended.current_user
    - flask_jwt_extended.get_current_user()
    - moflask.jwt.get_current_session()
    with the latter being considered the most idiomatic.
    """
    return Session.from_raw_token(jwt_data)


@manager.additional_claims_loader
def session_to_token(session: Session):
    """Generate JWT claims that represent the session."""
    return session.to_token_data()


# Deactivate the default callback. session_to_token takes care of everything.
manager.user_identity_loader(lambda session: None)


def check_roles(session: Session, admitted_roles: Iterable[str]):
    """Check whether the session has any of the admitted roles."""
    if not session.has_any_role_of(admitted_roles):
        raise werkzeug.exceptions.Forbidden("The user has none of the admitted roles.")


def required(admitted_roles: Iterable[str] = None, optional=False, **kwargs):
    """Require JWT authentication for a route.

    This decorator is a replacement for all of the flask_jwt_extended decorators.

    If you decorate an endpoint with this, it will ensure that the requester
    has a valid access token before allowing the endpoint to be called.

    The behaviour can be configured using the keyword parameters:
    - admitted_roles: Only allow session with any of these roles to access the route.
    """
    decorator_kwargs = kwargs

    def wrap(wrapped_fn):
        @functools.wraps(wrapped_fn)
        def wrapper(*args, **kwargs):
            if flask_jwt_extended.verify_jwt_in_request(optional=optional, **decorator_kwargs):
                session = get_current_session()
            elif optional:
                session = Session.create_anonymous_session()
                # pylint: disable=protected-access
                flask.g._jwt_extended_jwt_user = {"loaded_user": session}
            manager.push_context(session)
            if session and admitted_roles is not None:
                check_roles(session, admitted_roles)
            return wrapped_fn(*args, **kwargs)

        return wrapper

    return wrap
