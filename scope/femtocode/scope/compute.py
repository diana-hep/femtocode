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
import threading
import time
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.scope.cache import *
from femtocode.scope.communication import *
from femtocode.scope.execution import *
from femtocode.scope.fetch import *
from femtocode.scope.messages import *
from femtocode.scope.metadata import *
from femtocode.scope.util import *

########################################### TODO: temporary!
import sys
minionName = sys.argv[1]
###########################################

class Work(object):
    def __init__(self, foreman, query, groups, metadata, executorClass):
        self.foreman = foreman
        self.query = query
        self.groups = groups
        self.dataset = metadata.dataset(self.query.dataset, self.groups, self.query.inputs)
        self.executor = executorClass(self.query)

    def __repr__(self):
        return "<Work for {0} at {1:012x}>".format(self.query.queryid, id(self))

class Result(object):
    def __init__(self, foreman, queryid, group, data):
        self.foreman = foreman
        self.queryid = queryid
        self.group = group
        self.data = data

    def __repr__(self):
        return "<Result for {0}({1}) at {2:012x}>".format(self.queryid, self.group, id(self))

class WorkItem(object):
    def __init__(self, work, group):
        self.work = work
        self.group = group

        self.occupants = []

    def __repr__(self):
        return "<WorkItem for {0}({1}) at {2:012x}>".format(self.work.query.queryid, self.group, id(self))

    def requires(self):
        return [DataAddress(self.work.query.dataset, column, self.group) for column in self.work.query.inputs]

    def columnBytes(self, column):
        for group in self.work.dataset.groups:
            if group.id == self.group:
                return group.segments[column].dataLength * self.columnDtype(column).itemsize
        assert False, "group {0} not found in dataset metadata".format(self.group)

    def columnDtype(self, column):
        return self.work.dataset.columns[column].dataType

    def attachOccupant(self, occupant):
        self.occupants.append(occupant)

    def ready(self):
        assert len(self.occupants) != 0
        return all(occupant.ready() for occupant in self.occupants)

    def decrementNeed(self):
        assert len(self.occupants) != 0
        for occupant in self.occupants:
            occupant.decrementNeed()

    def run(self):
        return Result(self.work.foreman,
                      self.work.query.queryid,
                      self.group,
                      self.work.executor.run(dict((occupant.address.column, occupant.array()) for occupant in self.occupants)))

    def decrementNeed(self):
        assert len(self.occupants) != 0
        for occupant in self.occupants:
            occupant.decrementNeed()

class Minion(threading.Thread):
    def __init__(self):
        super(Minion, self).__init__()
        self.incoming = queue.Queue()
        self.outgoing = queue.Queue()

        self.daemon = True

    def __repr__(self):
        return "<Minion at {0:012x}>".format(id(self))

    def run(self):
        while True:
            workItem = self.incoming.get()
            result = workItem.run()
            workItem.decrementNeed()
            self.outgoing.put(result)

class CacheMaster(threading.Thread):
    loopdelay = 0.001           # 1 ms       pause time at the end of the loop

    def __init__(self, needWantCache, workToMinion):
        super(CacheMaster, self).__init__()
        self.incoming = queue.Queue()
        self.outgoing = workToMinion

        # treat as thread-local
        self.needWantCache = needWantCache
        self.waitingRoom = []
        self.downloading = []

        self.daemon = True

    def __repr__(self):
        return "<CacheMaster at {0:012x}>".format(id(self))

    def run(self):
        while True:
            # put new work in the waitingRoom
            self.waitingRoom.extend(drainQueue(self.incoming))

            # move work from waitingRoom to downloading or Minion
            while True:
                workItem = self.needWantCache.maybeReserve(self.waitingRoom)
                if workItem is None:
                    break
                elif workItem.ready():
                    self.outgoing.put(workItem)
                else:
                    self.downloading.append(workItem)

            # move work from downloading to Minion
            toremove = []
            for index, workItem in enumerate(self.downloading):
                if workItem.ready():
                    toremove.append(index)
                    self.outgoing.put(workItem)
            while len(toremove) > 0:
                del self.downloading[toremove.pop()]

            # no busy wait
            time.sleep(self.loopdelay)

class Gabo(threading.Thread):
    heartbeat = 0.030           # 30 ms      period of response to foreman; can be same as responseThreshold
    listenThreshold = 0.5       # 500 ms     no response from the foreman; reset Client send/recv state

    def __init__(self, foreman, foremanAddress, workToCacheMaster, firstQuery, metadata, executorClass):
        super(Gabo, self).__init__()
        self.foreman = foreman
        self.workToCacheMaster = workToCacheMaster
        self.newQueries = queue.Queue()
        self.newQueries.put(firstQuery)
        self.metadata = metadata
        self.executorClass = executorClass

        # treat as thread-local
        self.gabo = Client(foremanAddress, self.listenThreshold)
        self.queries = {}

        self.daemon = True

    def __repr__(self):
        return "<Gabo at {0:012x}>".format(id(self))

    def handle(self, message):
        if message is None:
            raise StopIteration

        elif isinstance(message, Heartbeat):
            assert message.identity == self.foreman

        elif isinstance(message, WorkAssignment):
            assert message.foreman == self.foreman

            for queryid, groups in message.assignment.items():
                assert queryid in self.queries
                work = Work(self.foreman, self.queries[queryid], sorted(groups), self.metadata, self.executorClass)
                for group in work.groups:
                    self.workToCacheMaster.put(WorkItem(work, group))

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

executorClass = DummyExecutor

metadata = MetadataFromMongoDB("mongodb://localhost:27017", "metadb", "datasets", ROOTDataset, 1.0)

minion = Minion()
minion.start()

cacheMaster = CacheMaster(NeedWantCache(1024**3, DummyFetcher), minion.incoming)
cacheMaster.start()

gabos = {}
def respondToCall(query):
    if query.foreman in gabos and gabos[query.foreman].isAlive():
        gabos[query.foreman].newQueries.put(query)
    else:
        gabos[query.foreman] = Gabo(query.foreman, "tcp://127.0.0.1:5556", cacheMaster.incoming, query, metadata, executorClass)
        gabos[query.foreman].start()

print("minion {} starting".format(minionName))
listener = Listen("tcp://127.0.0.1:5557", respondToCall)

listenloop()
