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
for i in xrange(100):
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