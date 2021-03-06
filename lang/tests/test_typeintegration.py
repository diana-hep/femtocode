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
from femtocode.asts import typedtree
from femtocode.defs import SymbolTable
from femtocode.inference import *
from femtocode.lib.standard import StandardLibrary
from femtocode.parser import parse
from femtocode.py23 import *
from femtocode.typesystem import *

class TestTypeIntegration(unittest.TestCase):
    def runTest(self):
        pass

    @staticmethod
    def expecting(result, code, verbose=False, **symbolTypes):
        def doit():
            lt, frame = lispytree.build(parse(code), StandardLibrary.table.fork(dict((n, lispytree.Ref(n)) for n in symbolTypes)))
            tt, frame = typedtree.build(lt, SymbolTable(dict((lispytree.Ref(n), t) for n, t in symbolTypes.items())))
            return tt.schema

        if isinstance(result, Schema):
            actual = doit()
            if actual != result:
                raise AssertionError("\"{0}\" resulted in the wrong type:\n\n{1}".format(code, compare(result, actual, ("expected", "actual"))))
        else:
            try:
                actual = doit()
            except result as err:
                if verbose:
                    print("\n" + str(err))
            else:
                raise AssertionError("\"{0}\" was supposed to raise {1} but instead returned {2}".format(code, result, actual))

    def test_add(self):
        self.expecting(integer, "x + y", x=integer, y=integer)
        self.expecting(integer(7, 15), "x + y", x=integer(3, 10), y=integer(4, 5))
        self.expecting(real(7, 15), "x + y", x=integer(3, 10), y=real(4, 5))
        self.expecting(real(15, 25), "x + 5", x=real(10, 20))
        self.expecting(real, "x + y + z", x=integer, y=integer, z=real)
        self.expecting(extended, "x + y", x=real, y=extended)
        self.expecting(union(integer(100, 106), real(110, 121)), "x + y", x=union(integer(0, 5), real(10, 20)), y=integer(100, 101))
        self.expecting(FemtocodeError, "x + y", x=extended, y=extended)
        self.expecting(extended(0, inf), "x + y", x=extended(0, inf), y=extended(0, inf))

    def test_equal(self):
        self.expecting(boolean, "x == y", x=integer, y=integer)
        self.expecting(boolean, "x == y", x=integer, y=real)
        self.expecting(boolean, "x == 5", x=integer)
        self.expecting(boolean, "5 == x", x=integer)
        self.expecting(FemtocodeError, "x == y", x=real(0, almost(5)), y=real(almost(5), 10))
        self.expecting(FemtocodeError, "x == 5", x=real(0, almost(5)))
        self.expecting(boolean, "x == y == z", x=integer, y=integer, z=integer)
        self.expecting(boolean, "x == y + 5", x=integer, y=integer)
        self.expecting(boolean, "x == y", x=integer(0, 5), y=integer(5, 10))
        self.expecting(FemtocodeError, "x == y + 1", x=integer(0, 5), y=integer(5, 10))
        self.expecting(FemtocodeError, "x == y", x=integer, y=string)
        self.expecting(FemtocodeError, "2.2 + 2 == y", y=string)
        self.expecting(FemtocodeError, "x == 'hello'", x=integer)
        self.expecting(FemtocodeError, "x == \"hello\"", x=integer)
        self.expecting(FemtocodeError, "x == inf", x=integer, y=integer)
        self.expecting(FemtocodeError, "x == inf", x=real, y=integer)
        self.expecting(boolean, "x == inf", x=extended, y=integer)

    def test_and(self):
        self.expecting(boolean, "x and y", x=boolean, y=boolean)
        self.expecting(boolean, "x and y == z", x=boolean, y=integer, z=integer)
        self.expecting(FemtocodeError, "x and y == z", x=boolean, y=integer, z=boolean)
        self.expecting(FemtocodeError, "x and y == z", x=integer, y=integer, z=integer)
        self.expecting(FemtocodeError, "x is integer and x is string", x=union(integer, string))
        self.expecting(FemtocodeError, "x == 5 and x == 6", x=integer)
        self.expecting(boolean, "x == 5 and y == 6", x=integer, y=integer)
        self.expecting(FemtocodeError, "x == 5 and y == 6 and x == y", x=integer, y=integer)
        self.expecting(FemtocodeError, "x == y and x == 5 and y == 6", x=integer, y=integer)
        self.expecting(FemtocodeError, "x == 5 and x == y and y == 6", x=integer, y=integer)
        self.expecting(FemtocodeError, "x == y and x == 5 and y == 3 + 3", x=integer, y=integer)

    def test_or(self):
        self.expecting(boolean, "x or y", x=boolean, y=boolean)
        self.expecting(boolean, "x or y == z", x=boolean, y=integer, z=integer)
        self.expecting(FemtocodeError, "x or y == z", x=boolean, y=integer, z=boolean)
        self.expecting(FemtocodeError, "x or y == z", x=integer, y=integer, z=integer)
        self.expecting(boolean, "x == 5 or x == 10", x=integer)
        self.expecting(FemtocodeError, "(x == 5 or x == 7) and x == 7", x=integer)
        self.expecting(FemtocodeError, "(x == 7 or x == 5) and x == 7", x=integer)
        self.expecting(FemtocodeError, "(x == 5 or x == 10) and x == 7", x=integer)

    def test_if(self):
        self.expecting(union(integer(10, 10), integer(20, 20)), "if test: 10 else: 20", test=boolean)
        self.expecting(union(integer(10, 10), null), "if test: 10 else: None", test=boolean)
        self.expecting(FemtocodeError, "if x is real: x + 5 else: None", x=real)
        self.expecting(union(real(min=15), null), "if x is real(min=10): x + 5 else: None", x=real)
        self.expecting(union(real(5, 5), null), "if x == 5: x else: None", x=real)
        self.expecting(union(real(5, 5), real(0, 0)), "if x == 5: x else: 0", x=real)
        self.expecting(union(real(5, almost(inf)), null), "if x is real(0, almost(inf)): x + 5 else: None", x=real)
        self.expecting(union(integer(10, 10), integer(20, 20), integer(30, 30)), "if test1: 10 elif test2: 20 else: 30", test1=boolean, test2=boolean)

    def test_map(self):
        self.expecting(collection(real), "data.map(x => x + 10)", data=collection(real))
        self.expecting(collection(real(15, 20)), "data.map(x => x + 10)", data=collection(real(5, 10)))
        self.expecting(collection(real(15, 20)), "data.map($1 + 10)", data=collection(real(5, 10)))
        self.expecting(collection(real), "data.map(x => x + y)", data=collection(real), y=real)
        self.expecting(collection(real(6, 12)), "data.map(x => x + y)", data=collection(real(5, 10)), y=real(1, 2))
        self.expecting(collection(real(6, 12)), "data.map($1 + y)", data=collection(real(5, 10)), y=real(1, 2))
        self.expecting(FemtocodeError, "data.map({x => x}, 4)", data=collection(real))
        self.expecting(FemtocodeError, "data.map()", data=collection(real))
        self.expecting(collection(real(15, 20)), "data.map(fcn = {x => x + 10})", data=collection(real(5, 10)))
        self.expecting(collection(real(15, 20)), "data.map({x => x + 10})", data=collection(real(5, 10)))
        self.expecting(collection(real(15, 20)), "addten = {x => x + 10}; data.map(addten)", data=collection(real(5, 10)))
        self.expecting(collection(real(15, 20)), "def addten(x): x + 10; data.map(addten)", data=collection(real(5, 10)))
        self.expecting(collection(real(15, 20)), """
def addten(x): x + 10;
data.map(addten)""", data=collection(real(5, 10)))
        self.expecting(collection(real(15, 20)), """
def addten(x) {
  x + 10
}
data.map(addten)""", data=collection(real(5, 10)))
