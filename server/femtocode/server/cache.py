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
import math
try:
    import cPickle as pickle
except:
    import pickle

class RolloverCache(object):
    def __init__(self, directory, partitionMarginBytes, rolloverTime, gcTime, idchars):
        self.directory = directory
        self.partitionMarginBytes = partitionMarginBytes
        self.rolloverTime = rolloverTime
        self.idchars = idchars

        assert os.path.exists(self.directory) and os.path.isdir(self.directory)

        self.lock = threading.Lock

        def gc():
            while True:
                while os.statvfs(self.directory).f_bavail * os.statvfs(self.directory).f_frsize < self.partitionMarginBytes:
                    rollovers = self.rollovers(time.time())
                    for dirpath, dirnames, filnames in os.walk(rollovers[-1], topdown=False):
                        for name in filenames:
                            with self.lock:
                                os.remove(os.path.join(dirpath, name))
                        for name in dirnames:
                            with self.lock:
                                os.rmdir(os.path.join(dirpath, name))
                time.sleep(gcTime)

        self.gcThread = threading.Thread(target=gc, name="RolloverCache-GarbageCollector")
        self.gcThread.daemon = True
        self.gcThread.start()
        
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

    def get(self, query):
        with self.lock:
            now = time.time()
            for fullpath in self.fullpaths(now, query.id):
                if os.path.exists(fullpath):
                    # each query contains *in principle* multiple queries because of (very unlikely) query.id collision
                    for que, res in pickle.load(open(fullpath, "rb")):
                        if que == query:
                            return res
            return None

    def put(self, query, result):
        with self.lock:
            now = time.time()
            self.rollovers(now)

            # each query contains *in principle* multiple queries because of (very unlikely) query.id collision
            fullpath = self.fullpath(self.fulldir(now), query.id)
            if os.path.exists(fullpath):
                values = pickle.load(open(fullpath, "rb"))
            else:
                values = []

            if query not in [q for q, r in values]:
                values = values + [(query, result)]

            self.ensure(os.path.split(fullpath)[0])
            picke.dump(values, open(fullpath, "wb", pickle.HIGHEST_PROTOCOL))
