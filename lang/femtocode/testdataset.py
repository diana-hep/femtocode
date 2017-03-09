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
from collections import namedtuple

from femtocode.dataset import *
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.workflow import Source
from femtocode.execution import Executor

class TestSegment(Segment):
    def __init__(self, numEntries, dataLength, sizeLength, data, size):
        super(TestSegment, self).__init__(numEntries, dataLength, sizeLength)
        self.data = data
        self.size = size

    def toJson(self):
        out = super(TestSegment, self).toJson()
        out["data"] = self.data
        out["size"] = self.size
        return out

    @staticmethod
    def fromJson(segment):
        return TestSegment(
            segment["numEntries"],
            segment["dataLength"],
            segment["sizeLength"],
            segment["data"],
            segment["size"])

    def __eq__(self, other):
        return other.__class__ == TestSegment and self.numEntries == other.numEntries and self.dataLength == other.dataLength and self.sizeLength == other.sizeLength and self.data == other.data

    def __hash__(self):
        return hash(("TestSegment", self.numEntries, self.dataLength, self.sizeLength, tuple(self.data)))

class TestGroup(Group):
    def __init__(self, id, segments, numEntries):
        super(TestGroup, self).__init__(id, segments, numEntries)

    def toJson(self):
        return super(TestGroup, self).toJson()

    @staticmethod
    def fromJson(group):
        return TestGroup(
            group["id"],
            dict((ColumnName.parse(k), TestSegment.fromJson(v)) for k, v in group["segments"].items()),
            group["numEntries"])

    def __eq__(self, other):
        return other.__class__ == TestGroup and self.id == other.id and self.segments == other.segments and self.numEntries == other.numEntries

    def __hash__(self):
        return hash(("TestGroup", self.id, tuple(sorted(self.segments.items())), self.numEntries))

class TestColumn(Column):
    def __init__(self, data, size, dataType):
        super(TestColumn, self).__init__(data, size, dataType)

    def toJson(self):
        return super(TestColumn, self).toJson()

    @staticmethod
    def fromJson(column):
        return TestColumn(
            ColumnName.parse(column["data"]),
            None if column["size"] is None else ColumnName.parse(column["size"]),
            column["dataType"])

    def __eq__(self, other):
        return other.__class__ == TestColumn and self.data == other.data and self.size == other.size and self.dataType == other.dataType

    def __hash__(self):
        return hash(("TestColumn", self.data, self.size, self.dataType))

class TestDataset(Dataset):
    def __init__(self, name, schema, columns, groups, numEntries):
        super(TestDataset, self).__init__(name, schema, columns, groups, numEntries)

        self.types = {None: namedtuple(name, sorted(self.schema))}
        def gettypes(n, t):
            if isinstance(t, Collection):
                gettypes(n.coll(), t.items)

            elif isinstance(t, Record):
                self.types[n] = namedtuple(str(n).replace(ColumnName.colltag, "").replace(ColumnName.recordsep, "_"), sorted(t.fields))
                for fn, ft in t.fields.items():
                    gettypes(n.rec(fn), ft)

            elif isinstance(t, Union):
                raise NotImplementedError

        for n, t in self.schema.items():
            gettypes(ColumnName(n), t)

    @staticmethod
    def fromJson(dataset):
        return TestDataset(
            dataset["name"],
            dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
            dict((ColumnName.parse(k), TestColumn.fromJson(v)) for k, v in dataset["columns"].items()),
            [TestGroup.fromJson(x) for x in dataset["groups"]],
            dataset["numEntries"])

    def __eq__(self, other):
        return other.__class__ == TestDataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries

    def __hash__(self):
        return hash(("TestDataset", self.name, tuple(sorted(self.schema.items())), tuple(sorted(self.columns.items())), tuple(self.groups), self.numEntries))

    @staticmethod
    def fromSchema(name, asdict=None, **askwds):
        if asdict is None:
            schema = {}
        else:
            schema = dict(asdict)
        schema.update(askwds)

        columns = {}
        def getcolumns(n, t, hasSize):
            if isinstance(t, Null):
                raise NotImplementedError

            elif isinstance(t, (Boolean, Number)):
                if isinstance(t, Boolean):
                    dataType = "bool"
                elif t.whole:
                    dataType = "int"
                else:
                    dataType = "float"

                columns[n] = TestColumn(n, n.size() if hasSize else None, dataType)

            elif isinstance(t, String):
                raise NotImplementedError

            elif isinstance(t, Collection):
                getcolumns(n.coll(), t.items, True)

            elif isinstance(t, Record):
                for fn, ft in t.fields.items():
                    getcolumns(n.rec(fn), ft, hasSize)

            elif isinstance(t, Union):
                raise NotImplementedError

            else:
                assert False, "unexpected type: {0} {1}".format(type(t), t)

        for n, t in schema.items():
            getcolumns(ColumnName(n), t, False)

        out = TestDataset(name, schema, columns, [], 0)
        for n, c in out.columns.items():
            c.size = out.sizeColumn(n)    # point all equivalent size columns to the first, alphabetically
        return out

    def clear(self):
        self.groups = []
        self.numEntries = 0

    def newGroup(self):
        self.groups.append(TestGroup(len(self.groups), dict((n, TestSegment(0, 0, 0, [], [] if c.size == n.size() else None)) for n, c in self.columns.items()), 0))

    def _fill(self, group, datum, name, schema):
        if datum not in schema:
            raise FemtocodeError("Datum {0} is not an instance of schema:\n\n{1}".format(datum, pretty(schema, prefix="    ")))

        if isinstance(schema, Null):
            raise NotImplementedError

        elif isinstance(schema, (Boolean, Number)):
            segment = group.segments[name]

            if isinstance(schema, Boolean):
                d = True if datum else False
            elif schema.whole:
                d = int(datum)
            else:
                d = float(datum)

            segment.data.append(d)
            segment.dataLength += 1

        elif isinstance(schema, String):
            raise NotImplementedError

        elif isinstance(schema, Collection):
            sz = len(datum)
            for n, s in group.segments.items():
                if n.startswith(name) and s.size is not None:
                    s.size.append(sz)
            coll = name.coll()
            items = schema.items
            for x in datum:
                self._fill(group, x, coll, items)

        elif isinstance(schema, Record):
            for fn, ft in schema.fields.items():
                try:
                    sub = getattr(datum, fn)
                except AttributeError:
                    try:
                        sub = datum[fn]
                    except KeyError:
                        raise FemtocodeError("Datum {0} does not have an attribute or item \"{1}\" whereas the schema requires it:\n\n{2}".format(datum, fn, pretty(schema, prefix="    ")))

                self._fill(group, sub, name.rec(fn), ft)

        elif isinstance(schema, Union):
            raise NotImplementedError

        else:
            assert False, "unexpected type: {0} {1}".format(type(schema), schema)

    def fill(self, datum, groupLimit=None):
        if len(self.groups) == 0 or (groupLimit is not None and self.groups[-1].numEntries >= groupLimit):
            self.newGroup()
        group = self.groups[-1]

        for n, t in self.schema.items():
            try:
                sub = getattr(datum, n)
            except AttributeError:
                try:
                    sub = datum[n]
                except KeyError:
                    raise FemtocodeError("Datum {0} does not have an attribute or item \"{1}\" whereas the schema requires it:\n\n{2}".format(datum, n, pretty(schema, prefix="    ")))

            self._fill(group, sub, ColumnName(n), t)

        for segment in group.segments.values():
            segment.numEntries += 1
        group.numEntries += 1
        self.numEntries += 1

    def fillall(self, data, groupLimit=None):
        for datum in data:
            self.fill(datum, groupLimit)

    class TestDatasetIterator(object):
        def __init__(self, dataset):
            self.dataset = dataset
            self.groupIndex = 0
            self.entryInGroupIndex = 0
            self.dataIndex = dict((n, 0) for n, c in self.dataset.columns.items())
            self.sizeIndex = dict((n, 0) for n, c in self.dataset.columns.items() if c.size == n.size())

        def _next(self, group, name, schema):
            if isinstance(schema, Null):
                raise NotImplementedError

            elif isinstance(schema, (Boolean, Number)):
                i = self.dataIndex[name]
                self.dataIndex[name] += 1
                return group.segments[name].data[i]

            elif isinstance(schema, String):
                raise NotImplementedError

            elif isinstance(schema, Collection):
                sz = None
                for n, s in group.segments.items():
                    if n.startswith(name) and s.size is not None:
                        i = self.sizeIndex[n]
                        self.sizeIndex[n] += 1
                        if sz is None:
                            sz = s.size[i]
                        else:
                            assert sz == s.size[i], "misaligned collection index"

                assert sz is not None, "missing collection index"

                coll = name.coll()
                items = schema.items
                return [self._next(group, coll, items) for i in xrange(sz)]

            elif isinstance(schema, Record):
                nt = self.dataset.types[name]
                return nt(*[self._next(group, name.rec(fn), schema.fields[fn]) for fn in nt._fields])

            elif isinstance(schema, Union):
                raise NotImplementedError

            else:
                assert False, "unexpected type: {0} {1}".format(type(schema), schema)

        def __next__(self):
            if self.groupIndex >= len(self.dataset.groups):
                raise StopIteration
            group = self.dataset.groups[self.groupIndex]

            nt = self.dataset.types[None]
            out = nt(*[self._next(group, ColumnName(n), self.dataset.schema[n]) for n in nt._fields])

            self.entryInGroupIndex += 1

            if self.entryInGroupIndex >= group.numEntries:
                self.groupIndex += 1
                self.entryInGroupIndex = 0
                for n in self.dataIndex:
                    self.dataIndex[n] = 0
                for n in self.sizeIndex:
                    self.sizeIndex[n] = 0

            return out

        def next(self):
            return self.__next__()

    def __iter__(self):
        return TestDataset.TestDatasetIterator(self)

class TestSession(object):
    def source(self, name, asdict=None, **askwds):
        return Source(self, TestDataset.fromSchema(name, asdict, **askwds))

    def submit(self, query):
        executor = Executor(query)

        tally = executor.initialize()

        for group in query.dataset.groups:
            subtally = executor.run(executor.inarrays(group), group)
            executor.update(tally, subtally)

        return executor.finalize(tally)
