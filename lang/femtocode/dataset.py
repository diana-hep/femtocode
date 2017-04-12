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

import importlib
import json
import os
import re

from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.util import *

sizeType = "uint64"
        
class ColumnName(object):
    recordsep = "-"
    colltag = "[]"
    sizetag = "@size"

    class Coll(object):
        def __repr__(self):
            return "ColumnName.Coll()"
        def __eq__(self, other):
            return other.__class__ == ColumnName.Coll
        def __hash__(self):
            return hash(("ColumnName.Coll",))
        def __lt__(self, other):
            if isinstance(other, string_types):
                return other
            elif isinstance(other, ColumnName.Size):
                return other
            else:
                return False

    _coll = Coll()

    class Size(object):
        def __repr__(self):
            return "ColumnName.Size()"
        def __eq__(self, other):
            return other.__class__ == ColumnName.Size
        def __hash__(self):
            return hash(("ColumnName.Size",))
        def __lt__(self, other):
            if isinstance(other, string_types):
                return other
            elif isinstance(other, ColumnName.Coll):
                return self
            else:
                return False

    _size = Size()

    @staticmethod
    def parse(string):
        path = []
        while len(string) > 0:
            m = re.match(r"^([a-zA-Z_#][a-zA-Z0-9_]*)", string)
            if m is not None:
                path.append(m.group(1))
                string = string[len(m.group(1)):]

            elif string.startswith(ColumnName.colltag):
                path.append(ColumnName._coll)
                string = string[len(ColumnName.colltag):]

            elif string.startswith(ColumnName.sizetag):
                path.append(ColumnName._size)
                string = string[len(ColumnName.sizetag):]

            else:
                raise ValueError("could not parse {0} as a ColumnName".format(string))

            if string.startswith(ColumnName.recordsep):
                string = string[1:]

        return ColumnName(*path)

    def __init__(self, first, *rest):
        if isinstance(first, int):
            assert len(rest) == 0, "temporary column arrays have no substructure"
            self.path = ("#" + repr(first),)
        else:
            self.path = (first,) + rest

    def __repr__(self):
        return "ColumnName.parse({0})".format(json.dumps(str(self)))

    def __str__(self):
        out = [self.path[0]]
        for x in self.path[1:]:
            if isinstance(x, string_types):
                out.append(self.recordsep + x)
            elif x == self._coll:
                out.append(self.colltag)
            elif x == self._size:
                out.append(self.sizetag)
            else:
                assert False, "unexpected path item in ColumnName: {0}".format(x)
        return "".join(out)

    def __eq__(self, other):
        if isinstance(other, string_types):
            return self == ColumnName.parse(other)
        else:
            return other.__class__ == ColumnName and self.path == other.path

    def __req__(self, other):
        return self.__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __rne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def __lt__(self, other):
        if other.__class__ == ColumnName:
            return self.path < other.path
        else:
            return self.__class__ < other.__class__

    def rec(self, field):
        return ColumnName(*(self.path + (field,)))

    def coll(self):
        return ColumnName(*(self.path + (self._coll,)))

    def size(self):
        return ColumnName(*(self.path + (self._size,)))

    def level(self):
        index = len(self.path)
        while index >= 0:
            index -= 1
            if self.path[index] == ColumnName._coll:
                return ColumnName(*self.path[:index])
        return None

    def samelevel(self, other):
        return self.level() is not None and self.level() == other.level()

    def issize(self):
        return self.path[-1] == self._size

    def depth(self):
        return self.path.count(ColumnName._coll)

    def explosions(self):
        out = []
        for i in range(1, len(self.path) + 1):
            if self.path[i - 1] == ColumnName._coll:
                out.append(ColumnName(*self.path[:i]))
        return tuple(out)

    def istmp(self):
        return self.path[0].startswith("#")

    def startswith(self, prefix):
        return len(prefix.path) <= len(self.path) and self.path[:len(prefix.path)] == prefix.path

def progressionOf(explosions, sizeColumn):
    if not progression(explosions):
        return False

    if len(explosions) == 0:
        return sizeColumn is None
    else:
        return sizeColumn == explosions[-1].size()

def progression(explosions):
    if len(explosions) == 0:
        return True

    last = explosions[-1]
    depth = last.depth()
    for x in reversed(explosions[:-1]):
        if x.depth() != depth - 1 or not last.startswith(x):
            return False
        last = x
        depth -= 1

    return depth == 1

def explosionsToSizes(explosions):
    uniques = []
    for explosion in reversed(explosions):
        found = False
        for unique in uniques:
            if unique.startswith(explosion):
                found = True

        if not found:
            uniques.append(explosion.size())

    return list(reversed(uniques))

class Metadata(Serializable): pass

class Segment(Metadata):
    def __init__(self, numEntries, dataLength, sizeLength):
        self.numEntries = numEntries
        self.dataLength = dataLength
        self.sizeLength = sizeLength

    def __repr__(self):
        return "<{0} numEntries={1} dataLength={2} sizeLength={3} at 0x{4:012x}>".format(self.__class__.__name__, self.numEntries, self.dataLength, self.sizeLength, id(self))

    def toJson(self):
        return {"numEntries": self.numEntries, "dataLength": self.dataLength, "sizeLength": self.sizeLength}

    @staticmethod
    def fromJson(segment):
        return Segment(
            segment["numEntries"],
            segment["dataLength"],
            segment["sizeLength"])

    def __eq__(self, other):
        return other.__class__ == Segment and self.numEntries == other.numEntries and self.dataLength == other.dataLength and self.sizeLength == other.sizeLength

    def __hash__(self):
        return hash(("Segment", self.numEntries, self.dataLength, self.sizeLength))

class Group(Metadata):
    def __init__(self, id, segments, numEntries):
        self.id = id
        self.segments = segments
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} id={1} numEntries={2} at 0x{3:012x}>".format(self.__class__.__name__, self.id, self.numEntries, id(self))

    def toJson(self):
        return {"id": self.id, "segments": dict((str(k), v.toJson()) for k, v in self.segments.items()), "numEntries": self.numEntries}

    @staticmethod
    def fromJson(group):
        return Group(
            group["id"],
            dict((ColumnName.parse(k), Segment.fromJson(v)) for k, v in group["segments"].items()),
            group["numEntries"])

    def __eq__(self, other):
        return other.__class__ == Group and self.id == other.id and self.segments == other.segments and self.numEntries == other.numEntries

    def __hash__(self):
        return hash(("Group", self.id, tuple(sorted(self.segments.items())), self.numEntries))

class Column(Metadata):
    def __init__(self, data, size, dataType):
        self.data = data
        self.size = size
        self.dataType = dataType

    def __repr__(self):
        return "<{0} data={1} size={2} at 0x{3:012x}>".format(self.__class__.__name__, self.data, self.size, id(self))

    def toJson(self):
        return {"data": str(self.data), "size": None if self.size is None else str(self.size), "dataType": str(self.dataType)}

    @staticmethod
    def fromJson(column):
        return Column(
            ColumnName.parse(column["data"]),
            None if column["size"] is None else ColumnName.parse(column["size"]),
            column["dataType"])

    def __eq__(self, other):
        return other.__class__ == Column and self.data == other.data and self.size == other.size and self.dataType == other.dataType

    def __hash__(self):
        return hash(("Column", self.data, self.size, self.dataType))

class Dataset(Metadata):
    def __init__(self, name, schema, columns, groups, numEntries, numGroups):
        self.name = name
        self.schema = schema
        self.columns = columns
        self.groups = groups
        self.numEntries = numEntries
        self.numGroups = numGroups

    def strip(self):
        # remove class specialization and per-group information (femtocode-run or femtocode-server will reconstruct it by name from the metadata database)
        return Dataset(self.name, self.schema, self.columns, [], self.numEntries, self.numGroups)

    def __repr__(self):
        return "<{0} name={1} numEntries={2} numGroups={3} at 0x{4:012x}>".format(self.__class__.__name__, self.name, self.numEntries, self.numGroups, id(self))

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "name": self.name,
                "schema": None if self.schema is None else dict((k, v.toJson()) for k, v in self.schema.items()),
                "columns": dict((str(k), v.toJson()) for k, v in self.columns.items()),
                "groups": [x.toJson() for x in self.groups],
                "numEntries": self.numEntries,
                "numGroups": self.numGroups}

    @staticmethod
    def fromJson(dataset, ignoreclass=False):
        assert isinstance(dataset, dict)
        assert "class" in dataset

        mod = dataset["class"][:dataset["class"].rindex(".")]
        cls = dataset["class"][dataset["class"].rindex(".") + 1:]
        
        if ignoreclass or (mod == Dataset.__module__ and cls == Dataset.__name__):
            return Dataset(
                dataset["name"],
                None if dataset["schema"] is None else dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
                dict((ColumnName.parse(k), Column.fromJson(v)) for k, v in dataset["columns"].items()),
                [Group.fromJson(x) for x in dataset["groups"]],
                dataset["numEntries"],
                dataset["numGroups"])
        else:
            return getattr(importlib.import_module(mod), cls).fromJson(dataset)

    def __eq__(self, other):
        return other.__class__ == Dataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries and self.numGroups == other.numGroups

    def __hash__(self):
        return hash(("Dataset", self.name, tuple(sorted(self.schema.items())), tuple(sorted(self.columns.items())), tuple(self.groups), self.numEntries, self.numGroups))

    def dataColumn(self, columnName):
        if isinstance(columnName, string_types):
            columnName = ColumnName(columnName)

        schema = self.schema[columnName.path[0]]
        for i, item in enumerate(columnName.path[1:]):
            if isinstance(item, string_types):
                assert isinstance(schema, Record), "column {0} not a Record at {1}".format(columnName, ColumnName(*columnName.path[:i+2]))
                schema = schema.fields[item]

            elif isinstance(item, ColumnName.Coll):
                assert isinstance(schema, Collection), "column {0} not a Collection at {1}".format(columnName, ColumnName(*columnName.path[:i+2]))
                schema = schema.items

            else:
                assert False, "unexpected item in ColumnName for data: {0}".format(item)

        if columnName in self.columns:
            return self.columns[columnName].data
        else:
            return None

    def sizeColumn(self, columnName):
        if isinstance(columnName, string_types):
            columnName = ColumnName(columnName)

        schema = self.schema[columnName.path[0]]
        for i, item in enumerate(columnName.path[1:]):
            if isinstance(item, string_types):
                assert isinstance(schema, Record), "column {0} not a Record at {1}".format(columnName, ColumnName(*columnName.path[:i+2]))
                schema = schema.fields[item]

            elif isinstance(item, ColumnName.Coll):
                assert isinstance(schema, Collection), "column {0} not a Collection at {1}".format(columnName, ColumnName(*columnName.path[:i+2]))
                schema = schema.items

            else:
                assert False, "unexpected item in ColumnName for data: {0}".format(item)

        if columnName in self.columns:
            return self.columns[columnName].size
        else:
            for c in self.columns.values():
                if c.size == columnName.size():
                    return c.size
            return None

class MetadataFromJson(object):
    def __init__(self, directory="."):
        self.directory = directory
        self._cache = {}

    def dataset(self, name, groups=(), columns=None, schema=True):
        key = (name, tuple(sorted(groups)), None if columns is None else tuple(sorted(columns)), schema)
        if key not in self._cache:
            fileName = os.path.join(self.directory, name) + ".json"
            try:
                file = open(fileName)
            except IOError:
                raise IOError("dataset {0} not found (no file named {1})".format(name, fileName))

            # get the whole dataset (only thing you can do from a plain text file)
            dataset = Dataset.fromJson(json.loads(file.read()))

            # drop groups if not requested
            todrop = []
            for i, group in enumerate(dataset.groups):
                if group.id not in groups:
                    todrop.append(i)
            while len(todrop) > 0:
                del dataset.groups[todrop.pop()]

            # drop columns if not requested
            if columns is not None:
                for column in list(dataset.columns):
                    if column not in columns:
                        del dataset.columns[column]
                for group in dataset.groups:
                    todrop = []
                    for n, seg in group.segments.items():
                        if n not in columns:
                            todrop.append(n)
                    while len(todrop) > 0:
                        del group.segments[todrop.pop()]

            # drop schema if not requested
            if not schema:
                dataset.schema = {}

            self._cache[key] = dataset

        return self._cache[key]

def schemaToColumns(name, schema, dtype=True, sizeColumn=None):
    if isinstance(schema, Null):
        raise NotImplementedError   # not sure what I would do with this

    elif isinstance(schema, Boolean):
        return {name: Column(name, sizeColumn, "bool")}

    elif isInt(schema) or isNullInt(schema):
        return {name: Column(name, sizeColumn, "int64" if dtype else "int")}

    elif isFloat(schema) or isNullFloat(schema):
        return {name: Column(name, sizeColumn, "float64" if dtype else "float")}

    elif isinstance(schema, String):
        raise NotImplementedError   # TODO

    elif isinstance(schema, Collection):
        return schemaToColumns(name.coll(), schema.items, dtype, name.coll().size())

    elif isinstance(schema, Record):
        out = {}
        for fn, ft in schema.fields.items():
            out.update(schemaToColumns(name.rec(fn), ft, dtype, sizeColumn))
        return out

    elif isinstance(schema, Union):
        raise NotImplementedError   # TODO

    else:
        assert False, "unexpected type: {0} {1}".format(type(schema), schema)

def schemasToColumns(namesToSchemas, dtype=True):
    columns = {}
    for n, t in namesToSchemas.items():
        if not isinstance(n, ColumnName):
            n = ColumnName(n)
        columns.update(schemaToColumns(n, t, dtype, None))
    return columns
