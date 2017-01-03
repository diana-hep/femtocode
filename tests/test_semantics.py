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
from femtocode.typesystem import *
from femtocode.inference import *

import sys

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestSemantics(unittest.TestCase):
    def runTest(self):
        pass

    def test_simple1(self):
        p = lispytree.build(parse("x"), table.fork({"x": lispytree.Ref("x")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer}))[0].schema)

        p = lispytree.build(parse("x + 3"), table.fork({"x": lispytree.Ref("x")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer}))[0].schema)

        p = lispytree.build(parse("y = x + 3; y + 1"), table.fork({"x": lispytree.Ref("x")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer}))[0].schema)

        p = lispytree.build(parse("{x => x + 3}"), table.fork({"x": lispytree.Ref("x")}))[0]
        print(p)

        p = lispytree.build(parse("def f(x): x + 3.14;\nf"), table)[0]
        print(p)

        p = lispytree.build(parse("def f(q): q + 3;  f(x)"), table.fork({"x": lispytree.Ref("x")}))[0]
        print(p)

        p = lispytree.build(parse("xs.map({x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("xs.map(x => 3.14 + x)"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("xs.map(3.14 + $1)"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("xs.map(fcn = {x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        try:
            lispytree.build(parse("xs.map(wonky = {x => 3.14 + x}, fcn = {x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        except FemtocodeError as err:
            print(err)

        try:
            lispytree.build(parse("xs.map()"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        except FemtocodeError as err:
            print(err)
        
        try:
            lispytree.build(parse("xs.map({x => 3.14 + x}, {x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        except FemtocodeError as err:
            print(err)

        p = lispytree.build(parse("xs.map(3.14)"), table.fork({"xs": lispytree.Ref("xs")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("y = x + 3; y"), table.fork({"x": lispytree.Ref("x")}))[0]
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer, lispytree.Call(table["+"], [lispytree.Literal(3), lispytree.Ref("x")]): real}))[0].schema)

        print(lispytree.build(parse("def f(x): {y => x + y}; f"), table)[0])

        print(lispytree.build(parse("def f(x): {y => x + y}; f(3)"), table)[0])

        print(lispytree.build(parse("def f(x, z=99): {y => x + y + z}; f(3)"), table)[0])

        print(lispytree.build(parse("y == 2"), table.fork({"y": lispytree.Ref("y")}))[0])

        print(lispytree.build(parse("def f(x): x + 0.1; y == f(2)"), table.fork({"y": lispytree.Ref("y")}))[0])

        try:
            lispytree.build(parse("def f(x): x; g(2)"), table)[0]
        except FemtocodeError as err:
            print(err)

        try:
            lispytree.build(parse("g = 8; g(2)"), table)[0]
        except FemtocodeError as err:
            print(err)

    def test_simple2(self):
        columns = {}
        columns.update(statementlist.schemaToColumns("x", real))
        columns.update(statementlist.schemaToColumns("y", real))
        columns.update(statementlist.schemaToColumns("z", real))
        columns.update(statementlist.schemaToColumns("xs", collection(real)))

        lt = lispytree.build(parse("xs.map($1 + x).map($1 + y).map($1 + z)"), table.fork(dict((v, lispytree.Ref(v)) for v in ("x", "y", "z", "xs"))))[0]
        tt = typedtree.build(lt, SymbolTable(dict([(lispytree.Ref(v), real) for v in ("x", "y", "z")] + [(lispytree.Ref("xs"), collection(real))])))[0]
        result, ss, _ = statementlist.build(tt, columns)

        print("")
        for statement in ss:
            print(statement)
        print("-> " + str(result))

        lt = lispytree.build(parse("a = x + y; b = a + y + z; xs.map(x => x + a + a + b).map(y => y + 2)"), table.fork(dict((v, lispytree.Ref(v)) for v in ("x", "y", "z", "xs"))))[0]
        tt = typedtree.build(lt, SymbolTable(dict([(lispytree.Ref(v), real) for v in ("x", "y", "z")] + [(lispytree.Ref("xs"), collection(real))])))[0]
        result, ss, _ = statementlist.build(tt, columns)

        print("")
        for statement in ss:
            print(statement)
        print("-> " + str(result))

        columns = {}
        columns.update(statementlist.schemaToColumns("xss", collection(collection(real))))
        columns.update(statementlist.schemaToColumns("ys", collection(real)))

        lt = lispytree.build(parse("xss.map(xs => ys.map(y => xs.map(x => x + y)))"), table.fork(dict((v, lispytree.Ref(v)) for v in ("xss", "ys"))))[0]
        tt = typedtree.build(lt, SymbolTable({lispytree.Ref("xss"): collection(collection(real)), lispytree.Ref("ys"): collection(real)}))[0]
        result, ss, _ = statementlist.build(tt, columns)

        print("")
        for statement in ss:
            print(statement)
        print("-> " + str(result))

    def test_prototype1(self):
        class UnsizedColumn(object):
            def __init__(self, numEntries, data):
                self.numEntries = numEntries
                self.data = data

        class SizedColumn(object):
            def __init__(self, numEntries, numDeep, fixedSizes, data, size):
                self.numEntries = numEntries
                self.numDeep = numDeep
                self.fixedSizes = fixedSizes
                self.data = data
                self.size = size

        OPEN = ["(", "[", "{", "<"]
        CLOSE = [")", "]", "}", ">"]

        # The Antikythera Mechanism
        def explodeSized(numEntries, numLevels, levels, numColumns, columns, outsize, outdata):
            ini = 0
            countdown = [[None] * columns[i].numDeep for i in xrange(numColumns)]
            deepi = [-1] * numColumns
            datai = [0] * numColumns
            sizei = [0] * numColumns
                    
            outi = 0
            entry = 0
            while entry < numEntries:
                deepi[ini] += 1
                countdown[ini][deepi[ini]] = columns[ini].fixedSizes[deepi[ini]]
                if countdown[ini][deepi[ini]] == 0:
                    countdown[ini][deepi[ini]] = columns[ini].size[sizei[ini]]
                else:
                    assert False    # no fixed sizes for now
                print OPEN[ini],

                if deepi[ini] == columns[ini].numDeep - 1:
                    while countdown[ini][deepi[ini]] != 0:
                        print columns[ini].data[datai[ini]],
                        countdown[ini][deepi[ini]] -= 1
                    deepi[ini] -= 1
                    print CLOSE[ini],

                if countdown[ini][deepi[ini]] != 0:
                    countdown[ini][deepi[ini]] -= 1
                else:
                    while deepi[ini] != -1 and countdown[ini][deepi[ini]] == 0:
                        deepi[ini] -= 1
                        print CLOSE[ini],

                sizei[ini] += 1

                if deepi[0] == -1:
                    entry += 1
                    print

        # outsize = []
        # outdata = []
        # print
        # explodeSized(3, 1, [0], [SizedColumn(3, 2, [0, 0], [1.1, 2.2, 3.3], [0, 1, 1, 2, 0, 2])], outsize, outdata)

        outsize = []
        outdata = []
        print
        explodeSized(1, 2, [0, 1], 1, [SizedColumn(1, 2, [0, 0], ["a", "b", "c", "d", "e", "f"], [3, 2, 2, 2])], outsize, outdata)
        print "outsize", outsize
        print "outdata", outdata
