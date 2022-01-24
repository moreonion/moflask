"""Useful wrappers for requests."""

# Also provide exceptions to make them available with a single import.
from requests import exceptions  # pylint: disable=unused-import

from . import auth, sessions

Session = sessions.Session
__all__ = ["auth", "exceptions", "Session"]
