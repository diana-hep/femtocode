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

import numpy

from femtocode.dataset import ColumnName
from femtocode.dataset import Segment
from femtocode.dataset import Group
from femtocode.dataset import Column
from femtocode.dataset import Dataset

class NumpySegment(Segment):
    def __init__(self, numEntries, dataLength, sizeLength, files):
        super(NumpySegment, self).__init__(numEntries, dataLength, sizeLength)
        self.files = files

    def toJson(self):
        out = super(NumpySegment, self).toJson()
        out["files"] = self.files
        return out

    @staticmethod
    def fromJson(segment):
        return NumpySegment(
            segment["numEntries"],
            segment["dataLength"],
            segment["sizeLength"],
            segment["files"])

    def __eq__(self, other):
        return other.__class__ == NumpySegment and self.numEntries == other.numEntries and self.dataLength == other.dataLength and self.sizeLength == other.sizeLength and self.files == other.files

    def __hash__(self):
        return hash(("NumpySegment", self.numEntries, self.dataLength, self.sizeLength, None if self.files is None else tuple(self.files)))

class NumpyGroup(Group):
    def __init__(self, id, segments, numEntries, files):
        super(NumpyGroup, self).__init__(id, segments, numEntries)
        self.files = files

    def toJson(self):
        out = super(NumpyGroup, self).toJson()
        out["files"] = self.files
        return out

    @staticmethod
    def fromJson(group):
        return NumpyGroup(
            group["id"],
            dict((ColumnName.parse(k), NumpySegment.fromJson(v)) for k, v in group["segments"].items()),
            group["numEntries"],
            group["files"])

    def __eq__(self, other):
        return other.__class__ == NumpyGroup and self.id == other.id and self.segments == other.segments and self.numEntries == other.numEntries and self.files == other.files

    def __hash__(self):
        return hash(("NumpyGroup", self.id, tuple(sorted(self.segments.items())), self.numEntries, None if self.files is None else tuple(self.files)))

class NumpyColumn(Column):
    def __init__(self, data, size, dataType):
        super(NumpyColumn, self).__init__(data, size, dataType)

    def toJson(self):
        return super(NumpyColumn, self).toJson()

    @staticmethod
    def fromJson(column):
        return NumpyColumn(
            ColumnName.parse(column["data"]),
            None if column["size"] is None else ColumnName.parse(column["size"]),
            column["dataType"])

    def __eq__(self, other):
        return other.__class__ == NumpyColumn and self.data == other.data and self.size == other.size and self.dataType == other.dataType

    def __hash__(self):
        return hash(("NumpyColumn", self.data, self.size, self.dataType))

class NumpyDataset(Dataset):
    def __init__(self, name, schema, columns, groups, numEntries):
        super(NumpyDataset, self).__init__(name, schema, columns, groups, numEntries)

    @staticmethod
    def fromJson(dataset):
        return NumpyDataset(
            dataset["name"],
            dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
            dict((ColumnName.parse(k), NumpyColumn.fromJson(v)) for k, v in dataset["columns"].items()),
            [NumpyGroup.fromJson(x) for x in dataset["groups"]],
            dataset["numEntries"])

    def __eq__(self, other):
        return other.__class__ == NumpyDataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries

    def __hash__(self):
        return hash(("NumpyDataset", self.name, tuple(sorted(self.schema.items())), tuple(sorted(self.columns.items())), tuple(self.groups), self.numEntries))
