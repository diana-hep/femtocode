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

from femtocode.lang.py23 import *
from femtocode.lang.dataset import ColumnName
from femtocode.fromroot._fastreader import fillarrays
from femtocode.scope.messages import *
from femtocode.scope.util import *

class DataAddress(object):
    __slots__ = ("dataset", "column", "group")
    def __init__(self, dataset, column, group):
        self.dataset = dataset
        self.column = column
        self.group = group

    def __repr__(self):
        return "DataAddress({0}, {1}, {2})".format(dataset, column, group)

    def __eq__(self, other):
        return other.__class__ == DataAddress and other.dataset == self.dataset and other.column == self.column and other.group == self.group

    def __hash__(self):
        return hash((DataAddress, self.dataset, self.column, self.group))

class Fetcher(threading.Thread):
    def __init__(self, occupants, workItem, cancelQueue):
        super(Fetcher, self).__init__()
        self.occupants = occupants
        self.workItem = workItem
        self.cancelQueue = cancelQueue

    def updateCancels(self):
        for address in drainQueue(self.cancelQueue):
            i = 0
            for occupant in self.occupants:
                if occupant.address == address:
                    break
                i += 1
            # it might already be done
            if i < len(self.occupants):
                del self.occupants[i]

class ROOTFetcher(Fetcher):
    def __init__(self, occupants, workItem, cancelQueue):
        super(ROOTFetcher, self).__init__(occupants, workItem, cancelQueue)

    def files(self, column):
        if column.issize():
            out = self.workItem.group.segments[column.dropsize()].files
        else:
            out = self.workItem.group.segments[column].files

        if out is None:
            out = self.workItem.group.files
        return out

    def run(self):
        self.updateCancels()

        filesetsToColumns = {}
        for occupant in self.occupants:
            column = ColumnName.parse(occupant.address.column)
            fileset = tuple(self.files(column))
            if fileset not in filesetsToColumns:
                filesetsToColumns[fileset] = []
            filesetsToColumns[fileset].append(column)

        for fileset, columns in filesetsToColumns.items():
            toget = []
            for column in columns:
                if not column.issize():
                    if column.size() in columns:
                        toget.append((w, x, y, z))

# HERE!!!

                    elif workItem.work.dataset.columns[column].size is not None:
                        toget.append((w, x, y, z))

                    else:
                        toget.append((x, y))

            for file in fileset:
                fillarrays(file, tree, toget)
