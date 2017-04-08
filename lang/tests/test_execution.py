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
import json
import re
import sys
import unittest

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.dataset import ColumnName
from femtocode.defs import SymbolTable
from femtocode.execution import *
from femtocode.lib.standard import StandardLibrary
from femtocode.parser import parse
from femtocode.testdataset import TestDataset
from femtocode.testdataset import TestSession
from femtocode.typesystem import *
from femtocode.workflow import *

session = TestSession()

oldexample = session.source("OldExample", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)
oldexample.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
oldexample.dataset.fill({"xss": [[7, 8], [9, 10], [11, 12]], "ys": [5, 6, 7, 8], "c": 2000, "d": 321})

class TestExecution(unittest.TestCase):
    def runTest(self):
        pass

    def test_oldexample1(self):
        statements = oldexample.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => 100*x + y)))").compile().statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#4"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]
    
        loop.prerun.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdindex_v2 = [0, 0, 0]
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        xdindex_v3 = [0, 0]
        tarray_v4 = [0] * dataLength
        tsarray_v5 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1, xdarray_v2, xdindex_v2, xdarray_v3, xdindex_v3, tarray_v4, tsarray_v5)
        self.assertEqual(numEntries, [2, 48, 20])
        self.assertEqual(tarray_v4, [101, 102, 103, 104, 201, 202, 203, 204, 301, 302, 303, 304, 401, 402, 403, 404, 501, 502, 503, 504, 601, 602, 603, 604, 705, 706, 707, 708, 805, 806, 807, 808, 905, 906, 907, 908, 1005, 1006, 1007, 1008, 1105, 1106, 1107, 1108, 1205, 1206, 1207, 1208])
        self.assertEqual(tsarray_v5, [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

    def test_oldexample2(self):
        statements = oldexample.toPython(a = "xss.map(xs => ys.map(y => xs.map(x => 100*x + y)))").compile().statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#4"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]
    
        loop.prerun.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdindex_v2 = [0, 0, 0]
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        xdindex_v3 = [0, 0]
        tarray_v4 = [0] * dataLength
        tsarray_v5 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1, xdarray_v2, xdindex_v2, xdarray_v3, xdindex_v3, tarray_v4, tsarray_v5)
        self.assertEqual(numEntries, [2, 48, 32])
        self.assertEqual(tarray_v4, [101, 201, 102, 202, 103, 203, 104, 204, 301, 401, 302, 402, 303, 403, 304, 404, 501, 601, 502, 602, 503, 603, 504, 604, 705, 805, 706, 806, 707, 807, 708, 808, 905, 1005, 906, 1006, 907, 1007, 908, 1008, 1105, 1205, 1106, 1206, 1107, 1207, 1108, 1208])
        self.assertEqual(tsarray_v5, [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

    def test_minimal(self):
        statements = oldexample.toPython(a = "c + d").compile().statements

        loop = Loop(None)
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#0"))
        loop.compileToPython("fcnname", {"c": real, "d": real}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = []
        darray_v0 = oldexample.dataset.groups[0].segments["c"].data
        darray_v1 = oldexample.dataset.groups[0].segments["d"].data
        tarray_v2 = [0] * oldexample.dataset.numEntries
        
        loop.run.fcn(numEntries, countdown, darray_v0, darray_v1, tarray_v2)
        self.assertEqual(numEntries, [2, 2, 0])
        self.assertEqual(tarray_v2, [1123, 2321])

    def test_no_explodes(self):
        statements = oldexample.toPython(a = "ys.map(y => y + y)").compile().statements

        loop = Loop(ColumnName.parse("ys[]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#0"))
        loop.compileToPython("fcnname", {"ys[]": collection(real)}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v0 = [0, 0]
        darray_v1 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v2 = [0] * oldexample.dataset.groups[0].segments["ys[]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, darray_v1, tarray_v2)
        self.assertEqual(numEntries, [2, 8, 2])
        self.assertEqual(tarray_v2, [2, 4, 6, 8, 10, 12, 14, 16])
        self.assertEqual(sarray_v0, [4, 4])

    def test_no_explodes2(self):
        statements = oldexample.toPython(a = "ys.map(y => y + 100)").compile().statements

        loop = Loop(ColumnName.parse("ys[]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#0"))
        loop.compileToPython("fcnname", {"ys[]": collection(real)}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v0 = [0, 0]
        darray_v1 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v2 = [0] * oldexample.dataset.groups[0].segments["ys[]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, darray_v1, tarray_v2)
        self.assertEqual(numEntries, [2, 8, 2])
        self.assertEqual(tarray_v2, [101, 102, 103, 104, 105, 106, 107, 108])
        self.assertEqual(sarray_v0, [4, 4])

    def test_simple_explode(self):
        statements = oldexample.toPython(a = "ys.map(y => y + c)").compile().statements

        loop = Loop(ColumnName.parse("ys[]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#1"))
        loop.compileToPython("fcnname", {"ys[]": collection(real), "c": real}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v0 = [0, 0]
        xarray_v1 = oldexample.dataset.groups[0].segments["c"].data
        darray_v2 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v3 = [0] * oldexample.dataset.groups[0].segments["ys[]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, xarray_v1, darray_v2, tarray_v3)
        self.assertEqual(numEntries, [2, 8, 2])
        self.assertEqual(tarray_v3, [1001, 1002, 1003, 1004, 2005, 2006, 2007, 2008])
        self.assertEqual(sarray_v0, [4, 4])

    def test_simple_explode2(self):
        statements = oldexample.toPython(a = "xss.map(xs => xs.map(x => x + c))").compile().statements

        loop = Loop(ColumnName.parse("xss[][]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#1"))
        loop.compileToPython("fcnname", {"xss[][]": collection(collection(real)), "c": real}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        xarray_v1 = oldexample.dataset.groups[0].segments["c"].data
        darray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        tarray_v3 = [0] * oldexample.dataset.groups[0].segments["xss[][]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, xarray_v1, darray_v2, tarray_v3)
        self.assertEqual(numEntries, [2, 12, 8])
        self.assertEqual(tarray_v3, [1001, 1002, 1003, 1004, 1005, 1006, 2007, 2008, 2009, 2010, 2011, 2012])
        self.assertEqual(sarray_v0, [3, 2, 2, 2, 3, 2, 2, 2])

    def test_megaexample1(self):
        statements = oldexample.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => c*x + y)))").compile().statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#5"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]

        loop.prerun.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdindex_v2 = [0, 0, 0]
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        xdindex_v3 = [0, 0]
        xarray_v4 = oldexample.dataset.groups[0].segments["c"].data
        tarray_v5 = [0] * dataLength
        tsarray_v6 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1, xdarray_v2, xdindex_v2, xdarray_v3, xdindex_v3, xarray_v4, tarray_v5, tsarray_v6)
        self.assertEqual(numEntries, [2, 48, 20])
        self.assertEqual(tarray_v5, [1001, 1002, 1003, 1004, 2001, 2002, 2003, 2004, 3001, 3002, 3003, 3004, 4001, 4002, 4003, 4004, 5001, 5002, 5003, 5004, 6001, 6002, 6003, 6004, 14005, 14006, 14007, 14008, 16005, 16006, 16007, 16008, 18005, 18006, 18007, 18008, 20005, 20006, 20007, 20008, 22005, 22006, 22007, 22008, 24005, 24006, 24007, 24008])
        self.assertEqual(tsarray_v6, [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

    def test_megaexample2(self):
        statements = oldexample.toPython(a = "xss.map(xs => ys.map(y => xs.map(x => c*x + y)))").compile().statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#5"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]

        loop.prerun.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sindex_v0 = [0, 0, 0]
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        sindex_v1 = [0, 0]
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdindex_v2 = [0, 0, 0]
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        xdindex_v3 = [0, 0]
        xarray_v4 = oldexample.dataset.groups[0].segments["c"].data
        tarray_v5 = [0] * dataLength
        tsarray_v6 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sindex_v0, sarray_v1, sindex_v1, xdarray_v2, xdindex_v2, xdarray_v3, xdindex_v3, xarray_v4, tarray_v5, tsarray_v6)
        self.assertEqual(numEntries, [2, 48, 32])
        self.assertEqual(tarray_v5, [1001, 2001, 1002, 2002, 1003, 2003, 1004, 2004, 3001, 4001, 3002, 4002, 3003, 4003, 3004, 4004, 5001, 6001, 5002, 6002, 5003, 6003, 5004, 6004, 14005, 16005, 14006, 16006, 14007, 16007, 14008, 16008, 18005, 20005, 18006, 20006, 18007, 20007, 18008, 20008, 22005, 24005, 22006, 24006, 22007, 24007, 22008, 24008])
        self.assertEqual(tsarray_v6, [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

    def test_graphs(self):
        pass



    # def test_submit(self):
    #     session = TestSession()

    #     source = session.source("Test", x=integer, y=real)
    #     for i in xrange(100):
    #         source.dataset.fill({"x": i, "y": 0.2})

    #     def callback(x):
    #         self.assertEqual(source.dataset.numEntries, x.numEntries)

    #     result = source.define(z = "x + y").toPython(a = "z - 3", b = "z - 0.5").submit(callback)

    #     # TestDataset is synchronous, so both callback and assuming it's blocking work

    #     for old, new in zip(source.dataset, result):
    #         self.assertAlmostEqual(old.x + old.y - 3, new.a)
    #         self.assertAlmostEqual(old.x + old.y - 0.5, new.b)
