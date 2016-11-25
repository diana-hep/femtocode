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

from femtocode.asts.functiontree import *
from femtocode.defs import SymbolTable
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.typesystem import *
from femtocode.inference import *

import sys

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestTypeIntegration(unittest.TestCase):
    def runTest(self):
        pass

    @staticmethod
    def expecting(result, code, verbose=False, **symbolTypes):
        if isinstance(result, Schema):
            actual = build(parse(code), table).schema(SymbolTable(symbolTypes))
            if actual != result:
                raise AssertionError("\"{0}\" resulted in the wrong type:\n\n{1}".format(code, compare(result, actual, ("expected", "actual"))))
        else:
            try:
                build(parse(code), table).schema(SymbolTable(symbolTypes))
            except result as err:
                if verbose:
                    print("\n" + str(err))
            else:
                raise AssertionError("\"{0}\" was supposed to raise {1}".format(code, result))

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

    def test_and(self):
        self.expecting(boolean, "x and y", x=boolean, y=boolean)
        self.expecting(boolean, "x and y == z", x=boolean, y=integer, z=integer)
        self.expecting(FemtocodeError, "x and y == z", x=boolean, y=integer, z=boolean)
        self.expecting(FemtocodeError, "x and y == z", x=integer, y=integer, z=integer)

    def test_or(self):
        self.expecting(boolean, "x or y", x=boolean, y=boolean)
        self.expecting(boolean, "x or y == z", x=boolean, y=integer, z=integer)
        self.expecting(FemtocodeError, "x or y == z", x=boolean, y=integer, z=boolean)
        self.expecting(FemtocodeError, "x or y == z", x=integer, y=integer, z=integer)

    def test_not(self):
        self.expecting(boolean, "not x", x=boolean)
        self.expecting(boolean, "not y == z", y=integer, z=integer)
        self.expecting(boolean, "not (x and y == z)", x=boolean, y=integer, z=integer)
        self.expecting(FemtocodeError, "not y + z", y=integer, z=integer)

