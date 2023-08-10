"""Unit-test the REST-API client."""

from unittest import mock

import pytest
import requests
import requests.exceptions

from .. import rest


class ClientTest:
    """Unit-tests for the REST-API client."""

    @mock.patch("moflask.requests.sessions.Session.request")
    def test_request_to_root_url(self, mock_request):
        """Test making a request to the root URL of the API."""
        mock_request.return_value = mock.Mock(json=mock.Mock(return_value={"status": "OK"}))
        client = rest.Client("https://base.example.org")
        assert client.get().json() == {"status": "OK"}
        assert mock_request.mock_calls == [
            mock.call("GET", "https://base.example.org/"),
            mock.call().raise_for_status(),
            mock.call().json(),
        ]

    @mock.patch("moflask.requests.sessions.Session.request")
    def test_request_using_path_parts(self, mock_request):
        """Test making a request using path parts."""
        mock_request.return_value = mock.Mock(json=mock.Mock(return_value={"status": "OK"}))
        client = rest.Client("https://base.example.org")
        assert client.get("part", "escaped?/=").json() == {"status": "OK"}
        assert mock_request.mock_calls == [
            mock.call("GET", "https://base.example.org/part/escaped%3F%2F%3D"),
            mock.call().raise_for_status(),
            mock.call().json(),
        ]

    @mock.patch("moflask.requests.sessions.Session.request")
    def test_request_using_path(self, mock_request):
        """Test making a request by passing the path."""
        mock_request.return_value = mock.Mock(json=mock.Mock(return_value={"status": "OK"}))
        client = rest.Client("https://base.example.org")
        assert client.get(path="test=?path").json() == {"status": "OK"}
        assert mock_request.mock_calls == [
            mock.call("GET", "https://base.example.org/test=?path"),
            mock.call().raise_for_status(),
            mock.call().json(),
        ]

    @mock.patch("moflask.requests.sessions.Session.request")
    def test_base_url_restriction(self, mock_request):
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

    @mock.patch("moflask.requests.sessions.Session.request")
    def test_returning_data_as_response(self, mock_request):
        """Test that Client.request(json_response=True) returns the json data."""
        test_data = {"data": "test"}
        mock_request.return_value = mock.Mock(json=mock.Mock(return_value=test_data))
        assert mock_request().json() == test_data
        client = rest.Client("https://example.org")
        data = client.get(json_response=True)
        assert data == {"data": "test"}

    @mock.patch("requests.Session.send")
    def test_auth_middleware(self, mock_send):
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
