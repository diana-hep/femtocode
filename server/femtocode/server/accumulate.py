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
from femtocode.server.cache import RolloverCache
from femtocode.remote import Result

class Tallyman(object):
    def __init__(self, minions, executor, timeout):
        self.minions = minions   # order matters
        self.clients = [HTTPInternalClient(minion, timeout) for minion in self.minions]
        self.executor = executor
        self.minionToGroupids = {}
        self.lock = threading.Lock()

        print "TALLYMAN CONSTRUCT"

    def assign(self, survivors):
        print "TALLYMAN ASSIGN SURVIVORS", survivors, "MINIONS", self.minions

        with self.lock:
            offset = abs(hash(self.executor.query))
            groupids = list(xrange(self.executor.query.dataset.numGroups))
            native = self.executor.toNativeExecutor()

            for minion, client in zip(self.minions, self.clients):
                if minion in survivors:
                    subset = assign(offset, groupids, self.executor.query.dataset.numGroups, minion, self.minions, survivors)

                    if len(subset) > 0 and self.minionToGroupids.get(minion, []) != subset:
                        print "TALLYMAN ASSIGNING", subset

                        client.async(AssignExecutorGroupids(native, subset))
                        # don't care about the result; failures-to-launch will be cleaned up afterward

                    self.minionToGroupids[minion] = subset

                else:
                    self.minionToGroupids[minion] = []

    def cancel(self):
        for client in self.clients:
            client.async(CancelQueryById(self.executor.query.id))

    def result(self):
        print "TALLYMAN RESULT"

        with self.lock:
            return self.executor.result

    def update(self, minionToGroupids, messages):
        print "TALLYMAN UPDATE"

        with self.lock:
            for minion in self.minions:
                # missing = what I think the minion ought to be working on that it doesn't know about
                missing = set(self.minionToGroupids[minion]).difference(set(minionToGroupids[minion]))
                if len(missing) > 0:
                    native = self.executor.toNativeExecutor()
                    client.async(AssignExecutorGroupids(native, sorted(missing)))
                    # don't care about the result; failures-to-launch will be cleaned up afterward

                for message in messages:
                    if isinstance(message, OneLoadDone):
                        self.executor.oneLoadDone(message.groupid)
                    elif isinstance(message, OneComputeDone):
                        self.executor.oneComputeDone(message.groupid, message.computeTime, message.subtally)
                    elif isinstance(message, OneFailure):
                        self.executor.oneFailure(message.failure)

class Assignments(object):
    def __init__(self, minions, timeout):
        self.minions = minions
        self.timeout = timeout

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

    def gettallymans(self):
        with self.lock:
            return list(self.tallymans)

    def dead(self, minion):
        with self.lock:
            if minion in self.survivors:
                self.survivors.discard(minion)
                return self.survivors
            else:
                return None

    def alive(self, minion):
        with self.lock:
            if minion not in self.survivors:
                self.survivors.add(minion)
                return self.survivors
            else:
                return None

    def assign(self, executor):
        with self.lock:
            tallyman = self.tallymans.get(executor.query.id)
            if tallyman is None:
                tallyman = Tallyman(self.minions, executor, self.timeout)
                self.tallymans[executor.query.id] = tallyman

        tallyman.assign(self.survivors)
        return tallyman

class ResultPull(threading.Thread):
    period  = 0.200    # poll for results every 200 ms
    timeout = 1.000    # no response after 1 second means it's dead

    def __init__(self, minion, assignments):
        super(ResultPull, self).__init__()
        self.minion = minion
        self.client = HTTPInternalClient(self.minion, self.timeout)
        self.assignments = assignments
        self.daemon = True
        self.start()   # a self-starter

    def poll(self):
        try:
            results = self.client.sync(GetResults(self.assignments.queryids()))

        except socket.timeout:
            newsurvivors = self.assignments.dead(self.minion)
            if newsurvivors is not None:
                for tallyman in self.assignments.gettallymans():
                    tallyman.assign(newsurvivors)

            print "TIMEOUT", newsurvivors

        except HTTPError as err:
            print(err.read())   # TODO: send compute error to log
            raise

        else:
            if isinstance(results, ExecutionFailure):
                results.reraise()

            self.assignments.alive(self.minion)

            print "MINION ALIVE", self.minion
            print "queryidToAssignment", list(results.queryidToAssignment.keys())
            print "queryidToMessages", list(results.queryidToMessages.keys())

            for queryid, assignment in results.queryidToAssignment.items():
                messages = results.queryidToMessages[queryid]   # asserting this structure

                tallyman = self.assignments.tallyman(queryid)

                print "assignment", assignment
                print "messages", messages
                print "tallyman", tallyman

                if tallyman is not None:
                    tallyman.update(assignment, messages)
                else:
                    self.client.sync(CancelQueryById(queryid))

    def run(self):
        while True:
            self.poll()
            time.sleep(self.period)

class Accumulate(HTTPInternalProcess):
    def __init__(self, name, pipe, minions, timeout, cacheDirectory, partitionMarginBytes, rolloverTime, gcTime, idchars):
        super(Accumulate, self).__init__(name, pipe)

        self.assignments = Assignments(minions, timeout)
        self.resultPulls = [ResultPull(minion, self.assignments) for minion in minions]
        
        if not os.path.exists(cacheDirectory):
            os.mkdir(cacheDirectory)
        assert os.path.isdir(cacheDirectory)

        myCacheDirectory = os.path.join(cacheDirectory, name)
        if not os.path.exists(myCacheDirectory):
            os.mkdir(myCacheDirectory)

        self.cache = RolloverCache(myCacheDirectory, partitionMarginBytes, rolloverTime, gcTime, idchars)

    def initialize(self):
        # start with a fresh list of self.assignments.survivors
        for resultPull in self.resultPulls:
            resultPull.poll()

    def cycle(self):
        message = self.recv()

        if isinstance(message, GetQueryById):
            if self.assignments.has(message.queryid) or self.cache.has(message.queryid):
                self.send(HaveIdPleaseSendQuery())
            else:
                self.send(DontHaveQuery())

        elif isinstance(message, GetQuery):
            tallyman = self.assignments.tallyman(message.query.id)
            if tallyman is not None:
                self.send(tallyman.result())
            else:
                result = self.cache.get(message.query)
                if result is not None:
                    self.send(result)
                else:
                    self.send(DontHaveQuery())

        elif isinstance(message, AssignExecutor):
            tallyman = self.assignments.assign(message.executor)
            self.send(tallyman.result())

        elif isinstance(message, CancelQuery):
            tallyman = self.assignments.tallyman(message.query.id)
            if tallyman is not None:
                tallyman.cancel()
            self.send(None)

        else:
            assert False, "unrecognized message: {0}".format(message)

        return True

if __name__ == "__main__":
    server = HTTPInternalServer(Accumulate, (["http://localhost:8082/bob"], 1.0, "/tmp/downloads/cache", 100*1024**2, 60*60*24, 60, 8,), 1.0)
    server.start("", 8081)
