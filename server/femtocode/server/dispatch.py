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
import threading

import femtocode.asts.statementlist as statementlist
from femtocode.py23 import *
from femtocode.execution import ExecutionFailure
from femtocode.server.assignment import assign
from femtocode.server.communication import *

class Watchman(threading.Thread):
    def __init__(self, minions, checkperiod, deadthreshold):
        super(Watchman, self).__init__()
        self.minions = minions
        self.checkperiod = checkperiod
        self.deadthreshold = deadthreshold

        self.lock = threading.Lock()
        self.survivors = set(minions)
        self.daemon = True

    def declaredead(self, minion):
        with self.lock:
            self.survivors.discard(minion)

    def declarelive(self, minion):
        with self.lock:
            if minion in self.minions:
                self.survivors.add(minion)

    def run(self):
        while True:
            for minion in self.minions:
                try:
                    sendpickle(minion, None, self.deadthreshold)
                except:
                    self.declaredead(minion)
                else:
                    self.declarelive(minion)

            time.sleep(self.checkperiod)

    def assign(self, executor, uniqueid, groupids, numGroups):
        offset = abs(hash(executor.query))
        unassigned = []
        with self.lock:
            for minion in self.survivors:
                subset = assign(offset, groupids, numGroups, minion, self.minions, self.survivors)
                try:
                    sendpickle(minion, AssignExecutor(executor, uniqueid, subset), self.deadthreshold)
                except:
                    self.declaredead(minion)
                    unassigned.extend(subset)
                else:
                    self.declarelive(minion)

        if len(unassigned) > 0:
            self.assign(executor, unassigned, numGroups)

    def cancel(self, query):
        with self.lock:
            for minion in self.minions:
                try:
                    sendpickle(minion, CancelQuery(query), self.deadthreshold)
                except:
                    self.declaredead(minion)
                else:
                    self.declarelive(minion)

class Tallyman(object):
    @staticmethod
    def tallyme(executor, wholeData):
        action = executor.query.actions[-1]
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"

        numGroups = executor.query.dataset.numGroups

        loadsDone = float(len(set(wholeData.loaded))) / numGroups

        missing = set(range(numGroups))
        computeResults = {}
        for computeResult in wholeData.computeResults:
            # take the last computed value
            computeResults[computeResult.groupid] = computeResult
            missing.discard(computeResult.groupid)

        computesDone = float(len(computeResults)) / numGroups

        done = len(computeResults) == numGroups

        computeTime = sum(x.computeTime for x in computeResults)

        lastUpdate = wholeData.lastUpdate.isoformat(" ") + " UTC"

        if wholeData.failure is not None:
            done = True
            return Result(loadsDone, computesDone, done, computeTime, lastUpdate, wholeData.failure), sorted(missing)

        else:
            tally = action.initialize()
            for computeResult in computeResults.values():
                tally = action.update(tally, computeResult.subtally)
            if done:
                tally = action.finalize(tally)

            return Result(loadsDone, computesDone, done, computeTime, lastUpdate, tally), missing
