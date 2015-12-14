from copy import copy
from unittest import TestCase

from ..wsgi import ProxyFix


class ProxyFixTest(TestCase):
    def app_stub(self, trusted):
        class Object(object):
            wsgi_app = None
        app = Object()
        app.config = {}
        app.config['PROXYFIX_TRUSTED'] = trusted
        return app

    def test_one_forwarded_for_layer(self):
        fix = ProxyFix(self.app_stub(['127.0.0.1']))
        env = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_HOST': 'example.com',
            'wsgi.url_scheme': 'https',
            'HTTP_X_FORWARDED_FOR': '8.8.8.8',
        }
        e = copy(env)
        e['REMOTE_ADDR'] = '8.8.8.8'
        e['werkzeug.proxy_fix.orig_http_host'] = env['HTTP_HOST']
        e['werkzeug.proxy_fix.orig_remote_addr'] = env['REMOTE_ADDR']
        e['werkzeug.proxy_fix.orig_wsgi_url_scheme'] = env['wsgi.url_scheme']
        fix.update_environ(env)
        self.assertEqual(e, env)

    def test_multiple_trusted_multiple_untrusted(self):
        fix = ProxyFix(self.app_stub(['127.0.0.1', '10.0.0.1']))
        rm = fix.get_remote_addr(
            ['8.8.8.8', '10.0.0.1', '127.0.0.1'],
            '1.1.1.1',
        )
        self.assertEqual('8.8.8.8', rm)

    def test_all_trusted(self):
        fix = ProxyFix(self.app_stub(['127.0.0.1']))
        self.assertEqual('127.0.0.1', fix.get_remote_addr([], '127.0.0.1'))

    def test_no_trusted_layer(self):
        fix = ProxyFix(self.app_stub(['127.0.0.1']))
        env = {
            'REMOTE_ADDR': '8.8.8.8',
            'HTTP_HOST': 'example.com',
            'wsgi.url_scheme': 'https',
            'HTTP_X_FORWARDED_FOR': '8.8.8.8',
            'HTTP_X_FORWARDED_HOST': 'untrusted.com',
            'HTTP_X_FORWARDED_PROTO': 'http',
        }
        e = copy(env)
        e['REMOTE_ADDR'] = '8.8.8.8'
        e['werkzeug.proxy_fix.orig_http_host'] = env['HTTP_HOST']
        e['werkzeug.proxy_fix.orig_remote_addr'] = env['REMOTE_ADDR']
        e['werkzeug.proxy_fix.orig_wsgi_url_scheme'] = env['wsgi.url_scheme']
        fix.update_environ(env)
        self.assertEqual(e, env)
