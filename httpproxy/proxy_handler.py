from __future__ import unicode_literals

from flask import Blueprint

proxy_handler = Blueprint('proxy_handler', __name__)


@proxy_handler.route(
    '/', defaults={'path': ''}, methods=['GET', 'HEAD', 'PATCH', 'DELETE']
)
@proxy_handler.route(
    '/<path:path>', methods=['GET', 'HEAD', 'PATCH', 'DELETE', 'POST', 'PUT']
)
def proxy_pass(*args, **kwargs):
    return 'foobar'
