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
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.dataset import MetadataFromJson
from femtocode.numpyio.dataset import NumpyDataset
from femtocode.run.cache import *
from femtocode.run.execution import *
from femtocode.util import *
from femtocode.workflow import Source

class FutureQueryResult(object):
    class _KeepPythonAlive(threading.Thread):
        def __init__(self):
            super(FutureQueryResult._KeepPythonAlive, self).__init__()
            self.done = threading.Event()
            self.daemon = False
        def run(self):
            self.done.wait()

    def __init__(self, query):
        self.query = query
        self.loaded = 0.0
        self.computed = 0.0
        self.done = False
        self.wallTime = 0.0
        self.computeTime = 0.0
        self.data = None
        self._lock = threading.Lock()
        # self._keepPythonAlive = FutureQueryResult._KeepPythonAlive()
        # self._keepPythonAlive.start()

    def __repr__(self):
        return "<FutureQueryResult {0}% loaded {1}% computed{2}>".format(roundup(self.loaded * 100), roundup(self.computed * 100), " (wall: {0:.2g} sec, cpu: {1:.2g} core-sec)".format(self.wallTime, self.computeTime) if self.done else "")

    def update(self, loaded, computed, done, wallTime, computeTime, data):
        with self._lock:
            self.loaded = loaded
            self.computed = computed
            self.done = done
            self.wallTime = wallTime
            self.computeTime = computeTime
            self.data = data
        if done is True:
            print("FIXME {0}".format(self))
            self._keepPythonAlive.done.set()

class StandaloneSession(object):
    def __init__(self,
                 numMinions=multiprocessing.cpu_count(),
                 cacheLimitBytes=1024**3,
                 metadata=MetadataFromJson("."),
                 datasetClass=NumpyDataset):

        minionsIncoming = queue.Queue()
        self.minions = [Minion(minionsIncoming, None) for i in range(numMinions)]
        self.cacheMaster = CacheMaster(NeedWantCache(cacheLimitBytes), self.minions)
        self.metadata = metadata

        for minion in self.minions:
            minion.start()
        self.cacheMaster.start()

    def source(self, name):
        return Source(self, self.metadata.dataset(name))

    def submit(self, query):
        # create an executor with a reference to the FutureQueryResult we will return to the user
        executor = NativeAsyncExecutor(query, FutureQueryResult(query))

        # modify the dataset to include detailed group information (may come as nothing but a dataset.name)
        # query.dataset = self.metadata.dataset(query.dataset.name, range(query.dataset.numGroups), executor.requires)
        ### not in a StandaloneSession, but hold this thought for the server implementation

        # queue it up
        self.cacheMaster.incoming.put(executor)

        # user can watch it fill
        return executor.future

########################################### TODO: temporary!

session = StandaloneSession()
session.metadata.directory = "/home/pivarski/diana/femtocode/tests"

result = session.source("xy").toPython("Test", a = "x + y").submit()

import time
time.sleep(10)
