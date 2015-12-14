import os

from flask import Flask
from werkzeug.utils import import_string


class BaseApp(Flask):
    @staticmethod
    def config_obj_from_env():
        path = os.getenv('FLASK_CONFIG_OBJECT', 'settings.DevelopmentConfig')
        return import_string(path)()

    def __init__(self, *args, **kwargs):
        config = kwargs.pop('config', None)
        super().__init__(*args, **kwargs)
        # load app config
        # 1. from an import path specfied in the FLASK_CONFIG_OBJECT
        #    environmentfrom variable. Default: settings.DevelopmentConfig
        # 2. A config object passed as keyword argument: config=Object
        self.config.from_object(self.config_obj_from_env())
        self.config.from_object(config)

        for handler in self.config.get('LOG_HANDLERS', []):
            for logger in [self.logger]:
                logger.addHandler(handler)

        if not self.sanity_check():
            raise RuntimeError('Sanity checks failed. Aborting!')

    def sanity_check(self):
        return True
