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
import math
from collections import deque
try:
    import cPickle as pickle
except:
    import pickle

import psutil

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
    def fromJson(obj):
        return Result(obj["loadsDone"],
                      obj["computesDone"],
                      obj["done"],
                      obj["wallTime"],
                      obj["computeTime"],
                      obj["lastUpdate"],
                      obj["data"])

class SimpleCacheOccupant(object):
    def __init__(self, query, result):
        self.query = query
        self.result = result

class PartitionedCacheOccupant(object):
    def __init__(self, query, pieces):
        self.query = query
        self.pieces = pieces

    @property
    def result(self):
        raise NotImplementedError

class RolloverCache(object):
    def __init__(self, directory, memoryMarginBytes, diskMarginBytes, rolloverTime):
        self.directory = "/tmp/downloads/cache"
        self.memoryMarginBytes = memoryMarginBytes
        self.diskMarginBytes = diskMarginBytes
        self.rolloverTime = rolloverTime

        assert os.path.exists(self.directory) and os.path.isdir(self.directory)

        self.queryids = {}
        self.order = deque()
        self.lookup = {}

        self.updateRollovers()

    def currentDir(self):
        return str(int(math.floor(time.time() / self.rolloverTime)))

    def updateRollovers(self):
        self.rollovers = os.listdir(self.directory)
        if currentDir not in self.rollovers:
            os.mkdir(os.path.join(self.directory, currentDir))
            self.rollovers = os.listdir(self.directory)
            assert currentDir in self.rollovers

        self.rollovers.sort(key=lambda x: -int(x))

    def __contains__(self, query):
        if isinstance(query, (int, long)):
            return query in self.queryids or self.ondisk(query)
        else:
            return query in self.lookup or self.ondisk(query)

    def result(self, query):
        out = self.lookup.get(query)
        if out is not None:
            return out.result
        else:
            return self.fromdisk(query)

    def assign(self, query):
        # TODO: determine if this is a SimpleCacheOccupant or a PartitionedCacheOccupant
        occupant = SimpleCacheOccupant(query, None)

        self.queryids[query.id] = self.queryids.get(query.id, 0) + 1
        self.order.append(occupant)
        self.lookup[query] = occupant

        self.rolloverMemory()
        self.rolloverDisk()

    def rolloverMemory(self):
        while psutil.virtual_memory().available < self.memoryMarginBytes:
            occupant = self.deque.popleft()
            del self.lookup[occupant.query]
            self.queryids[occupant.query.id] -= 1
            if self.queryids[occupant.query.id] == 0:
                del self.queryids[occupant.query.id]

            occupant.todisk()

