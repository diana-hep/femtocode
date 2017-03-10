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
    class Callback(threading.Thread):
        def __init__(self, fcn):
            super(FutureQueryResult.Callback, self).__init__()
            self.incoming = queue.Queue()
            self.fcn = fcn
            self.daemon = False

        def run(self):
            data = self.incoming.get()
            if isinstance(data, ExecutionFailure):
                data.reraise()
            else:
                self.fcn(data)

    def __init__(self, query, callback):
        self.query = query

        self.loaded = 0.0
        self.computed = 0.0
        self.done = False
        self.wallTime = 0.0
        self.computeTime = 0.0
        self.data = None
        self._lock = threading.Lock()

        if callback is not None:
            self._callback = FutureQueryResult.Callback(callback)
            self._callback.start()
        else:
            self._callback = None
        self._doneevent = threading.Event()

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

        if done:
            if self._callback is not None:
                self._callback.incoming.put(data)  # not self.data because not in lock
            self._doneevent.set()

    def await(self, timeout=None):
        self._doneevent.wait(timeout)
        if isinstance(self.data, ExecutionFailure):
            self.data.reraise()
        else:
            return self.data

    def cancel(self):
        self.query.cancelled = True

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

    def submit(self, query, callback=None):
        # create an executor with a reference to the FutureQueryResult we will return to the user
        executor = NativeAsyncExecutor(query, FutureQueryResult(query, callback))

        # queue it up
        self.cacheMaster.incoming.put(executor)

        # user can watch it fill
        return executor.future

########################################### TODO: temporary!

# session = StandaloneSession()
# session.metadata.directory = "/home/pivarski/diana/femtocode/tests"

# def callback(outputdataset):
#     print outputdataset, len(list(outputdataset))

# result = session.source("xy").toPython("Test", a = "x + y").submit()

# print result.await()
