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

from femtocode.run.cache import NeedWantCache
from femtocode.server.messages import *
from femtocode.server.communication import *

class Compute(HTTPInternalProcess):
    experationAfterDone = 60    # a fail-safe against accidental memory leaks: if a query result hasn't been requested in a minute, expire it

    def __init__(self, name, pipe, cacheLimitBytes, metadb):
        super(Compute, self).__init__(name, pipe)

        self.active = {}
        self.expiration = {}
        self.cacheMaster = CacheMaster(NeedWantCache(cacheLimitBytes), self.minions)
        self.metadb = metadb

    def cycle(self):
        message = self.recv()

        if isinstance(message, AssignExecutorGroupids):
            dataset = self.metadb.dataset(message.executor.query.dataset.name, message.groupids, message.executor.query.statements.columnNames(), False)
            executor = NativeComputeExecutor.fromNativeExecutor(message.executor, dataset, message.groupids)

            self.active[executor.query.id] = self.active.get(executor.query.id, []) + [executor]
            self.cacheMaster.incoming.put(executor)

            self.send(None)

        elif isinstance(message, GetResults):
            queryidToAssignment = {}
            queryidToMessages = {}

            for queryid, executors in self.active.items():
                todrop = []
                for i, executor in enumerate(executors):
                    with executor.lock:
                        if executor.query.id in message.queryids:
                            queryidToAssignment[executor.query.id] = queryidToAssignment.get(executor.query.id, []) + executor.groupids
                            queryidToMessages[executor.query.id] = queryidToMessages.get(executor.query.id, []) + executor.messages

                            if executor.done():
                                todrop.append(i)

                        elif executor.done():
                            expirationDate = self.expiration.get(executor.query, time.time())
                            self.expiration[executor.query] = expirationDate

                            if time.time() - expirationDate > self.expirationAfterDone:
                                todrop.append(i)
                                del self.expiration[executor.query]

                while len(todrop) > 0:
                    del executors[todrop.pop()]

            self.send(Results(queryidToAssignment, queryidToMessages))
                    
        elif isinstance(message, CancelQueryById):
            # FIXME

            message.queryid
            
        else:
            assert False, "unrecognized message: {0}".format(message)

        return True

# HTTPInternalServer(Compute, (cacheLimitBytes, MetadataFromJson(".")), timeout)






# class Results(Message):
#     def __init__(self, queryidToAssignment, queryidToMessages):
#         self. = queryidToAssignment
#         self. = queryidToMessages
