"""Basic Flask App with a few enhancements."""

import os

from flask import Flask

from moflask.logging import init_logger


class BaseApp(Flask):
    """Flask App."""

    def __init__(self, *args, **kwargs):
        """Create a new app object."""
        config = kwargs.pop("config", {})
        super().__init__(*args, **kwargs)
        self.sentry = None
        self.load_config(config)
        self.init_defaults()

        if not self.sanity_check():
            raise RuntimeError("Sanity checks failed. Aborting!")

    def load_config(self, config=None, env_prefix="FLASK"):
        """Load app config.

        1. config file set in FLASK_SETTINGS environment variable (defaults to settings/base.py)
        2. config object or dict passed as keyword argument
        3. prefer "FLASK_" prefixed environment variables
        """
        settings_file = os.environ.get("FLASK_SETTINGS", "settings/base.py")
        self.config.from_pyfile(settings_file, silent=True)
        if isinstance(config, dict):
            self.config.update(config)
        elif config:
            self.config.from_object(config)
        self.config.from_prefixed_env(prefix=env_prefix)

    def init_defaults(self):
        """Initialize default app extensions."""
        init_logger(self)
        self.init_sentry()

    def init_sentry(self):
        """Initialize Sentry."""
        # pylint: disable=import-outside-toplevel
        if config := self.config.get("SENTRY_CONFIG"):
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration

            defaults = {"integrations": [FlaskIntegration()]}
            self.sentry = sentry_sdk.Client(**{**defaults, **config})

    @staticmethod
    def sanity_check():
        """Check sanity."""
        return True
