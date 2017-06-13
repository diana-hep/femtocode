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

try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.run.compute import Minion
from femtocode.run.cache import CacheMaster
from femtocode.run.cache import NeedWantCache
from femtocode.execution import ExecutionFailure
from femtocode.py23 import *
from femtocode.run.execution import NativeExecutor
from femtocode.server.communication import *
from femtocode.server.mongodb import *

class InProgress(object):
    def __init__(self, metadb):
        self.metadb = metadb
        self.queryToGroupids = {}
        self.lock = threading.Lock()

    def _queryref(self, query):
        return [x for x in self.queryToGroupids if x == query][0]

    def cleanup(self):
        pass  # FIXME (remove cancelled queries)

    def add(self, executor, groupids):
        with self.lock:
            newgroupids = set(groupids)

            if executor.query not in self.queryToGroupids or self._queryref(executor.query).cancelled:
                self.queryToGroupids[executor.query] = newgroupids

                # upgrade the dataset on this query to include group-level information
                dataset = self.metadb.dataset(executor.query.dataset.name, groupids, executor.query.statements.columnNames(), False)
                executor.query.dataset = dataset

            else:
                newgroupids = newgroupids.difference(self.queryToGroupids[executor.query])
                self.queryToGroupids[executor.query].update(newgroupids)

                # make this executor share a reference with the established query so that .cancel affects both
                executor.query = self._queryref(executor.query)

                # get the additional group-level information you don't currently have and add it to the dataset
                if len(newgroupids) > 0:
                    dataset = self.metadb.dataset(executor.query.dataset.name, sorted(newgroupids), executor.query.statements.columnNames(), False)
                    executor.query.dataset.groups.extend(dataset.groups)

            return newgroupids

    def remove(self, executor, groupid):
        with self.lock:
            self.queryToGroupids[executor.query].discard(groupid)
            if len(self.queryToGroupids[executor.query]) == 0:
                del self.queryToGroupids[executor.query]

    def cancel(self, query):
        with self.lock:
            if query in self.queryToGroupids:
                self._queryref(query).cancelled = True

class NativeDistribExecutor(NativeExecutor):
    @staticmethod
    def convert(executor, groupidToUniqueid, inprogress, store):
        executor.__class__ = NativeDistribExecutor
        executor.groupidToUniqueid = groupidToUniqueid
        executor.inprogress = inprogress
        executor.store = store
        
    def __init__(self, query, groupidToUniqueid, inprogress, store):
        super(NativeDistribExecutor, self).__init__(query)
        self.groupidToUniqueid = groupidToUniqueid
        self.inprogress = inprogress
        self.store = store

    def oneLoadDone(self, groupid):
        self.store.setload(self.groupidToUniqueid[groupid])

    def oneComputeDone(self, groupid, computeTime, subtally):
        self.inprogress.remove(self, groupid)
        self.store.setresult(self.groupidToUniqueid[groupid], computeTime, subtally)

    def oneFailure(self, failure):
        self.query.cancelled = True
        self.inprogress.remove(self, groupid)
        self.store.setresult(self.groupidToUniqueid[groupid], 0.0, failure)

class Compute(HTTPServer):
    def __init__(self, metadb, cacheMaster, store):
        self.cacheMaster = cacheMaster
        self.store = store
        self.inprogress = InProgress(metadb)

    def __call__(self, environ, start_response):
        try:
            message = self.getpickle(environ)

            if message is None:
                # just a heartbeat; be sure to respond with None (below)
                self.inprogress.cleanup()

            elif isinstance(message, AssignExecutor):
                # turn the NativeExecutor into a NativeDistribExecutor (in place)
                NativeDistribExecutor.convert(message.executor, message.groupidToUniqueid, self.inprogress, self.store)
                message.executor.query.lock = threading.Lock()

                # either start a new executor or add the new groups to an already-running one
                newgroupids = self.inprogress.add(message.executor, message.groupids)

                # if any of the groups are new, queue them up to get serviced
                if len(newgroupids) > 0:
                    self.cacheMaster.incoming.put(message.executor)
                        
            elif isinstance(message, CancelQuery):
                # ensure that all instances of this query have .cancelled = True
                self.inprogress.cancel(message.query)

            else:
                assert False, "unrecognized message: {0}".format(message)

            return self.sendpickle(None, start_response)

        except Exception as err:
            return self.senderror("500 Internal Server Error", start_response)

if __name__ == "__main__":
    from femtocode.dataset import MetadataFromJson

    metadb = MetadataFromJson("../tests/")
    # metadb = MetadataFromMongoDB("mongodb://localhost:27017", "metadb", "datasets", ROOTDataset, 1.0)

    minion = Minion(queue.Queue())
    minion.start()

    cacheMaster = CacheMaster(NeedWantCache(1024**3), [minion])
    cacheMaster.start()

    store = ResultStore("mongodb://localhost:27017", "store", "queries", "groups", 1.0)

    server = Compute(metadb, cacheMaster, store)
    server.start("", 8081)
