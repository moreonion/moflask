import os
import logging as _logging

from flask import Flask
from werkzeug.utils import import_string

from moflask.logging import configure_logger


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

        logger = _logging.getLogger('flask.app')
        configure_logger(logger, self.config)

        if not self.sanity_check():
            raise RuntimeError('Sanity checks failed. Aborting!')

        self.init_sentry()

    def init_sentry(self):
        if self.config.get('SENTRY_DSN', False):
            from raven.contrib.flask import Sentry
            self.sentry = Sentry(self)

    def sanity_check(self):
        return True
