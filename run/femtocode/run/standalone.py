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
from femtocode.execution import ExecutionFailure
from femtocode.numpyio.dataset import NumpyDataset
from femtocode.py23 import *
from femtocode.run.cache import *
from femtocode.run.compute import *
from femtocode.run.execution import *
from femtocode.util import *
from femtocode.workflow import Source

class FutureQueryResult(object):
    class OnDone(threading.Thread):
        def __init__(self, fcn):
            super(FutureQueryResult.OnDone, self).__init__()
            self.incoming = queue.Queue()
            self.fcn = fcn
            self.daemon = False   # why this is a thread: don't let Python exit until the callback is done!

        def run(self):
            data = self.incoming.get()
            if isinstance(data, ExecutionFailure):
                data.reraise()
            else:
                self.fcn(data)

    def __init__(self, query, ondone, onupdate):
        self.query = query

        self.loaded = 0.0
        self.computed = 0.0
        self.done = False
        self.wallTime = 0.0
        self.computeTime = 0.0
        self.data = None
        self._lock = threading.Lock()

        if ondone is not None:
            self._ondone = FutureQueryResult.OnDone(ondone)
            self._ondone.start()
        else:
            self._ondone = None
        self._onupdate = onupdate
        self._doneevent = threading.Event()

    def __repr__(self):
        return "<FutureQueryResult {0}% loaded {1}% computed{2}>".format(roundup(self.loaded * 100), roundup(self.computed * 100), " (wall: {0:.2g} sec, cpu: {1:.2g} core-sec)".format(self.wallTime, self.computeTime) if self.done else "")

    def _update(self, loaded, computed, done, wallTime, computeTime, data):
        with self._lock:
            self.loaded = loaded
            self.computed = computed
            self.done = done
            self.wallTime = wallTime
            self.computeTime = computeTime
            self.data = data

        if self._onupdate is not None:
            self._onupdate(data)                 # not self.data because not in lock

        if done:
            if self._ondone is not None:
                self._ondone.incoming.put(data)  # not self.data because not in lock
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
                 metadata=MetadataFromJson(".")):

        minionsIncoming = queue.Queue()
        self.minions = [Minion(minionsIncoming) for i in range(numMinions)]
        self.cacheMaster = CacheMaster(NeedWantCache(cacheLimitBytes), self.minions)
        self.metadata = metadata

        for minion in self.minions:
            minion.start()
        self.cacheMaster.start()

    def source(self, name):
        return Source(self, self.metadata.dataset(name).strip())

    def submit(self, query, ondone=None, onupdate=None, debug=False):
        # attach a more detailed Dataset to the query (same content, but with runtime details)
        query.dataset = self.metadata.dataset(query.dataset.name, list(xrange(query.dataset.numGroups)), query.statements.columnNames(), False)

        # create an executor with a reference to the FutureQueryResult we will return to the user
        query.lock = threading.Lock()
        executor = NativeAsyncExecutor(query, FutureQueryResult(query, ondone, onupdate), debug)

        # queue it up
        self.cacheMaster.incoming.put(executor)

        # user can watch it fill
        return executor.future

########################################### TODO: temporary!

if __name__ == "__main__":
    session = StandaloneSession()
    session.metadata.directory = "/home/pivarski/diana/femtocode/tests"

    def callback(outputdataset):
        print outputdataset, len(list(outputdataset))

    result = session.source("xy").define(z = "x + y").toPython(a = "z - 3", b = "z - 0.5").submit()

    for event in result.await():
        print event
