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
import traceback
import socket
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

import zmq
import zmq.eventloop.zmqstream
import zmq.eventloop.ioloop

from femtocode.py23 import *
from femtocode.util import *

#################################################################### ZeroMQ (for internal communication)

# global
context = zmq.Context()

def serialize(message, protocol=pickle.HIGHEST_PROTOCOL):
    return pickle.dumps(message, protocol)

def deserialize(message):
    return pickle.loads(message)

class ZMQServer(object):
    def __init__(self, bindaddr, timeout=None, protocol=pickle.HIGHEST_PROTOCOL):
        self.bindaddr = bindaddr
        self.timeout = timeout     # in seconds
        self.protocol = protocol

        self.socket = context.socket(zmq.REP)
        self.socket.bind(self.bindaddr)
        if self.timeout is not None:
            self.socket.RCVTIMEO = roundup(self.timeout * 1000)

    def send(self, message):
        self.socket.send_pyobj(message)

    def recv(self):
        try:
            return self.socket.recv_pyobj()
        except zmq.Again:
            return None

class ZMQClient(object):
    def __init__(self, connaddr, timeout=None, protocol=pickle.HIGHEST_PROTOCOL):
        self.connaddr = connaddr
        self.timeout = timeout
        self.protocol = protocol

        self.socket = context.socket(zmq.REQ)
        self.socket.connect(self.connaddr)
        if timeout is not None:
            self.socket.RCVTIMEO = roundup(self.timeout * 1000)

    def send(self, message):
        self.socket.send_pyobj(message)

    def recv(self):
        try:
            return self.socket.recv_pyobj()
        except zmq.Again:
            return None

class ZMQBroadcast(object):
    def __init__(self, bindaddr, protocol=pickle.HIGHEST_PROTOCOL):
        self.bindaddr = bindaddr
        self.protocol = protocol

        self.socket = context.socket(zmq.PUB)
        self.socket.bind(self.bindaddr)

    def send(self, message):
        self.socket.send(serialize(message, self.protocol))

class ZMQListen(object):
    def __init__(self, connaddr, callback):
        self.callback = callback
        self.connaddr = connaddr

        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")   # no topics, please
        self.stream = zmq.eventloop.zmqstream.ZMQStream(self.socket)

        def handle(messages):
            for message in messages:
                callback(deserialize(message))

        self.stream.on_recv(handle)
        self.socket.connect(self.connaddr)

def zmqloop():
    zmq.eventloop.ioloop.IOLoop.instance().start()

#################################################################### HTTP (for APIs)

class HTTPServer(object):
    # assumes you have a bindaddr, bindport, and __call__ handles HTTP requests

    def start(self):
        server = make_server(self.bindaddr, self.bindport, self)
        server.serve_forever()

    def getstring(self, environ):
        length = int(environ.get("CONTENT_LENGTH", "0"))
        return environ["wsgi.input"].read(length)

    def getjson(self, environ):
        length = int(environ.get("CONTENT_LENGTH", "0"))
        return json.loads(environ["wsgi.input"].read(length))

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
