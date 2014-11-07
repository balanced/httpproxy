from __future__ import unicode_literals
import unittest
import collections
import socket
import threading

import werkzeug.serving
import werkzeug.wrappers

from webtest import TestApp
from httpproxy import HTTPProxyApplication


class HTTPOrigin(object):

    def __init__(self, trace_id_header):
        self.trace_id_header = trace_id_header
        self.requests = collections.defaultdict(list)
        self.responses = collections.defaultdict(list)

    def no_trace(self, request):
        return werkzeug.wrappers.Response(
            response='I dont have a trace',
            status=400,
            content_type='text/plain'
        )

    def no_response(self, request):
        return werkzeug.wrappers.Response(
            response='I dont have a response for {}'.format(
                request.headers[self.trace_id_header]
            ),
            status=503,
            content_type='text/plain'
        )

    def __call__(self, environ, start_response):
        request = werkzeug.wrappers.Request(environ)
        trace_id = request.headers.get(self.trace_id_header)
        if trace_id is None:
            response = self.no_trace(request)
        else:
            self.requests[trace_id].append(request)
            try:
                response = self.responses[trace_id].pop(0)
            except IndexError:
                response = self.no_response(request)
        return response(environ, start_response)


class TestHTTPProxyBase(unittest.TestCase):

    org_app = None
    trace_id_header = b'X-Balanced-Guru'

    @classmethod
    def setUpClass(cls):
        super(TestHTTPProxyBase, cls).setUpClass()

        # origin

        cls.org_app = HTTPOrigin(cls.trace_id_header)
        cls.org_port = cls._select_port()

        def serve_org():
            werkzeug.serving.run_simple(
                hostname='localhost',
                port=cls.org_port,
                application=cls.org_app,
                use_reloader=False,
                threaded=True,
            )

        org_thd = threading.Thread(target=serve_org)
        org_thd.daemon = True
        org_thd.start()

    @classmethod
    def _select_port(cls):
        # http://stackoverflow.com/a/1365284
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def setUp(self):
        super(TestHTTPProxyBase, self).setUp()
        self.proxy_app = HTTPProxyApplication('httpproxy.test')
        self.proxy_app.config['TRACE_ID_HTTP_HEADER'] = self.trace_id_header
        self.proxy_app.tracer.reset()
        self.trace_id = self.proxy_app.tracer.id
        self.testapp = TestApp(self.proxy_app.wsgi_app)

    def tearDown(self):
        super(TestHTTPProxyBase, self).tearDown()

    @property
    def _requests(self):
        return self.org_app.requests[self.trace_id]

    @property
    def _responses(self):
        return self.org_app.responses[self.trace_id]

    def _add_response(self, status_code, content_type, data):
        return self._responses.append(werkzeug.wrappers.Response(
            response=data,
            status=status_code,
            content_type=content_type,
        ))
