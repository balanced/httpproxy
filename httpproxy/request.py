from __future__ import unicode_literals

import flask
import netaddr
import werkzeug.exceptions
import werkzeug.http
import werkzeug.datastructures
import werkzeug.utils

exc = werkzeug.exceptions


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


class RequestTraceMixin(object):

    @werkzeug.utils.cached_property
    def trace_id(self):
        return flask.current_app.tracer.id


class RequestNetworkMixin(object):

    @werkzeug.utils.cached_property
    def remote_ip_addr(self):
        return netaddr.IPAddress(self.remote_addr)

    @property
    def is_remote_ip_allowed(self):
        return any(
            self.remote_ip_addr in cidr
            for cidr in flask.current_app.config['HTTP_PROXY_ALLOWED_CIDRS']
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
        proxy.scheme = 'http'
        proxy.host = 'example.com'
        return proxy


class ProxyRequest(
    RequestTraceMixin,
    RequestNetworkMixin,
    # RequestMIMEMixin,
    RequestProxyMixin,
    flask.Request,
):
    pass
