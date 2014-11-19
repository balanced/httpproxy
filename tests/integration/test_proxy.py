from __future__ import unicode_literals

import requests

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
                headers['Content-Length'] = str(len(data))
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
        self.assertEqual(req.data, data * 2)
        self.assertEqual(int(req.headers['Content-Length']), len(data) * 2)

    def test_egress_handler(self):

        class EgressModifyProxy(DummyProxy):

            def egress_handler(self, uri, method, status, headers, data):
                status = 201
                data = data.replace('foobar', 'eggs spam')
                headers['Content-Length'] = str(len(data))
                return dict(
                    status=status,
                    headers=headers,
                    data=data,
                )
        proxy = EgressModifyProxy()
        proxy.scheme = 'http'
        proxy.host = 'localhost:{}'.format(self.org_port)
        self.proxy_app.config['HTTP_PROXY_FACTORY'] = lambda request: proxy
        data = 'I love foobar'
        self._add_response(
            status_code=200,
            content_type='text/html',
            data=data,
        )

        resp = self.testapp.post(
            '/',
            headers={
                self.trace_id_header: str(self.trace_id),
            },
            status=201,
        )
        expected_body = 'I love eggs spam'
        self.assertEqual(resp.body, expected_body)
        self.assertEqual(
            int(resp.headers['Content-Length']),
            len(expected_body),
        )

    def test_post(self):
        passed_data = []

        class PostProxy(DummyProxy):

            def ingress_handler(self, uri, method, headers, data, charset):
                passed_data.append(data)
                return dict(
                    uri=uri,
                    method=method,
                    headers=headers,
                    data=data,
                    charset=charset,
                )

        proxy = PostProxy()
        proxy.scheme = 'http'
        proxy.host = 'localhost:{}'.format(self.org_port)
        self.proxy_app.config['HTTP_PROXY_FACTORY'] = lambda request: proxy
        self._add_response(
            status_code=200,
            content_type='text/html',
            data='hi',
        )

        self.testapp.post('/', dict(foo='bar'), headers={
            self.trace_id_header: str(self.trace_id),
        })
        self.assertEqual(passed_data, ['foo=bar'])

    def test_real_server_uri(self):
        uris = []

        class PostProxy(DummyProxy):

            def ingress_handler(self, uri, method, headers, data, charset):
                uris.append(uri)
                return dict(
                    uri=uri,
                    method=method,
                    headers=headers,
                    data=data,
                    charset=charset,
                )

        proxy = PostProxy()
        proxy.scheme = 'http'
        proxy.host = 'localhost:{}'.format(self.org_port)
        self.proxy_app.config['HTTP_PROXY_FACTORY'] = lambda request: proxy

        proxy_port, _ = self.run_app(self.proxy_app.wsgi_app)
        requests.get(
            'http://localhost:{}/Foo/Bar'.format(self.org_port),
            proxies=dict(http='http://localhost:{}'.format(proxy_port)),
        )

        self.assertEqual(uris, ['/Foo/Bar'])
