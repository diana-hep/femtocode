#!/usr/bin/env python

# Copyright 2016 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import multiprocessing
import socket
import traceback
import threading
from wsgiref.simple_server import make_server
try:
    from urllib2 import urlparse, urlopen, HTTPError
except ImportError:
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.error import HTTPError
try:
    import cPickle as pickle
except ImportError:
    import pickle

from femtocode.py23 import *
from femtocode.util import *
from femtocode.execution import ExecutionFailure

#################################################################### HTTP for public-facing APIs

class HTTPServer(object):
    # assumes you have a and __call__ handles HTTP requests

    def start(self, bindaddr, bindport):
        server = make_server(bindaddr, bindport, self)
        server.serve_forever()

    def getpath(self, environ):
        return environ.get("PATH_INFO", "").lstrip("/")

    def getstring(self, environ):
        length = int(environ.get("CONTENT_LENGTH", "0"))
        return environ["wsgi.input"].read(length)

    def getjson(self, environ):
        length = int(environ.get("CONTENT_LENGTH", "0"))
        return json.loads(environ["wsgi.input"].read(length))

    def getpickle(self, environ):
        length = int(environ.get("CONTENT_LENGTH", "0"))
        return pickle.loads(environ["wsgi.input"].read(length))

    def sendstring(self, string, start_response):
        start_response("200 OK", [("Content-type", "application/json")])
        return [string]

    def sendjson(self, obj, start_response):
        try:
            serialized = json.dumps(obj)
        except:
            return self.senderror("500 Internal Server Error", start_response)
        else:
            start_response("200 OK", [("Content-type", "application/json")])
            return [serialized]

    def sendpickle(self, obj, start_response):
        try:
            serialized = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            return self.senderror("500 Internal Server Error", start_response)
        else:
            start_response("200 OK", [("Content-type", "application/octet-stream")])
            return [serialized]

    def senderror(self, code, start_response, message=None):
        if isinstance(code, HTTPError):
            code = "{0} {1}".format(code.code, code.reason)
        start_response(code, [("Content-Type", "text/plain")])
        if message is None:
            return [traceback.format_exc()]
        else:
            return [message]

    def gateway(self, url, environ, start_response):
        try:
            remote = urlopen(url, self.getstring(environ), self.timeout)
            result = remote.read()
        except socket.timeout:
            return self.senderror("502 Bad Gateway", start_response)
        except HTTPError as err:
            return self.senderror(err, start_response, err.read())
        else:
            return self.sendstring(result, start_response)
