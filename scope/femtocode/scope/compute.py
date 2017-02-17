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

import multiprocessing
try:
    import cPickle as pickle
except ImportError:
    import pickle

import zmq
import zmq.eventloop.zmqstream
import zmq.eventloop.ioloop

from femtocode.scope.messages import *
        
class QueryStore(multiprocessing.Process):
    def __init__(self, from_accumulate):
        super(QueryStore, self).__init__()
        self.from_accumulate = from_accumulate
        # self.daemon = True

    def run(self):
        context = zmq.Context()

        compiledQueries = {}

        def install(messages):
            for message in messages:
                compiledQuery = Message.recv(message, b"install")
                compiledQueries[compiledQuery.id] = compiledQuery
                print(compiledQueries)

        install_socket = context.socket(zmq.SUB)
        install_socket.setsockopt(zmq.SUBSCRIBE, "install")
        install_stream = zmq.eventloop.zmqstream.ZMQStream(install_socket)
        install_stream.on_recv(install)

        def remove(messages):
            for message in messages:
                queryid = Message.recv(message, b"remove")
                try:
                    del compiledQueries[queryid]
                except KeyError:
                    pass
                print(compiledQueries)

        remove_socket = context.socket(zmq.SUB)
        remove_socket.setsockopt(zmq.SUBSCRIBE, "remove")
        remove_stream = zmq.eventloop.zmqstream.ZMQStream(remove_socket)
        remove_stream.on_recv(remove)

        def clear(messages):
            compiledQueries.clear()
            print(compiledQueries)

        clear_socket = context.socket(zmq.SUB)
        clear_socket.setsockopt(zmq.SUBSCRIBE, "clear")
        clear_stream = zmq.eventloop.zmqstream.ZMQStream(clear_socket)
        clear_stream.on_recv(clear)

        for x in install_socket, remove_socket, clear_socket:
            x.connect(self.from_accumulate)

        zmq.eventloop.ioloop.IOLoop.instance().start()




queryStore = QueryStore("tcp://127.0.0.1:5557")

queryStore.start()
