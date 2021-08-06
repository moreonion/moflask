from copy import copy
from unittest import TestCase

from ..wsgi import ProxyFix


class ProxyFixTest(TestCase):
    def app_stub(self, trusted):
        class Object(object):
            wsgi_app = None

        app = Object()
        app.config = {}
        app.config["PROXYFIX_TRUSTED"] = trusted
        return app

    def _copy_env(self, env):
        e = copy(env)
        e["werkzeug.proxy_fix.orig_http_host"] = env["HTTP_HOST"]
        e["werkzeug.proxy_fix.orig_remote_addr"] = env["REMOTE_ADDR"]
        e["werkzeug.proxy_fix.orig_wsgi_url_scheme"] = env["wsgi.url_scheme"]
        return e

    def test_one_forwarded_for_layer(self):
        fix = ProxyFix(self.app_stub(["127.0.0.1"]))
        env = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_HOST": "example.com",
            "wsgi.url_scheme": "http",
            "HTTP_X_FORWARDED_FOR": "8.8.8.8",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        e = self._copy_env(env)
        e["REMOTE_ADDR"] = "8.8.8.8"
        e["wsgi.url_scheme"] = "https"
        fix.update_environ(env)
        self.assertEqual(e, env)

    def test_multiple_trusted_multiple_untrusted(self):
        fix = ProxyFix(self.app_stub(["127.0.0.1", "10.0.0.1"]))
        rm = fix.get_remote_addr(
            ["8.8.8.8", "10.0.0.1", "127.0.0.1"],
            "1.1.1.1",
        )
        self.assertEqual("8.8.8.8", rm)

    def test_all_trusted(self):
        fix = ProxyFix(self.app_stub(["127.0.0.1"]))
        self.assertEqual("127.0.0.1", fix.get_remote_addr([], "127.0.0.1"))

    def test_no_trusted_layer(self):
        fix = ProxyFix(self.app_stub(["127.0.0.1"]))
        env = {
            "REMOTE_ADDR": "8.8.8.8",
            "HTTP_HOST": "example.com",
            "wsgi.url_scheme": "http",
            "HTTP_X_FORWARDED_FOR": "8.8.8.8",
            "HTTP_X_FORWARDED_HOST": "untrusted.com",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        e = self._copy_env(env)
        fix.update_environ(env)
        self.assertEqual(e, env)

    def test_new_ip_equals_old_ip(self):
        fix = ProxyFix(self.app_stub(["127.0.0.1"]))
        env = {
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_HOST": "example.com",
            "wsgi.url_scheme": "http",
            "HTTP_X_FORWARDED_FOR": "127.0.0.1",
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        e = self._copy_env(env)
        e["wsgi.url_scheme"] = "https"
        fix.update_environ(env)
        self.assertEqual(e, env)

    def test_no_proxy_works_transparently(self):
        fix = ProxyFix(self.app_stub(["127.0.0.1"]))
        env = {"REMOTE_ADDR": "127.0.0.1", "HTTP_HOST": "example.com", "wsgi.url_scheme": "http"}
        e = self._copy_env(env)
        fix.update_environ(env)
        self.assertEqual(e, env)
