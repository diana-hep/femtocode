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
import math
import re
import sys
import unittest

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.defs import SymbolTable
from femtocode.execution import Executor
from femtocode.parser import parse
from femtocode.testdataset import TestDataset
from femtocode.testdataset import TestSession
from femtocode.typesystem import *
from femtocode.workflow import *

session = TestSession()

numerical = session.source("Numerical", x=integer, xlim=integer(0, almost(10)), xlim2=integer(1, almost(11)), y=real, ylim=real(0, almost(10)), ylim2=real(almost(0), almost(10)))
for i in xrange(100):
    numerical.dataset.fill({"x": i, "xlim": i % 10, "xlim2": (i % 10) + 1, "y": i + 0.2, "ylim": (i + 0.2) % 10.0, "ylim2": (i + 0.2) % 10.0})

semiflat = session.source("SemiFlat", muon=record(pt=real(0, almost(inf)), eta=real, phi=real(-pi, pi)), jet=record(mass=real(0, almost(inf)), pt=real(0, almost(inf)), eta=real, phi=real(-pi, pi)))
for i in xrange(100):
    semiflat.dataset.fill({"muon": semiflat.dataset.types["muon"](pt=float(i), eta=(float(i) % 10 - 5), phi=((float(i) % 60 - 30)/10)), "jet": semiflat.dataset.types["jet"](mass=float(i), pt=float(i), eta=(float(i) % 10 - 5), phi=((float(i) % 60 - 30)/10))})

nonflat = session.source("NonFlat", met=real(0, almost(inf)), muons=collection(record(pt=real(0, almost(inf)), eta=real, phi=real(-pi, pi))), jets=collection(record(mass=real(0, almost(inf)), pt=real(0, almost(inf)), eta=real, phi=real(-pi, pi))))
for i in xrange(10):   # FIXME: 100
    muons = []
    jets = []
    for j in xrange(i % 3):
        muons.append(nonflat.dataset.types["muons[]"](pt=float(i), eta=(float(i) % 10 - 5), phi=((float(i) % 60 - 30)/10)))
    for j in xrange(i % 10):
        jets.append(nonflat.dataset.types["jets[]"](mass=float(i), pt=float(i), eta=(float(i) % 10 - 5), phi=((float(i) % 60 - 30)/10)))
    nonflat.dataset.fill({"met": float(i), "muons": muons, "jets": jets})

def mapp(obj, fcn):
    return list(map(fcn, obj))

class TestLibStandard(unittest.TestCase):
    def runTest(self):
        pass

    ### FIXME! (see also in test_execution.py)
    # def test_literal(self):
    #     values = [entry.a for entry in numerical.toPython(a = "3.14").submit()]
    #     self.assertEqual(values, [3.14] * 100)

########################################################## Basic calculator

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

    def test_plus_literal(self):
        self.assertEqual(numerical.type("+2"), integer(+2, +2))
        for entry in numerical.toPython(x = "x", a = "+2 + x").submit():
            self.assertAlmostEqual(+2 + entry.x, entry.a)

    def test_plus(self):
        self.assertEqual(numerical.type("+xlim"), integer(0, +9))
        self.assertEqual(numerical.type("+ylim"), real(0, almost(+10)))
        self.assertEqual(numerical.type("+ylim2"), real(almost(0), almost(+10)))
        for entry in numerical.toPython(x = "x", a = "+x").submit():
            self.assertAlmostEqual(+entry.x, entry.a)
        for entry in numerical.toPython(y = "y", a = "+y").submit():
            self.assertAlmostEqual(+entry.y, entry.a)

    def test_minus_literal(self):
        self.assertEqual(numerical.type("-2"), integer(-2, -2))
        for entry in numerical.toPython(x = "x", a = "-2 + x").submit():
            self.assertAlmostEqual(-2 + entry.x, entry.a)

    def test_minus(self):
        self.assertEqual(numerical.type("-xlim"), integer(-9, 0))
        self.assertEqual(numerical.type("-ylim"), real(almost(-10), 0))
        self.assertEqual(numerical.type("-ylim2"), real(almost(-10), almost(0)))
        for entry in numerical.toPython(x = "x", a = "-x").submit():
            self.assertAlmostEqual(-entry.x, entry.a)
        for entry in numerical.toPython(y = "y", a = "-y").submit():
            self.assertAlmostEqual(-entry.y, entry.a)

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

    def test_modulo_literal(self):
        for entry in numerical.toPython(x = "x", a = "x % 7").submit():
            self.assertAlmostEqual(entry.x % 7, entry.a)
        for entry in numerical.toPython(x = "x", a = "x % 5.7").submit():
            self.assertAlmostEqual(entry.x % 5.7, entry.a)
        for entry in numerical.toPython(x = "x", a = "x % -7").submit():
            self.assertAlmostEqual(entry.x % -7, entry.a)
        for entry in numerical.toPython(x = "x", a = "x % -5.7").submit():
            self.assertAlmostEqual(entry.x % -5.7, entry.a)

    def test_modulo_literal2(self):
        for entry in numerical.toPython(ylim2 = "ylim2", a = "7 % ylim2").submit():
            self.assertAlmostEqual(7 % entry.ylim2, entry.a)
        for entry in numerical.toPython(ylim2 = "ylim2", a = "5.7 % ylim2").submit():
            self.assertAlmostEqual(5.7 % entry.ylim2, entry.a)
        for entry in numerical.toPython(ylim2 = "ylim2", a = "-7 % ylim2").submit():
            self.assertAlmostEqual(-7 % entry.ylim2, entry.a)
        for entry in numerical.toPython(ylim2 = "ylim2", a = "-5.7 % ylim2").submit():
            self.assertAlmostEqual(-5.7 % entry.ylim2, entry.a)

    def test_modulo(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("x % y"))
        for entry in numerical.toPython(x = "x", ylim2 = "ylim2", a = "x % ylim2").submit():
            self.assertAlmostEqual(entry.x % entry.ylim2, entry.a)

########################################################## Predicates

    def test_equal_literal(self):
        self.assertEqual(numerical.type("x == 5"), boolean)
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim == -5"))
        for entry in numerical.toPython(x = "x", a = "x == 5").submit():
            self.assertEqual(entry.x == 5, entry.a)

    def test_equal(self):
        for entry in numerical.toPython(x = "x", xlim = "xlim", a = "x == xlim").submit():
            self.assertEqual(entry.x == entry.xlim, entry.a)

    def test_notequal_literal(self):
        self.assertEqual(numerical.type("x != 5"), boolean)
        self.assertEqual(numerical.type("xlim != -5"), boolean)
        self.assertRaises(FemtocodeError, lambda: numerical.type("-5 != -5"))
        for entry in numerical.toPython(x = "x", a = "x != 5").submit():
            self.assertEqual(entry.x != 5, entry.a)

    def test_notequal(self):
        for entry in numerical.toPython(x = "x", xlim = "xlim", a = "x != xlim").submit():
            self.assertEqual(entry.x != entry.xlim, entry.a)

    def test_lessthan_literal(self):
        self.assertEqual(numerical.type("x < 100"), boolean)
        self.assertEqual(numerical.type("xlim < 100"), boolean(True))
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim < -100"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("100 < xlim"))
        for entry in numerical.toPython(x = "x", a = "x < 5").submit():
            self.assertEqual(entry.x < 5, entry.a)
        for entry in numerical.toPython(x = "x", a = "5 < x").submit():
            self.assertEqual(5 < entry.x, entry.a)

    def test_lessthan(self):
        self.assertEqual(numerical.type("xlim < ylim + 100"), boolean(True))
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim < ylim - 100"))
        for entry in numerical.toPython(x = "x", y = "y", a = "x < y").submit():
            self.assertEqual(entry.x < entry.y, entry.a)

    def test_lessequal_literal(self):
        self.assertEqual(numerical.type("x <= 100"), boolean)
        self.assertEqual(numerical.type("xlim <= 100"), boolean(True))
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim <= -100"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("100 <= xlim"))
        for entry in numerical.toPython(x = "x", a = "x <= 5").submit():
            self.assertEqual(entry.x <= 5, entry.a)
        for entry in numerical.toPython(x = "x", a = "5 <= x").submit():
            self.assertEqual(5 <= entry.x, entry.a)

    def test_lessequal(self):
        self.assertEqual(numerical.type("xlim <= ylim + 100"), boolean(True))
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim <= ylim - 100"))
        for entry in numerical.toPython(x = "x", y = "y", a = "x <= y").submit():
            self.assertEqual(entry.x < entry.y, entry.a)

    def test_greaterthan_literal(self):
        self.assertEqual(numerical.type("x > 100"), boolean)
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim > 100"))
        self.assertEqual(numerical.type("xlim > -100"), boolean(True))
        self.assertEqual(numerical.type("100 > xlim"), boolean(True))
        for entry in numerical.toPython(x = "x", a = "x > 5").submit():
            self.assertEqual(entry.x > 5, entry.a)
        for entry in numerical.toPython(x = "x", a = "5 > x").submit():
            self.assertEqual(5 > entry.x, entry.a)

    def test_greaterthan(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim > ylim + 100"))
        self.assertEqual(numerical.type("xlim > ylim - 100"), boolean(True))
        for entry in numerical.toPython(x = "x", y = "y", a = "x > y").submit():
            self.assertEqual(entry.x > entry.y, entry.a)

    def test_greaterequal_literal(self):
        self.assertEqual(numerical.type("x >= 100"), boolean)
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim >= 100"))
        self.assertEqual(numerical.type("xlim >= -100"), boolean(True))
        self.assertEqual(numerical.type("100 >= xlim"), boolean(True))
        for entry in numerical.toPython(x = "x", a = "x >= 5").submit():
            self.assertEqual(entry.x >= 5, entry.a)
        for entry in numerical.toPython(x = "x", a = "5 >= x").submit():
            self.assertEqual(5 >= entry.x, entry.a)

    def test_greaterequal(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("xlim >= ylim + 100"))
        self.assertEqual(numerical.type("xlim >= ylim - 100"), boolean(True))
        for entry in numerical.toPython(x = "x", y = "y", a = "x >= y").submit():
            self.assertEqual(entry.x >= entry.y, entry.a)

    def test_and_literal(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("x == 5 and x == 6"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("x == 5 and x == 5 + 1"))
        self.assertEqual(numerical.type("x == 5 and xlim == 6"), boolean)

    def test_and(self):
        for entry in numerical.toPython(x = "x", xlim = "xlim", a = "x == 5 and x == xlim").submit():
            self.assertEqual(entry.x == 5 and entry.x == entry.xlim, entry.a)

    def test_or_literal(self):
        self.assertEqual(numerical.type("x == 5 or x == 6"), boolean)
        self.assertEqual(numerical.type("x == 5 or x == 5 + 1"), boolean)
        self.assertEqual(numerical.type("x == 5 or xlim == 6"), boolean)
        for entry in numerical.toPython(x = "x", xlim = "xlim", a = "x == 5 or xlim == 6").submit():
            self.assertEqual(entry.x == 5 or entry.xlim == 6, entry.a)

    def test_or(self):
        for entry in numerical.toPython(x = "x", xlim = "xlim", a = "x == 5 or x == xlim").submit():
            self.assertEqual(entry.x == 5 or entry.x == entry.xlim, entry.a)

    def test_not_literal(self):
        # Note: uses DeMorgan's laws to put this into a form it can check
        self.assertRaises(FemtocodeError, lambda: numerical.type("not (x != 5 or x != 6)"))

    def test_not(self):
        for entry in numerical.toPython(x = "x", xlim = "xlim", a = "not x == xlim").submit():
            self.assertEqual(not entry.x == entry.xlim, entry.a)

    def test_if_literal(self):
        self.assertEqual(numerical.type("10 == 10"), boolean)
        self.assertRaises(FemtocodeError, lambda: numerical.type("if 9 == 10: x else: y"))
        self.assertRaises(FemtocodeError, lambda: numerical.type("if 10 == 10: x else: y"))

    def test_if(self):
        for entry in numerical.toPython(x = "x", y = "y", a = "if x == 5: x else: y").submit():
            self.assertEqual(entry.x if entry.x == 5 else entry.y, entry.a)

        for entry in numerical.toPython(x = "x", y = "y", a = "if x == 5: x elif x == 6: x - 1 else: y").submit():
            self.assertEqual(entry.x if entry.x == 5 else (entry.x - 1 if entry.x == 6 else entry.y), entry.a)
        
    def test_if_nullable(self):
        self.assertRaises(FemtocodeError, lambda: numerical.type("z = if x - y != 0: x / (x - y) else: None; z + 1"))
        self.assertEqual(numerical.type("z = if x - y != 0: x / (x - y) else: None; if z != None: z + 1 else: None"), union(null, real))

        for entry in numerical.toPython(xlim = "xlim", a = "if xlim < 5: xlim else: None").submit():
            if entry.xlim < 5:
                self.assertEqual(entry.a, entry.xlim)
            else:
                self.assertEqual(entry.a, None)

        for entry in numerical.toPython(ylim = "ylim", a = "if ylim < 5: ylim else: None").submit():
            if entry.ylim < 5:
                self.assertEqual(entry.a, entry.ylim)
            else:
                self.assertEqual(entry.a, None)

    def test_is(self):
        ### FIXME: this is another case of pure Literals not being passed through
        # for entry in numerical.toPython(a = "x is integer").submit():
        #     self.assertEqual(entry.a, True)

        for entry in numerical.toPython(x = "x", a = "x is integer(50, 100)").submit():
            self.assertEqual(entry.x in integer(50, 100), entry.a)

        for entry in numerical.toPython(y = "y", a = "y is integer(50, 100)").submit():
            self.assertEqual(entry.y in integer(50, 100), entry.a)

        for entry in numerical.toPython(y = "y", a = "y is real(50, 100)").submit():
            self.assertEqual(entry.y in real(50, 100), entry.a)

        self.assertRaises(FemtocodeError, lambda: numerical.type("ylim is real(50, 100)"))
        for entry in numerical.toPython(ylim = "ylim", a = "ylim is real(5, almost(10))").submit():
            self.assertEqual(entry.ylim in real(5, almost(10)), entry.a)

        for entry in numerical.toPython(y = "y", a = "y is union(real(0, 25), real(50, 75))").submit():
            self.assertEqual(entry.y in union(real(0, 25), real(50, 75)), entry.a)

        for entry in numerical.define(z = "if x / 25 == 1: None else: x").toPython(z = "z", a = "z is integer").submit():
            self.assertEqual(entry.z in integer, entry.a)

        for entry in numerical.define(z = "if x / 25 == 1: None else: x").toPython(z = "z", a = "z is integer(0, 75)").submit():
            self.assertEqual(entry.z in integer(0, 75), entry.a)

        for entry in numerical.define(z = "if x / 25 == 1: None else: x").toPython(z = "z", a = "z is union(null, integer(0, 75))").submit():
            self.assertEqual(entry.z in union(null, integer(0, 75)), entry.a)

        for entry in numerical.define(z = "if y / 25 == 1: None else: y").toPython(z = "z", a = "z is real").submit():
            self.assertEqual(entry.z in real, entry.a)

        for entry in numerical.define(z = "if y / 25 == 1: None else: y").toPython(z = "z", a = "z is real(0, 75)").submit():
            self.assertEqual(entry.z in real(0, 75), entry.a)

        for entry in numerical.define(z = "if y / 25 == 1: None else: y").toPython(z = "z", a = "z is union(null, real(0, 75))").submit():
            self.assertEqual(entry.z in union(null, real(0, 75)), entry.a)

########################################################## Structure

    def test_dot(self):
        self.assertEqual(semiflat.type("muon.phi + jet.mass"), real(-pi, almost(inf)))

        for entry in semiflat.toPython(muonphi = "muon.phi", jetmass = "jet.mass", a = "muon.phi + jet.mass").submit():
            self.assertEqual(entry.muonphi + entry.jetmass, entry.a)

    def test_map(self):
        self.assertEqual(nonflat.type("muons.map($1.pt + $1.phi)"), collection(real(-pi, almost(inf))))

        for entry in nonflat.toPython(pt = "muons.map($1.pt)", phi = "muons.map($1.phi)", a = "muons.map(mu => mu.pt + mu.phi)").submit():
            self.assertEqual(mapp(zip(entry.pt, entry.phi), lambda x: x[0] + x[1]), entry.a)

    def test_map_realistic(self):
        nonflat.define(mumass = "0.105658").toPython(mass = """
muons.map(mu1 => muons.map({mu2 =>

  p1x = mu1.pt * cos(mu1.phi);
  p1y = mu1.pt * sin(mu1.phi);
  p1z = mu1.pt * sinh(mu1.eta);
  E1 = sqrt(p1x**2 + p1y**2 + p1z**2 + mumass**2);

  p2x = mu2.pt * cos(mu2.phi);
  p2y = mu2.pt * sin(mu2.phi);
  p2z = mu2.pt * sinh(mu2.eta);
  E2 = sqrt(p2x**2 + p2y**2 + p2z**2 + mumass**2);

  px = p1x + p2x;
  py = p1y + p2y;
  pz = p1z + p2z;
  E = E1 + E2;

  if E**2 - px**2 - py**2 - pz**2 >= 0:
    sqrt(E**2 - px**2 - py**2 - pz**2)
  else:
    None

}))
""").submit()

########################################################## Core math

    def test_round(self):
        self.assertEqual(session.source("Test", x=integer(3, 6)).type("round(x)"), integer(3, 6))
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("round(x)"), integer(3, 7))
        self.assertEqual(session.source("Test", x=real(almost(-inf), 6.5)).type("round(x)"), integer(almost(-inf), 7))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(almost(-inf), inf)).type("round(x)"))
        self.assertEqual(session.source("Test", x=union(real(-6.5, -3.14), real(3.14, 6.5))).type("round(x)"), union(integer(-7, -3), integer(3, 7)))
        for entry in numerical.toPython(x = "x", y = "y", a = "round(y)").submit():
            self.assertEqual(entry.a, entry.x)

    def test_floor(self):
        self.assertEqual(session.source("Test", x=integer(3, 6)).type("floor(x)"), integer(3, 6))
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("floor(x)"), integer(3, 6))
        self.assertEqual(session.source("Test", x=real(almost(-inf), 6.5)).type("floor(x)"), integer(almost(-inf), 6))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(almost(-inf), inf)).type("floor(x)"))
        self.assertEqual(session.source("Test", x=union(real(-6.5, -3.14), real(3.14, 6.5))).type("floor(x)"), union(integer(-7, -4), integer(3, 6)))
        for entry in numerical.toPython(x = "x", y = "y", a = "floor(y)").submit():
            self.assertEqual(entry.a, entry.x)

    def test_ceil(self):
        self.assertEqual(session.source("Test", x=integer(3, 6)).type("ceil(x)"), integer(3, 6))
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("ceil(x)"), integer(4, 7))
        self.assertEqual(session.source("Test", x=real(almost(-inf), 6.5)).type("ceil(x)"), integer(almost(-inf), 7))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(almost(-inf), inf)).type("ceil(x)"))
        self.assertEqual(session.source("Test", x=union(real(-6.5, -3.14), real(3.14, 6.5))).type("ceil(x)"), union(integer(-6, -3), integer(4, 7)))
        for entry in numerical.toPython(x = "x", y = "y", a = "ceil(y)").submit():
            self.assertEqual(entry.a, entry.x + 1)

    def test_abs(self):
        self.assertEqual(session.source("Test", x=integer(-6, -3)).type("abs(x)"), integer(3, 6))
        self.assertEqual(session.source("Test", x=real(-6.28, -3.14)).type("abs(x)"), real(3.14, 6.28))
        self.assertEqual(session.source("Test", x=integer(-6, 3)).type("abs(x)"), integer(0, 6))
        self.assertEqual(session.source("Test", x=real(-6.28, 3.14)).type("abs(x)"), real(0, 6.28))

        self.assertEqual(session.source("Test", x=integer(almost(-inf), -3)).type("abs(x)"), integer(3, almost(inf)))
        self.assertEqual(session.source("Test", x=real(almost(-inf), -3.14)).type("abs(x)"), real(3.14, almost(inf)))
        self.assertEqual(session.source("Test", x=integer(almost(-inf), 3)).type("abs(x)"), integer(0, almost(inf)))
        self.assertEqual(session.source("Test", x=real(almost(-inf), 3.14)).type("abs(x)"), real(0, almost(inf)))
        self.assertEqual(session.source("Test", x=real(-inf, -3.14)).type("abs(x)"), real(3.14, inf))
        self.assertEqual(session.source("Test", x=real(-inf, 3.14)).type("abs(x)"), real(0, inf))

        self.assertEqual(session.source("Test", x=integer(6, almost(inf))).type("abs(x)"), integer(6, almost(inf)))
        self.assertEqual(session.source("Test", x=real(3.14, almost(inf))).type("abs(x)"), real(3.14, almost(inf)))
        self.assertEqual(session.source("Test", x=integer(-3, almost(inf))).type("abs(x)"), integer(0, almost(inf)))
        self.assertEqual(session.source("Test", x=real(-3.14, almost(inf))).type("abs(x)"), real(0, almost(inf)))
        self.assertEqual(session.source("Test", x=real(3.14, inf)).type("abs(x)"), real(3.14, inf))
        self.assertEqual(session.source("Test", x=real(-3.14, inf)).type("abs(x)"), real(0, inf))

        for entry in numerical.toPython(y = "y", a = "abs(y - 50)").submit():
            self.assertEqual(entry.a, abs(entry.y - 50))

    def test_sqrt(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("sqrt(x)"), real(math.sqrt(3.14), math.sqrt(6.5)))
        self.assertEqual(session.source("Test", x=real(almost(0), 6.5)).type("sqrt(x)"), real(almost(0), math.sqrt(6.5)))
        self.assertEqual(session.source("Test", x=real(0, 6.5)).type("sqrt(x)"), real(0, math.sqrt(6.5)))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 6.5)).type("sqrt(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 0)).type("sqrt(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, almost(0))).type("sqrt(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, -0.1)).type("sqrt(x)"))
        for entry in numerical.toPython(ylim = "ylim", a = "sqrt(ylim)").submit():
            self.assertEqual(entry.a, math.sqrt(entry.ylim))

    def test_exp(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("exp(x)"), real(math.exp(3.14), math.exp(6.5)))
        for entry in numerical.toPython(y = "y", a = "exp(y)").submit():
            self.assertEqual(entry.a, math.exp(entry.y))

    def test_log(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("log(x)"), real(math.log(3.14), math.log(6.5)))
        self.assertEqual(session.source("Test", x=real(almost(0), 6.5)).type("log(x)"), real(almost(-inf), math.log(6.5)))
        self.assertEqual(session.source("Test", x=real(0, 6.5)).type("log(x)"), real(-inf, math.log(6.5)))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 6.5)).type("log(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 0)).type("log(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, almost(0))).type("log(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, -0.1)).type("log(x)"))
        for entry in numerical.toPython(ylim = "ylim", a = "log(ylim)").submit():
            self.assertEqual(entry.a, math.log(entry.ylim))

    def test_log2(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("log2(x)"), real(math.log(3.14, 2), math.log(6.5, 2)))
        self.assertEqual(session.source("Test", x=real(almost(0), 6.5)).type("log2(x)"), real(almost(-inf), math.log(6.5, 2)))
        self.assertEqual(session.source("Test", x=real(0, 6.5)).type("log2(x)"), real(-inf, math.log(6.5, 2)))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 6.5)).type("log2(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 0)).type("log2(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, almost(0))).type("log2(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, -0.1)).type("log2(x)"))
        for entry in numerical.toPython(ylim = "ylim", a = "log2(ylim)").submit():
            self.assertEqual(entry.a, math.log(entry.ylim, 2))

    def test_log10(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("log10(x)"), real(math.log(3.14, 10), math.log(6.5, 10)))
        self.assertEqual(session.source("Test", x=real(almost(0), 6.5)).type("log10(x)"), real(almost(-inf), math.log(6.5, 10)))
        self.assertEqual(session.source("Test", x=real(0, 6.5)).type("log10(x)"), real(-inf, math.log(6.5, 10)))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 6.5)).type("log10(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, 0)).type("log10(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, almost(0))).type("log10(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1, -0.1)).type("log10(x)"))
        for entry in numerical.toPython(ylim = "ylim", a = "log10(ylim)").submit():
            self.assertEqual(entry.a, math.log(entry.ylim, 10))

    def test_sin(self):
        self.assertEqual(session.source("Test", x=real(-0.1, 1.0)).type("sin(x)"), real(math.sin(-0.1), math.sin(1.0)))
        self.assertEqual(session.source("Test", x=real(-0.1, almost(1.0))).type("sin(x)"), real(math.sin(-0.1), almost(math.sin(1.0))))
        self.assertEqual(session.source("Test", x=real(-0.1, math.pi/2)).type("sin(x)"), real(math.sin(-0.1), math.sin(math.pi/2)))
        self.assertEqual(session.source("Test", x=real(-0.1, almost(math.pi/2))).type("sin(x)"), real(math.sin(-0.1), almost(math.sin(math.pi/2))))
        self.assertEqual(session.source("Test", x=real(-0.1, 3.2)).type("sin(x)"), real(math.sin(-0.1), 1.0))
        self.assertEqual(session.source("Test", x=real(-0.1, almost(3.2))).type("sin(x)"), real(math.sin(-0.1), 1.0))
        self.assertEqual(session.source("Test", x=real(-0.1, 10.0)).type("sin(x)"), real(-1.0, 1.0))
        self.assertEqual(session.source("Test", x=real(-0.1, almost(10.0))).type("sin(x)"), real(-1.0, 1.0))
        self.assertEqual(session.source("Test", x=real(-0.1, almost(inf))).type("sin(x)"), real(-1.0, 1.0))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-0.1, inf)).type("sin(x)"))
        self.assertEqual(session.source("Test", x=real(almost(0), 1)).type("sin(1/x)"), real(-1.0, 1.0))
        for entry in numerical.toPython(y = "y", a = "sin(y)").submit():
            self.assertEqual(entry.a, math.sin(entry.y))

    def test_cos(self):
        self.assertEqual(session.source("Test", x=real(0.1, 1.0)).type("cos(x)"), real(math.cos(1.0), math.cos(0.1)))
        self.assertEqual(session.source("Test", x=real(almost(0.0), 1.0)).type("cos(x)"), real(math.cos(1.0), almost(1.0)))
        self.assertEqual(session.source("Test", x=real(0.0, 1.0)).type("cos(x)"), real(math.cos(1.0), 1.0))
        self.assertEqual(session.source("Test", x=real(-0.1, 1.0)).type("cos(x)"), real(math.cos(1.0), 1.0))
        self.assertEqual(session.source("Test", x=real(-10.0, 1.0)).type("cos(x)"), real(-1.0, 1.0))
        self.assertEqual(session.source("Test", x=real(almost(-inf), 1.0)).type("cos(x)"), real(-1.0, 1.0))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-inf, 1.0)).type("cos(x)"))
        for entry in numerical.toPython(y = "y", a = "cos(y)").submit():
            self.assertEqual(entry.a, math.cos(entry.y))

    def test_tan(self):
        self.assertEqual(session.source("Test", x=real(0.1, 1.0)).type("tan(x)"), real(math.tan(0.1), math.tan(1.0)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(math.pi/2))).type("tan(x)"), real(math.tan(0.1), almost(inf)))
        self.assertEqual(session.source("Test", x=real(0.1, math.pi/2)).type("tan(x)"), real(math.tan(0.1), inf))
        self.assertEqual(session.source("Test", x=real(0.1, 2.0)).type("tan(x)"), union(extended(-inf, math.tan(2.0)), extended(math.tan(0.1), max=inf)))
        self.assertEqual(session.source("Test", x=real(0.1, 3.5)).type("tan(x)"), extended)
        self.assertEqual(session.source("Test", x=real(0.1, 10)).type("tan(x)"), extended)
        self.assertEqual(session.source("Test", x=real(0.1, almost(inf))).type("tan(x)"), real(-inf, inf))
        for entry in numerical.toPython(y = "y", a = "tan(y)").submit():
            self.assertEqual(entry.a, math.tan(entry.y))

    def test_asin(self):
        self.assertEqual(session.source("Test", x=real(0.1, 0.5)).type("asin(x)"), real(math.asin(0.1), math.asin(0.5)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(0.5))).type("asin(x)"), real(math.asin(0.1), almost(math.asin(0.5))))
        self.assertEqual(session.source("Test", x=real(0.1, 1.0)).type("asin(x)"), real(math.asin(0.1), math.asin(1.0)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(1.0))).type("asin(x)"), real(math.asin(0.1), almost(math.asin(1.0))))
        self.assertEqual(session.source("Test", x=real(-1.0, 0.5)).type("asin(x)"), real(math.asin(-1.0), math.asin(0.5)))
        self.assertEqual(session.source("Test", x=real(almost(-1.0), 0.5)).type("asin(x)"), real(almost(math.asin(-1.0)), math.asin(0.5)))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0.1, 1.1)).type("asin(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0.1, almost(1.1))).type("asin(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1.1, 0.5)).type("asin(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(almost(-1.1), 0.5)).type("asin(x)"))
        for entry in numerical.toPython(ylim2 = "ylim2", a = "asin(ylim2 / 10)").submit():
            self.assertEqual(entry.a, math.asin(entry.ylim2 / 10))

    def test_acos(self):
        self.assertEqual(session.source("Test", x=real(0.1, 0.5)).type("acos(x)"), real(math.acos(0.5), math.acos(0.1)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(0.5))).type("acos(x)"), real(almost(math.acos(0.5)), math.acos(0.1)))
        self.assertEqual(session.source("Test", x=real(0.1, 1.0)).type("acos(x)"), real(math.acos(1.0), math.acos(0.1)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(1.0))).type("acos(x)"), real(almost(math.acos(1.0)), math.acos(0.1)))
        self.assertEqual(session.source("Test", x=real(-1.0, 0.5)).type("acos(x)"), real(math.acos(0.5), math.acos(-1.0)))
        self.assertEqual(session.source("Test", x=real(almost(-1.0), 0.5)).type("acos(x)"), real(math.acos(0.5), almost(math.acos(-1.0))))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0.1, 1.1)).type("acos(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0.1, almost(1.1))).type("acos(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1.1, 0.5)).type("acos(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(almost(-1.1), 0.5)).type("acos(x)"))
        for entry in numerical.toPython(ylim2 = "ylim2", a = "acos(ylim2 / 10)").submit():
            self.assertEqual(entry.a, math.acos(entry.ylim2 / 10))

    def test_atan(self):
        self.assertEqual(session.source("Test", x=real(0.1, 1.0)).type("atan(x)"), real(math.atan(0.1), math.atan(1.0)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(1.0))).type("atan(x)"), real(math.atan(0.1), almost(math.atan(1.0))))
        self.assertEqual(session.source("Test", x=real(almost(0.1), 1.0)).type("atan(x)"), real(almost(math.atan(0.1)), math.atan(1.0)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(inf))).type("atan(x)"), real(math.atan(0.1), almost(math.pi/2)))
        self.assertEqual(session.source("Test", x=real(0.1, inf)).type("atan(x)"), real(math.atan(0.1), math.pi/2))
        self.assertEqual(session.source("Test", x=real(almost(-inf), 1.0)).type("atan(x)"), real(almost(-math.pi/2), math.atan(1.0)))
        self.assertEqual(session.source("Test", x=real(-inf, 1.0)).type("atan(x)"), real(-math.pi/2, math.atan(1.0)))
        self.assertEqual(session.source("Test", x=real).type("atan(x)"), real(almost(-math.pi/2), almost(math.pi/2)))
        self.assertEqual(session.source("Test", x=extended).type("atan(x)"), real(-math.pi/2, math.pi/2))
        for entry in numerical.toPython(y = "y", a = "atan(y)").submit():
            self.assertEqual(entry.a, math.atan(entry.y))

    def test_atan2(self):
        self.assertEqual(session.source("Test", x=real(0.1, 1.0), y=real(0.1, 1.0)).type("atan2(y, x)"), real(-math.pi/2, math.pi/2))
        self.assertEqual(session.source("Test", x=real, y=real).type("atan2(y, x)"), real(-math.pi/2, math.pi/2))
        for entry in numerical.toPython(y = "y", a = "atan2(y, y)").submit():
            self.assertEqual(entry.a, math.atan2(entry.y, entry.y))
            break

    def test_sinh(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("sinh(x)"), real(math.sinh(3.14), math.sinh(6.5)))
        self.assertEqual(session.source("Test", x=real(3.14, almost(6.5))).type("sinh(x)"), real(math.sinh(3.14), almost(math.sinh(6.5))))
        self.assertEqual(session.source("Test", x=real(3.14, almost(inf))).type("sinh(x)"), real(math.sinh(3.14), almost(math.sinh(inf))))
        self.assertEqual(session.source("Test", x=real(3.14, inf)).type("sinh(x)"), real(math.sinh(3.14), inf))
        self.assertEqual(session.source("Test", x=real).type("sinh(x)"), real(almost(-inf), almost(inf)))
        self.assertEqual(session.source("Test", x=extended).type("sinh(x)"), real(-inf, inf))
        for entry in numerical.toPython(y = "y", a = "sinh(y)").submit():
            self.assertEqual(entry.a, math.sinh(entry.y))

    def test_cosh(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("cosh(x)"), real(math.cosh(3.14), math.cosh(6.5)))
        self.assertEqual(session.source("Test", x=real(3.14, almost(6.5))).type("cosh(x)"), real(math.cosh(3.14), almost(math.cosh(6.5))))
        self.assertEqual(session.source("Test", x=real(3.14, almost(inf))).type("cosh(x)"), real(math.cosh(3.14), almost(math.cosh(inf))))
        self.assertEqual(session.source("Test", x=real(3.14, inf)).type("cosh(x)"), real(math.cosh(3.14), inf))
        self.assertEqual(session.source("Test", x=real(-3.14, 6.5)).type("cosh(x)"), real(1.0, math.cosh(6.5)))
        self.assertEqual(session.source("Test", x=real(-13.14, 6.5)).type("cosh(x)"), real(1.0, math.cosh(13.14)))
        self.assertEqual(session.source("Test", x=real(-3.14, almost(6.5))).type("cosh(x)"), real(1.0, almost(math.cosh(6.5))))
        self.assertEqual(session.source("Test", x=real(-13.14, almost(6.5))).type("cosh(x)"), real(1.0, math.cosh(13.14)))
        self.assertEqual(session.source("Test", x=real(-3.14, almost(inf))).type("cosh(x)"), real(1.0, almost(math.cosh(inf))))
        self.assertEqual(session.source("Test", x=real(-3.14, inf)).type("cosh(x)"), real(1.0, inf))
        self.assertEqual(session.source("Test", x=real).type("cosh(x)"), real(1.0, almost(inf)))
        self.assertEqual(session.source("Test", x=extended).type("cosh(x)"), real(1.0, inf))
        for entry in numerical.toPython(y = "y", a = "cosh(y)").submit():
            self.assertEqual(entry.a, math.cosh(entry.y))

    def test_tanh(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("tanh(x)"), real(math.tanh(3.14), math.tanh(6.5)))
        self.assertEqual(session.source("Test", x=real(3.14, almost(6.5))).type("tanh(x)"), real(math.tanh(3.14), almost(math.tanh(6.5))))
        self.assertEqual(session.source("Test", x=real(3.14, inf)).type("tanh(x)"), real(math.tanh(3.14), 1.0))
        self.assertEqual(session.source("Test", x=real(3.14, almost(inf))).type("tanh(x)"), real(math.tanh(3.14), almost(1.0)))
        self.assertEqual(session.source("Test", x=real(-inf, almost(inf))).type("tanh(x)"), real(-1.0, almost(1.0)))
        self.assertEqual(session.source("Test", x=real(almost(-inf), almost(inf))).type("tanh(x)"), real(almost(-1.0), almost(1.0)))
        for entry in numerical.toPython(y = "y", a = "tanh(y)").submit():
            self.assertEqual(entry.a, math.tanh(entry.y))

    def test_asinh(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("asinh(x)"), real(math.asinh(3.14), math.asinh(6.5)))
        self.assertEqual(session.source("Test", x=real(3.14, almost(6.5))).type("asinh(x)"), real(math.asinh(3.14), almost(math.asinh(6.5))))
        self.assertEqual(session.source("Test", x=real(3.14, inf)).type("asinh(x)"), real(math.asinh(3.14), inf))
        self.assertEqual(session.source("Test", x=real(3.14, almost(inf))).type("asinh(x)"), real(math.asinh(3.14), almost(inf)))
        self.assertEqual(session.source("Test", x=real).type("asinh(x)"), real)
        self.assertEqual(session.source("Test", x=extended).type("asinh(x)"), extended)
        for entry in numerical.toPython(y = "y", a = "asinh(y)").submit():
            self.assertEqual(entry.a, math.asinh(entry.y))

    def test_acosh(self):
        self.assertEqual(session.source("Test", x=real(3.14, 6.5)).type("acosh(x)"), real(math.acosh(3.14), math.acosh(6.5)))
        self.assertEqual(session.source("Test", x=real(almost(1), 6.5)).type("acosh(x)"), real(almost(0), math.acosh(6.5)))
        self.assertEqual(session.source("Test", x=real(1, 6.5)).type("acosh(x)"), real(0, math.acosh(6.5)))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0, 6.5)).type("acosh(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0, 0.5)).type("acosh(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0, almost(0.5))).type("acosh(x)"))
        for entry in numerical.toPython(ylim = "ylim", a = "acosh(ylim + 1)").submit():
            self.assertEqual(entry.a, math.acosh(entry.ylim + 1))

    def test_atanh(self):
        self.assertEqual(session.source("Test", x=real(0.1, 0.5)).type("atanh(x)"), real(math.atanh(0.1), math.atanh(0.5)))
        self.assertEqual(session.source("Test", x=real(0.1, almost(0.5))).type("atanh(x)"), real(math.atanh(0.1), almost(math.atanh(0.5))))
        self.assertEqual(session.source("Test", x=real(0.1, 1.0)).type("atanh(x)"), real(math.atanh(0.1), inf))
        self.assertEqual(session.source("Test", x=real(0.1, almost(1.0))).type("atanh(x)"), real(math.atanh(0.1), almost(inf)))
        self.assertEqual(session.source("Test", x=real(-1.0, 0.5)).type("atanh(x)"), real(-inf, math.atanh(0.5)))
        self.assertEqual(session.source("Test", x=real(almost(-1.0), 0.5)).type("atanh(x)"), real(almost(-inf), math.atanh(0.5)))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0.1, 1.1)).type("atanh(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(0.1, almost(1.1))).type("atanh(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(-1.1, 0.5)).type("atanh(x)"))
        self.assertRaises(FemtocodeError, lambda: session.source("Test", x=real(almost(-1.1), 0.5)).type("atanh(x)"))
        for entry in numerical.toPython(ylim2 = "ylim2", a = "atanh(ylim2 / 10)").submit():
            self.assertEqual(entry.a, math.atanh(entry.ylim2 / 10))
