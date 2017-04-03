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
from femtocode.defs import SymbolTable
from femtocode.execution import Executor
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.testdataset import TestDataset
from femtocode.testdataset import TestSession
from femtocode.typesystem import *
from femtocode.workflow import *

session = TestSession()

numerical = session.source("Test", x=integer, xlim=integer(0, almost(10)), xlim2=integer(1, almost(11)), y=real, ylim=real(0, almost(10)), ylim2=real(almost(0), almost(10)))
for i in xrange(100):
    numerical.dataset.fill({"x": i, "xlim": i % 10, "xlim2": (i % 10) + 1, "y": i + 0.2, "ylim": (i + 0.2) % 10.0, "ylim2": (i + 0.2) % 10.0})

class TestLibStandard(unittest.TestCase):
    def runTest(self):
        pass

    def test_add_literal(self):
        self.assertEqual(numerical.type("x + 3"), integer)
        self.assertEqual(numerical.type("x + 3.14"), real)
        self.assertEqual(numerical.type("xlim + 3"), integer(3, almost(10 + 3)))
        self.assertEqual(numerical.type("xlim + 3.14"), real(3.14, 9 + 3.14))
        self.assertEqual(numerical.type("ylim + 3"), real(3, almost(10 + 3)))
        self.assertEqual(numerical.type("ylim + 3.14"), real(3.14, almost(10 + 3.14)))
        for entry in numerical.toPython(x = "x", a = "x + 3.14").submit():
            self.assertAlmostEqual(entry.x + 3.14, entry.a)

    def test_add(self):
        self.assertEqual(numerical.type("x + y"), real)
        self.assertEqual(numerical.type("x + ylim"), real)
        self.assertEqual(numerical.type("xlim + ylim"), real(0, almost(9 + 10)))
        for entry in numerical.toPython(x = "x", y = "y", a = "x + y").submit():
            self.assertAlmostEqual(entry.x + entry.y, entry.a)

    def test_subtract_literal(self):
        self.assertEqual(numerical.type("x - 3"), integer)
        self.assertEqual(numerical.type("x - 3.14"), real)
        self.assertEqual(numerical.type("xlim - 3"), integer(-3, almost(10 - 3)))
        self.assertEqual(numerical.type("xlim - 3.14"), real(-3.14, 9 - 3.14))
        self.assertEqual(numerical.type("ylim - 3"), real(-3, almost(10 - 3)))
        self.assertEqual(numerical.type("ylim - 3.14"), real(-3.14, almost(10 - 3.14)))
        for entry in numerical.toPython(x = "x", a = "x - 3.14").submit():
            self.assertAlmostEqual(entry.x - 3.14, entry.a)

    def test_subtract_literal2(self):
        self.assertEqual(numerical.type("3 - x"), integer)
        self.assertEqual(numerical.type("3.14 - x"), real)
        self.assertEqual(numerical.type("3 - xlim"), integer(almost(3 - 10), 3))
        self.assertEqual(numerical.type("3.14 - xlim"), real(3.14 - 9, 3.14))
        self.assertEqual(numerical.type("3 - ylim"), real(almost(3 - 10), 3))
        self.assertEqual(numerical.type("3.14 - ylim"), real(almost(3.14 - 10), 3.14))
        for entry in numerical.toPython(x = "x", a = "3.14 - x").submit():
            self.assertAlmostEqual(3.14 - entry.x, entry.a)

    def test_subtract(self):
        self.assertEqual(numerical.type("x - y"), real)
        self.assertEqual(numerical.type("x - ylim"), real)
        self.assertEqual(numerical.type("xlim - ylim"), real(almost(-10), 9))
        for entry in numerical.toPython(x = "x", y = "y", a = "x - y").submit():
            self.assertAlmostEqual(entry.x - entry.y, entry.a)

    def test_multiply_literal(self):
        self.assertEqual(numerical.type("x * 3"), integer)
        self.assertEqual(numerical.type("x * 3.14"), real)
        self.assertEqual(numerical.type("xlim * 3"), integer(0, 9 * 3))
        self.assertEqual(numerical.type("xlim * 3.14"), real(0, 9 * 3.14))
        self.assertEqual(numerical.type("ylim * 3"), real(0, almost(10 * 3)))
        self.assertEqual(numerical.type("ylim * 3.14"), real(0, almost(10 * 3.14)))
        for entry in numerical.toPython(x = "x", a = "x * 3.14").submit():
            self.assertAlmostEqual(entry.x * 3.14, entry.a)

    def test_multiply(self):
        self.assertEqual(numerical.type("x * y"), real)
        self.assertEqual(numerical.type("x * ylim"), real)
        self.assertEqual(numerical.type("xlim * ylim"), real(0, almost(9 * 10)))
        for entry in numerical.toPython(x = "x", y = "y", a = "x * y").submit():
            self.assertAlmostEqual(entry.x * entry.y, entry.a)

    def test_divide_literal(self):
        self.assertEqual(numerical.type("3 / x"), extended)
        self.assertEqual(numerical.type("3.14 / x"), extended)
        self.assertEqual(numerical.type("3 / xlim"), extended(3 / 9.0, inf))
        self.assertEqual(numerical.type("3.14 / xlim"), extended(3.14 / 9, inf))
        self.assertEqual(numerical.type("3 / ylim"), extended(almost(3 / 10.0), inf))
        self.assertEqual(numerical.type("3.14 / ylim"), extended(almost(3.14 / 10), inf))
        self.assertEqual(numerical.type("3 / ylim2"), real(almost(3 / 10.0), almost(inf)))
        self.assertEqual(numerical.type("3.14 / ylim2"), real(almost(3.14 / 10), almost(inf)))
        for entry in numerical.toPython(x = "x", a = "3.14 / x").submit():
            self.assertAlmostEqual(3.14 / entry.x if entry.x != 0 else float("inf"), entry.a)

    def test_divide_literal2(self):
        self.assertEqual(numerical.type("x / 3"), real)
        self.assertEqual(numerical.type("x / 3.14"), real)
        self.assertEqual(numerical.type("xlim / 3"), real(0, 9 / 3.0))
        self.assertEqual(numerical.type("xlim / 3.14"), real(0, 9 / 3.14))
        self.assertEqual(numerical.type("ylim / 3"), real(0, almost(10 / 3.0)))
        self.assertEqual(numerical.type("ylim / 3.14"), real(0, almost(10 / 3.14)))
        self.assertEqual(numerical.type("ylim2 / 3"), real(almost(0), almost(10 / 3.0)))
        self.assertEqual(numerical.type("ylim2 / 3.14"), real(almost(0), almost(10 / 3.14)))
        for entry in numerical.toPython(x = "x", a = "x / 3.14").submit():
            self.assertAlmostEqual(entry.x / 3.14, entry.a)

    def test_divide(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("x / y"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("x / ylim"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim / ylim"))
        self.assertEqual(numerical.type("xlim / ylim2"), real(0, almost(inf)))
        for entry in numerical.toPython(x = "x", ylim2 = "ylim2", a = "x / ylim2").submit():
            self.assertAlmostEqual(entry.x / entry.ylim2, entry.a)

    def test_floordivide_literal(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("3 // x"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("3.14 // x"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("3 // xlim"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("3 // ylim"))
        self.assertEqual(numerical.type("3 // xlim2"), integer(0, 3))
        for entry in numerical.toPython(xlim2 = "xlim2", a = "3 // xlim2").submit():
            self.assertAlmostEqual(3 // entry.xlim2, entry.a)

    def test_floordivide_literal2(self):
        self.assertEqual(numerical.type("x // 3"), integer)
        self.assertRaises(FemtocodeError, lambda: numerical.type("x // 3.14"))
        self.assertEqual(numerical.type("xlim // 3"), integer(0, 9 // 3))
        self.assertRaises(FemtocodeError, lambda: numerical.type("ylim // 3"))
        for entry in numerical.toPython(x = "x", a = "x // 3").submit():
            self.assertAlmostEqual(entry.x // 3, entry.a)

    def test_floordivide(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("x // xlim"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim // xlim"))
        for entry in numerical.toPython(x = "x", xlim = "xlim", a = "x // (xlim + 1)").submit():
            self.assertAlmostEqual(entry.x // (entry.xlim + 1), entry.a)

    def test_power_literal(self):
        for entry in numerical.toPython(x = "x", a = "x**5").submit():
            self.assertAlmostEqual(entry.x**5, entry.a)

    def test_power_literal2(self):
        for entry in numerical.toPython(x = "x", a = "2**x").submit():
            self.assertAlmostEqual(2**entry.x, entry.a)

    def test_power_literal3(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("x**(1/2)"))
        for entry in numerical.toPython(xlim = "xlim", a = "xlim**(1/2)").submit():
            self.assertAlmostEqual(math.sqrt(entry.xlim), entry.a)

    def test_power(self):
        for entry in numerical.toPython(x = "x", y = "y", a = "x**y").submit():
            self.assertAlmostEqual(entry.x ** entry.y, entry.a)
