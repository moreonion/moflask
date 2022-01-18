"""Unit-test the REST-API client."""

from unittest import mock

import pytest
import requests
import requests.exceptions

from .. import rest


class ClientTest:
    """Unit-tests for the REST-API client."""

    @staticmethod
    @mock.patch("moflask.requests.sessions.Session.request")
    def test_base_url_restriction(mock_request):
        """Test that requests to a different base URL are denied.

        This is useful for APIs that provide URLs to other objects in their responses. This way
        we can ensure that no data is sent to an unintended location, even if we follow such
        untrusted URLs.
        """
        client = rest.Client("https://base.example.org")
        expected_message = "This client only sends requests to https://base.example.org"
        with pytest.raises(requests.exceptions.URLRequired, match=expected_message):
            client.get(url="https://other.example.org")
        assert not mock_request.called

    @staticmethod
    @mock.patch("requests.Session.send")
    def test_auth_middleware(mock_send):
        """Test that the a configured auth middleware is called and can manipulate the request."""

        def middleware(request: requests.PreparedRequest):
            request.headers["X-Middleware-Test"] = "success"
            return request

        client = rest.Client("https://base.example.org", auth=middleware)
        client.get("path")

        assert mock_send.called
        _, args, _ = mock_send.mock_calls[0]
        request = args[0]
        assert request.headers["X-Middleware-Test"] == "success"
