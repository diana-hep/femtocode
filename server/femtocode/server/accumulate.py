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

from femtocode.server.messages import *
from femtocode.server.communication import *
from femtocode.remote import ResultMessage

class Tallyman(object):
    def __init__(self, minions, executor):
        self.minions = minions
        self.executor = executor
        self.assignments = {}
        self.lock = threading.Lock()

    def update(self, groupidToChange):
        with self.lock:
            pass

class Assignments(object):
    def __init__(self, minions):
        self.minions = minions
        self.survivors = set()
        self.tallymans = {}
        self.lock = threading.Lock()

    def queryids(self):
        pass

    def dead(self, minion):
        with self.lock:
            self.survivors.discard(minion)

    def alive(self, minion):
        with self.lock:
            self.survivors.add(minion)

class ResultPull(threading.Thread):
    period  = 0.030    # poll for results every 30 ms
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

                for queryid, groupidToChange in results.queryToGroupids.items():
                    tallyman = self.assignments.tallymans.get(queryid)
                    if tallyman is not None:
                        tallyman.update(groupidToChange)
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

        myCacheDirectory = os.path.join(cacheDirectory, name)
        if not os.path.exists(myCacheDirectory):
            os.mkdir(myCacheDirectory)

        self.cache = RolloverCache(myCacheDirectory, partitionMarginBytes, rolloverTime, gcTime, idchars)

    def cycle(self):
        message = self.recv()

        if isinstance(message, GetQueryById):
            pass

        elif isinstance(message, GetQuery):
            pass

        elif isinstance(message, AssignExecutor):
            pass

        elif isinstance(message, CancelQuery):
            pass

        self.send(obj)

        return True

# HTTPInternalServer(Accumulate, (minions, cacheDirectory, partitionMarginBytes, rolloverTime, gcTime, idchars,), timeout)
