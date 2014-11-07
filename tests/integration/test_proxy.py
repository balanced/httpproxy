from __future__ import unicode_literals

from . import TestHTTPProxyBase


class DummyProxy(object):
    pass


class TestHTTPProxy(TestHTTPProxyBase):

    def test_simple_request(self):
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

        self.assertEqual(len(self._requests), 1)
        req = self._requests[0]
        self.assertEqual(req.headers[self.trace_id_header], self.trace_id)
