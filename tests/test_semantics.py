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
            def __init__(self, data):
                self.data = data

        class SizedColumn(object):
            def __init__(self, numDeep, fixedSizes, data, size):
                self.numDeep = numDeep
                self.fixedSizes = fixedSizes
                self.data = data
                self.size = size

        OPEN = ["(", "[", "{", "<"]
        CLOSE = [")", "]", "}", ">"]

        # The Antikythera Mechanism
        def explodeSized(numEntries, numLevels, levels, numColumns, columns, outsize, outdata):
            countdown = [[numEntries] + [None] * columns[i].numDeep for i in xrange(numColumns)]
            deepi = [0] * numColumns
            datai = [0] * numColumns
            sizei = [0] * numColumns

            datarewind = [None] * numLevels
            sizerewind = [None] * numLevels

            coli = 0
            leveli = 0
            entry = 0
            while entry < numEntries:
                if leveli < numLevels:
                    coli = levels[leveli]
                    datarewind[leveli] = datai[coli]
                    sizerewind[leveli] = sizei[coli]

                # each real time through counts down
                countdown[coli][deepi[coli]] -= 1

                print ".".join(map(str, sizerewind)),

                if deepi[coli] == columns[coli].numDeep:
                    # move forward in datai
                    print columns[coli].data[datai[coli]],
                    datai[coli] += 1

                else:
                    # move forward in sizei
                    leveli += 1
                    deepi[coli] += 1
                    countdown[coli][deepi[coli]] = columns[coli].fixedSizes[deepi[coli] - 1]
                    if countdown[coli][deepi[coli]] == 0:
                        countdown[coli][deepi[coli]] = columns[coli].size[sizei[coli]]
                        sizei[coli] += 1
                    print OPEN[coli],

                # remove all completed countdowns
                while deepi[coli] != 0 and countdown[coli][deepi[coli]] == 0:
                    if leveli < len(datarewind): datarewind[leveli] = None   # just for show
                    if leveli < len(sizerewind): sizerewind[leveli] = None   # just for show
                    leveli -= 1

                    countdown[coli][deepi[coli]] = None   # just for show
                    deepi[coli] -= 1
                    print CLOSE[coli],

                    if leveli != 0 and levels[leveli] != levels[leveli - 1]:
                        datai[levels[leveli]] = datarewind[leveli]
                        sizei[levels[leveli]] = sizerewind[leveli]

                if leveli == 0:
                    entry += 1
                    print

        # outsize = []
        # outdata = []
        # print
        # explodeSized(3, 2, [0, 0], 1, [SizedColumn(2, [0, 0], [1.1, 2.2, 3.3], [0, 1, 1, 2, 0, 2])], outsize, outdata)

        outsize = []
        outdata = []
        print
        # explodeSized(1, 2, [0, 0], 1, [SizedColumn(2, [0, 0], ["a", "b", "c", "d", "e", "f"], [3, 2, 2, 2])], outsize, outdata)
        explodeSized(1, 4, [0, 0, 1, 1], 2, [SizedColumn(2, [0, 0], ["a", "b", "c", "d", "e", "f"], [3, 2, 2, 2]), SizedColumn(2, [0, 0], ["A", "B", "C", "D", "E", "F"], [3, 2, 2, 2])], outsize, outdata)
        print "outsize", outsize
        print "outdata", outdata
