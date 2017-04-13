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

import sys
import threading

from femtocode.dataset import ColumnName
from femtocode.dataset import sizeType
from femtocode.execution import ExecutionFailure
from femtocode.run.compute import DataAddress
from femtocode.rootio._fastreader import fillarrays

class ROOTFetcher(threading.Thread):
    def __init__(self, occupants, workItem):
        super(ROOTFetcher, self).__init__()
        self.occupants = occupants
        self.workItem = workItem
        self.daemon = True

    class _Pair(object):
        def __init__(self, dataBranch, sizeBranch, dataoccupant, sizeoccupant, dtype):
            self.dataBranch = dataBranch
            self.sizeBranch = sizeBranch
            self.dataoccupant = dataoccupant
            self.sizeoccupant = sizeoccupant
            self.dtype = dtype

    class _FilesetTree(object):
        def __init__(self, fileset, tree):
            self.fileset = tuple(sorted(fileset))
            self.tree = tree

        def __eq__(self, other):
            return other.__class__ == ROOTFetcher._FilesetTree and self.fileset == other.fileset and self.tree == other.tree

        def __hash__(self):
            return hash(("ROOTFetcher._FilesetTree", self.fileset, self.tree))

    def run(self):
        try:
            filesetsToPairs = {}

            for dataoccupant in self.occupants:
                if not dataoccupant.address.column.issize():
                    fileset = self.workItem.group.segments[dataoccupant.address.column].files
                    if fileset is None:
                        fileset = self.workItem.group.files

                    tree = self.workItem.executor.query.dataset.columns[dataoccupant.address.column].tree

                    key = ROOTFetcher._FilesetTree(fileset, tree)
                    if key not in filesetsToPairs:
                        filesetsToPairs[key] = []

                    filesetsToPairs[key].append(ROOTFetcher._Pair(
                        self.workItem.executor.query.dataset.columns[dataoccupant.address.column].dataBranch,
                        self.workItem.executor.query.dataset.columns[dataoccupant.address.column].sizeBranch,
                        dataoccupant,
                        None,
                        self.workItem.executor.query.dataset.columns[dataoccupant.address.column].dataType))

            for sizeoccupant in self.occupants:
                if sizeoccupant.address.column.issize():
                    found = False
                    for filesetTree, pairs in filesetsToPairs.items():
                        for pair in pairs:
                            c = self.workItem.executor.query.dataset.columns.get(pair.dataoccupant.address.column)
                            if c is not None and c.size == sizeoccupant.address.column:
                                pair.sizeoccupant = sizeoccupant
                                found = True

                    if not found:
                        found = False
                        for c in self.workItem.executor.query.dataset.columns.values():
                            if c.size == sizeoccupant.address.column:
                                fileset = self.workItem.group.segments[c.data].files
                                if fileset is None:
                                    fileset = self.workItem.group.files

                                key = ROOTFetcher._FilesetTree(fileset, c.tree)
                                if key not in filesetsToPairs:
                                    filesetsToPairs[key] = []

                                filesetsToPairs[key].append(ROOTFetcher._Pair(
                                    self.workItem.executor.query.dataset.columns[c.data].dataBranch,
                                    self.workItem.executor.query.dataset.columns[c.data].sizeBranch,
                                    None,
                                    sizeoccupant,
                                    self.workItem.executor.query.dataset.columns[c.data].dataType))
                                break

                        assert found

            for filesetTree, pairs in filesetsToPairs.items():
                toget = []
                for pair in pairs:
                    if pair.sizeBranch is None:
                        toget.append((pair.dataBranch, None if pair.dataoccupant is None else pair.dataoccupant.rawarray.view(pair.dtype)))
                    else:
                        toget.append((pair.dataBranch, pair.sizeBranch,
                                      None if pair.dataoccupant is None else pair.dataoccupant.rawarray.view(pair.dtype),
                                      None if pair.sizeoccupant is None else pair.sizeoccupant.rawarray.view(sizeType)))

                for file in filesetTree.fileset:
                    fillarrays(file, filesetTree.tree, toget)

                for pair in pairs:
                    if pair.dataoccupant is not None:
                        pair.dataoccupant.filledBytes = pair.dataoccupant.totalBytes
                    if pair.sizeoccupant is not None:
                        pair.sizeoccupant.filledBytes = pair.sizeoccupant.totalBytes

        except Exception as exception:
            for occupant in self.occupants:
                with occupant.lock:
                    occupant.fetchfailure = ExecutionFailure(exception, sys.exc_info()[2])
