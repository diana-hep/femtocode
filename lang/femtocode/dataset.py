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
import re

import numpy

from femtocode.typesystem import Schema
from femtocode.py23 import *

class Metadata(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

sizeType = numpy.uint64

class ColumnName(object):
    recordsep = "-"
    arraytag = "[]"
    sizetag = "@size"

    class Array(object):
        def __repr__(self):
            return "ColumnName.Array()"
        def __eq__(self, other):
            return other.__class__ == ColumnName.Array
        def __hash__(self):
            return hash((ColumnName.Array,))
        def __lt__(self, other):
            if isinstance(other, string_types):
                return other
            elif isinstance(other, ColumnName.Size):
                return other
            else:
                return False

    _array = Array()

    class Size(object):
        def __repr__(self):
            return "ColumnName.Size()"
        def __eq__(self, other):
            return other.__class__ == ColumnName.Size
        def __hash__(self):
            return hash((ColumnName.Size,))
        def __lt__(self, other):
            if isinstance(other, string_types):
                return other
            elif isinstance(other, ColumnName.Array):
                return self
            else:
                return False

    _size = Size()

    @staticmethod
    def parse(string):
        path = []
        while len(string) > 0:
            m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", string)
            if m is not None:
                path.append(m.group(1))
                string = string[len(m.group(1)):]

            elif string.startswith(ColumnName.arraytag):
                path.append(ColumnName._array)
                string = string[len(ColumnName.arraytag):]

            elif string.startswith(ColumnName.sizetag):
                path.append(ColumnName._size)
                string = string[len(ColumnName.sizetag):]

            else:
                raise ValueError("could not parse {0} as a ColumnName".format(string))

            if string.startswith(ColumnName.recordsep):
                string = string[1:]

        return ColumnName(*path)

    def __init__(self, first, *rest):
        self.path = (first,) + rest

    def __repr__(self):
        return "ColumnName({0})".format(", ".join(map(repr, self.path)))

    def __str__(self):
        out = [self.path[0]]
        for x in self.path[1:]:
            if isinstance(x, string_types):
                out.append(self.recordsep + x)
            elif x == self._array:
                out.append(self.arraytag)
            elif x == self._size:
                out.append(self.sizetag)
            else:
                assert False, "unexpected path item in ColumnName: {0}".format(x)
        return "".join(out)

    def __eq__(self, other):
        if isinstance(other, string_types):
            return str(self) == other
        else:
            return other.__class__ == ColumnName and self.path == other.path

    def __req__(self, other):
        return self.__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def __lt__(self, other):
        if other.__class__ == ColumnName:
            return self.path < other.path
        else:
            return self.__class__ < other.__class__

    def rec(self, field):
        return ColumnName(*(self.path + (field,)))

    def array(self):
        return ColumnName(*(self.path + (self._array,)))

    def size(self):
        return ColumnName(*(self.path + (self._size,)))

    def arraylevel(self):
        index = len(self.path)
        while index >= 0:
            index -= 1
            if self.path[index] == ColumnName._array:
                return ColumnName(*self.path[:index])
        return None

    def issize(self):
        return self.path[-1] == self._size

class Segment(Metadata):
    def __init__(self, numEntries, dataLength):
        self.numEntries = numEntries
        self.dataLength = dataLength

    def __repr__(self):
        return "<{0} numEntries={1} dataLength={2} at 0x{3:012x}>".format(self.__class__.__name__, self.numEntries, self.dataLength, id(self))

    def toJson(self):
        return {"numEntries": self.numEntries, "dataLength": self.dataLength}

    @classmethod
    def fromJson(cls, segment):
        return Segment(
            segment["numEntries"],
            segment["dataLength"])

    def __eq__(self, other):
        return other.__class__ == Segment and self.numEntries == other.numEntries and self.dataLength == other.dataLength

    def __hash__(self):
        return hash((Segment, self.numEntries, self.dataLength))

class Group(Metadata):
    def __init__(self, id, segments, numEntries):
        self.id = id
        self.segments = segments
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} id={1} numEntries={2} at 0x{3:012x}>".format(self.__class__.__name__, self.id, self.numEntries, id(self))

    def toJson(self):
        return {"id": self.id, "segments": dict((str(k), v.toJson()) for k, v in self.segments.items()), "numEntries": self.numEntries}

    @classmethod
    def fromJson(cls, group):
        return Group(
            group["id"],
            dict((ColumnName.parse(k), Segment.fromJson(v)) for k, v in group["segments"].items()),
            group["numEntries"])

    def __eq__(self, other):
        return other.__class__ == Group and self.id == other.id and self.segments == other.segments and self.numEntries == other.numEntries

    def __hash__(self):
        return hash((Group, self.id, tuple(self.segments.items()), self.numEntries))

class Column(Metadata):
    def __init__(self, data, size, dataType):
        self.data = data
        self.size = size
        self.dataType = dataType

    def __repr__(self):
        return "<{0} data={1} size={2} at 0x{3:012x}>".format(self.__class__.__name__, self.data, self.size, id(self))

    def toJson(self):
        return {"data": str(self.data), "size": None if self.size is None else str(self.size), "dataType": str(self.dataType)}

    @classmethod
    def fromJson(cls, column):
        return Column(
            ColumnName.parse(column["data"]),
            None if column["size"] is None else ColumnName.parse(column["size"]),
            numpy.dtype(column["dataType"]))

    def __eq__(self, other):
        return other.__class__ == Column and self.data == other.data and self.size == other.size and self.dataType == other.dataType

    def __hash__(self):
        return hash((Column, self.data, self.size, self.dataType))

class Dataset(Metadata):
    def __init__(self, name, schema, columns, groups, numEntries):
        self.name = name
        self.schema = schema
        self.columns = columns
        self.groups = groups
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} name={1} len(groups)={2}, numEntries={3} at 0x{4:012x}>".format(self.__class__.__name__, self.name, len(self.groups), self.numEntries, id(self))

    def toJson(self):
        return {"name": self.name, "schema": dict((k, v.toJson()) for k, v in self.schema.items()), "columns": dict((str(k), v.toJson()) for k, v in self.columns.items()), "groups": [x.toJson() for x in self.groups], "numEntries": self.numEntries}

    @classmethod
    def fromJsonString(cls, dataset):
        return cls.fromJson(json.loads(dataset))

    @classmethod
    def fromJson(cls, dataset):
        return Dataset(
            dataset["name"],
            dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
            dict((ColumnName.parse(k), Column.fromJson(v)) for k, v in dataset["columns"].items()),
            [Group.fromJson(x) for x in dataset["groups"]],
            dataset["numEntries"])

    def __eq__(self, other):
        return other.__class__ == Dataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries

    def __hash__(self):
        return hash((Dataset, self.name, self.schema, tuple(self.columns.items()), tuple(self.groups), self.numEntries))
