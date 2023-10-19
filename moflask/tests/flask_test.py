"""Tests for the app initialization."""

import pytest

from moflask import flask


def test_app_with_sentry():
    """Test initializing the app with a sentry-config."""
    app = flask.BaseApp("moflask", config={"SENTRY_CONFIG": {"dsn": "https://user:pass@foo/1"}})
    assert app.sentry


def test_config_getter():
    """Test the config_getter."""
    app = flask.BaseApp("moflask", config={"foo": 42})
    assert app.config_getter("foo") == 42
    assert app.config_getter("foo", "default") == 42
    assert app.config_getter("bar", "default") == "default"
    with pytest.raises(KeyError):
        assert app.config_getter("bar")
