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
import select
import socket
import struct
import sys
import threading
import traceback
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

class SimpleServer(object):
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
                    self.connection.close()
                    break

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

    def start(self):
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
        self.socket = None
        self.sent = False

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.connaddr, self.connport))
        self.socket.setblocking(0)
        self.sent = False
        
    def send(self, obj):
        assert not self.sent, "two subsequent calls to send"
        if self.socket is None:
            self.connect()

        sendobj(obj, self.socket, self.chunksize, self.protocol)

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

    def close(self):
        if self.socket is not None:
            self.socket.close()
        self.socket = None

#################################################################### HTTP (public-facing APIs)

class HTTPServer(object):
    # assumes you have a and __call__ handles HTTP requests

    def start(self, bindaddr, bindport):
        server = make_server(bindaddr, bindport, self)
        server.serve_forever()

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

#################################################################### HTTP and multiprocessing (alternative for internal communication)

class HTTPInternalProcess(multiprocessing.Process):
    def __init__(self, name, pipe):
        super(HTTPInternalProcess, self).__init__()
        self.pipe = pipe
        self.daemon = True

    def recv(self):
        return pickle.loads(self.pipe.recv_bytes())

    def send(self, obj):
        self.pipe.send_bytes(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))

class HTTPInternalClient(object):
    class Error(object):
        def __init__(self, message):
            self.message = message
            
    class Response(object):
        def __init__(self, fid):
            self.fid = fid
            self.data = None

        def get(self):
            if self.data is None:
                try:
                    data = self.fid.read()
                except socket.timeout as err:
                    self.data = HTTPInternalClient.Error("timeout")
                except HTTPError as err:
                    self.data = HTTPInternalClient.Error(err.read())
                else:
                    self.data = pickle.loads(data)

            return self.data

    class FailedResponse(object):
        def __init__(self, error):
            self.error = error

        def get(self):
            return self.error

    def __init__(self, connaddr, connport, timeout):
        self.connaddr = connaddr
        self.connport = connport
        self.timeout = timeout

    def send(self, path, obj):
        message = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        try:
            fid = urlopen("http://{0}:{1}/{2}".format(self.connaddr, self.connport, path), message, self.timeout)
        except socket.timeout:
            return HTTPInternalClient.FailedResponse(HTTPInternalClient.Error("timeout"))
        except HTTPError as err:
            return HTTPInternalClient.FailedResponse(HTTPInternalClient.Error(err.read()))
        else:
            return HTTPInternalClient.Response(fid)

class HTTPInternalServer(HTTPServer):
    def __init__(self, procclass, timeout):
        super(HTTPInternalServer, self).__init__()
        self.procclass = procclass
        self.timeout = timeout

        self.lock = threading.Lock()
        self.processes = {}

    def startProcess(self, path):
        oldproc = self.processes.get(path)

        if oldproc is not None and oldproc.is_alive():
            oldproc.terminate()

        myend, yourend = multiprocessing.Pipe()
        proc = self.procclass(path, yourend)
        proc.start()

        self.processes[path] = (proc, myend)

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "").strip("/")

        try:
            if path == "":
                # broadcast to all processes (that exist)
                data = self.getstring(environ)

                for proc, myend in self.processes.values():
                    myend.send_bytes(data)

                alive = []
                for path, (proc, myend) in list(self.processes.items()):
                    if myend.poll(self.timeout):
                        myend.recv_bytes()
                        alive.append(path)
                    else:
                        proc.terminate()
                        del self.processes[path]

                # return a list of the processes that still exist
                return self.sendjson(alive, start_response)

            else:
                # send to a particular process, creating it if necessary
                if path not in self.processes or not self.processes[path][0].is_alive():
                    self.startProcess(path)

                proc, myend = self.processes[path]
                myend.send_bytes(self.getstring(environ))

                if myend.poll(self.timeout):
                    return self.sendstring(myend.recv_bytes(), start_response)
                else:
                    proc.terminate()
                    del self.processes[path]
                    return self.senderror("500 Internal Server Error", start_response, "process unresponsive; killed")

        except Exception as err:
            return self.senderror("500 Internal Server Error", start_response)

import time

class TestProc(HTTPInternalProcess):
    def __init__(self, name, pipe):
        super(TestProc, self).__init__(name, pipe)

    def run(self):
        while True:
            x = self.recv()
            self.send(x + 10)

application = HTTPInternalServer(TestProc, 1.0)
