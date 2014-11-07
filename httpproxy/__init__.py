from __future__ import unicode_literals

import flask

__version__ = '0.0.0'

from .proxy_handler import proxy_handler


class ProxyRequest(
    # RequestTraceMixin,
    # RequestNetworkMixin,
    # RequestMIMEMixin,
    # RequestProxyMixin,
    flask.Request,
):
    pass


class HTTPProxyApplication(flask.Flask):

    request_class = ProxyRequest

    def __init__(self, *args, **kwargs):
        kwargs['static_folder'] = None
        super(HTTPProxyApplication, self).__init__(*args, **kwargs)
        self.register_blueprint(proxy_handler)
