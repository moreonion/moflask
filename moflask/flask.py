"""Basic Flask App with a few enhancements."""

from flask import Flask

from moflask.logging import init_logger


class BaseApp(Flask):
    """Flask App."""

    def __init__(self, *args, **kwargs):
        """Create a new app object."""
        config = kwargs.pop("config", {})
        testing = kwargs.pop("testing", False)
        super().__init__(*args, **kwargs)
        self.sentry = None
        self.load_config(config, testing)
        self.init_defaults()

        if not self.sanity_check():
            raise RuntimeError("Sanity checks failed. Aborting!")

    def load_config_defaults(self):
        """Load app default config from "config_defaults.py" if available."""
        self.config.from_pyfile("settings/base.py", silent=True)

    def load_config(self, config=None, testing=False):
        """Load app config.

        1. default config provided by the app
        2. config object or dict passed as keyword argument
        3. config file set in FLASK_SETTINGS environment variable
        4. in testing, prefer "TEST_" prefixed settings if available
        """
        self.config["TESTING"] = testing
        self.load_config_defaults()
        if isinstance(config, dict):
            self.config.update(config)
        elif config:
            self.config.from_object(config)
        self.config.from_envvar("FLASK_SETTINGS", silent=True)
        if self.testing:
            self.config.update(self.config.get_namespace("TEST_", lowercase=False))

    def init_defaults(self):
        """Initialize default app extensions."""
        init_logger(self)
        self.init_sentry()

    def init_sentry(self):
        """Initialize Sentry."""
        if self.config.get("SENTRY_DSN", False):
            # pylint: disable=import-outside-toplevel,import-error
            from raven.contrib.flask import Sentry

            self.sentry = Sentry(self)

    @staticmethod
    def sanity_check():
        """Check sanity."""
        return True
