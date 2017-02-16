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

import json

from femtocode.dataset import level
from femtocode.dataset import Segment
from femtocode.dataset import Group
from femtocode.dataset import Dataset
from femtocode.fromroot.declare import DatasetDeclaration
from femtocode.fromroot._fastreader import fillarrays
from femtocode.fromroot.xrootd import filesFromPath

class ROOTSegment(Segment):
    def __init__(self, data, size, numEntries, dataLength, dataType, files, tree, dataBranch, sizeBranch):
        super(ROOTSegment, self).__init__(data, size, numEntries, dataLength, dataType)
        self.files = files
        self.tree = tree
        self.dataBranch = dataBranch
        self.sizeBranch = sizeBranch

class ROOTGroup(Group):
    def __init__(self, id, segments, numEntries):
        super(ROOTGroup, self).__init__(id, segments, numEntries)

class ROOTDataset(Dataset):
    @staticmethod
    def fromYamlString(declaration):
        return ROOTDataset.fromDeclaration(DatasetDeclaration.fromYamlString(declaration))

    @staticmethod
    def _sanityCheck(quantity, collectionDepth=0):
        if isinstance(quantity, DatasetDeclaration):
            for x in quantity.fields.values():
                ROOTDataset._sanityCheck(x, collectionDepth)

        elif isinstance(quantity, DatasetDeclaration.Collection):
            ROOTDataset._sanityCheck(quantity.items, collectionDepth + 1)

        elif isinstance(quantity, DatasetDeclaration.Record):
            for name, field in quantity.fields.items():
                ROOTDataset._sanityCheck(field, collectionDepth)

        elif isinstance(quantity, DatasetDeclaration.Primitive):
            if quantity.frm.size is None and collectionDepth != 0:
                raise DatasetDeclaration.Error(quantity.lc, "field has no declared 'size' but it is nested within a collection")
            elif quantity.frm.size is not None and collectionDepth == 0:
                raise DatasetDeclaration.Error(quantity.lc, "field has a 'size' attribute but it is not nested within a collection")

    @staticmethod
    def _getPaths(quantity):
        if isinstance(quantity, DatasetDeclaration):
            for x in quantity.fields.values():
                for y in ROOTDataset._getPaths(x):
                    yield y

        elif isinstance(quantity, DatasetDeclaration.Collection):
            for x in ROOTDataset._getPaths(quantity.items):
                yield x

        elif isinstance(quantity, DatasetDeclaration.Record):
            for field in quantity.fields.values():
                for x in ROOTDataset._getPaths(field):
                    yield x

        elif isinstance(quantity, DatasetDeclaration.Primitive):
            for source in quantity.frm.sources:
                for path in source.paths:
                    yield (path, source.tree)

        else:
            assert False, "expected either a DatasetDeclaration or a Quantity"

    @staticmethod
    def _getBranchesForPaths(quantity, paths):
        if isinstance(quantity, DatasetDeclaration):
            for x in quantity.fields.values():
                ROOTDataset._getBranchesForPaths(x, paths)

        elif isinstance(quantity, DatasetDeclaration.Collection):
            ROOTDataset._getBranchesForPaths(quantity.items, paths)

        elif isinstance(quantity, DatasetDeclaration.Record):
            for field in quantity.fields.values():
                ROOTDataset._getBranchesForPaths(field, paths)

        elif isinstance(quantity, DatasetDeclaration.Primitive):
            for source in quantity.frm.sources:
                for path in source.paths:
                    paths[(path, source.tree)].append((quantity.frm.data, quantity.frm.size))

    @staticmethod
    def _makeGroups(quantity, filesToNumEntries, fileColumnsToLengths, pathsToFiles, name=None):
        if isinstance(quantity, DatasetDeclaration) or isinstance(quantity, DatasetDeclaration.Record):
            nameToSegments = {}
            for k, v in quantity.fields.items():
                if isinstance(quantity, DatasetDeclaration):
                    subname = k
                else:
                    subname = name + "." + k

                for group in ROOTDataset._makeGroups(v, filesToNumEntries, fileColumnsToLengths, pathsToFiles, subname):
                    for n, segment in group.segments.items():
                        if n not in nameToSegments:
                            nameToSegments[n] = []
                        nameToSegments[n].append(segment)

            lastname = None
            numSegments = None
            numEntries = None
            levelToDataLength = {}

            for subname, segments in nameToSegments.items():
                if numSegments is None:
                    numSegments = len(segments)
                elif numSegments != len(segments):
                    raise DatasetDeclaration.Error(quantity.lc, "number of groups in {0} is {1} but in {2} is {3}".format(json.dumps(subname), len(segments), lastname, numSegments))

                if numEntries is None:
                    numEntries = [x.numEntries for x in segments]
                elif numEntries != [x.numEntries for x in segments]:
                    raise DatasetDeclaration.Error(quantity.lc, "entries are partitioned differently in {0} and {1}:\n\n    {2}\n\n    {3}".format(json.dumps(subname), json.dumps(lastname), [x.numEntries for x in segments], numEntries))

                if level(subname) not in levelToDataLength:
                    levelToDataLength[level(subname)] = [x.dataLength for x in segments]
                elif levelToDataLength[level(subname)] != [x.dataLength for x in segments]:
                    raise DatasetDeclaration.Error(quantity.lc, "data lengths of {0} and {1} in the {2} collection are partitioned differently:\n\n    {2}\n\n    {3}".format(json.dumps(subname), json.dumps(lastname), json.dumps(level(subname)), [x.dataLength for x in segments], levelToDataLength[level(subname)]))

                lastname = subname

            if numSegments is None:
                raise DatasetDeclaration.Error(quantity.lc, "record contains no groups")

            return [ROOTGroup(i, dict((n, segments[i]) for n, segments in nameToSegments.items()), numEntries[i]) for i in xrange(numSegments)]

        elif isinstance(quantity, DatasetDeclaration.Collection):
            return ROOTDataset._makeGroups(quantity.items, filesToNumEntries, fileColumnsToLengths, pathsToFiles, name + "[]")

        elif isinstance(quantity, DatasetDeclaration.Primitive):
            segments = []

            groupid = 0
            group = 0
            index = 0
            for source in quantity.frm.sources:
                for path in source.paths:
                    for file in pathsToFiles[(path, source.tree)]:
                        numEntries = filesToNumEntries[(file, source.tree)]
                        dataLength = fileColumnsToLengths[(file, source.tree, quantity.frm.data)]

                        if index != 0 and segments[-1].tree != source.tree:
                            index = 0
                            group += 1

                        if index == 0:
                            segments.append(ROOTSegment(
                                name,
                                name + "@size" if quantity.frm.size is not None else None,
                                numEntries,
                                dataLength,
                                quantity.frm.dtype,
                                [file],
                                source.tree,
                                quantity.frm.data,
                                quantity.frm.size))
                        else:
                            segments[-1].numEntries += numEntries
                            segments[-1].dataLength += dataLength
                            segments[-1].files.append(file)

                        index += 1
                        if index > source.groupsize:
                            index = 0
                            group += 1

            if len(segments) == 0:
                raise DatasetDeclaration.Error(quantity.loc, "quantity contains no groups")

            return [ROOTGroup(i, {name: x}, x.numEntries) for i, x in enumerate(segments)]

        else:
            assert False, "expected either a DatasetDeclaration or a Quantity"

    @staticmethod
    def fromDeclaration(declaration):
        ROOTDataset._sanityCheck(declaration)

        pathsToFiles = {}
        for path, tree in set(ROOTDataset._getPaths(declaration)):
            pathsToFiles[(path, tree)] = []
            for file in filesFromPath(path):
                pathsToFiles[(path, tree)].append(file)

        pathsToBranches = dict((x, []) for x in pathsToFiles)
        ROOTDataset._getBranchesForPaths(declaration, pathsToBranches)

        filesToNumEntries = {}
        fileColumnsToLengths = {}
        for (path, tree), files in pathsToFiles.items():
            for file in files:
                sizeToData = {}
                for dataName, sizeName in pathsToBranches[(path, tree)]:
                    if sizeName is not None:
                        sizeToData[sizeName] = dataName   # get rid of duplicate sizeNames

                dataSizeNoDuplicates = [(dataName, sizeName) for sizeName, dataName in sizeToData.items()]

                lengths = fillarrays(file, tree, [(dataName, sizeName, None, None) for dataName, sizeName in dataSizeNoDuplicates])
                filesToNumEntries[(file, tree)] = int(lengths[0])

                sizeToLength = {}
                for (dataName, sizeName), length in zip(dataSizeNoDuplicates, lengths[1:]):
                    sizeToLength[sizeName] = int(length)

                # no allowing duplicate sizeNames (to get all the dataNames)
                for dataName, sizeName in pathsToBranches[(path, tree)]:
                    if sizeName is None:
                        fileColumnsToLengths[(file, tree, dataName)] = filesToNumEntries[(file, tree)]
                    else:
                        fileColumnsToLengths[(file, tree, dataName)] = sizeToLength[sizeName]

        groups = ROOTDataset._makeGroups(declaration, filesToNumEntries, fileColumnsToLengths, pathsToFiles)

        return ROOTDataset(
            declaration.name,
            dict((k, v.schema) for k, v in declaration.fields.items()),
            groups,
            sum(x.numEntries for x in groups))

    def __init__(self, name, schema, groups, numEntries):
        super(ROOTDataset, self).__init__(name, schema, groups, numEntries)
