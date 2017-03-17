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

import femtocode.asts.statementlist as statementlist
from femtocode.run.execution import NativeExecutor
from femtocode.workflow import Message

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
    def fromJson(obj, action):
        if ExecutionFailure.failureJson(obj["data"]):
            data = ExecutionFailure.fromJson(obj["data"])
        else:
            data = action.tallyFromJson(obj["data"])

        return Result(obj["loadsDone"],
                      obj["computesDone"],
                      obj["done"],
                      obj["wallTime"],
                      obj["computeTime"],
                      obj["lastUpdate"],
                      data)

class NativeAccumulateExecutor(NativeExecutor):
    def __init__(self, query):
        super(NativeAccumulateExecutor, self).__init__(query)

        self.loadsDone = dict((group.id, False) for group in query.dataset.groups)
        self.computesDone = dict((group.id, False) for group in query.dataset.groups)
        self.startTime = time.time()

        self._setaction()
        self.result = Result(0.0, 0.0, False, 0.0, 0.0, self.startTime, self.action.initialize())

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
        out.result = Result.fromJson(self.action)
        return out

    def toCompute(self, groupids, connaddr):
        out = NativeComputeExecutor.__new__(NativeComputeExecutor)
        out.query = self.query
        out.required = self.required
        out.temporaries = self.temporaries
        out.order = self.order
        out.tmptypes = self.tmptypes

        out.groupids = groupids
        out.client = TallymanClient(connaddr, NativeComputeExecutor.listenThreshold)

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
    listenThreshold = 0.030     # 30 ms      no response from tallyman; reset ZMQClient recv/send state

    def __init__(self, query, groupids, connaddr):
        super(NativeComputeExecutor, self).__init__(query)
        self.groupids = groupids
        self.client = TallymanClient(connaddr, self.listenThreshold)

    def toJson(self):
        out = super(NativeComputeExecutor, self).toJson()
        out["connaddr"] = self.client.connaddr
        out["timeout"] = self.client.timeout
        return out

    @staticmethod
    def fromJson(obj):
        out = NativeExecutor.fromJson(obj)
        out.__class__ = NativeComputeExecutor
        out.client = TallymanClient(obj["connaddr"], obj["timeout"])
        return out

    def oneLoadDone(self, groupid):
        if self.client.oneLoadDone(self.query, groupid) is None:
            self.query.cancelled = True

    def oneComputeDone(self, groupid, computeTime, subtally):
        if self.client.oneComputeDone(self.query, groupid, computeTime, subtally) is None:
            self.query.cancelled = True

    def oneFailure(self, failure):
        if self.client.oneFailure(self.query, failure) is None:
            self.query.cancelled = True
