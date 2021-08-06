# moflask

Utility library to build flask apps faster and more consistent. It includes:

* `moflask.flask.BaseApp`: A base class that handles config objects and config
  environments.
* `moflask.wsgi.ProxyFix`: A middleware that safely handles `X-Forwarded-For`
  and related headers.
* `moflask.mail`: Hacky wrappers around Flask-Mail to support custom a envelope_from
  and local hostname.
* `moflask.logging`: Logging helpers with preconfigured handlers and filters.
Enabled on the BaseApp.
