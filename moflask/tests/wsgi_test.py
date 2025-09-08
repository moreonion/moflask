"""Test the WSGI middlewares."""

from copy import copy
from unittest import mock

from moflask import wsgi


def create_app_stub(trusted):
    """Create a stub Flask app."""
    app = mock.Mock()
    app.wsgi_app = mock.Mock()
    app.original_wsgi_app = app.wsgi_app
    config = {"PROXYFIX_TRUSTED": trusted}
    app.config_getter = mock.Mock(side_effect=config.get)
    return app


def copy_env(env):
    """Create a copy of a WSGI environment with the original values backed up."""
    new_env = copy(env)
    new_env["werkzeug.proxy_fix.orig_http_host"] = env["HTTP_HOST"]
    new_env["werkzeug.proxy_fix.orig_remote_addr"] = env["REMOTE_ADDR"]
    new_env["werkzeug.proxy_fix.orig_wsgi_url_scheme"] = env["wsgi.url_scheme"]
    return new_env


def test_proxyfix_one_forwarded_for_layer():
    """Test a single trusted reverse proxy."""
    app = create_app_stub(["127.0.0.1"])
    wsgi.ProxyFix.wrap_app(app)
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
    app.wsgi_app(env, mock.Mock())
    assert app.original_wsgi_app.mock_calls == [mock.call(expected_env, mock.ANY)]
