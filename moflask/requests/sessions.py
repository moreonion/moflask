"""Wrapper for the requests Session object."""

import requests


class Session(requests.Session):
    """Wrap the `requests.Session` to add default timeouts."""

    timeout = None

    def request(self, *args, **kwargs):
        """Send a request with a a default timeout for the session."""
        kwargs.setdefault("timeout", self.timeout)
        return super().request(*args, **kwargs)
