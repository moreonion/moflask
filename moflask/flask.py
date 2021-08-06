"""Basic Flask App with a few enhancements."""

import os

from flask import Flask
from werkzeug.utils import import_string

from moflask.logging import init_logger


class BaseApp(Flask):
    """Flask App."""

    @staticmethod
    def config_obj_from_env(env=None):
        """Find a config object that matches the current environment."""
        env = env or os.getenv("FLASK_ENV", "production").capitalize()
        path = os.getenv("FLASK_CONFIG_OBJECT", "settings." + env + "Config")
        return import_string(path)()

    def __init__(self, *args, **kwargs):
        """Create a new app object."""
        config = kwargs.pop("config", None)
        env = kwargs.pop("env", None)
        super().__init__(*args, **kwargs)
        # load app config
        # 1. from an import path specfied in the FLASK_CONFIG_OBJECT
        #    environmentfrom variable. Default: settings.DevelopmentConfig
        # 2. A config object passed as keyword argument: config=Object
        self.config.from_object(self.config_obj_from_env(env))
        self.config.from_object(config)
        init_logger(self)

        if not self.sanity_check():
            raise RuntimeError("Sanity checks failed. Aborting!")

        self.init_sentry()

    def init_sentry(self):
        """Initialize Sentry."""
        if self.config.get("SENTRY_DSN", False):
            from raven.contrib.flask import Sentry

            self.sentry = Sentry(self)

    @staticmethod
    def sanity_check():
        """Check sanity."""
        return True
