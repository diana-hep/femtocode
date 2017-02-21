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
try:
    import Queue as queue
except ImportError:
    import queue

import numpy

class CacheOccupant(object):
    untyped = numpy.uint8

    @staticmethod
    def allocate(numBytes):
        return numpy.empty(numBytes, dtype=CacheOccupant.untyped)

    def __init__(self, address, totalBytes, dtype, cancelQueue, allocate=CacheOccupant.allocate):
        self.address = address
        self.totalBytes = totalBytes
        self.dtype = dtype
        self.cancelQueue = cancelQueue

        self.filledBytes = 0
        self.rawarray = allocate(totalBytes)    # maybe use an alternative allocation method, maybe not
        self.needCount = 1
        self.lock = threading.Lock()            # CacheMaster and Minion both change needCount
                                                # Fetcher sets filledBytes and Minion checks it

    def __repr__(self):
        return "<CacheOccupant for {0} at {1:012x}>".format(self.address, id(self))

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
        assert self.filledBytes + numBytes < self.totalBytes
        self.rawarray[self.filledBytes : self.filledBytes + numBytes] = numpy.frombuffer(data, dtype=self.untyped)
        with self.lock:
            self.filledBytes += numBytes
        return numBytes

    def ready(self):
        with self.lock:
            return self.filledBytes == self.totalBytes

class CacheOrder(object):
    def __init__(self):
        self.order = []     # from oldest to newest (add with .append, evict with [:occupantsToEvict])
        self.lookup = {}

    def __repr__(self):
        return "<CacheOrder for {0} at {1:012x}>".format(self.address, id(self))

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
    def __init__(self, limitBytes, fetcherClass):
        self.limitBytes = limitBytes
        self.fetcherClass = fetcherClass

        self.usedBytes = 0
        self.need = {}             # unordered: we need them all, cannot proceed without them
        self.want = CacheOrder()   # least recently used is most likely to be evicted

    def __repr__(self):
        return "<NeedWantCache with {0} at {1:012x}>".format(self.fetcherClass, id(self))

    def demoteNeedsToWants(self):
        # migrate occupants from 'need' to 'want' if the minion thread is done using it for calculations
        todemote = []
        for occupant in self.need.values():
            if not occupant.stillNeeded():
                todemote.append(occupant)

        for x in todemote:
            del self.need[occupant.address]
            self.want.add(occupant)
            
    def howManyToEvict(self, workItem, metadata):
        requires = workItem.requires()

        neededBytes = 0
        for address in requires:
            if address not in self.need and address not in self.want:
                neededBytes += metadata.bytesForAddress(address)

        numToEvict = 0
        reclaimableBytes = 0
        for occupant in self.want:
            if occupant.address not in requires:
                numToEvict += 1
                reclaimableBytes += occupant.totalBytes
                if reclaimableBytes >= neededBytes:
                    break

        if reclaimableBytes >= neededBytes:
            return numToEvict
        else:
            return None

    def reserve(self, workItem, metadata, numToEvict):
        # clear some space
        self.want.evict(numToEvict)

        tofetch = []
        cancelQueue = None
        for address in workItem.requires():
            if address in self.need:                        # case 1: "I need it, too!"
                self.need[address].incrementNeed()

            elif address in self.want:                      # case 2: a "want" becomes a "need"
                occupant = self.want.extract(address)
                occupant.incrementNeed()
                self.need[address] = occupant

            else:                                           # case 3: brand new, need to fetch it
                if cancelQueue is None:
                    cancelQueue = queue.Queue()
                occupant = CacheOccupant(address,
                                         metadata.bytesForAddress(address),
                                         metadata.dtypeForAddress(address),
                                         cancelQueue)
                # (need starts at 1, don't have to incrementNeed)
                self.need[address] = occupant
                tofetch.append(occupant)

            workItem.attachOccupant(self.need[address])

        if len(tofetch) > 0:
            fetcher = self.fetcherClass(tofetch, cancelQueue)
            fetcher.start()

    def maybeReserve(self, waitingRoom, metadata):
        # make sure occupants no longer in use by Minion are in the "wants" list and can be evicted
        # (actually just a snapshot in time, so maybeReserve often!)
        self.demoteNeedsToWants()

        minToEvict = None
        bestIndex = None
        for index, workItem in enumerate(waitingRoom):
            numToEvict = self.howManyToEvict(workItem, metadata)
            if numToEvict == 0:
                # work that doesn't require eviction is always best (starting with oldest assigned)
                minToEvict = 0
                bestIndex = index
                break

            elif numToEvict is not None:
                # second to that is work that requires minimal eviction
                if minToEvict is None:
                    minToEvict = numToEvict
                    bestIndex = index

        if bestIndex is not None:
            # remove it from the waitingRoom
            workItem = waitingRoom[bestIndex]
            del waitingRoom[bestIndex]

            # reserve it
            self.reserve(workItem, metadata, minToEvict)
            return workItem

        else:
            return None
