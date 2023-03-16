# moflask

Utility library to build flask apps faster and more consistent. It includes:

* `moflask.flask.BaseApp`: A base class that handles:
    - Config loading using Python files indicated by the `FLASK_SETTINGS` environment variable.
    - Logger intialization.
    - Sentry initialization with config read from `SENTRY_CONFIG`.
* `moflask.wsgi.ProxyFix`: A middleware that safely handles `X-Forwarded-For`
  and related headers.
* `moflask.logging`: Logging helpers with preconfigured handlers and filters.
Enabled on the BaseApp.
