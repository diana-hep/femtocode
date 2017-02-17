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
        socket = context.socket(zmq.PAIR)
        socket.connect(self.from_accumulate)
        stream = zmq.eventloop.zmqstream.ZMQStream(socket)

        compiledQueries = {}

        def respond_to_accumulate(messages):
            for message in messages:
                obj = pickle.loads(message)
                if isinstance(obj, InstallCompiledQuery):
                    compiledQueries[obj.compiledQuery.id] = obj.compiledQuery
                elif isinstance(obj, RemoveCompiledQuery):
                    try:
                        del compiledQueries[obj.queryid]
                    except KeyError:
                        pass
                elif isinstance(obj, RemoveAllCompiledQueries):
                    compiledQueries.clear()

                print(compiledQueries)

        stream.on_recv(respond_to_accumulate)
        zmq.eventloop.ioloop.IOLoop.instance().start()




queryStore = QueryStore("tcp://127.0.0.1:5557")

queryStore.start()
