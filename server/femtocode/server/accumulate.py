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

from femtocode.server.assignment import *
from femtocode.server.communication import *
from femtocode.workflow import Query

# class GaboClient(threading.Thread):
#     listenThreshold = 0.030     # 30 ms      no response from the minion; reset ZMQClient recv/send state

#     def __init__(self, minionaddr):
#         super(GaboClient, self).__init__()
#         self.minionaddr = minionaddr
#         self.client = ZMQClient(self.minionaddr, self.listenThreshold)
#         self.incoming = queue.Queue()
#         self.failures = queue.Queue()
#         self.daemon = True

#     def run(self):
#         while True:
#             query = self.incoming.get()
#             self.client.send(query)

#             if self.client.recv() is None:
#                 self.client = ZMQClient(self.minionaddr, self.listenThreshold)
#                 self.failures.put(query.groupids)
#             else:
#                 self.failures.put([])

# class GaboClients(object):
#     def __init__(self, minionaddrs):
#         self.minionaddrs = minionaddrs
#         self.clients = [GaboClient(minionaddr) for minionaddr in self.minionaddrs]
#         for client in self.clients:
#             client.start()

#     def sendQuery(self, query):
#         for i, client in enumerate(self.clients):
#             if not client.isAlive():
#                 self.clients[i] = GaboClient(client.minionaddr)
#                 self.clients[i].start()

#         offset = query.queryid
#         groupids = query.groupids
#         numGroups = len(query.groupids)
#         workers = self.minionaddrs
#         survivors = set(self.minionaddrs)   # start each query optimistically

#         while len(groupids) > 0:
#             if len(survivors) == 0:
#                 raise IOError("cannot send query; no surviving workers")

#             activeclients = []
#             for client in self.clients:
#                 subquery = query.copy()
#                 subquery.groupids = assign(offset, groupids, numGroups, client.minionaddr, workers, survivors)
#                 if len(subquery.groupids) > 0:
#                     client.incoming.put(subquery)
#                     activeclients.append(client)

#             groupids = []
#             for client in activeclients:
#                 failures = client.failures.get()
#                 if len(failures) > 0:
#                     survivors.discard(client.minionaddr)
#                     groupids.extend(failures)

class StatusUpdate(object):
    def __init__(self, load):
        self.load = load

class Tallyman(object):
    def __init__(self, rolloverCache, gabos):
        self.rolloverCache = rolloverCache
        self.gabos = gabos

    def result(self, query):
        if query in self.rolloverCache:
            return self.rolloverCache.result(query)

        else:
            return StatusUpdate(self.rolloverCache.load())

    def assign(self, query):
        return self.rolloverCache.assign(query)

    def oneLoadDone(self, groupid):
        raise NotImplementedError  # FIXME

    def oneComputeDone(self, groupid, computeTime, subtally):
        raise NotImplementedError  # FIXME

    def oneFailure(self, failure):
        raise NotImplementedError  # FIXME

class Assign(object):
    def __init__(self, query):
        self.query = query

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

class TallymanServer(threading.Thread):
    def __init__(self, tallyman, bindaddr, timeout):
        self.tallyman = tallyman
        self.server = ZMQServer(bindaddr, timeout)
        self.daemon = True

    def run(self):
        while True:
            message = self.server.recv()

            if isinstance(message, (int, long)):
                if message in self.tallyman.rolloverCache:
                    self.server.send(SendWholeQuery(message))

            elif isinstance(message, Query):
                self.server.send(self.tallyman.result(message))

            elif isinstance(message, Assign):
                self.server.send(self.tallyman.assign(message.query))

            else:
                self.server.send(None)

class TallymanClient(Tallyman):
    def __init__(self, connaddr, timeout):
        self.client = ZMQClient(connaddr, timeout)

    def result(self, query):
        self.client.send(query.id)
        result = self.client.recv()

        if isinstance(result, SendWholeQuery):
            self.client.send(query)
            return self.client.recv()

        elif isinstance(result, (Result, StatusUpdate)):
            return result

        elif result is None:
            return result      # timeout; dispatch will ignore this tallyman

        else:
            assert False, "unexpected result: {0}".format(result)

    def assign(self, query):
        self.client.send(query)
        result = self.client.recv()
        assert isinstance(result, Result), "unexpected response from assign: {0}".format(result)

    def oneLoadDone(self, query, groupid):
        self.client.send(OneLoadDone(query.id, groupid))
        response = self.client.recv()

        if isinstance(response, SendWholeQuery):
            self.client.send(OneLoadDone(query, groupid))
            return self.client.recv()
        else:
            return response

    def oneComputeDone(self, query, groupid, computeTime, subtally):
        self.client.send(OneComputeDone(query.id, groupid, computeTime, subtally))
        response = self.client.recv()

        if isinstance(response, SendWholeQuery):
            self.client.send(OneComputeDone(query, groupid, computeTime, subtally))
            return self.client.recv()
        else:
            return response

    def oneFailure(self, query, failure):
        self.client.send(OneFailure(query.id, failure))
        response = self.client.recv()

        if isinstance(response, SendWholeQuery):
            self.client.send(OneFailure(query, failure))
            return self.client.recv()
        else:
            return response


########################################### TODO: temporary!






########################################### TODO: temporary!

# import sys

# gaboClients = GaboClients(["tcp://localhost:5556"])

# for i in range(1000):
#     print("submit {}!".format(i))
#     try:
#         gaboClients.sendQuery(CompiledQuery("retaddr", i, "MuOnia", ["muons[]-pt", "jets[]-pt"], [0]))
#     except IOError:
#         print("oops")

# time.sleep(5)

# for i in range(1000):
#     print("submit {}!".format(i))
#     try:
#         gaboClients.sendQuery(CompiledQuery("retaddr", i, "MuOnia", ["muons[]-pt", "jets[]-pt"], [0]))
#     except IOError:
#         print("oops")
