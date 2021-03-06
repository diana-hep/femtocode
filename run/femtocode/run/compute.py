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
import sys

import numpy

from femtocode.py23 import *
from femtocode.util import *
from femtocode.dataset import ColumnName
from femtocode.dataset import sizeType
from femtocode.execution import ExecutionFailure

class DataAddress(object):
    def __init__(self, dataset, column, group):
        self.dataset = dataset
        self.column = column
        self.group = group

    def __repr__(self):
        return "DataAddress({0}, {1}, {2})".format(repr(self.dataset), repr(self.column), repr(self.group))

    def __eq__(self, other):
        return other.__class__ == DataAddress and other.dataset == self.dataset and other.column == self.column and other.group == self.group

    def __hash__(self):
        return hash(("DataAddress", self.dataset, self.column, self.group))

class WorkItem(object):
    def __init__(self, executor, group):
        self.executor = executor
        self.group = group
        self.occupants = []

    def __repr__(self):
        return "<WorkItem for query {0}, group {1} at 0x{2:012x}>".format(self.executor.query.id, self.group.id, id(self))

    def required(self):
        return [DataAddress(self.executor.query.dataset.name, column, self.group.id) for column in self.executor.required]

    def columnBytes(self, column):
        if isinstance(column, string_types):
            column = ColumnName.parse(column)

        if column.issize():
            return self.group.numEntries * numpy.dtype(sizeType).itemsize
        else:
            return self.group.segments[column].dataLength * self.columnDtype(column).itemsize

    def columnDtype(self, column):
        if column.issize():
            return numpy.dtype(sizeType)
        else:
            return numpy.dtype(self.executor.query.dataset.columns[column].dataType)

    def attachOccupant(self, occupant):
        self.occupants.append(occupant)

    def ready(self):
        assert len(self.occupants) != 0
        return all(occupant.ready() for occupant in self.occupants)

    def fetchfailure(self):
        for occupant in self.occupants:
            with occupant.lock:
                fetchfailure = occupant.fetchfailure
            if fetchfailure is not None:
                return fetchfailure
        return None

    def decrementNeed(self):
        assert len(self.occupants) != 0
        for occupant in self.occupants:
            occupant.decrementNeed()

    def run(self):
        inarrays = dict((x.address.column, x.array()) for x in self.occupants)
        return self.executor.run(inarrays, self.group, self.executor.query.dataset.columns)

    def decrementNeed(self):
        assert len(self.occupants) != 0
        for occupant in self.occupants:
            occupant.decrementNeed()

class Minion(threading.Thread):
    def __init__(self, incoming):
        super(Minion, self).__init__()
        self.incoming = incoming
        self.daemon = True

    def __repr__(self):
        return "<Minion at 0x{0:012x}>".format(id(self))

    def run(self):
        while True:
            workItem = self.incoming.get()

            # don't process cancelled queries
            if workItem.executor.query.cancelled:
                workItem.executor.oneFailure(ExecutionFailure("User cancelled query.", None))
            with workItem.executor.query.lock:
                cancelled = workItem.executor.query.cancelled
            if cancelled: continue

            try:
                # actually do the work; ideally 99.999% of the time spent in this whole project
                # should be in that second line there
                subtally, subtime = workItem.run()
            except Exception as exception:
                workItem.executor.oneFailure(ExecutionFailure(exception, sys.exc_info()[2]))
            else:
                workItem.executor.oneComputeDone(workItem.group.id, subtime, subtally)

            # for the cache
            workItem.decrementNeed()
