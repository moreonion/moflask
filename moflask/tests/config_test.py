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


def test_config_dict():
    """Test app gets passed a config dict."""
    config = {"A": "My setting"}
    app = BaseApp("moflask.tests.test_app1", config=config)
    assert app.config.get("A") == "My setting"


def test_config_object():
    """Test app gets passed a config object."""

    class Config:
        # pylint: disable=too-few-public-methods
        """My config object."""

        A = "My setting"

    app = BaseApp("moflask.tests.test_app1", config=Config)
    assert app.config.get("A") == "My setting"


@mock.patch.dict(os.environ, {"FLASK_SETTINGS": "config_overrides.py"})
def test_config_override():
    """Test local config overrides app config."""
    config = {"A": "My setting"}
    app = BaseApp("moflask.tests.test_app1", config=config)
    assert app.config.get("A") == "My override setting"


def test_testing_config():
    """Test testing config is used."""
    app = BaseApp("moflask.tests.test_app1", testing=True)
    assert app.testing is True
    assert app.config.get("A") == "My default test setting"


@mock.patch.dict(os.environ, {"FLASK_SETTINGS": "config_overrides.py"})
def test_testing_config_override():
    """Test local test config overrides app config."""
    config = {"A": "My setting", "TEST_A": "My test setting"}
    app = BaseApp("moflask.tests.test_app1", config=config, testing=True)
    assert app.config.get("A") == "My override test setting"
