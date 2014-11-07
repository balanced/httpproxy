from __future__ import unicode_literals

from . import TestHTTPProxyBase


class DummyProxy(object):

    def ingress_handler(self, uri, method, headers, data, charset):
        return dict(
            uri=uri,
            method=method,
            headers=headers,
            data=data,
            charset=charset,
        )

    def egress_handler(self, uri, method, status, headers, data):
        return dict(
            uri=uri,
            method=method,
            status=status,
            headers=headers,
            data=data,
        )


class TestHTTPProxy(TestHTTPProxyBase):

    def test_foo(self):
        proxy = DummyProxy()
        proxy.scheme = 'http'
        proxy.host = 'localhost:{}'.format(self.org_port)

        self.proxy_app.config['HTTP_PROXY_FACTORY'] = lambda request: proxy

        self._add_response(
            status_code=200,
            content_type='text/html',
            data='hi',
        )
        resp = self.testapp.get('/', headers={
            self.trace_id_header: str(self.trace_id),
        })
        self.assertEqual(resp.body, 'hi')
