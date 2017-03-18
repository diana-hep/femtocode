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
import threading
import socket
import select
import struct
import sys
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

#################################################################### sockets (internal communication)

def sendobj(obj, sock, chunksize, protocol=pickle.HIGHEST_PROTOCOL):
    message = pickle.dumps(obj, protocol)
    length = len(message)

    if sock.send(struct.pack("!Q", length)) != 8:
        raise socket.error("connection closed early")

    uploaded = 0
    while uploaded < length:
        nextlength = min(chunksize, length - uploaded)
        if sock.send(message[uploaded : uploaded + nextlength]) != nextlength:
            raise socket.error("connection closed early")
        uploaded += nextlength

def recvobj(sock, chunksize, timeout=None):
    if timeout is not None:
        ready = select.select([sock], [], [], timeout)
        if not ready[0]:
            raise socket.timeout("no response in {0} seconds".format(timeout))

    recv = sock.recv(8)
    if len(recv) != 8:
        raise socket.error("connection closed early")
    length, = struct.unpack("!Q", recv)

    data = []
    downloaded = 0
    while downloaded < length:
        nextlength = min(chunksize, length - downloaded)
        next = sock.recv(nextlength)
        if len(next) != nextlength:
            raise socket.error("connection closed early")
        data.append(next)
        downloaded += nextlength

    try:
        return pickle.loads("".join(data))
    except:
        raise socket.error("bad object in wire protocol")

class SimpleServerError(object):
    def __init__(self, exception):
        self.type = exception.__class__.__name__
        self.message = str(exception)
        self.traceback = "".join(traceback.format_exception(exception.__class__, exception, sys.exc_info()[2]))

class SimpleServer(threading.Thread):
    class Handler(threading.Thread):
        def __init__(self, connection, address, handler, chunksize, protocol):
            super(SimpleServer.Handler, self).__init__()
            self.connection = connection
            self.address = address
            self.handler = handler
            self.chunksize = chunksize
            self.protocol = protocol
            self.daemon = True

        def run(self):
            while True:
                try:
                    arg = recvobj(self.connection, self.chunksize, None)
                    ret = self.handler(arg)
                except Exception as err:
                    ret = SimpleServerError(err)

                try:
                    sendobj(ret, self.connection, self.chunksize, self.protocol)
                except:
                    break

            # recv = self.connection.recv(8)
            # while len(recv) == 8:
            #     try:
            #         length, = struct.unpack("!Q", recv)
            #         data = self.connection.recv(length)
            #         arg = pickle.loads(data)
            #         ret = self.handler(arg)
            #     except Exception as err:
            #         ret = Error(err)
            #     message = pickle.dumps(ret, self.protocol)
            #     self.connection.send(struct.pack("!Q", len(message)))
            #     self.connection.send(message)
            #     recv = self.connection.recv(8)

    def __init__(self, bindaddr, bindport, handler, chunksize=2**12, protocol=pickle.HIGHEST_PROTOCOL):
        super(SimpleServer, self).__init__()
        self.bindaddr = bindaddr
        self.bindport = bindport
        self.handler = handler
        self.chunksize = chunksize
        self.protocol = protocol
        self.daemon = True

        assert callable(self.handler)
        self.bind()

    def bind(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.bindaddr, self.bindport))
        self.socket.listen(0)

    def run(self):
        while True:
            try:
                connection, address = self.socket.accept()

            except:
                self.socket.close()
                self.bind()

            else:
                SimpleServer.Handler(connection, address, self.handler, self.chunksize, self.protocol).start()

class SimpleClient(object):
    def __init__(self, connaddr, connport, timeout, chunksize=2**12, protocol=pickle.HIGHEST_PROTOCOL):
        self.connaddr = connaddr
        self.connport = connport
        self.timeout = timeout
        self.chunksize = chunksize
        self.protocol = protocol
        self.connect()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.connaddr, self.connport))
        self.socket.setblocking(0)
        self.sent = False
        
    def send(self, obj):
        assert not self.sent, "two subsequent calls to send"

        sendobj(obj, self.socket, self.chunksize, self.protocol)

        # message = pickle.dumps(obj)
        # length = len(message)
        # self.socket.send(struct.pack("!Q", length))
        # uploaded = 0
        # while uploaded < length:
        #     nextlength = min(self.chunksize, length - uploaded)
        #     assert self.socket.send(message[uploaded : uploaded + nextlength]) == nextlength
        #     uploaded += nextlength
        # self.socket.send(message)

        self.sent = True

    def recv(self):
        assert self.sent, "recv called before send"

        try:
            return recvobj(self.socket, self.chunksize, self.timeout)

        except Exception:
            self.socket.close()
            self.connect()
            raise

        finally:
            self.sent = False

        # ready = select.select([self.socket], [], [], self.timeout)
        # if ready[0]:
        #     recv = self.socket.recv(8)
        #     assert len(recv) == 8
        #     length, = struct.unpack("!Q", recv)

            # data = []
            # downloaded = 0
            # while downloaded < length:
            #     nextlength = min(self.chunksize, length - downloaded)
            #     next = self.socket.recv(nextlength)
            #     assert len(next) == nextlength
            #     data.append(next)
            #     downloaded += nextlength
            # out = pickle.loads("".join(data))

        #     data = self.socket.recv(length)
        #     assert len(data) == length
        #     out = pickle.loads(data)

        #     return out

        # else:
        #     raise socket.timeout("server did not respond in {0} seconds".format(self.timeout))

#################################################################### HTTP (public-facing APIs)

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
