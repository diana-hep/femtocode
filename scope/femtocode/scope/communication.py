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

# global
context = zmq.Context()

class Broadcast(object):
    @staticmethod
    def serialize(message, protocol=pickle.HIGHEST_PROTOCOL):
        return pickle.dumps(message, protocol)

    def __init__(self, port, protocol=pickle.HIGHEST_PROTOCOL):
        self.port = port
        self.protocol = protocol

        self.socket = context.socket(zmq.PUB)
        self.socket.bind("tcp://*:{0}".format(self.port))

    def send(self, message):
        self.socket.send(self.serialize(message, self.protocol))

class Listen(object):
    @staticmethod
    def deserialize(message):
        return pickle.loads(message)

    def __init__(self, address, callback):
        self.callback = callback
        self.address = address

        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.stream = zmq.eventloop.zmqstream.ZMQStream(self.socket)

        def handle(messages):
            for message in messages:
                callback(self.deserialize(message))

        self.stream.on_recv(handle)
        self.socket.connect(self.address)

def loop():
    zmq.eventloop.ioloop.IOLoop.instance().start()