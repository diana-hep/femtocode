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
from femtocode.workflow import Message
from femtocode.workflow import Query

class GaboClient(threading.Thread):
    listenThreshold = 0.030     # 30 ms      no response from the minion; reset ZMQClient recv/send state

    def __init__(self, minionaddr):
        super(GaboClient, self).__init__()
        self.minionaddr = minionaddr
        self.client = ZMQClient(self.minionaddr, self.listenThreshold)
        self.incoming = queue.Queue()
        self.failures = queue.Queue()
        self.daemon = True

    def run(self):
        while True:
            query = self.incoming.get()
            self.client.send(query)

            if self.client.recv() is None:
                self.client = ZMQClient(self.minionaddr, self.listenThreshold)
                self.failures.put(query.groupids)
            else:
                self.failures.put([])

class GaboClients(object):
    def __init__(self, minionaddrs):
        self.minionaddrs = minionaddrs
        self.clients = [GaboClient(minionaddr) for minionaddr in self.minionaddrs]
        for client in self.clients:
            client.start()

    def sendQuery(self, query):
        for i, client in enumerate(self.clients):
            if not client.isAlive():
                self.clients[i] = GaboClient(client.minionaddr)
                self.clients[i].start()

        offset = query.queryid
        groupids = query.groupids
        numGroups = len(query.groupids)
        workers = self.minionaddrs
        survivors = set(self.minionaddrs)   # start each query optimistically

        while len(groupids) > 0:
            if len(survivors) == 0:
                raise IOError("cannot send query; no surviving workers")

            activeclients = []
            for client in self.clients:
                subquery = query.copy()
                subquery.groupids = assign(offset, groupids, numGroups, client.minionaddr, workers, survivors)
                if len(subquery.groupids) > 0:
                    client.incoming.put(subquery)
                    activeclients.append(client)

            groupids = []
            for client in activeclients:
                failures = client.failures.get()
                if len(failures) > 0:
                    survivors.discard(client.minionaddr)
                    groupids.extend(failures)

class Result(Message):
    def __init__(self, loadsDone, computesDone, done, wallTime, computeTime, lastUpdate, data):
        self.loadsDone = loadsDone
        self.computesDone = computesDone
        self.done = done
        self.wallTime = wallTime
        self.computeTime = computeTime
        self.lastUpdate = lastUpdate
        self.data = data

    def __repr__(self):
        return "Result({0}, {1}, {2}, {3}, {4}, {5}, {6})".format(self.loadsDone, self.computesDone, self.done, self.wallTime, self.computeTime, self.lastUpdate, self.data)

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "loadsDone": self.loadsDone,
                "computesDone": self.computesDone,
                "done": self.done,
                "wallTime": self.wallTime,
                "computeTime": self.computeTime,
                "lastUpdate": self.lastUpdate,
                "data": self.data.toJson()}

    @staticmethod
    def fromJson(obj):
        return Result(obj["loadsDone"],
                      obj["computesDone"],
                      obj["done"],
                      obj["wallTime"],
                      obj["computeTime"],
                      obj["lastUpdate"],
                      obj["data"])

class StatusUpdate(Message):
    def __init__(self, load):
        self.load = load

    def __repr__(self):
        return "StatusUpdate({0})".format(self.load)

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "load": load}

    @staticmethod
    def fromJson(self):
        return StatusUpdate(obj["load"])

class AccumulateAPIServer(HTTPServer):
    def __init__(self, rolloverCache, bigdataCache, gabos, bindaddr="", bindport=8080):
        self.rolloverCache = rolloverCache
        self.bigdataCache = bigdataCache
        self.gabos = gabos
        self.bindaddr = bindaddr
        self.bindport = bindport

    def __call__(self, environ, start_response):
        try:
            message = Message.fromJson(self.getjson(environ))

            if isinstance(message, Query):
                if message.id in self.rolloverCache:
                    return self.sendjson(self.rolloverCache.current(message).toJson())

                elif message.id in self.bigdataCache:
                    return self.sendjson(self.bigdataCache.current(message).toJson())

            elif 
            



    # def __init__(self, metadb, bindaddr="", bindport=8080):
    #     self.metadb = metadb
    #     self.bindaddr = bindaddr
    #     self.bindport = bindport

    # def __call__(self, environ, start_response):
    #     try:
    #         obj = self.getjson(environ)
    #         name = obj["name"]
    #         assert isinstance(name, string_types)

    #     except:
    #         return self.senderror("400 Bad Request", start_response)

    #     else:
    #         try:
    #             dataset = self.metadb.dataset(name, (), None, True)
    #         except:
    #             return self.senderror("500 Internal Server Error", start_response)
    #         else:
    #             return self.sendjson(dataset.toJson(), start_response)

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