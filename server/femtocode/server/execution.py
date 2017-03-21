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

import datetime
import time
import threading

import femtocode.asts.statementlist as statementlist
from femtocode.execution import ExecutionFailure
from femtocode.run.execution import NativeExecutor
from femtocode.remote import ResultMessage
from femtocode.server.messages import *
from femtocode.workflow import Query

class NativeAccumulateExecutor(NativeExecutor):
    def __init__(self, query):
        super(NativeAccumulateExecutor, self).__init__(query)

        self.loadsDone = dict((group.id, False) for group in query.dataset.groups)
        self.computesDone = dict((group.id, False) for group in query.dataset.groups)
        self.startTime = time.time()

        self._setaction()
        self.result = ResultMessage(0.0, 0.0, False, 0.0, 0.0, self.startTime, self.action.initialize())

    def _setaction(self):
        self.action = self.query.actions[-1]
        assert isinstance(self.action, statementlist.Aggregation), "last action must always be an aggregation"

    def toJson(self):
        out = super(NativeAccumulateExecutor, self).toJson()
        out["loadsDone"] = self.loadsDone
        out["computesDone"] = self.computesDone
        out["startTime"] = self.startTime
        out["result"] = self.result.toJson()
        return out

    @staticmethod
    def fromJson(obj):
        out = NativeExecutor.fromJson(obj)
        out.__class__ = NativeAccumulateExecutor
        out.loadsDone = obj["loadsDone"]
        out.computesDone = obj["computesDone"]
        out.startTime = obj["startTime"]
        out._setaction()
        out.result = ResultMessage.fromJson(obj["result"], out.action)
        return out

    def toNativeExecutor(self):
        out = NativeExecutor.__new__(NativeExecutor)
        out.query = self.query
        out.required = self.required
        out.temporaries = self.temporaries
        out.order = self.order
        out.tmptypes = self.tmptypes
        return out

    def oneLoadDone(self, groupid):
        if not self.query.cancelled:
            self.loadsDone[groupid] = True
            self.result.loadsDone = sum(1.0 for x in self.loadsDone.values() if x) / len(self.loadsDone)
            now = time.time()
            self.result.wallTime = now - self.startTime
            self.result.lastUpdate = datetime.datetime.utcnow().isoformat(" ") + " UTC"

    def oneComputeDone(self, groupid, computeTime, subtally):
        if not self.query.cancelled:
            self.computesDone[groupid] = True
            self.result.computesDone = sum(1.0 for x in self.computesDone.values() if x) / len(self.computesDone)
            self.result.done = all(self.computesDone.values())
            now = time.time()
            self.result.wallTime = now - self.startTime
            self.result.computeTime += computeTime
            self.result.lastUpdate = datetime.datetime.utcnow().isoformat(" ") + " UTC"

            if not isinstance(self.result.data, ExecutionFailure):
                self.result.data = self.action.update(self.result.data, subtally)
                if self.result.done:
                    self.result.data = self.action.finalize(self.result.data)

    def oneFailure(self, failure):
        if not isinstance(self.result.data, ExecutionFailure):
            self.result.done = True
            now = time.time()
            self.result.wallTime = now - self.startTime
            self.result.data = failure   # only report the first failure
            self.result.lastUpdate = datetime.datetime.utcnow().isoformat(" ") + " UTC"

        self.query.cancelled = True

class NativeComputeExecutor(NativeExecutor):
    @staticmethod
    def fromNativeExecutor(executor, dataset, groupids):
        out = NativeComputeExecutor.__new__(NativeComputeExecutor)
        out.query = Query.fromJson(executor.query.toJson())  # because we'll be replacing the dataset
        out.query.dataset = dataset
        out.required = executor.required
        out.temporaries = executor.temporaries
        out.order = executor.order
        out.tmptypes = executor.tmptypes
        out._setTransients(groupids)
        return out

    def __init__(self, query, groupids):
        super(NativeComputeExecutor, self).__init__(query)
        self._setTransients(groupids)
        
    def _setTransients(self, groupids):
        # transient; only used on compute nodes
        self.groupids = groupids
        self.lock = threading.Lock()
        self.groupsDone = dict((x, False) for x in self.groupids)
        self.failed = False
        self.messages = []

    def oneLoadDone(self, groupid):
        with self.lock:
            self.messages.append(OneLoadDone(groupid))

    def oneComputeDone(self, groupid, computeTime, subtally):
        with self.lock:
            self.messages.append(OneComputeDone(groupid, computeTime, subtally))
            self.groupsDone[groupid] = True
        
    def oneFailure(self, failure):
        with self.lock:
            if not self.failed:
                self.messages.append(OneFailure(failure))
                self.failed = True

    def done(self):
        with self.lock:
            return self.failed or all(self.groupsDone.values())

    def cancel(self):
        with self.lock:
            self.query.cancelled = True
