"""Test the WSGI middlewares."""

from copy import copy
from unittest import mock

from moflask import wsgi


def create_app_stub(trusted):
    """Create a stub Flask app."""
    app = mock.Mock()
    app.wsgi_app = None
    app.config = {}
    app.config["PROXYFIX_TRUSTED"] = trusted
    return app


def copy_env(env):
    """Create a copy of a WSGI environment with the original values backed up."""
    new_env = copy(env)
    new_env["werkzeug.proxy_fix.orig_http_host"] = env["HTTP_HOST"]
    new_env["werkzeug.proxy_fix.orig_remote_addr"] = env["REMOTE_ADDR"]
    new_env["werkzeug.proxy_fix.orig_wsgi_url_scheme"] = env["wsgi.url_scheme"]
    return new_env


class ProxyFixTest:
    """Test the proxy fix middleware."""

    def test_one_forwarded_for_layer(self):
        """Test a single trusted reverse proxy."""
        fix = wsgi.ProxyFix(create_app_stub(["127.0.0.1"]))
        env = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_HOST": "example.com",
            "wsgi.url_scheme": "http",
            "HTTP_X_FORWARDED_FOR": "8.8.8.8",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        expected_env = copy_env(env)
        expected_env["REMOTE_ADDR"] = "8.8.8.8"
        expected_env["wsgi.url_scheme"] = "https"
        fix.update_environ(env)
        assert env == expected_env

    def test_multiple_trusted_multiple_untrusted(self):
        """Test getting the remote IP for multiple proxy layers."""
        fix = wsgi.ProxyFix(create_app_stub(["127.0.0.1", "10.0.0.1"]))
        remote_address = fix.get_remote_addr(
            ["8.8.8.8", "10.0.0.1", "127.0.0.1"],
            "1.1.1.1",
        )
        assert remote_address == "8.8.8.8"

    def test_all_trusted(self):
        """Test getting the remote IP with only trusted IPs."""
        fix = wsgi.ProxyFix(create_app_stub(["127.0.0.1"]))
        assert fix.get_remote_addr([], "127.0.0.1") == "127.0.0.1"

    def test_no_trusted_layer(self):
        """Test request from an untrusted remote."""
        fix = wsgi.ProxyFix(create_app_stub(["127.0.0.1"]))
        env = {
            "REMOTE_ADDR": "8.8.8.8",
            "HTTP_HOST": "example.com",
            "wsgi.url_scheme": "http",
            "HTTP_X_FORWARDED_FOR": "8.8.8.8",
            "HTTP_X_FORWARDED_HOST": "untrusted.com",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        expected_env = copy_env(env)
        fix.update_environ(env)
        assert env == expected_env

    def test_new_ip_equals_old_ip(self):
        """Test a local request with HTTPS."""
        fix = wsgi.ProxyFix(create_app_stub(["127.0.0.1"]))
        env = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_HOST": "example.com",
            "wsgi.url_scheme": "http",
            "HTTP_X_FORWARDED_FOR": "127.0.0.1",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        expected_env = copy_env(env)
        expected_env["wsgi.url_scheme"] = "https"
        fix.update_environ(env)
        assert env == expected_env

    def test_no_proxy_works_transparently(self):
        """Test updating the environment without any reverse proxy."""
        fix = wsgi.ProxyFix(create_app_stub(["127.0.0.1"]))
        env = {"REMOTE_ADDR": "127.0.0.1", "HTTP_HOST": "example.com", "wsgi.url_scheme": "http"}
        expected_env = copy_env(env)
        fix.update_environ(env)
        assert env == expected_env
