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
from femtocode.parser import parse
from femtocode.testdataset import TestDataset
from femtocode.testdataset import TestSession
from femtocode.typesystem import *
from femtocode.workflow import *

session = TestSession()

oldexample = session.source("OldExample", xss=collection(collection(integer)), ys=collection(integer), c=integer, d=integer)
oldexample.dataset.fill({"xss": [[1, 2], [3, 4], [5, 6]], "ys": [1, 2, 3, 4], "c": 1000, "d": 1000})
oldexample.dataset.fill({"xss": [[7, 8], [9, 10], [11, 12]], "ys": [5, 6, 7, 8], "c": 1000, "d": 1000})

def execed(codetext, fcnname):
    glob = {}
    exec(codetext, glob)
    return glob[fcnname]

class TestExecution(unittest.TestCase):
    def runTest(self):
        pass

    # def test_oldexample(self):
    #     print
    #     print "xss", oldexample.dataset.groups[0].segments["xss[][]"].size
    #     print "ys", oldexample.dataset.groups[0].segments["ys[]"].size

    #     print
    #     testy(oldexample.toPython(a = "c + d").compile().statements)

    #     print
    #     testy(oldexample.toPython(a = "ys.map(y => y + y)").compile().statements)

    #     print
    #     testy(oldexample.toPython(a = "ys.map(y => y + c)").compile().statements)

    #     print
    #     testy(oldexample.toPython(a = "xss.map(xs => xs.map(x => x + c))").compile().statements)

    #     print
    #     testy(oldexample.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => 100*x + y)))").compile().statements)

    #     print
    #     testy(oldexample.toPython(a = "xss.map(xs => ys.map(y => xs.map(x => 100*x + y)))").compile().statements)

    #     print
    #     testy(oldexample.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => c*x + y)))").compile().statements)

    #     print
    #     testy(oldexample.toPython(a = "xss.map(xs => ys.map(y => xs.map(x => c*x + y)))").compile().statements)

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

    def test_loop_generation(self):
        loop = Loop(ColumnName.parse("#0@size"))

        statements = oldexample.toPython(a = "xss.map(xs => xs.map(x => ys.map(y => 100*x + y)))").compile().statements
        # statements = oldexample.toPython(a = "xss.map(xs => ys.map(y => xs.map(x => 100*x + y)))").compile().statements
        print
        print statements

        for statement in statements:
            loop.newStatement(statement)

        validNames = {}
        def valid(n):
            if n not in validNames:
                validNames[n] = "v" + repr(len(validNames))
            return validNames[n]

        parameters, codetext = loop.codetext("fcnname", valid, False)
        print
        print codetext

        fcnname = execed(codetext, "fcnname")

        numEntries = [oldexample.dataset.numEntries, 0, 0]
        countdown = [0, 0, 0]
        array_v0 = oldexample.dataset.groups[0].segments["xss[][]"].size
        index_v0 = [0, 0, 0]
        array_v1 = oldexample.dataset.groups[0].segments["ys[]"].size
        index_v1 = [0, 0]
        array_v2 = oldexample.dataset.groups[0].segments["xss[][]"].data
        index_v2 = [0, 0, 0]
        array_v3 = oldexample.dataset.groups[0].segments["ys[]"].data
        index_v3 = [0, 0]
        
        fcnname(numEntries, countdown, array_v0, index_v0, array_v1, index_v1, array_v2, index_v2, array_v3, index_v3)
        print numEntries
