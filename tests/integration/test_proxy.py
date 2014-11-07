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

    def test_ingress_handler(self):

        class IngressModifyProxy(DummyProxy):

            def ingress_handler(self, uri, method, headers, data, charset):
                uri += 'appended'
                data *= 2
                headers['Content-Length'] = len(data)
                return dict(
                    uri=uri,
                    method=method,
                    headers=headers,
                    data=data,
                    charset=charset,
                )
        proxy = IngressModifyProxy()
        proxy.scheme = 'http'
        proxy.host = 'localhost:{}'.format(self.org_port)
        self.proxy_app.config['HTTP_PROXY_FACTORY'] = lambda request: proxy
        self._add_response(
            status_code=200,
            content_type='text/html',
            data='hi',
        )

        data = 'foobar'
        self.testapp.post('/', data, headers={
            self.trace_id_header: str(self.trace_id),
        })
        self.assertEqual(len(self._requests), 1)
        req = self._requests[0]
        self.assertEqual(req.url, 'http://localhost:80/appended')
        self.assertEqual(req.get_data(), data * 2)
        self.assertEqual(int(req.headers['Content-Length']), len(data) * 2)
