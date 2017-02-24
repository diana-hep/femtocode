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

import sys
import threading
import time
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.fromroot.dataset import ROOTDataset
from femtocode.fromroot.fetch import ROOTFetcher
from femtocode.run.cache import *
from femtocode.run.execution import *
from femtocode.run.messages import *
from femtocode.scope.communication import *
from femtocode.scope.metadata import *
from femtocode.util import *

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
            # FIXME:
            # self.outgoing.put(result)
            print("result {} in {:.2f} ms".format(result.data, (time.time() - workItem.startTime)*1e3))

class CacheMaster(threading.Thread):
    loopdelay = 0.001           # 1 ms       pause time at the end of the loop

    def __init__(self, needWantCache, minion, metadata, executorClass):
        super(CacheMaster, self).__init__()
        self.needWantCache = needWantCache
        self.minion = minion
        self.metadata = metadata
        self.executorClass = executorClass

        self.incoming = queue.Queue()
        self.outgoing = self.minion.incoming
        self.waitingRoom = []
        self.downloading = []

        self.daemon = True

    def __repr__(self):
        return "<CacheMaster at {0:012x}>".format(id(self))

    def run(self):
        while True:
            # put new work in the waitingRoom
            for query in drainQueue(self.incoming):
                work = Work(query, metadata.dataset(query.dataset, query.groupids, query.inputs), self.executorClass(query))
                for groupid in query.groupids:
                    self.waitingRoom.append(WorkItem(work, groupid))

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

class GaboServer(threading.Thread):
    def __init__(self, bindaddr, cacheMaster):
        super(GaboServer, self).__init__()
        self.server = Server(bindaddr, None)
        self.cacheMaster = cacheMaster
        self.outgoing = cacheMaster.incoming
        self.daemon = True

    def run(self):
        while True:
            message = self.server.recv()

            if isinstance(message, CompiledQuery):
                self.outgoing.put(message)

            self.server.send(Ack())


########################################### TODO: temporary!

fetcherClass = ROOTFetcher
executorClass = DummyExecutor

minion = Minion()
metadata = MetadataFromMongoDB("mongodb://localhost:27017", "metadb", "datasets", ROOTDataset, 1.0)
cacheMaster = CacheMaster(NeedWantCache(1024**3, fetcherClass), minion, metadata, executorClass)
gaboServer = GaboServer("tcp://*:5556", cacheMaster)

minion.start()
cacheMaster.start()
gaboServer.start()

while True:
    if not minion.isAlive() or not cacheMaster.isAlive() or not gaboServer.isAlive():
        sys.exit()
    time.sleep(1)

###########################################
