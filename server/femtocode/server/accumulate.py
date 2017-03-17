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

import threading
import time
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.dataset import MetadataFromJson
from femtocode.server.assignment import *
from femtocode.server.communication import *
from femtocode.workflow import Query
from femtocode.server.execution import Result

class SubmitStatus(object):
    def __init__(self, minionaddr, success):
        self.minionaddr = minionaddr
        self.success = success

class MinionDied(object):
    def __init__(self, minionaddr):
        self.minionaddr = minionaddr

class QueryDone(object): pass

class RunningQueries(object):      # a tallyman for each running query; has a lock to ensure synchronized access to the dictionary
    def __init__(self):
        self.tallymen = {}
        self.lock = threading.Lock()

    def get(self, query):
        with self.lock:
            return self.tallymen.get(query)

    def load(self):
        with self.lock:
            return len(self.tallymen)

    def startTallyman(self, tallyman):
        with self.lock:
            self.tallymen[tallyman.executor.query] = tallyman
        tallyman.start()

    def submitStatus(self, query, minionaddr, success):
        with self.lock:
            self.tallymen[query].events.put(SubmitStatus(minionaddr, success))

    def minionDied(self, minionaddr):
        with self.lock:
            for tallyman in self.tallymen.values():
                tallyman.events.put(MinionDied(minionaddr))

    def queryDone(self, query):
        with self.lock:
            self.tallymen[query].events.put(QueryDone())
            if query in self.tallymen:
                del self.tallymen[query]

# FIXME: heartbeats are gone and I need to replace them with something

class GaboClient(threading.Thread):
    listenThreshold = 0.030     # 30 ms      no response from the minion; reset ZMQClient recv/send state

    def __init__(self, minionaddr, runningQueries):
        super(GaboClient, self).__init__()
        self.minionaddr = minionaddr

        self.client = ZMQClient(self.minionaddr, self.listenThreshold)
        self.incoming = queue.Queue()
        self.runningQueries = runningQueries
        self.daemon = True

    def run(self):
        while True:
            subexec = self.incoming.get()
            self.client.send(subexec)

            # always return a SubmitStatus: success or failure
            success = self.client.recv() is not None
            self.runningQueries.submitStatus(subexec.query, self.minionaddr, success)

class Tallyman(threading.Thread):                                  # watches and accumulates results for just one query
    def __init__(self, gabos, executor, retaddr, rolloverCache):
        super(Tallyman, self).__init__()
        self.gabos = gabos
        self.executor = executor
        self.retaddr = retaddr
        self.rolloverCache = rolloverCache

        self.events = queue.Queue()
        self.daemon = True

    def assign(self, groupids):
        if len(self.survivors) == 0:
            raise IOError("cannot send query; no surviving workers")

        activeclients = []
        for gabo in self.gabos:
            subset = assign(offset, groupids, executor.query.numGroups, gabo.minionaddr, self.minionaddrs, survivors)

            if len(subset) > 0:
                subexec = self.executor.toCompute(subset, self.retaddr)
                self.assignment[gabo.minionaddr] = subset
                gabo.incoming.put(subexec)
                activeclients.append(gabo)

    def run(self):
        self.offset = hash(self.executor.query)
        self.survivors = set(gabo.minionaddr for gabo in self.gabos)   # start each query optimistically
        self.assignment = {}

        # first assignment of work
        self.assign(list(range(self.executor.query.numGroups)))

        while True:
            event = self.events.get()

            if isinstance(event, SubmitStatus):
                # every submission generates a SubmitStatus event; either success or failure
                if not event.success:
                    # mark this minion as dead
                    self.survivors.discard(event.minionaddr)
                    # reassign them
                    self.assign(self.assignment.pop(event.minionaddr))

            elif isinstance(event, MinionDied):
                # same issue, but this happened later in the processing of the query (and therefore won't always raise an event)
                self.survivors.discard(event.minionaddr)
                self.assign(self.assignment.pop(event.minionaddr))
                
            elif isinstance(event, QueryDone):
                break  # done!

        # done! put it in disk cache for future generations
        if self.rolloverCache is not None and not isinstance(self.executor.result, ExecutionFailure):
            self.rolloverCache.put(self.executor.query, self.executor.result)

class StatusUpdate(object):
    def __init__(self, load):
        self.load = load

class Foreman(object):
    def __init__(self, retaddr, minionaddrs, rolloverCache, heartbeatTimeout):   # FIXME: implement heartbeatTimeout
        self.retaddr = retaddr

        self.runningQueries = RunningQueries()
        self.rolloverCache = rolloverCache

        self.gabos = [GaboClient(minionaddr, self.runningQueries) for minionaddr in minionaddrs]
        for gabo in self.gabos:
            gabo.start()

    def result(self, query):
        # maybe it's running; if so, give them that
        tallyman = self.runningQueries.get(query)
        if tallyman is not None:
            return tallyman.executor.result

        # maybe it's done and on disk; if so, give them that
        if self.rolloverCache is None:
            result = None
        else:
            result = self.rolloverCache.get(query)  # returns None if not found

        if result is not None:
            return result
        else:
            # nope: just tell them our load
            return StatusUpdate(self.runningQueries.load())

    def assign(self, executor):
        self.runningQueries.startTallyman(Tallyman(self.gabos, executor, self.retaddr, self.rolloverCache))

    def oneLoadDone(self, query, groupid):
        tallyman = self.runningQueries.get(query)
        if tallyman is not None:
            tallyman.executor.oneLoadDone(groupid)
            return True
        else:
            return False

    def oneComputeDone(self, query, groupid, computeTime, subtally):
        tallyman = self.runningQueries.get(query)
        if tallyman is not None:
            tallyman.executor.oneComputeDone(groupid, computeTime, subtally)
            if tallyman.executor.result.done:
                self.runningQueries.queryDone(query)
            return True
        else:
            return False

    def oneFailure(self, query, failure):
        tallyman = self.runningQueries.get(query)
        if tallyman is not None:
            tallyman.executor.oneFailure(failure)
            self.runningQueries.queryDone(query)
            return True
        else:
            return False

class Assign(object):
    def __init__(self, executor):
        self.executor = executor

class OneLoadDone(object):
    def __init__(self, query, groupid):
        self.query = query
        self.groupid = groupid

class OneComputeDone(object):
    def __init__(self, query, groupid, computeTime, subtally):
        self.query = query
        self.groupid = groupid
        self.computeTime = computeTime
        self.subtally = subtally

class OneFailure(object):
    def __init__(self, query, failure):
        self.query = query
        self.failure = failure

class ForemanServer(threading.Thread):
    def __init__(self, foreman, bindaddr):
        super(ForemanServer, self).__init__()
        self.foreman = foreman
        self.server = ZMQServer(bindaddr)
        self.daemon = True

    def run(self):
        while True:
            message = self.server.recv()

            try:
                if isinstance(message, (int, long)):
                    if message in self.foreman.rolloverCache:
                        response = SendWholeQuery(message)

                elif isinstance(message, Query):
                    response = self.foreman.result(message)

                elif isinstance(message, Assign):
                    response = self.foreman.assign(message.executor)

                elif isinstance(message, OneLoadDone):
                    response = self.foreman.oneLoadDone(message.query, message.groupid)

                elif isinstance(message, OneComputeDone):
                    response = self.foreman.oneComputeDone(message.query, message.groupid, message.computeTime, message.subtally)

                elif isinstance(message, OneFailure):
                    response = self.foreman.oneFailure(message.query, message.failure)

                else:
                    response = None
                    
            except:
                self.server.send(None)
                raise

            else:
                self.server.send(response)

class ForemanClient(Foreman):
    def __init__(self, connaddr, timeout):
        self.client = ZMQClient(connaddr, timeout)

    def result(self, query):
        self.client.send(query)
        result = self.client.recv()

        if isinstance(result, (Result, StatusUpdate)):
            return result

        elif result is None:
            return result      # timeout; dispatch will ignore this foreman

        else:
            assert False, "unexpected result: {0}".format(result)

    def assign(self, executor):
        self.client.send(executor)
        result = self.client.recv()
        assert isinstance(result, Result), "unexpected response from assign: {0}".format(result)

    def oneLoadDone(self, query, groupid):
        self.client.send(OneLoadDone(query, groupid))
        return self.client.recv()

    def oneComputeDone(self, query, groupid, computeTime, subtally):
        self.client.send(OneComputeDone(query, groupid, computeTime, subtally))
        return self.client.recv()

    def oneFailure(self, query, failure):
        self.client.send(OneFailure(query, failure))
        return self.client.recv()
