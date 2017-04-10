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

import ast
import re
import sys
import unittest

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.dataset import *
from femtocode.defs import SymbolTable
from femtocode.lib.standard import StandardLibrary
from femtocode.parser import parse
from femtocode.typesystem import *

class TestStatementlist(unittest.TestCase):
    def runTest(self):
        pass

    def mockDataset(self, **symbolTypes):
        columns = {}
        def build(x, columnName, sizeColumn):
            if isinstance(x, Number):
                columns[columnName] = Column(columnName, sizeColumn, "int64" if x.whole else "float64")

            elif isinstance(x, Collection):
                build(x.items, columnName.coll(), columnName.coll().size())

            elif isinstance(x, Record):
                for fn, ft in x.fields.items():
                    build(ft, columnName.rec(fn), sizeColumn)

            else:
                raise NotImplementedError

        for n, t in symbolTypes.items():
            build(t, ColumnName(n), None)

        return Dataset("Mock", symbolTypes, columns, [], 0, 0)

    def compile(self, code, dataset):
        lt, frame = lispytree.build(parse(code), StandardLibrary.table.fork(dict((n, lispytree.Ref(n)) for n in dataset.schema)))
        tt, frame = typedtree.build(lt, SymbolTable(dict((lispytree.Ref(n), t) for n, t in dataset.schema.items())))
        result, statements, inputs, replacements, refnumber = statementlist.build(tt, dataset)
        return result, statements

    def check(self, observed, expectedjson):
        self.assertEqual(observed.toJson(), expectedjson)
        self.assertEqual(observed, statementlist.Statement.fromJson(expectedjson))
        
    def test_add(self):
        result, statements = self.compile("x + y", self.mockDataset(x=real, y=real))
        self.check(statements, [{"to": "#0", "fcn": "+", "args": ["x", "y"], "schema": "real", "tosize": None}])
        self.check(result, {"name": "#0", "schema": "real", "data": "#0", "size": None})

    def test_add3(self):
        result, statements = self.compile("x + y + z", self.mockDataset(x=real, y=real, z=real))
        self.check(statements, [{"to": "#0", "fcn": "+", "args": ["x", "y", "z"], "schema": "real", "tosize": None}])
        self.check(result, {"name": "#0", "schema": "real", "data": "#0", "size": None})

    def test_subtract(self):
        result, statements = self.compile("x - y", self.mockDataset(x=real, y=real))
        self.check(statements, [{"to": "#0", "fcn": "-", "args": ["x", "y"], "schema": "real", "tosize": None}])
        self.check(result, {"name": "#0", "schema": "real", "data": "#0", "size": None})

    def test_addsub(self):
        result, statements = self.compile("x + y - z", self.mockDataset(x=real, y=real, z=real))
        self.check(statements, [
            {"to": "#0", "fcn": "+", "args": ["x", "y"], "schema": "real", "tosize": None},
            {"to": "#1", "fcn": "-", "args": ["#0", "z"], "schema": "real", "tosize": None}
            ])
        self.check(result, {"name": "#1", "schema": "real", "data": "#1", "size": None})

    def test_mapadd(self):
        result, statements = self.compile("xs.map($1 + y)", self.mockDataset(xs=collection(real), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xs[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xs[]", "#0"], "schema": "real", "tosize": "xs[]@size"}
            ])
        self.check(result, {"name": "#1", "data": "#1", "size": "xs[]@size", "schema": {"type": "collection", "items": "real"}})

    def test_mapmapadd(self):
        result, statements = self.compile("xss.map($1.map($1 + y))", self.mockDataset(xss=collection(collection(real)), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xss[][]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xss[][]", "#0"], "schema": "real", "tosize": "xss[][]@size"}
            ])
        self.check(result, {"name": "#1", "data": "#1", "size": "xss[][]@size", "schema": {"type": "collection", "items": {"type": "collection", "items": "real"}}})

    def test_mapmapadd2(self):
        result, statements = self.compile("xss.map(xs => ys.map(y => xs.map(x => x + y)))", self.mockDataset(xss=collection(collection(real)), ys=collection(real)))
        self.check(statements, [
            {"to": "#0@size", "fcn": "$explodesize", "tosize": ["xss[][]@size", "ys[]@size", "xss[][]@size"]},
            {"to": "#0", "fcn": "$explodedata", "data": "xss[][]", "fromsize": "xss[][]@size", "explodesize": "#0@size", "schema": "real"},
            {"to": "#1", "fcn": "$explodedata", "data": "ys[]", "fromsize": "ys[]@size", "explodesize": "#0@size", "schema": "real"},
            {"to": "#2", "fcn": "+", "args": ["#0", "#1"], "schema": "real", "tosize": "#0@size"}
            ])
        self.check(result, {"name": "#2", "data": "#2", "size": "#0@size", "schema": {"type": "collection", "items": {"type": "collection", "items": {"type": "collection", "items": "real"}}}})

    def test_mapmapadd3(self):
        result, statements = self.compile("xss.map(xs => xs.map(x => ys.map(y => x + y)))", self.mockDataset(xss=collection(collection(real)), ys=collection(real)))
        self.check(statements, [
            {"to": "#0@size", "fcn": "$explodesize", "tosize": ["xss[][]@size", "xss[][]@size", "ys[]@size"]},
            {"to": "#0", "fcn": "$explodedata", "data": "xss[][]", "fromsize": "xss[][]@size", "explodesize": "#0@size", "schema": "real"},
            {"to": "#1", "fcn": "$explodedata", "data": "ys[]", "fromsize": "ys[]@size", "explodesize": "#0@size", "schema": "real"},
            {"to": "#2", "fcn": "+", "args": ["#0", "#1"], "schema": "real", "tosize": "#0@size"}
            ])
        self.check(result, {"name": "#2", "data": "#2", "size": "#0@size", "schema": {"type": "collection", "items": {"type": "collection", "items": {"type": "collection", "items": "real"}}}})

    def test_record(self):
        result, statements = self.compile("x.a + y", self.mockDataset(x=record(a=real), y=real))
        self.check(statements, [{"to": "#0", "fcn": "+", "args": ["x-a", "y"], "schema": "real", "tosize": None}])
        self.check(result, {"name": "#0", "schema": "real", "data": "#0", "size": None})

    def test_recordarray(self):
        result, statements = self.compile("x.a.map($1 + y)", self.mockDataset(x=record(a=collection(real)), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "x-a[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["x-a[]", "#0"], "schema": "real", "tosize": "x-a[]@size"}
            ])
        self.check(result, {"name": "#1", "schema": {"type": "collection", "items": "real"}, "data": "#1", "size": "x-a[]@size"})

    def test_arrayrecord(self):
        result, statements = self.compile("xs.map($1.b + y)", self.mockDataset(xs=collection(record(a=real, b=real)), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xs[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xs[]-b", "#0"], "schema": "real", "tosize": "xs[]@size"}
            ])
        self.check(result, {"name": "#1", "schema": {"type": "collection", "items": "real"}, "data": "#1", "size": "xs[]@size"})

    def test_arrayrecord2(self):
        result, statements = self.compile("xs.map($1.b + y)", self.mockDataset(xs=collection(record(a=collection(real), b=real)), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xs[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xs[]-b", "#0"], "schema": "real", "tosize": "xs[]@size"}
            ])
        self.check(result, {"name": "#1", "schema": {"type": "collection", "items": "real"}, "data": "#1", "size": "xs[]@size"})

    def test_arrayrecord3(self):
        result, statements = self.compile("xs.map($1.a.map($1 + y))", self.mockDataset(xs=collection(record(a=collection(real), b=real)), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xs[]-a[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xs[]-a[]", "#0"], "schema": "real", "tosize": "xs[]-a[]@size"}
            ])
        self.check(result, {"name": "#1", "schema": {"type": "collection", "items": {"type": "collection", "items": "real"}}, "data": "#1", "size": "xs[]-a[]@size"})

    def test_arrayrecord4(self):
        result, statements = self.compile("xs.map($1.b.c + y)", self.mockDataset(xs=collection(record(a=collection(real), b=record(c=real))), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xs[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xs[]-b-c", "#0"], "schema": "real", "tosize": "xs[]@size"}
            ])
        self.check(result, {"name": "#1", "schema": {"type": "collection", "items": "real"}, "data": "#1", "size": "xs[]@size"})

    def test_arrayrecord5(self):
        result, statements = self.compile("xs.map($1.b.map($1.c + y))", self.mockDataset(xs=collection(record(a=collection(real), b=collection(record(c=real)))), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xs[]-b[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xs[]-b[]-c", "#0"], "schema": "real", "tosize": "xs[]-b[]@size"}
            ])
        self.check(result, {"name": "#1", "schema": {"type": "collection", "items": {"type": "collection", "items": "real"}}, "data": "#1", "size": "xs[]-b[]@size"})

    def test_arrayrecord6(self):
        result, statements = self.compile("xs.map($1.b.c.map($1 + y))", self.mockDataset(xs=collection(record(a=collection(real), b=record(c=collection(real)))), y=real))
        self.check(statements, [
            {"to": "#0", "fcn": "$explode", "data": "y", "tosize": "xs[]-b-c[]@size", "schema": "real"},
            {"to": "#1", "fcn": "+", "args": ["xs[]-b-c[]", "#0"], "schema": "real", "tosize": "xs[]-b-c[]@size"}
            ])
        self.check(result, {"name": "#1", "schema": {"type": "collection", "items": {"type": "collection", "items": "real"}}, "data": "#1", "size": "xs[]-b-c[]@size"})
