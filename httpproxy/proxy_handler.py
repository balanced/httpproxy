from __future__ import unicode_literals
import urlparse

from flask import Blueprint
from flask import request
from flask import Response
from flask import current_app
import werkzeug.http


proxy_handler = Blueprint('proxy_handler', __name__)


@proxy_handler.route(
    '/', defaults={'path': ''}, methods=['GET', 'HEAD', 'PATCH', 'DELETE']
)
@proxy_handler.route(
    '/<path:path>', methods=['GET', 'HEAD', 'PATCH', 'DELETE', 'POST', 'PUT']
)
def proxy_pass(*args, **kwargs):
    proxy = request.proxy

    # call ingress handler of proxy to generate outgoing request to target
    # server
    uri = request.url[len(request.host_url.rstrip('/')):]
    method = request.method
    headers = dict(
        (h, v) for h, v in list(request.headers)
        if not werkzeug.http.is_hop_by_hop_header(h)
    )
    data = request.get_data()
    charset = request.charset
    outgoing_request = proxy.ingress_handler(
        uri=uri,
        method=method,
        headers=headers,
        data=data,
        charset=charset,
    )
    uri = outgoing_request['uri']
    method = outgoing_request['method']
    headers = outgoing_request['headers']
    data = outgoing_request['data']
    charset = outgoing_request['charset']

    # send outgoing request to server
    root = '{scheme}://{host}'.format(
        scheme=proxy.scheme,
        host=proxy.host or request.headers['Host'],
    )
    url = urlparse.urljoin(root, uri)
    headers = headers.copy()

    tracer_id_header = current_app.config['TRACE_ID_HTTP_HEADER']
    if tracer_id_header not in headers:
        headers[tracer_id_header] = current_app.tracer.id

    # http://stackoverflow.com/a/7993378
    if isinstance(url, unicode):
        url = url.encode('ascii')
    headers = dict(
        (k.encode('ascii') if isinstance(k, unicode) else k,
         v.encode('ascii') if isinstance(v, unicode) else v)
        for k, v in headers.items()
    )
    if isinstance(data, unicode):
        data = data.encode(charset)
    response = current_app.http_cli.urlopen(
        method, url, body=data, headers=headers, decode_content=False
    )

    # call egress handler of proxy to generate outputing response to client
    incoming_response = proxy.egress_handler(
        uri=uri,
        method=method,
        status=response.status,
        headers=response.headers,
        data=response.data,
    )
    status = incoming_response['status']
    headers = incoming_response['headers']
    data = incoming_response['data']

    return Response(status=status, headers=headers.items(), response=data)
