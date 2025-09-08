"""Implement WSGI middlewares for Flask apps."""

from impact_stack import proxyfix

from moflask import flask


class ProxyFix(proxyfix.ProxyFix):
    """This is a slightly modified version of werkzeug's ProxyFix.

    This sub-class adds a convenience layer for flask apps on top of the generic implementation.
    """

    @classmethod
    def wrap_app(cls, app: flask.BaseApp):
        """Wrap a Flask app and read variables from its config."""
        app.wsgi_app = cls.from_config(app.config_getter).wrap(app.wsgi_app)
