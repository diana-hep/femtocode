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

from femtocode.dataset import ColumnName
from femtocode.dataset import sizeType
from femtocode.run.cache import DataAddress
from femtocode.fromroot._fastreader import fillarrays

class Fetcher(threading.Thread):
    def __init__(self, occupants, workItem):
        super(Fetcher, self).__init__()
        self.occupants = occupants
        self.workItem = workItem
        self.daemon = True

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
        filesetsToOccupants = {}

        for occupant in self.occupants:
            column = ColumnName.parse(occupant.address.column)
            columnNameToArray[column] = occupant.rawarray

            filesetTree = (tuple(sorted(self.files(column))),
                       self.workItem.work.dataset.columns[column].tree)

            if not column.issize():
                if filesetTree not in filesetsToColumns:
                    filesetsToColumns[filesetTree] = []
                filesetsToColumns[filesetTree].append(column)

            if filesetTree not in filesetsToOccupants:
                filesetsToOccupants[filesetTree] = []
            filesetsToOccupants[filesetTree].append(occupant)

        for (fileset, tree), columns in filesetsToColumns.items():
            toget = []
            for column in columns:
                if not column.issize():
                    dataBranch = self.workItem.work.dataset.columns[column].dataBranch
                    sizeBranch = self.workItem.work.dataset.columns[column].sizeBranch
                    dataArray = columnNameToArray[column].view(self.workItem.work.dataset.columns[column].dataType)

                    if sizeBranch is None:
                        toget.append((dataBranch, dataArray))
                    else:
                        sizeArray = columnNameToArray.get(str(column.size()))
                        if sizeArray is not None:
                            sizeArray = sizeArray.view(sizeType)

                        toget.append((dataBranch, sizeBranch, dataArray, sizeArray))

            for file in fileset:
                fillarrays(file, tree, toget)

            for occupant in filesetsToOccupants[(fileset, tree)]:
                occupant.filledBytes = occupant.totalBytes
