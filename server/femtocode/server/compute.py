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

import time
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.run.cache import CacheMaster
from femtocode.run.cache import NeedWantCache
from femtocode.run.compute import Minion
from femtocode.server.communication import *
from femtocode.server.messages import *
from femtocode.server.execution import NativeComputeExecutor

class Compute(HTTPInternalProcess):
    experationAfterDone = 60    # a fail-safe against accidental memory leaks: if a query result hasn't been requested in a minute, expire it

    def __init__(self, name, pipe, cacheLimitBytes, metadb):
        super(Compute, self).__init__(name, pipe)

        self.minion = Minion(queue.Queue())

        self.active = {}
        self.expiration = {}
        self.cacheMaster = CacheMaster(NeedWantCache(cacheLimitBytes), [self.minion])
        self.metadb = metadb

    def cycle(self):
        message = self.recv()

        if isinstance(message, AssignExecutorGroupids):
            dataset = self.metadb.dataset(message.executor.query.dataset.name, message.groupids, message.executor.query.statements.columnNames(), False)
            executor = NativeComputeExecutor.fromNativeExecutor(message.executor, dataset, message.groupids)
            # HERE: the problem is that the executor's lock is engaged, but I don't
            # see any calls to its methods that would set the lock.

            self.active[executor.query.id] = self.active.get(executor.query.id, []) + [executor]
            self.cacheMaster.incoming.put(executor)
            self.send(None)

        elif isinstance(message, GetResults):
            try:
                queryidToAssignment = {}
                queryidToMessages = {}

                print "ONE", self.active

                for queryid, executors in self.active.items():
                    todrop = []
                    print "TWO", executors

                    for i, executor in enumerate(executors):
                        print "THREE", executor

                        with executor.lock:
                            print "FOUR", executor.query.id in message.queryids

                            if executor.query.id in message.queryids:
                                print "FIVE"

                                queryidToAssignment[executor.query.id] = queryidToAssignment.get(executor.query.id, []) + executor.groupids

                                print "SIX", queryidToAssignment[executor.query.id]

                                queryidToMessages[executor.query.id] = queryidToMessages.get(executor.query.id, []) + executor.messages

                                print "SEVEN", queryidToMessages[executor.query.id]

                                if executor.done():
                                    todrop.append(i)

                            elif executor.done():
                                print "EIGHT"

                                expirationDate = self.expiration.get(executor.query, time.time())
                                self.expiration[executor.query] = expirationDate

                                if time.time() - expirationDate > self.expirationAfterDone:
                                    todrop.append(i)
                                    del self.expiration[executor.query]

                                print "NINE"

                    print "TEN", todrop

                    while len(todrop) > 0:
                        del executors[todrop.pop()]

                    print "ELEVEN"

                print "GET RESULTS", queryidToAssignment, queryidToMessages

                self.send(Results(queryidToAssignment, queryidToMessages))

            except Exception as err:
                import traceback
                import sys
                print "".join(traceback.format_exception(err.__class__, err, sys.exc_info()[2]))
                raise
                    
        elif isinstance(message, CancelQueryById):
            try:
                executor = self.active.pop(message.queryid)
            except KeyError:
                pass
            else:
                executor.cancel()
            
        else:
            assert False, "unrecognized message: {0}".format(message)

        return True

if __name__ == "__main__":
    from femtocode.dataset import MetadataFromJson
    server = HTTPInternalServer(Compute, (1024**3, MetadataFromJson("/home/pivarski/diana/femtocode/tests/")), 1.0)
    server.start("", 8082)
