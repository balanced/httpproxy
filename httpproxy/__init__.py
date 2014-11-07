from __future__ import unicode_literals

import urllib3
import flask
import werkzeug.exceptions
import werkzeug.http
import werkzeug.datastructures
import werkzeug.utils

from .proxy_handler import proxy_handler

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


class DummyProxy(object):
    # XXX: just a dummy proxy for dev

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


class RequestProxyMixin(object):

    @werkzeug.utils.cached_property
    def proxy_authorization(self):
        header = self.environ.get('HTTP_PROXY_AUTHORIZATION')
        value = werkzeug.http.parse_authorization_header(header)
        if isinstance(value, tuple):
            username, password = value
            value = werkzeug.datastructures.Authorization('Basic', {
                'username': username,
                'password': password,
            })
        return value

    @werkzeug.utils.cached_property
    def has_proxy(self):
        try:
            self.proxy
        except exc.HTTPException:
            return False
        return True

    @werkzeug.utils.cached_property
    def proxy(self):
        # XXX
        proxy = DummyProxy()
        return proxy


class ProxyRequest(
    # RequestTraceMixin,
    # RequestNetworkMixin,
    # RequestMIMEMixin,
    RequestProxyMixin,
    flask.Request,
):
    pass


class HTTPProxyApplication(flask.Flask):

    request_class = ProxyRequest

    def __init__(self, *args, **kwargs):
        kwargs['static_folder'] = None
        super(HTTPProxyApplication, self).__init__(*args, **kwargs)
        self.register_blueprint(proxy_handler)

        # XXX: what if the config is changed after app is created?
        self.http_cli = urllib3.PoolManager(
            # num_pools=self.config.HTTP_CLIENT['num_pools'],
            # **self.config.HTTP_CLIENT['pool']
        )
