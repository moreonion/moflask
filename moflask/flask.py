import os

from flask import Flask
from werkzeug.utils import import_string


class BaseApp(Flask):
    @staticmethod
    def config_obj_from_env(env=None):
        env = env or os.getenv('FLASK_ENV', 'Development').capitalize()
        path = os.getenv('FLASK_CONFIG_OBJECT', 'settings.' + env + 'Config')
        return import_string(path)()

    def __init__(self, *args, **kwargs):
        config = kwargs.pop('config', None)
        env = kwargs.pop('env', None)
        super().__init__(*args, **kwargs)
        # load app config
        # 1. from an import path specfied in the FLASK_CONFIG_OBJECT
        #    environmentfrom variable. Default: settings.DevelopmentConfig
        # 2. A config object passed as keyword argument: config=Object
        self.config.from_object(self.config_obj_from_env(env))
        self.config.from_object(config)

        for handler in self.config.get('LOG_HANDLERS', []):
            for logger in [self.logger]:
                logger.addHandler(handler)

        if not self.sanity_check():
            raise RuntimeError('Sanity checks failed. Aborting!')

        self.init_sentry()

    def init_sentry(self):
        """Initialize Sentry

        If there is an optin into the newer Sentry Python SDK
        this will be used. The old "raven" library otherwise.

        The boolean current_app.use_sentry_sdk signifies if the newer library
        is to be used
        """
        self.use_sentry_sdk = True if 'sentry_sdk' == self.config.get(
            'SENTRY_CLIENT', 'raven') else False
        if self.config.get('SENTRY_DSN', False):
            if self.use_sentry_sdk:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                sentry_sdk.init(
                    dsn=self.config.get('SENTRY_DSN'),
                    integrations=[FlaskIntegration()]
                )
                self.sentry = sentry_sdk
            else:
                from raven.contrib.flask import Sentry
                self.sentry = Sentry(self)

    def sanity_check(self):
        return True
