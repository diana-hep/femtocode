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
from femtocode.dataset import Column
from femtocode.dataset import Dataset
from femtocode.fromroot.declare import DatasetDeclaration
from femtocode.fromroot._fastreader import fillarrays
from femtocode.fromroot.xrootd import filesFromPath
from femtocode.typesystem import Schema

class ROOTSegment(Segment):
    def __init__(self, numEntries, dataLength, files):
        super(ROOTSegment, self).__init__(numEntries, dataLength)
        self.files = files

    def toJson(self):
        out = super(ROOTSegment, self).toJson()
        out["files"] = self.files
        return out

    @classmethod
    def fromJson(cls, segment):
        out = cls.__new__(cls)
        out.numEntries = segment["numEntries"]
        out.dataLength = segment["dataLength"]
        return out

    @classmethod
    def fromJson(cls, segment):
        return ROOTSegment(
            segment["numEntries"],
            segment["dataLength"],
            segment["files"])

    def __eq__(self, other):
        return other.__class__ == ROOTSegment and self.numEntries == other.numEntries and self.dataLength == other.dataLength and self.files == other.files

    def __hash__(self):
        return hash((ROOTSegment, self.numEntries, self.dataLength, None if self.files is None else tuple(self.files)))

class ROOTGroup(Group):
    def __init__(self, id, segments, numEntries, files):
        super(ROOTGroup, self).__init__(id, segments, numEntries)
        self.files = files

    def toJson(self):
        out = super(ROOTGroup, self).toJson()
        out["files"] = self.files
        return out

    @classmethod
    def fromJson(cls, group):
        return ROOTGroup(
            group["id"],
            dict((k, ROOTSegment.fromJson(v)) for k, v in group["segments"].items()),
            group["numEntries"],
            group["files"])

    def __eq__(self, other):
        return other.__class__ == ROOTGroup and self.id == other.id and self.segments == other.segments and self.numEntries == other.numEntries and self.files == other.files

    def __hash__(self):
        return hash((ROOTGroup, self.id, tuple(self.segments.items()), self.numEntries, None if self.files is None else tuple(self.files)))

class ROOTColumn(Column):
    def __init__(self, data, size, dataType, tree, dataBranch, sizeBranch):
        super(ROOTColumn, self).__init__(data, size, dataType)
        self.tree = tree
        self.dataBranch = dataBranch
        self.sizeBranch = sizeBranch

    def toJson(self):
        out = super(ROOTColumn, self).toJson()
        out["tree"] = self.tree
        out["dataBranch"] = self.dataBranch
        out["sizeBranch"] = self.sizeBranch
        return out

    @classmethod
    def fromJson(cls, column):
        return ROOTColumn(
            column["data"],
            column["size"],
            column["dataType"],
            column["tree"],
            column["dataBranch"],
            column["sizeBranch"])

    def __eq__(self, other):
        return other.__class__ == ROOTColumn and self.data == other.data and self.size == other.size and self.dataType == other.dataType and self.tree == other.tree and self.dataBranch == other.dataBranch and self.sizeBranch == other.sizeBranch

    def __hash__(self):
        return hash((ROOTColumn, self.data, self.size, self.dataType, self.tree, self.dataBranch, self.sizeBranch))

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
                    yield (path, quantity.frm.tree)

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
                    paths[(path, quantity.frm.tree)].append((quantity.frm.data, quantity.frm.size))

    @staticmethod
    def _makeGroups(quantity, filesToNumEntries, fileColumnsToLengths, pathsToFiles, name=None):
        if isinstance(quantity, DatasetDeclaration) or isinstance(quantity, DatasetDeclaration.Record):
            newColumns = {}

            nameToSegments = {}
            for k, v in quantity.fields.items():
                if isinstance(quantity, DatasetDeclaration):
                    subname = k
                else:
                    subname = name + "." + k

                columns, groups = ROOTDataset._makeGroups(v, filesToNumEntries, fileColumnsToLengths, pathsToFiles, subname)

                for n, c in columns.items():
                    assert n not in newColumns
                    newColumns[n] = c

                for group in groups:
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

            newGroups = [ROOTGroup(i, dict((n, segments[i]) for n, segments in nameToSegments.items()), numEntries[i], None) for i in xrange(numSegments)]

            if isinstance(quantity, DatasetDeclaration):
                for group in newGroups:
                    filesets = []
                    filesetCounts = []
                    for segment in group.segments.values():
                        found = False
                        for i, x in enumerate(filesets):
                            if x == segment.files:
                                filesetCounts[i] += 1
                                found = True
                                break
                        if not found:
                            filesets.append(segment.files)
                            filesetCounts.append(1)

                    majorityFiles, count = max(zip(filesets, filesetCounts), key=lambda x: x[1])

                    group.files = majorityFiles
                    for segment in group.segments.values():
                        if segment.files == majorityFiles:
                            segment.files = None

            return newColumns, newGroups

        elif isinstance(quantity, DatasetDeclaration.Collection):
            return ROOTDataset._makeGroups(quantity.items, filesToNumEntries, fileColumnsToLengths, pathsToFiles, name + "[]")

        elif isinstance(quantity, DatasetDeclaration.Primitive):
            column = ROOTColumn(name,
                                name + "@size" if quantity.frm.size is not None else None,
                                quantity.frm.dtype,
                                quantity.frm.tree,
                                quantity.frm.data,
                                quantity.frm.size)
            segments = []

            groupid = 0
            group = 0
            index = 0
            for source in quantity.frm.sources:
                for path in source.paths:
                    for file in pathsToFiles[(path, quantity.frm.tree)]:
                        numEntries = filesToNumEntries[(file, quantity.frm.tree)]
                        dataLength = fileColumnsToLengths[(file, quantity.frm.tree, quantity.frm.data)]

                        if index == 0:
                            segments.append(ROOTSegment(
                                numEntries,
                                dataLength,
                                [file]))
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

            return {name: column}, [ROOTGroup(i, {name: x}, x.numEntries, x.files) for i, x in enumerate(segments)]

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

                # now allowing duplicate sizeNames (to get all the dataNames)
                for dataName, sizeName in pathsToBranches[(path, tree)]:
                    if sizeName is None:
                        fileColumnsToLengths[(file, tree, dataName)] = filesToNumEntries[(file, tree)]
                    else:
                        fileColumnsToLengths[(file, tree, dataName)] = sizeToLength[sizeName]

        columns, groups = ROOTDataset._makeGroups(declaration, filesToNumEntries, fileColumnsToLengths, pathsToFiles)

        return ROOTDataset(
            declaration.name,
            dict((k, v.schema) for k, v in declaration.fields.items()),
            columns,
            groups,
            sum(x.numEntries for x in groups))

    def __init__(self, name, schema, columns, groups, numEntries):
        super(ROOTDataset, self).__init__(name, schema, columns, groups, numEntries)

    @classmethod
    def fromJson(cls, dataset):
        return ROOTDataset(
            dataset["name"],
            dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
            dict((k, ROOTColumn.fromJson(v)) for k, v in dataset["columns"].items()),
            [ROOTGroup.fromJson(x) for x in dataset["groups"]],
            dataset["numEntries"])

    def __eq__(self, other):
        return other.__class__ == ROOTDataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries

    def __hash__(self):
        return hash((ROOTDataset, self.name, self.schema, tuple(self.columns.items()), tuple(self.groups), self.numEntries))
