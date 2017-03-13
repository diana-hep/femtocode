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
    def __init__(self, directory, memoryMarginBytes, diskMarginBytes, rolloverTime=24*60*60, idchars=4):
        self.directory = "/tmp/downloads/cache"
        self.memoryMarginBytes = memoryMarginBytes
        self.diskMarginBytes = diskMarginBytes
        self.rolloverTime = rolloverTime
        self.idchars = idchars

        assert os.path.exists(self.directory) and os.path.isdir(self.directory)

        self.queryids = {}
        self.order = deque()
        self.lookup = {}

    def partialdir(self, when):
        return str(int(math.floor(when / self.rolloverTime)))

    def fulldir(self, when):
        return os.path.join(self.directory, self.partialdir(when))

    def fullpath(self, fulldir, queryid):
        return reduce(os.path.join, [fulldir] + [queryid[start:start + self.idchars] for start in range(0, len(queryid), self.idchars)]) + ".pkl"

    def fullpaths(self, when, queryid):
        return [self.fullpath(fulldir, queryid) for fulldir in self.rollovers(when)]
            
    def rollovers(self, when):
        rollovers = os.listdir(self.directory)
        if self.partialdir(when) not in rollovers:
            os.mkdir(self.fulldir(when))
            rollovers = os.listdir(self.directory)
            assert self.partialdir(when) in rollovers

        rollovers.sort(key=lambda x: -int(x))
        return [os.path.join(self.directory, partialdir) for partialdir in rollovers]

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

            self.todisk(occupant)

    def rolloverDisk(self):
        while psutil.disk_usage(self.directory).free < self.diskMarginBytes:
            rollovers = self.rollovers(time.time())
            for dirpath, dirnames, filnames in os.walk(rollovers[-1], topdown=False):
                for name in filenames:
                    os.remove(os.path.join(dirpath, name))
                for name in dirnames:
                    os.rmdir(os.path.join(dirpath, name))

    def todisk(self, occupant):
        now = time.time()
        self.rollovers(now)

        if isinstance(occupant, SimpleCacheOccupant):
            # each query contains *in principle* multiple queries because of (very unlikely) query.id collision
            fullpath = self.fullpath(self.fulldir(now), occupant.query.id)
            if os.path.exists(fullpath):
                values = pickle.load(open(fullpath, "rb"))
            else:
                values = []

            if occupant.query not in [x.query for x in values]:
                values = values + [occupant]
            
            pickle.dump(values, open(fullpath, "wb"), pickle.HIGHEST_PROTOCOL)

        else:
            raise NotImplementedError

    def fromdisk(self, query):
        now = time.time()
        for fullpath in self.fullpaths(now, query.id):
            if os.path.exists(fullpath):
                # each query contains *in principle* multiple queries because of (very unlikely) query.id collision
                for occupant in pickle.load(open(fullpath, "rb")):
                    if occupant.query == query:
                        # if we found this in and old (not the most recent) directory
                        if fullpath != self.fullpath(self.fulldir(now), query.id):
                            self.todisk(occupant)   # put it in the most recent directory

                        return occupant

        assert False, "couldn't find {0} on disk".format(query.id)

    def ondisk(self, query):
        if isinstance(query, (int, long)):
            queryid = query
        else:
            queryid = query.id

        for fullpath in self.fullpaths(time.time(), queryid):
            if os.path.exists(fullpath):
                if isinstance(query, (int, long)):
                    return True

                for occupant in pickle.load(open(fullpath, "rb")):
                    if occupant.query == query:
                        return True

        return False
