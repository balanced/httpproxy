httpproxy
=========

[![Build Status](https://travis-ci.org/balanced/httpproxy.svg?branch=master)](https://travis-ci.org/balanced/httpproxy)

httpproxy is a simple transparent HTTP proxy library.

Example
=======

With httpproxy, it's very easy to implement a transparent proxy that can manipulate both requests and responses. Following is a Hodor proxy example, it replaces all words with `hodor` in the response.

```python
from __future__ import unicode_literals
import re

from httpproxy import HTTPProxyApplication


class HodorProxy(object):
    word_pattern = re.compile(r'(\w+)')

    def __init__(self):
        self.scheme = 'http'
        self.host = 'example.com'

    def egress_handler(self, uri, method, status, headers, data):
        hodor = 'hodor'
        data = self.word_pattern.sub(hodor, data)
        headers['Content-Length'] = str(len(data))
        return dict(
            status=status,
            headers=headers,
            data=data,
        )

if __name__ == '__main__':
    proxy_app = HTTPProxyApplication(__name__)
    proxy_app.config['DEBUG'] = True
    proxy_app.config['HTTP_PROXY_FACTORY'] = lambda request: HodorProxy()
    proxy_app.run()

```

It works like this, the first thing is to create the `HTTPProxyApplication` application, then you set the `HTTP_PROXY_FACTORY` value in the app configuration. Then we a new request comes in, a `HodorProxy` will be created, upon receiving response from target server, `egress_handler` of `HodorProxy` will be called to generate hodor content. In this example, you can run it, and hit the proxy like this

```
curl localhost:5000 -H "Host: example.com"
```

then you should be able to see the beautiful Hodor web content like this:

```html
<!hodor hodor>
<hodor>
<hodor>
    <hodor>hodor hodor</hodor>

    <hodor hodor="hodor-hodor" />
    <hodor hodor-hodor="hodor-hodor" hodor="hodor/hodor; hodor=hodor-hodor" />
    <hodor hodor="hodor" hodor="hodor=hodor-hodor, hodor-hodor=hodor" />
    <hodor hodor="hodor/hodor">
...
```

Proxy object
============

Proxy object should be created via the factory set to application configuration with key `HTTP_PROXY_FACTORY`. The factory function accepts incoming request as the argument, and return the proxy instance.

A proxy object should provides

 - scheme
 - host

attributes. The `scheme` is target HTTP server scheme to be used, can be either
`http` or `https`. And the `host` is the host name of target server. Proxy can
also provides `ingress_handler` and `egress_handler` methods for manipulating
ingress requests and egress requests. 

ingress_handler
---------------

`ingress_handler` method will be called to handle incoming requests and return outgoing requests if provided. Passed arguments are

 - `uri` - Target URI in the request
 - `method` - HTTP method, e.g. `GET`, `POST` and etc.
 - `headers` - Headers of the request as a `dict`
 - `data` - HTTP request body as a string
 - `charset` - Encoding of the data body

And the handler should return the outgoing request a dict which contains keys listed above. A do-nothing `ingress_handler` looks like this:

```python
def ingress_handler(self, uri, method, headers, data, charset):
    return dict(
        uri=uri,
        method=method,
        headers=headers,
        data=data,
        charset=charset,
    )

```

egress_handler
--------------

`egress_handler` method will be called to handle incoming responses and return outgoing responses if provided. Passed arguments are

 - `uri` - Target URI in the response
 - `method` - HTTP method, e.g. `GET`, `POST` and etc.
 - `headers` - Headers of the response as a `dict`
 - `status` - Status code
 - `data` - HTTP response body as a string

And the handler should return a dict which contains 

 - `status`
 - `headers`
 - `data`

A do-nothing `egress_handler` looks like this:

```python
def egress_handler(self, uri, method, status, headers, data):
    return dict(
        status=status,
        headers=headers,
        data=data,
    )

```

Handler returns flask.Response object
-------------------------------------

Sometimes you want your handler returns a response to the client without doing
proxying, you can actually return a `flask.Response` object. For example,
in your `ingress_handler`, you only want to echo the content of request,
you can write a handler like this

```python
from flask import Response

def ingress_handler(self, uri, method, headers, data, charset):
    return Response(data)

```

then the response object will be returned to the client immediately. No outging
request will be sent to the target server.
