from __future__ import unicode_literals

import urllib3
import flask
import coid
import ohmr
import werkzeug.exceptions
import werkzeug.http
import werkzeug.datastructures
import werkzeug.utils

from .proxy_handler import proxy_handler
from .request import ProxyRequest

__version__ = '0.0.0'

exc = werkzeug.exceptions


class ProxyAuthentication(werkzeug.exceptions.HTTPException):

    code = 407

    description = (
        'The server could not verify that you are authorized to access '
        'the URL requested.  You either supplied the wrong credentials (e.g. '
        'a bad password), or your browser doesn\'t understand how to supply '
        'the credentials required.'
    )


class HTTPProxyApplication(flask.Flask):

    request_class = ProxyRequest

    def __init__(self, *args, **kwargs):
        kwargs['static_folder'] = None
        super(HTTPProxyApplication, self).__init__(*args, **kwargs)
        self.register_blueprint(proxy_handler)

        self.tracer = ohmr.Tracer(coid.Id(prefix='OHM-'))
        self.before_request(self.set_trace_id)
        self._http_cli = None

    @property
    def http_cli(self):
        # lazy evaulation so that if config is modified after the application
        # is created
        if not self._http_cli:
            client_config = self.config.get('HTTP_CLIENT', {})
            self._http_cli = urllib3.PoolManager(
                num_pools=client_config.get('num_pools', 1),
                **client_config.get('pool', {})
            )
        return self._http_cli

    def set_trace_id(self):
        self.tracer.reset()
