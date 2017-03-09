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

from femtocode.scope.assignment import *
from femtocode.scope.communication import *
from femtocode.run.messages import *

class GaboClient(threading.Thread):
    listenThreshold = 0.030     # 30 ms      no response from the minion; reset Client recv/send state

    def __init__(self, minionaddr):
        super(GaboClient, self).__init__()
        self.minionaddr = minionaddr
        self.client = Client(self.minionaddr, self.listenThreshold)
        self.incoming = queue.Queue()
        self.failures = queue.Queue()
        self.daemon = True

    def run(self):
        while True:
            query = self.incoming.get()
            self.client.send(query)

            if self.client.recv() is None:
                self.client = Client(self.minionaddr, self.listenThreshold)
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

########################################### TODO: temporary!

import sys

gaboClients = GaboClients(["tcp://localhost:5556"])

for i in range(1000):
    print("submit {}!".format(i))
    try:
        gaboClients.sendQuery(CompiledQuery("retaddr", i, "MuOnia", ["muons[]-pt", "jets[]-pt"], [0]))
    except IOError:
        print("oops")

time.sleep(5)

for i in range(1000):
    print("submit {}!".format(i))
    try:
        gaboClients.sendQuery(CompiledQuery("retaddr", i, "MuOnia", ["muons[]-pt", "jets[]-pt"], [0]))
    except IOError:
        print("oops")

###########################################
