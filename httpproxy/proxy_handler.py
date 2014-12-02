from __future__ import unicode_literals
import urlparse

from flask import Blueprint
from flask import request
from flask import Response
from flask import current_app
import werkzeug.http


proxy_handler = Blueprint('proxy_handler', __name__)


@proxy_handler.route(
    '/', defaults={'path': ''}, methods=['GET', 'HEAD', 'PATCH', 'DELETE', 'POST', 'PUT']
)
@proxy_handler.route(
    '/<path:path>', methods=['GET', 'HEAD', 'PATCH', 'DELETE', 'POST', 'PUT']
)
def proxy_pass(*args, **kwargs):
    proxy = request.proxy

    # call ingress handler of proxy to generate outgoing request to target
    # server
    path_info = request.environ['PATH_INFO']
    lower_path_info = path_info.lower()
    # in some cases, the PATH_INFO will be passed as an absolute URL,
    # for that case, request.url will be encoded like this
    # http://example.com/http%3A//example.com/foo/bar
    # please reference to https://github.com/balanced/httpproxy/issues/5
    if (
        lower_path_info.startswith('http://') or
        lower_path_info.startswith('https://')
    ):
        url = path_info
    else:
        url = request.url
    uri = url[len(request.host_url.rstrip('/')):]
    method = request.method
    headers = dict(
        (h, v) for h, v in list(request.headers)
        if not werkzeug.http.is_hop_by_hop_header(h)
    )
    data = request.data
    charset = request.charset
    if hasattr(proxy, 'ingress_handler'):
        outgoing_request = proxy.ingress_handler(
            uri=uri,
            method=method,
            headers=headers,
            data=data,
            charset=charset,
        )
        # if the ingress handler returns a response, that means it doesn't
        # want to do the proxying, so we simply return the response
        if isinstance(outgoing_request, Response):
            return outgoing_request
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

    tracer_id_header = current_app.config.get('TRACE_ID_HTTP_HEADER')
    if tracer_id_header and tracer_id_header not in headers:
        headers[tracer_id_header] = request.trace_id

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
    status = response.status
    headers = response.headers
    data = response.data
    if hasattr(proxy, 'egress_handler'):
        incoming_response = proxy.egress_handler(
            uri=uri,
            method=method,
            status=status,
            headers=headers,
            data=data,
        )
        if isinstance(incoming_response, Response):
            return incoming_response
        status = incoming_response['status']
        headers = incoming_response['headers']
        data = incoming_response['data']

    return Response(status=status, headers=headers.items(), response=data)
