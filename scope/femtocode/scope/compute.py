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

import threading
import multiprocessing
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.scope.messages import *
from femtocode.scope.communication import *
from femtocode.scope.util import *

import sys
import time

minion = sys.argv[1]

class WorkItem(Message):
    __slots__ = ("query", "groups")
    def __init__(self, tallyman, query, groups):
        self.tallyman = tallyman
        self.query = query
        self.groups = groups

class Gabo(threading.Thread):
    delay = 1.0
    deadThreshold = 10

    def __init__(self, tallyman, newWork, firstQuery):
        super(Gabo, self).__init__()
        self.tallyman = tallyman
        self.newWork = newWork
        self.newQueries = queue.Queue()
        self.newQueries.put(firstQuery)
        self.daemon = True

    def run(self):
        gabo = context.socket(zmq.REQ)
        gabo.connect("tcp://127.0.0.1:5556")
        gabo.RCVTIMEO = int(self.delay * self.deadThreshold * 1000)

        while True:
            queries = drainQueue(self.newQueries)

            try:
                for query in queries:
                    gabo.send_pyobj(GiveMeWork(minion, self.tallyman, query.queryid))
                    heresSomeWork = gabo.recv_pyobj()
                    assert heresSomeWork.tallyman == self.tallyman
                    assert heresSomeWork.queryid == query.queryid
                    self.newWork.put(WorkItem(self.tallyman, query, heresSomeWork.groups))

                if len(queries) == 0:
                    gabo.send_pyobj(Heartbeat(minion))
                    heartbeat = gabo.recv_pyobj()
                    assert heartbeat.identity == self.tallyman

            except zmq.Again:
                print("{} is dead".format(self.tallyman))
                break

            time.sleep(self.delay)

class CacheMaster(threading.Thread):
    def __init__(self):
        super(CacheMaster, self).__init__()
        self.newWork = queue.Queue()
        self.daemon = True

    def run(self):
        while True:
            print("{} has to do {}".format(minion, self.newWork.get()))

cacheMaster = CacheMaster()
cacheMaster.start()

gabos = {}
def respondToQuery(query):
    if query.tallyman in gabos and gabos[query.tallyman].isAlive():
        gabos[query.tallyman].newQueries.put(query)
    else:
        gabos[query.tallyman] = Gabo(query.tallyman, cacheMaster.newWork, query)
        gabos[query.tallyman].start()

print("minion {} starting".format(minion))
listener = Listen("tcp://127.0.0.1:5557", respondToQuery)

loop()
