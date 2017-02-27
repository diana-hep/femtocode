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

import femtocode.asts.lispytree as lispytree
import femtocode.asts.typedtree as typedtree
import femtocode.asts.statementlist as statementlist
from femtocode.defs import SymbolTable
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.dataset import *
from femtocode.typesystem import *

import numpy

import sys

# dataset = MetadataFromJson(Dataset, "/home/pivarski/diana/femtocode/tests").dataset("MuOnia")

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestStatementlist(unittest.TestCase):
    def runTest(self):
        pass

    def mockDataset(self, **symbolTypes):
        columns = {}
        def build(x, columnName, hasSize):
            if isinstance(x, Number):
                columns[columnName] = Column(
                    columnName,
                    columnName.size() if hasSize else None,
                    numpy.dtype(numpy.int64) if x.whole else numpy.dtype(numpy.float64))

            elif isinstance(x, Collection):
                build(x.items, columnName.array(), True)

            elif isinstance(x, Record):
                for fn, ft in x.fields.items():
                    build(ft, columnName.rec(fn), hasSize)

            else:
                raise NotImplementedError

        for n, t in symbolTypes.items():
            build(t, ColumnName(n), False)

        return Dataset("Dummy", symbolTypes, columns, [], 0)

    def compile(self, code, dataset):
        lt, frame = lispytree.build(parse(code), table.fork(dict((n, lispytree.Ref(n)) for n in dataset.schema)))
        tt, frame = typedtree.build(lt, SymbolTable(dict((lispytree.Ref(n), t) for n, t in dataset.schema.items())))
        result, statements, refnumber = statementlist.build(tt, dataset)
        return result, statements

    def test_add(self):
        result, statements = self.compile("x + y", self.mockDataset(x=real, y=real))
        self.assertEqual(statements.toJson(), [{"to": "#0", "fcn": "+", "args": ["x", "y"]}])
        self.assertEqual(result.toJson(), {"schema": "real", "data": "#0", "size": None})

    def test_add3(self):
        result, statements = self.compile("x + y + z", self.mockDataset(x=real, y=real, z=real))
        self.assertEqual(statements.toJson(), [{"to": "#0", "fcn": "+", "args": ["x", "y", "z"]}])
        self.assertEqual(result.toJson(), {"schema": "real", "data": "#0", "size": None})

    def test_subtract(self):
        result, statements = self.compile("x - y", self.mockDataset(x=real, y=real))
        self.assertEqual(statements.toJson(), [{"to": "#0", "fcn": "-", "args": ["x", "y"]}])
        self.assertEqual(result.toJson(), {"schema": "real", "data": "#0", "size": None})

    def test_addsub(self):
        result, statements = self.compile("x + y - z", self.mockDataset(x=real, y=real, z=real))
        self.assertEqual(statements.toJson(), [
            {"to": "#0", "fcn": "+", "args": ["x", "y"]},
            {"to": "#1", "fcn": "-", "args": ["#0", "z"]}
            ])
        self.assertEqual(result.toJson(), {"schema": "real", "data": "#1", "size": None})

    def test_mapadd(self):
        result, statements = self.compile("xs.map($1 + y)", self.mockDataset(xs=collection(real), y=real))
        self.assertEqual(statements.toJson(), [
            {"to": "#0", "fcn": "$explode", "data": "y", "size": "xs[]@size"},
            {"to": "#1", "fcn": "+", "args": ["xs[]", "#0"]}
            ])
        self.assertEqual(result.toJson(), {"data": "#1", "size": "xs[]@size", "schema": {"type": "collection", "items": "real"}})

    def test_mapmapadd(self):
        result, statements = self.compile("xss.map($1.map($1 + y))", self.mockDataset(xss=collection(collection(real)), y=real))
        self.assertEqual(statements.toJson(), [
            {"to": "#0", "fcn": "$explode", "data": "y", "size": "xss[][]@size"},
            {"to": "#1", "fcn": "+", "args": ["xss[][]", "#0"]}
            ])
        self.assertEqual(result.toJson(), {"data": "#1", "size": "xss[][]@size", "schema": {"type": "collection", "items": {"type": "collection", "items": "real"}}})

    def test_mapmapadd2(self):
        result, statements = self.compile("xss.map(xs => ys.map(y => xs.map(x => x + y)))", self.mockDataset(xss=collection(collection(real)), ys=collection(real)))
        self.assertEqual(statements.toJson(), [
            {"to": "#0@size", "fcn": "$explodesize", "levels": ["ys[]@size", "xss[][]@size"]},
            {"to": "#0", "fcn": "$explodedata", "data": "xss[][]", "size": "xss[][]@size", "levels": ["ys[]@size", "xss[][]@size"]},
            {"to": "#1", "fcn": "$explodedata", "data": "ys[]", "size": "ys[]@size", "levels": ["ys[]@size", "xss[][]@size"]},
            {"to": "#2", "fcn": "+", "args": ["#0", "#1"]}
            ])
        self.assertEqual(result.toJson(), {"data": "#2", "size": "#0@size", "schema": {"type": "collection", "items": {"type": "collection", "items": {"type": "collection", "items": "real"}}}})

    def test_mapmapadd3(self):
        result, statements = self.compile("xss.map(xs => xs.map(x => ys.map(y => x + y)))", self.mockDataset(xss=collection(collection(real)), ys=collection(real)))
        self.assertEqual(statements.toJson(), [
            {"to": "#0@size", "fcn": "$explodesize", "levels": ["xss[][]@size", "ys[]@size"]},
            {"to": "#0", "fcn": "$explodedata", "data": "xss[][]", "size": "xss[][]@size", "levels": ["xss[][]@size", "ys[]@size"]},
            {"to": "#1", "fcn": "$explodedata", "data": "ys[]", "size": "ys[]@size", "levels": ["xss[][]@size", "ys[]@size"]},
            {"to": "#2", "fcn": "+", "args": ["#0", "#1"]}
            ])
        self.assertEqual(result.toJson(), {"data": "#2", "size": "#0@size", "schema": {"type": "collection", "items": {"type": "collection", "items": {"type": "collection", "items": "real"}}}})

    def test_record(self):
        result, statements = self.compile("x.a + y", self.mockDataset(x=record(a=real), y=real))
        self.assertEqual(statements.toJson(), [{"to": "#0", "fcn": "+", "args": ["x-a", "y"]}])
        self.assertEqual(result.toJson(), {"schema": "real", "data": "#0", "size": None})

    def test_recordarray(self):
        result, statements = self.compile("x.a.map($1 + y)", self.mockDataset(x=record(a=collection(real)), y=real))
        self.assertEqual(statements.toJson(), [
            {"to": "#0", "fcn": "$explode", "data": "y", "size": "x-a[]@size"},
            {"to": "#1", "fcn": "+", "args": ["x-a[]", "#0"]}
            ])
        self.assertEqual(result.toJson(), {"schema": {"type": "collection", "items": "real"}, "data": "#1", "size": "x-a[]@size"})

    # def test_arrayrecord(self):
    #     result, statements = self.compile("xs.map($1.a + y)", self.mockDataset(xs=collection(record(a=real)), y=real))

    #     print
    #     print statements
    #     print result
