from __future__ import unicode_literals

from pyramid.response import Response
from pyramid.config import Configurator

__version__ = '0.0.0'


def main(global_config, **settings):
    proxy_app = HTTPProxyApp(**settings)
    return proxy_app.wsgi_app


class HTTPProxyApp(object):

    def __init__(self, **settings):
        self.settings = settings
        self.config = None
        self.init_config()

    def init_config(self):
        self.config = Configurator(
            settings=self.settings,
        )
        self.config.add_route('proxy_handler', '*path')
        self.config.add_view(self.handle_request, route_name='proxy_handler')
        self.wsgi_app = self.config.make_wsgi_app()

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def handle_request(self, request):
        # TODO: pick a proxy handler object
        # TODO: call the ingress handler to modify the request
        # TODO: send the request to the target server
        # TODO: call the egress handler to modify the response
        return Response('yooooo~')
