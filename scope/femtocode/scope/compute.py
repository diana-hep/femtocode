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
from femtocode.scope.communication import *
from femtocode.scope.metadata import MetadataFromMongoDB
from femtocode.run.metadata import MetadataFromJson

class GaboServer(threading.Thread):
    def __init__(self, bindaddr, metadata, cacheMaster, executorClass):
        super(GaboServer, self).__init__()
        self.server = Server(bindaddr, None)
        self.metadata = metadata
        self.cacheMaster = cacheMaster
        self.executorClass = executorClass
        self.outgoing = cacheMaster.incoming
        self.daemon = True

    def run(self):
        while True:
            message = self.server.recv()

            if isinstance(message, CompiledQuery):
                work = Work(message,
                            self.metadata.dataset(message.dataset, message.groupids, message.inputs),
                            self.executorClass(message),
                            None)
                self.outgoing.put(work)

            self.server.send(Ack())

########################################### TODO: temporary!

datasetClass = ROOTDataset
fetcherClass = ROOTFetcher
executorClass = DummyExecutor

minion = Minion(queue.Queue(), queue.Queue())
# metadata = MetadataFromMongoDB(datasetClass, "mongodb://localhost:27017", "metadb", "datasets", 1.0)
metadata = MetadataFromJson(datasetClass, "/home/pivarski/diana/femtocode/tests")

cacheMaster = CacheMaster(NeedWantCache(1024**3, fetcherClass), [minion])
gaboServer = GaboServer("tcp://*:5556", metadata, cacheMaster, executorClass)

minion.start()
cacheMaster.start()
gaboServer.start()

while True:
    if not minion.isAlive() or not cacheMaster.isAlive() or not gaboServer.isAlive():
        sys.exit()
    time.sleep(1)

###########################################
