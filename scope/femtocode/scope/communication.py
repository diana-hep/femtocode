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

try:
    import cPickle as pickle
except ImportError:
    import pickle

import zmq
import zmq.eventloop.zmqstream
import zmq.eventloop.ioloop

from femtocode.scope.util import *

# global
context = zmq.Context()

def serialize(message, protocol=pickle.HIGHEST_PROTOCOL):
    return pickle.dumps(message, protocol)

def deserialize(message):
    return pickle.loads(message)

class Server(object):
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

class Client(object):
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

class Broadcast(object):
    def __init__(self, bindaddr, protocol=pickle.HIGHEST_PROTOCOL):
        self.bindaddr = bindaddr
        self.protocol = protocol

        self.socket = context.socket(zmq.PUB)
        self.socket.bind(self.bindaddr)

    def send(self, message):
        self.socket.send(serialize(message, self.protocol))

class Listen(object):
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

def listenloop():
    zmq.eventloop.ioloop.IOLoop.instance().start()
