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

########################################### TODO: temporary!
import sys
import time
minionName = sys.argv[1]
###########################################

class WorkItem(Message):
    __slots__ = ("query", "groups")
    def __init__(self, foreman, query, groups):
        self.foreman = foreman
        self.query = query   # (foreman, queryid, dataset, inputs, numGroups)
        self.groups = groups

class Gabo(threading.Thread):
    heartbeat = 0.030           # 30 ms      period of response to foreman; can be same as responseThreshold
    listenThreshold = 0.5       # 500 ms     no response from the foreman; reset Client send/recv state

    def __init__(self, foreman, foremanAddress, newWork, firstQuery):
        super(Gabo, self).__init__()
        self.foreman = foreman
        self.newWork = newWork
        self.newQueries = queue.Queue()
        self.newQueries.put(firstQuery)

        # treat as thread-local
        self.gabo = Client(foremanAddress, self.listenThreshold)
        self.queries = {}

        self.daemon = True

    def handle(self, message):
        if message is None:
            raise StopIteration

        elif isinstance(message, Heartbeat):
            assert message.identity == self.foreman

        elif isinstance(message, WorkAssignment):
            assert message.foreman == self.foreman

            for queryid, groups in message.assignment.items():
                assert queryid in self.queries
                self.newWork.put(WorkItem(self.foreman, self.queries[queryid], sorted(groups)))

        else:
            assert False, "unrecognized message from foreman on gabo channel {0}".format(message)

    def run(self):
        try:
            while True:
                newQueries = drainQueue(self.newQueries)

                for query in newQueries:
                    self.queries[query.queryid] = query
                    self.gabo.send(ResponseToQuery(minionName, self.foreman, query.queryid))
                    self.handle(self.gabo.recv())

                if len(newQueries) == 0:
                    self.gabo.send(Heartbeat(minionName))
                    self.handle(self.gabo.recv())

                time.sleep(self.heartbeat)

        except StopIteration:
            print("{} is dead".format(self.foreman))
            pass  # and so is this thread

class CacheMaster(threading.Thread):
    def __init__(self):
        super(CacheMaster, self).__init__()
        self.newWork = queue.Queue()
        self.daemon = True

    def run(self):
        while True:
            print("{} has to do {}".format(minionName, self.newWork.get()))

cacheMaster = CacheMaster()
cacheMaster.start()

gabos = {}
def respondToCall(query):
    if query.foreman in gabos and gabos[query.foreman].isAlive():
        gabos[query.foreman].newQueries.put(query)
    else:
        gabos[query.foreman] = Gabo(query.foreman, "tcp://127.0.0.1:5556", cacheMaster.newWork, query)
        gabos[query.foreman].start()

print("minion {} starting".format(minionName))
listener = Listen("tcp://127.0.0.1:5557", respondToCall)

listenloop()
