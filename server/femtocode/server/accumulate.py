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

import os
import os.path
import time
import threading
import socket

from femtocode.server.assignment import assign
from femtocode.server.messages import *
from femtocode.server.communication import *
from femtocode.remote import ResultMessage

class Tallyman(object):
    def __init__(self, minions, executor):
        self.minions = minions   # order matters
        self.clients = [HTTPInternalClient(minion, self.timeout) for minion in self.minions]
        self.executor = executor
        self.minionToGroupids = {}
        self.lock = threading.Lock()
    
    def assign(self, survivors, groupids):
        with self.lock:
            offset = abs(hash(self.executor.query))

            for minion, client in zip(self.minions, self.clients):
                subset = assign(offset, groupids, self.executor.query.dataset.numGroups, minion, self.minions, survivors)
                self.minionToGroupids[minion] = subset

                if len(subset) > 0:
                    subexec = self.executor.toCompute(subset)
                    client.async(AssignExecutorGroupids(subexec))
                    # don't care about the result; failures will be cleaned up later
                    
    def cancel(self):
        for client in self.clients:
            client.async(CancelQueryById(self.executor.query.id))

    def result(self):
        with self.lock:
            return self.executor.result

    def update(self, minionToGroupids, messages):
        with self.lock:
            for minion in self.minions:
                # missing = what I think the minion ought to be working on that it doesn't know about
                missing = set(self.minionToGroupids[minion]).difference(set(minionToGroupids[minion]))
                if len(missing) > 0:
                    subexec = self.executor.toCompute(sorted(missing))
                    client.async(AssignExecutorGroupids(subexec))

                for message in messages:
                    if isinstance(message, OneLoadDone):
                        self.executor.oneLoadDone(message.groupid)
                    elif isinstance(message, OneComputeDone):
                        self.executor.oneComputeDone(message.groupid, message.computeTime, message.subtally)
                    elif isinstance(message, OneFailure):
                        self.executor.oneFailure(message.failure)

class Assignments(object):
    def __init__(self, minions):
        self.minions = minions
        self.survivors = set()
        self.tallymans = {}
        self.lock = threading.Lock()

    def has(self, queryid):
        with self.lock:
            return queryid in self.tallymans

    def queryids(self):
        with self.lock:
            return list(self.tallymans)

    def tallyman(self, queryid):
        with self.lock:
            return self.tallymans.get(queryid)

    def dead(self, minion):
        with self.lock:
            self.survivors.discard(minion)

    def alive(self, minion):
        with self.lock:
            self.survivors.add(minion)

    def assign(self, executor):
        with self.lock:
            tallyman = self.tallymans.get(executor.query.id)
            if tallyman is None:
                tallyman = Tallyman(self.minions, executor)
                tallyman.assign(self.survivors, list(xrange(executor.query.dataset.numGroups)))
                self.tallymans[executor.query.id] = tallyman
            return tallyman

class ResultPull(threading.Thread):
    period  = 0.200    # poll for results every 200 ms
    timeout = 1.000    # no response after 1 second means it's dead

    def __init__(self, minion, assignments):
        super(HeartbeatMonitor, self).__init__()
        self.minion = minion
        self.client = HTTPInternalClient(self.minion, self.timeout)
        self.assignments = assignments
        self.daemon = True
        self.start()   # a self-starter

    def run(self):
        while True:
            try:
                results = self.client.sync(GetResults(self.assignments.queryids()))
            except socket.timeout:
                self.assignments.dead(self.minion)
            else:
                self.assignments.alive(self.minion)

                for queryid, assignment in results.queryidToAssignment.items():
                    messages = results.queryidToMessages[queryid]   # asserting this structure

                    tallyman = self.assignments.tallymans.get(queryid)
                    if tallyman is not None:
                        tallyman.update(assignment, messages)
                    else:
                        self.client.sync(CancelQueryById(queryid))
                        
            time.sleep(self.period)

class Accumulate(HTTPInternalProcess):
    def __init__(self, name, pipe, minions, cacheDirectory, partitionMarginBytes, rolloverTime, gcTime, idchars):
        super(Accumulate, self).__init__(name, pipe)

        self.assignments = Assignments(minions)
        self.resultPulls = [ResultPull(minion, self.assignments) for minion in minions]

        if not os.path.exists(cacheDirectory):
            os.mkdir(cacheDirectory)
        assert os.path.isdir(cacheDirectory)

        myCacheDirectory = os.path.join(cacheDirectory, name)
        if not os.path.exists(myCacheDirectory):
            os.mkdir(myCacheDirectory)

        self.cache = RolloverCache(myCacheDirectory, partitionMarginBytes, rolloverTime, gcTime, idchars)

    def cycle(self):
        message = self.recv()

        if isinstance(message, GetQueryById):
            if self.assignments.has(message.queryid) or self.cache.has(message.queryid):
                self.send(HaveIdPleaseSendQuery())
            else:
                self.send(DontHaveQuery())

        elif isinstance(message, GetQuery):
            tallyman = self.assignments.get(message.query.id)
            if tallyman is not None:
                self.send(Result(tallyman.result()))
            else:
                result = self.cache.get(message.query)
                if result is not None:
                    self.send(Result(result))
                else:
                    self.send(DontHaveQuery())

        elif isinstance(message, AssignExecutor):
            tallyman = self.assignments.assign(message.executor)
            self.send(tallyman.result())

        elif isinstance(message, CancelQuery):
            tallyman = self.assignments.get(message.query.id)
            if tallyman is not None:
                tallyman.cancel()
            self.send(None)

        else:
            assert False, "unrecognized message: {0}".format(message)

        return True

# HTTPInternalServer(Accumulate, (minions, cacheDirectory, partitionMarginBytes, rolloverTime, gcTime, idchars,), timeout)
