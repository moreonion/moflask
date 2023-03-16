# moflask

Utility library to build flask apps faster and more consistent. It includes:

* `moflask.flask.BaseApp`: A base class that handles config loading and default
  extensions.
* `moflask.wsgi.ProxyFix`: A middleware that safely handles `X-Forwarded-For`
  and related headers.
* `moflask.logging`: Logging helpers with preconfigured handlers and filters.
Enabled on the BaseApp.
