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

import numpy

from femtocode.py23 import *
from femtocode.util import *
from femtocode.execution import ExecutionFailure
from femtocode.run.compute import WorkItem

class CacheOccupant(object):
    untyped = numpy.uint8

    @staticmethod
    def allocate(numBytes):
        return numpy.empty(numBytes, dtype=CacheOccupant.untyped)

    def __init__(self, address, totalBytes, dtype, allocate):
        self.address = address
        self.totalBytes = totalBytes
        self.dtype = dtype

        self.filledBytes = 0
        self.rawarray = allocate(totalBytes)    # maybe use an alternative allocation method, maybe not
        self.needCount = 1
        self.lock = threading.Lock()            # CacheMaster and Minion both change needCount
        self.fetchfailure = None                # Fetcher sets filledBytes and CacheMaster checks it

    def __repr__(self):
        return "<CacheOccupant for {0} at 0x{1:012x}>".format(self.address, id(self))

    def array(self):
        return self.rawarray.view(self.dtype)

    def stillNeeded(self):
        with self.lock:
            return self.needCount > 0

    def incrementNeed(self):
        with self.lock:
            self.needCount += 1

    def decrementNeed(self):
        with self.lock:
            assert self.needCount > 0
            self.needCount -= 1

    def fill(self, data):
        numBytes = len(data)
        assert self.filledBytes + numBytes <= self.totalBytes
        self.rawarray[self.filledBytes : self.filledBytes + numBytes] = numpy.frombuffer(data, dtype=self.untyped)
        with self.lock:
            self.filledBytes += numBytes
        return numBytes

    def setfilled(self, value, absolute=True):
        with self.lock:
            if not absolute:
                value = roundup(value * self.totalBytes)
            self.filledBytes = max(0, min(self.totalBytes, value))

    def addtofilled(self, value, absolute=True):
        with self.lock:
            if not absolute:
                value = roundup(value * self.totalBytes)
            self.filledBytes = max(0, min(self.totalBytes, self.filledBytes + value))

    def ready(self):
        with self.lock:
            return self.filledBytes == self.totalBytes

class CacheOrder(object):
    def __init__(self):
        self.order = []     # from oldest to newest (add with .append, evict with [:occupantsToEvict])
        self.lookup = {}

    def __repr__(self):
        return "<CacheOrder len {0} at 0x{1:012x}>".format(len(self.order), id(self))

    def __len__(self):
        assert len(self.order) == len(self.lookup)
        return len(self.order)

    def __contains__(self, address):
        return address in self.lookup

    def __getitem__(self, address):
        return self.lookup[address]

    def __iter__(self):
        return iter(self.order)

    def add(self, occupant):
        assert occupant.address not in self.lookup
        self.order.append(occupant)
        self.lookup[occupant.address] = occupant

    def discard(self, occupant):
        try:
            self.order.remove(occupant)
        except ValueError:
            pass
        try:
            del self.lookup[occupant.address]
        except KeyError:
            pass

    def extract(self, address):
        assert address in self.lookup
        occupant = None
        i = len(self.order)   # walk backwards from the most recent because NeedWantCache is more likely
        while i > 0:          # to promote a recent item from 'want' to 'need' than an old item
            i -= 1
            if self.order[i].address == address:
                occupant = self.order[i]
                break
        assert occupant is not None
        del self.order[i]
        del self.lookup[address]
        return occupant

    def evict(self, numToEvict):
        # lose all Python references to the rawarrays in CacheOccupants so that they can be garbage collected
        if numToEvict > 0:
            for occupant in self.order[:numToEvict]:
                del self.lookup[occupant.address]
            self.order = self.order[numToEvict:]

class NeedWantCache(object):
    def __init__(self, limitBytes):
        self.limitBytes = limitBytes

        self.usedBytes = 0
        self.need = {}             # unordered: we need them all, cannot proceed without them
        self.want = CacheOrder()   # least recently used is most likely to be evicted

    def __repr__(self):
        return "<NeedWantCache at 0x{0:012x}>".format(id(self))

    def demoteNeedsToWants(self):
        # migrate occupants from 'need' to 'want' if the minion thread is done using it for calculations
        todemote = []
        for occupant in self.need.values():
            if not occupant.stillNeeded():
                todemote.append(occupant)

        for occupant in todemote:
            del self.need[occupant.address]
            self.want.add(occupant)

    def removeFailures(self):
        toremove = []
        for occupant in self.need.values():
            with occupant.lock:
                if occupant.fetchfailure is not None:
                    toremove.append(occupant)
        for occupant in toremove:
            del self.need[occupant.address]

        toremove = []
        for occupant in self.want:
            with occupant.lock:
                if occupant.fetchfailure is not None:
                    toremove.append(occupant)
        for occupant in toremove:
            self.want.discard(occupant)

    def howManyToEvict(self, workItem):
        required = workItem.required()

        neededBytes = 0
        for address in required:
            if address not in self.need and address not in self.want:
                neededBytes += workItem.columnBytes(address.column)

        additionalBytesRequired = max(neededBytes - (self.limitBytes - self.usedBytes), 0)

        numToEvict = 0
        reclaimableBytes = 0
        for occupant in self.want:
            if occupant.address not in required:
                if reclaimableBytes >= additionalBytesRequired:
                    break

                numToEvict += 1
                reclaimableBytes += occupant.totalBytes

        if reclaimableBytes >= additionalBytesRequired:
            return numToEvict
        else:
            return None

    def reserve(self, workItem, numToEvict):
        # clear some space
        self.want.evict(numToEvict)

        tofetch = []
        for address in workItem.required():
            if address in self.need:                        # case 1: "I need it, too!"
                self.need[address].incrementNeed()

            elif address in self.want:                      # case 2: a "want" becomes a "need"
                occupant = self.want.extract(address)
                occupant.incrementNeed()
                self.need[address] = occupant

            else:                                           # case 3: brand new, need to fetch it
                occupant = CacheOccupant(address,
                                         workItem.columnBytes(address.column),
                                         workItem.columnDtype(address.column),
                                         CacheOccupant.allocate)
                # (need starts at 1, don't have to incrementNeed)
                self.need[address] = occupant
                tofetch.append(occupant)

            workItem.attachOccupant(self.need[address])

        if len(tofetch) > 0:
            fetcher = workItem.executor.query.dataset.fetcher(tofetch, workItem)
            fetcher.start()

    def maybeReserve(self, waiting):
        # make sure occupants no longer in use by Minion are in the "wants" list and can be evicted
        # (actually just a snapshot in time, so maybeReserve often!)
        self.demoteNeedsToWants()

        minToEvict = None
        bestIndex = None
        for index, workItem in enumerate(waiting):
            numToEvict = self.howManyToEvict(workItem)

            if numToEvict == 0:
                # work that doesn't require eviction is always best (starting with oldest assigned)
                minToEvict = 0
                bestIndex = index
                break

            elif numToEvict is not None:
                # second to that is work that requires minimal eviction
                if minToEvict is None or numToEvict < minToEvict:   # strict < for FIRST of equal numToEvict
                    minToEvict = numToEvict
                    bestIndex = index

        if bestIndex is not None:
            # remove it from the waiting
            workItem = waiting[bestIndex]
            del waiting[bestIndex]

            # reserve it
            self.reserve(workItem, minToEvict)
            return workItem

        else:
            return None

class CacheMaster(threading.Thread):
    loopdelay = 0.001           # 1 ms       pause time at the end of the loop

    def __init__(self, needWantCache, minions):
        super(CacheMaster, self).__init__()
        self.needWantCache = needWantCache
        self.minions = minions

        assert len(self.minions) > 0

        self.incoming = queue.Queue()
        self.outgoing = minions[0].incoming
        self.waiting = []
        self.loading = []

        self.daemon = True

    def __repr__(self):
        return "<CacheMaster at 0x{0:012x}>".format(id(self))

    def prepare(self, executor):   # overloaded in the server
        return executor

    def run(self):
        while True:
            # put new work in the waiting
            for executor in drainQueue(self.incoming):
                executor = self.prepare(executor)
                for group in executor.query.dataset.groups:
                    self.waiting.append(WorkItem(executor, group))

            # check for cancelled executors
            todrop = []
            for i, workItem in enumerate(self.waiting):
                if workItem.executor.query.cancelled:
                    workItem.executor.oneFailure(ExecutionFailure("User cancelled query.", None))
                with workItem.executor.query.lock:
                    cancelled = workItem.executor.query.cancelled
                if cancelled:
                    todrop.append(i)

            # remove all workItems associated with cancelled executors
            while len(todrop) > 0:
                del self.waiting[todrop.pop()]

            # move work from waiting to loading or minions
            while True:
                # try to reserve space in the cache for the next surviving workItem
                workItem = self.needWantCache.maybeReserve(self.waiting)
                if workItem is None:
                    break
                elif workItem.ready():
                    self.outgoing.put(workItem)
                    workItem.executor.oneLoadDone(workItem.group.id)
                else:
                    self.loading.append(workItem)

            # move work from loading to minions
            toremove = []
            for index, workItem in enumerate(self.loading):
                if workItem.ready():
                    toremove.append(index)
                    self.outgoing.put(workItem)
                    workItem.executor.oneLoadDone(workItem.group.id)
                else:
                    fetchfailure = workItem.fetchfailure()
                    if fetchfailure is not None:
                        workItem.executor.oneFailure(fetchfailure)
                        toremove.append(index)
            while len(toremove) > 0:
                del self.loading[toremove.pop()]

            # no busy wait
            time.sleep(self.loopdelay)
