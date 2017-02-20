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

import numpy

class CacheOccupant(object):
    untyped = numpy.uint8

    @staticmethod
    def allocate(numBytes):
        return numpy.empty(numBytes, dtype=CacheOccupant.untyped)

    def __init__(self, address, totalBytes, dtype, allocate=CacheOccupant.allocate):
        self.address = address
        self.totalBytes = totalBytes
        self.dtype = dtype

        self.filledBytes = 0
        self.rawarray = allocate(totalBytes)    # maybe use an alternative allocation method, maybe not
        self.needCount = 1
        self.lock = threading.Lock()

    def __repr__(self):
        return "<CacheOccupant for {0} at {1:012x}>".format(self.address, id(self))

    @property
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

    def evict(self, occupantsToEvict):
        # lose all Python references to the rawarrays in CacheOccupants so that they can be garbage collected
        for occupant in self.order[:occupantsToEvict]:
            del self.lookup[occupant.address]
        self.order = self.order[occupantsToEvict:]


