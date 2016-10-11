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

from femtocode.asts.functiontree import build
from femtocode.defs import SymbolTable
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.typesystem import *

import sys

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestSemantics(unittest.TestCase):
    def runTest(self):
        pass

    def test_simple1(self):
        p = build(parse("x"), table)
        print(p)
        print(p.schema(SymbolTable({"x": integer})))

        p = build(parse("x + 3"), table)
        print(p)
        print(p.schema(SymbolTable({"x": integer})))

        p = build(parse("y = x + 3; y + 1"), table)
        print(p)
        print(p.schema(SymbolTable({"x": integer})))

        p = build(parse("{x => x + 3}"), table)
        print(p)
        print(p.schema(SymbolTable()))

        p = build(parse("def f(x): x + 3.14;\nf"), table)
        print(p)
        print(p.schema(SymbolTable()))

        p = build(parse("def f(q): q + 3;  f(x)"), table)
        print(p)
        print(p.schema(SymbolTable({"x": integer})))

