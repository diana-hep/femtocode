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

def mapp(obj, fcn):
    return list(map(fcn, obj))

class TestExecution(unittest.TestCase):
    def runTest(self):
        pass

    def test_no_literals(self):
        statements = oldexample.toPython(a = "100").compile().statements
        # FIXME: do something about this case!

    def test_no_literals2(self):
        statements = oldexample.toPython(a = "ys.map(y => 100)").compile().statements
        # FIXME: do something about this case!

    def test_oldexample1(self):
        query = oldexample.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => x + y)))").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#2"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
    
        loop.prerun.fcn(numEntries, countdown, sarray_v0, sarray_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v4 = [0] * dataLength
        tsarray_v5 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sarray_v1, xdarray_v2, xdarray_v3, tarray_v4, tsarray_v5)
        self.assertEqual(numEntries, [2, 48, 20])
        self.assertEqual(tarray_v4, [2, 3, 4, 5, 3, 4, 5, 6, 4, 5, 6, 7, 5, 6, 7, 8, 6, 7, 8, 9, 7, 8, 9, 10, 12, 13, 14, 15, 13, 14, 15, 16, 14, 15, 16, 17, 15, 16, 17, 18, 16, 17, 18, 19, 17, 18, 19, 20])
        self.assertEqual(tsarray_v5, [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: mapp(old.ys, lambda y: x + y))), new.a)

    def test_oldexample2(self):
        query = oldexample.toPython(a = "xss.map(xs => ys.map(y => xs.map(x => x + y)))").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#2"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["xss[][]"].size
    
        loop.prerun.fcn(numEntries, countdown, sarray_v0, sarray_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["xss[][]"].size
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v4 = [0] * dataLength
        tsarray_v5 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sarray_v1, xdarray_v2, xdarray_v3, tarray_v4, tsarray_v5)
        self.assertEqual(numEntries, [2, 48, 32])
        self.assertEqual(tarray_v4, [2, 3, 3, 4, 4, 5, 5, 6, 4, 5, 5, 6, 6, 7, 7, 8, 6, 7, 7, 8, 8, 9, 9, 10, 12, 13, 13, 14, 14, 15, 15, 16, 14, 15, 15, 16, 16, 17, 17, 18, 16, 17, 17, 18, 18, 19, 19, 20])
        self.assertEqual(tsarray_v5, [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(old.ys, lambda y: mapp(xs, lambda x: x + y))), new.a)

    def test_minimal(self):
        query = oldexample.toPython(a = "c + d").compile()
        statements = query.statements

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

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(old.c + old.d, new.a)

    def test_no_explodes(self):
        query = oldexample.toPython(a = "ys.map(y => y + y)").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("ys[]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#0"))
        loop.compileToPython("fcnname", {"ys[]": collection(real)}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        darray_v1 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v2 = [0] * oldexample.dataset.groups[0].segments["ys[]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, darray_v1, tarray_v2)
        self.assertEqual(numEntries, [2, 8, 2])
        self.assertEqual(tarray_v2, [2, 4, 6, 8, 10, 12, 14, 16])
        self.assertEqual(sarray_v0, [4, 4])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.ys, lambda y: y + y), new.a)

    def test_no_explodes2(self):
        query = oldexample.toPython(a = "ys.map(y => y + 100)").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("ys[]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#0"))
        loop.compileToPython("fcnname", {"ys[]": collection(real)}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        darray_v1 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v2 = [0] * oldexample.dataset.groups[0].segments["ys[]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, darray_v1, tarray_v2)
        self.assertEqual(numEntries, [2, 8, 2])
        self.assertEqual(tarray_v2, [101, 102, 103, 104, 105, 106, 107, 108])
        self.assertEqual(sarray_v0, [4, 4])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.ys, lambda y: y + 100), new.a)

    def test_simple_explode(self):
        query = oldexample.toPython(a = "ys.map(y => y + c)").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("ys[]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#1"))
        loop.compileToPython("fcnname", {"ys[]": collection(real), "c": real}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        xarray_v1 = oldexample.dataset.groups[0].segments["c"].data
        darray_v2 = oldexample.dataset.groups[0].segments["ys[]"].data
        tarray_v3 = [0] * oldexample.dataset.groups[0].segments["ys[]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, xarray_v1, darray_v2, tarray_v3)
        self.assertEqual(numEntries, [2, 8, 2])
        self.assertEqual(tarray_v3, [1001, 1002, 1003, 1004, 2005, 2006, 2007, 2008])
        self.assertEqual(sarray_v0, [4, 4])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.ys, lambda y: y + old.c), new.a)

    def test_simple_explode2(self):
        query = oldexample.toPython(a = "xss.map(xs => xs.map(x => x + c))").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("xss[][]@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#1"))
        loop.compileToPython("fcnname", {"xss[][]": collection(collection(real)), "c": real}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0]

        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        xarray_v1 = oldexample.dataset.groups[0].segments["c"].data
        darray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        tarray_v3 = [0] * oldexample.dataset.groups[0].segments["xss[][]"].dataLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, xarray_v1, darray_v2, tarray_v3)
        self.assertEqual(numEntries, [2, 12, 8])
        self.assertEqual(tarray_v3, [1001, 1002, 1003, 1004, 1005, 1006, 2007, 2008, 2009, 2010, 2011, 2012])
        self.assertEqual(sarray_v0, [3, 2, 2, 2, 3, 2, 2, 2])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: x + old.c)), new.a)

    def test_simple_explode3(self):
        query = oldexample.toPython(a = "ys.map(y => y + 1)").compile()
        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.ys, lambda y: y + 1), new.a)

    def test_simple_explode4(self):
        query = oldexample.toPython(a = "xss.map(xs => xs.map(x => x + 1))").compile()
        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: x + 1)), new.a)

    def test_megaexample1(self):
        query = oldexample.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => c * x + y)))").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#5"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size

        loop.prerun.fcn(numEntries, countdown, sarray_v0, sarray_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        xarray_v4 = oldexample.dataset.groups[0].segments["c"].data
        tarray_v5 = [0] * dataLength
        tsarray_v6 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sarray_v1, xdarray_v2, xdarray_v3, xarray_v4, tarray_v5, tsarray_v6)
        self.assertEqual(numEntries, [2, 48, 20])
        self.assertEqual(tarray_v5, [1001, 1002, 1003, 1004, 2001, 2002, 2003, 2004, 3001, 3002, 3003, 3004, 4001, 4002, 4003, 4004, 5001, 5002, 5003, 5004, 6001, 6002, 6003, 6004, 14005, 14006, 14007, 14008, 16005, 16006, 16007, 16008, 18005, 18006, 18007, 18008, 20005, 20006, 20007, 20008, 22005, 22006, 22007, 22008, 24005, 24006, 24007, 24008])
        self.assertEqual(tsarray_v6, [3, 2, 4, 4, 2, 4, 4, 2, 4, 4, 3, 2, 4, 4, 2, 4, 4, 2, 4, 4])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: mapp(old.ys, lambda y: old.c * x + y))), new.a)

    def test_megaexample2(self):
        query = oldexample.toPython(a = "xss.map(xs => ys.map(y => xs.map(x => c*x + y)))").compile()
        statements = query.statements

        loop = Loop(ColumnName.parse("#0@size"))
        for statement in statements:
            loop.newStatement(statement)
        loop.newTarget(ColumnName.parse("#5"))
        loop.compileToPython("fcnname", {}, StandardLibrary.table, False, False)

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["xss[][]"].size

        loop.prerun.fcn(numEntries, countdown, sarray_v0, sarray_v1)
        dataLength = numEntries[1]
        sizeLength = numEntries[2]

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        sarray_v0 = oldexample.dataset.groups[0].segments["ys[]"].size
        sarray_v1 = oldexample.dataset.groups[0].segments["xss[][]"].size
        xdarray_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        xdarray_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        xarray_v4 = oldexample.dataset.groups[0].segments["c"].data
        tarray_v5 = [0] * dataLength
        tsarray_v6 = [0] * sizeLength
        
        loop.run.fcn(numEntries, countdown, sarray_v0, sarray_v1, xdarray_v2, xdarray_v3, xarray_v4, tarray_v5, tsarray_v6)
        self.assertEqual(numEntries, [2, 48, 32])
        self.assertEqual(tarray_v5, [1001, 2001, 1002, 2002, 1003, 2003, 1004, 2004, 3001, 4001, 3002, 4002, 3003, 4003, 3004, 4004, 5001, 6001, 5002, 6002, 5003, 6003, 5004, 6004, 14005, 16005, 14006, 16006, 14007, 16007, 14008, 16008, 18005, 20005, 18006, 20006, 18007, 20007, 18008, 20008, 22005, 24005, 22006, 24006, 22007, 24007, 22008, 24008])
        self.assertEqual(tsarray_v6, [3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 3, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2, 2, 2])

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(old.ys, lambda y: mapp(xs, lambda x: old.c * x + y))), new.a)

    def test_graph_connections1(self):
        query = oldexample.define(z = "c - d").toPython(a = "xss.map(xs => xs.map(x => x + z))", b = "ys.map(y => y + z)").compile()
        targetsToEndpoints, lookup, required = DependencyGraph.wholedag(query)
        self.assertEqual(len(DependencyGraph.connectedSubgraphs(targetsToEndpoints.values())), 1)
        self.assertEqual(len(sum(DependencyGraph.loops(targetsToEndpoints.values()).values(), [])), 3)
        self.assertEqual(len(DependencyGraph.order(DependencyGraph.loops(targetsToEndpoints.values()), [], required)), 3)

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: x + (old.c - old.d))), new.a)
            self.assertEqual(mapp(old.ys, lambda y: y + (old.c - old.d)), new.b)

    def test_graph_connections2(self):
        query = oldexample.define(z = "c").toPython(a = "xss.map(xs => xs.map(x => x + z))", b = "ys.map(y => y + z)").compile()
        targetsToEndpoints, lookup, required = DependencyGraph.wholedag(query)
        self.assertEqual(len(DependencyGraph.connectedSubgraphs(targetsToEndpoints.values())), 2)
        self.assertEqual(len(sum(DependencyGraph.loops(targetsToEndpoints.values()).values(), [])), 2)

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: x + old.c)), new.a)
            self.assertEqual(mapp(old.ys, lambda y: y + old.c), new.b)

    def test_graph_connections3(self):
        query = oldexample.define(z = "c").toPython(a = "ys.map(y => y + z)", b = "ys.map(y => y + z)").compile()
        targetsToEndpoints, lookup, required = DependencyGraph.wholedag(query)
        self.assertEqual(len(sum(DependencyGraph.loops(targetsToEndpoints.values()).values(), [])), 1)

        for old, new in zip(oldexample.dataset, session.submit(query)):
            self.assertEqual(mapp(old.ys, lambda y: y + old.c), new.a)
            self.assertEqual(mapp(old.ys, lambda y: y + old.c), new.b)

    def test_submit(self):
        session = TestSession()

        source = session.source("Test", x=integer, y=real)
        for i in xrange(100):
            source.dataset.fill({"x": i, "y": 0.2})

        def callback(x):
            self.assertEqual(source.dataset.numEntries, x.numEntries)

        result = source.define(z = "x + y").toPython(a = "z - 3", b = "z - 0.5").submit(callback)

        # TestDataset is synchronous, so both callback and assuming it's blocking work

        for old, new in zip(source.dataset, result):
            self.assertAlmostEqual(old.x + old.y - 3, new.a)
            self.assertAlmostEqual(old.x + old.y - 0.5, new.b)

    def test_skipping(self):
        missings = session.source("Missings", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)
        missings.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[7, 8], [9, 10], [11, 12]], "ys": [5, 6, 7, 8], "c": 2000, "d": 321})
        missings.dataset.fill({"xss": [[], [], []], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[7, 8], [9, 10], [11, 12]], "ys": [5, 6, 7, 8], "c": 2000, "d": 321})

        query = missings.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => c * x + y)))").compile()
        for old, new in zip(missings.dataset, session.submit(query, debug=False)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: mapp(old.ys, lambda y: old.c * x + y))), new.a)

        empties = session.source("Empties", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)
        empties.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        empties.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        empties.dataset.fill({"xss": [], "ys": [], "c": 1000, "d": 123})

        query = empties.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => c * x + y)))").compile()
        for old, new in zip(empties.dataset, session.submit(query, debug=False)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: mapp(old.ys, lambda y: old.c * x + y))), new.a)

        emptiers = session.source("Emptiers", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)

        query = emptiers.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => c * x + y)))").compile()
        for old, new in zip(emptiers.dataset, session.submit(query, debug=False)):
            self.assertEqual(mapp(old.xss, lambda xs: mapp(xs, lambda x: mapp(old.ys, lambda y: old.c * x + y))), new.a)

    def test_double_explode(self):
        query = oldexample.toPython(a = "ys.map(y1 => ys.map(y2 => y1 + y2))").compile()
        statements = query.statements
        for old, new in zip(oldexample.dataset, session.submit(query, debug=False)):
            self.assertEqual(mapp(old.ys, lambda y1: mapp(old.ys, lambda y2: y1 + y2)), new.a)

        missings = session.source("Missings", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)
        missings.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[7, 8], [9, 10], [11, 12]], "ys": [5, 6, 7, 8], "c": 2000, "d": 321})
        missings.dataset.fill({"xss": [[], [], []], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [], "ys": [], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [1, 2, 3, 4], "c": 1000, "d": 123})
        missings.dataset.fill({"xss": [[7, 8], [9, 10], [11, 12]], "ys": [5, 6, 7, 8], "c": 2000, "d": 321})

        query = missings.toPython(a = "ys.map(y1 => ys.map(y2 => y1 + y2))").compile()
        statements = query.statements
        for old, new in zip(missings.dataset, session.submit(query, debug=False)):
            self.assertEqual(mapp(old.ys, lambda y1: mapp(old.ys, lambda y2: y1 + y2)), new.a)

        empties = session.source("Empties", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)
        empties.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        empties.dataset.fill({"xss": [[], [], []], "ys": [], "c": 1000, "d": 123})
        empties.dataset.fill({"xss": [], "ys": [], "c": 1000, "d": 123})

        query = empties.toPython(a = "ys.map(y1 => ys.map(y2 => y1 + y2))").compile()
        statements = query.statements
        for old, new in zip(empties.dataset, session.submit(query, debug=False)):
            self.assertEqual(mapp(old.ys, lambda y1: mapp(old.ys, lambda y2: y1 + y2)), new.a)

        emptier = session.source("Emptier", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)

        query = emptier.toPython(a = "ys.map(y1 => ys.map(y2 => y1 + y2))").compile()
        statements = query.statements
        for old, new in zip(emptier.dataset, session.submit(query, debug=False)):
            self.assertEqual(mapp(old.ys, lambda y1: mapp(old.ys, lambda y2: y1 + y2)), new.a)
