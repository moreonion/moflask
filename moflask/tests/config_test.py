"""Tests for config loading."""

import os
from unittest import mock

from moflask.flask import BaseApp


def test_no_config():
    """Test app without any config."""
    app = BaseApp("moflask")
    assert app.testing is False


def test_default_config():
    """Test app default config."""
    app = BaseApp("moflask.tests.test_app1")
    assert app.config.get("A") == "My default setting"
    assert app.config.get("B") == "base only"


def test_config_dict():
    """Test app gets passed a config dict."""
    config = {"A": "My setting"}
    app = BaseApp("moflask.tests.test_app1", config=config)
    assert app.config.get("A") == "My setting"
    assert app.config.get("B") == "base only"


def test_config_object():
    """Test app gets passed a config object."""

    class Config:
        # pylint: disable=too-few-public-methods
        """My config object."""

        A = "My setting"

    app = BaseApp("moflask.tests.test_app1", config=Config)
    assert app.config.get("A") == "My setting"
    assert app.config.get("B") == "base only"


@mock.patch.dict(os.environ, {"FLASK_SETTINGS": "settings/independent.py"})
def test_independent_config():
    """Test loading a config that doesn’t inherit from the base."""
    app = BaseApp("moflask.tests.test_app1")
    assert app.config.get("A") == "Independent settings"
    assert "B" not in app.config


@mock.patch.dict(os.environ, {"FLASK_SETTINGS": "settings/overrides.py"})
def test_config_override():
    """Test local config overrides app config."""
    app = BaseApp("moflask.tests.test_app1")
    assert app.config.get("A") == "My override setting"

    config = {"A": "My setting"}
    app = BaseApp("moflask.tests.test_app1", config=config)
    assert app.config.get("A") == "My setting"


@mock.patch.dict(os.environ, {"FLASK_A": "env config"})
@mock.patch.dict(os.environ, {"FLASK_SETTINGS": "settings/overrides.py"})
def test_envvar_override_config():
    """Test testing config is used."""
    app = BaseApp("moflask.tests.test_app1")
    assert app.config.get("A") == "env config"


@mock.patch.dict(os.environ, {"FLASK_A": "FLASK config"})
@mock.patch.dict(os.environ, {"FOO_A": "FOO config"})
@mock.patch.dict(os.environ, {"FLASK_SETTINGS": "settings/overrides.py"})
def test_envvar_override_with_custom_prefix():
    """Test testing config is used."""

    class _App(BaseApp):
        def load_config(self, config=None, env_prefix="FOO"):
            super().load_config(config, env_prefix)

    app = _App("moflask.tests.test_app1")
    assert app.config.get("A") == "FOO config"
