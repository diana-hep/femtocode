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
    def __init__(self, occupants, workItem):
        super(Fetcher, self).__init__()
        self.occupants = occupants
        self.workItem = workItem

class ROOTFetcher(Fetcher):
    def __init__(self, occupants, workItem):
        super(ROOTFetcher, self).__init__(occupants, workItem)

    def files(self, column):
        if column.issize():
            out = self.workItem.group.segments[column.dropsize()].files
        else:
            out = self.workItem.group.segments[column].files

        if out is None:
            out = self.workItem.group.files
        return out

    def run(self):
        columnNameToArray = {}
        filesetsToColumns = {}

        for occupant in self.occupants:
            column = ColumnName.parse(occupant.address.column)
            columnNameToArray[column] = occupant.rawarray

            if not column.issize():
                fileset = tuple(self.files(column))
                if fileset not in filesetsToColumns:
                    filesetsToColumns[fileset] = []
                filesetsToColumns[fileset].append(column)

        for fileset, columns in filesetsToColumns.items():
            toget = []
            for column in columns:
                if not column.issize():
                    dataBranch = workItem.work.datset.columns[column].dataBranch
                    sizeBranch = workItem.work.datset.columns[column].sizeBranch
                    dataArray = columnNameToArray[column]

                    if sizeBranch is None:
                        toget.append((dataBranch, dataArray))
                    else:
                        sizeArray = columnNameToArray[workItem.work.query.sizeEquivalents[str(column.size())]]
                        toget.append((dataBranch, sizeBranch, dataArray, sizeArray))

            for file in fileset:
                fillarrays(file, tree, toget)
