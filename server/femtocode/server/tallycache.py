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
try:
    import cPickle as pickle
except:
    import pickle

import psutil

class CacheOccupant(object):
    def __init__(self, executor):
        self.executor = executor
        self.query = self.executor.query
        self.result = self.executor.result

    def running(self):
        if self.executor.done:
            self.executor = None
        return not self.executor.done

class SendWholeQuery(object):
    def __init__(self, crossCheckId):
        self.crossCheckId = crossCheckId

class RolloverCache(object):
    def __init__(self, directory, memoryMarginBytes, diskMarginBytes, rolloverTime=24*60*60, idchars=4):
        self.directory = "/tmp/downloads/cache"
        self.memoryMarginBytes = memoryMarginBytes
        self.diskMarginBytes = diskMarginBytes
        self.rolloverTime = rolloverTime
        self.idchars = idchars

        assert os.path.exists(self.directory) and os.path.isdir(self.directory)

        self.queryids = {}
        self.order = []
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

    def ensure(self, dir):
        if not os.path.exists(dir):
            init, last = os.path.split(dir)
            self.ensure(init)
            os.mkdir(last)

    def __contains__(self, query):
        if isinstance(query, (int, long)):
            return len(self.queryids.get(query, [])) > 0 or self.ondisk(query)
        else:
            return query in self.lookup or self.ondisk(query)

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

    def get(self, query):
        if isinstance(query, (int, long)):
            matches = self.queryids.get(query, [])

            if len(matches) == 0:
                occupant = self.fromdisk(query)   # deletes from disk
                self.queryids[occupant.query.id] = self.queryids.get(occupant.query.id, []) + [occupant.query]
                self.order.append(occupant)
                self.lookup[occupant.query] = occupant
                return occupant

            elif len(matches) == 1:
                occupant = self.lookup[matches[0]]

                index = len(self.order)           # move occupant to the front of self.order
                while index >= 0:
                    index -= 1
                    if self.order[index].query.id == query:
                        del self.order[index]
                        break
                self.order.append(occupant)
                return occupant

            else:
                return SendWholeQuery(query)      # queryid is not unique; need more information

        else:
            occupant = self.lookup.get(query)

            if occupant is not None:
                index = len(self.order)           # move occupant to the front of self.order
                while index >= 0:
                    index -= 1
                    if self.order[index].query.id == query.id and self.order[index].query == query:
                        del self.order[index]
                        break
                self.order.append(occupant)
                return occupant

            else:
                occupant = self.fromdisk(query)   # deletes from disk
                self.queryids[occupant.query.id] = self.queryids.get(occupant.query.id, []) + [occupant.query]
                self.order.append(occupant)
                self.lookup[occupant.query] = occupant
                return occupant

    def fromdisk(self, query):
        now = time.time()
        if isinstance(query, (int, long)):
            queryid = query
        else:
            queryid = query.id

        out = []
        for fullpath in self.fullpaths(now, queryid):
            if os.path.exists(fullpath):
                # each query contains *in principle* multiple queries because of (very unlikely) queryid collision
                for occupant in pickle.load(open(fullpath, "rb")):
                    if occupant.query == query:
                        os.remove(fullpath)   # remove from disk so that it can be put in memory
                        return occupant

                    elif isinstance(query, (int, long)):
                        out.append((fullpath, occupant))

        if len(out) == 1:                     # found unique query by id alone
            fullpath, occupant = out[0]
            os.remove(fullpath)               # remove from disk so that it can be put in memory
            return occupant

        elif len(out) > 1:
            return SendWholeQuery(query)      # cannot disambiguate query by id alone

        assert False, "couldn't find {0} on disk".format(query.id)

    def result(self, query):
        return self.get(query)

    def assign(self, executor):
        occupant = CacheOccupant(executor)

        self.queryids[occupant.query.id] = self.queryids.get(occupant.query.id, []) + [occupant.query]
        self.order.append(occupant)
        self.lookup[occupant.query] = occupant

        self.rolloverMemory()
        self.rolloverDisk()

        return occupant

    def rolloverMemory(self):
        while psutil.virtual_memory().available < self.memoryMarginBytes:
            if len(self.order) > 0:
                occupant = self.order[0]
                if not occupant.running():
                    del self.order[0]

                    del self.lookup[occupant.query]
                    self.queryids[occupant.query.id].remove(occupant.query)
                    if len(self.queryids[occupant.query.id]) == 0:
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

        # each query contains *in principle* multiple queries because of (very unlikely) query.id collision
        fullpath = self.fullpath(self.fulldir(now), occupant.query.id)
        if os.path.exists(fullpath):
            values = pickle.load(open(fullpath, "rb"))
        else:
            values = []

        if occupant.query not in [x.query for x in values]:
            values = values + [occupant]

        self.ensure(os.path.split(fullpath)[0])
        pickle.dump(values, open(fullpath, "wb"), pickle.HIGHEST_PROTOCOL)
