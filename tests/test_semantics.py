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

class TestSemantics(unittest.TestCase):
    def runTest(self):
        pass

    def test_simple1(self):
        # p = build(parse("x"), table)
        # print(p)
        # print(p.schema(SymbolTable({"x": integer})))

        # p = build(parse("x + 3"), table)
        # print(p)
        # print(p.schema(SymbolTable({"x": integer})))

        # p = build(parse("y = x + 3; y + 1"), table)
        # print(p)
        # print(p.schema(SymbolTable({"x": integer})))

        # p = build(parse("{x => x + 3}"), table)
        # print(p)

        # p = build(parse("def f(x): x + 3.14;\nf"), table)
        # print(p)

        # p = build(parse("def f(q): q + 3;  f(x)"), table)
        # print(p)

        # p = build(parse("xs.map({x => 3.14 + x})"), table)
        # print(p)
        # print(p.schema(SymbolTable({"xs": collection(integer)})))

        # p = build(parse("xs.map(x => 3.14 + x)"), table)
        # print(p)
        # print(p.schema(SymbolTable({"xs": collection(integer)})))

        # p = build(parse("xs.map(3.14 + $1)"), table)
        # print(p)
        # print(p.schema(SymbolTable({"xs": collection(integer)})))

        # p = build(parse("xs.map(fcn = {x => 3.14 + x})"), table)
        # print(p)
        # print(p.schema(SymbolTable({"xs": collection(integer)})))

        # try:
        #     build(parse("xs.map(wonky = {x => 3.14 + x}, fcn = {x => 3.14 + x})"), table)
        # except SyntaxError as err:
        #     print(err)

        # try:
        #     build(parse("xs.map()"), table)
        # except SyntaxError as err:
        #     print(err)
        
        # try:
        #     build(parse("xs.map({x => 3.14 + x}, {x => 3.14 + x})"), table)
        # except SyntaxError as err:
        #     print(err)

        # p = build(parse("xs.map(3.14)"), table)
        # print(p)
        # print(p.schema(SymbolTable({"xs": collection(integer)})))

        # p = build(parse("y = x + 3; y"), table)
        # print(p)
        # print(p.schema(SymbolTable({Ref("x"): integer, Call(table["+"], [Literal(3), Ref("x")]): real})))

        # print(build(parse("def f(x): {y => x + y}; f"), table))

        # print(build(parse("def f(x): {y => x + y}; f(3)"), table))

        # print(build(parse("def f(x, z=99): {y => x + y + z}; f(3)"), table))

        # print(build(parse("y == 2"), table))

        # print(build(parse("def f(x): x + 0.1; y == f(2)"), table))

        # def dump(x):
        #     if isinstance(x, Call) and x.fcn.name == "not":
        #         return "not " + dump(x.args[0])
        #     elif isinstance(x, Call) and x.fcn.name in ["and", "or"]:
        #         return "(" + (" " + x.fcn.name + " ").join(dump(y) for y in x.args) + ")"
        #     else:
        #         return repr(x)

        # def dump(x):
        #     if isinstance(x, Call):
        #         return x.fcn.name + "(" + ", ".join(dump(y) for y in x.args) + ")"
        #     elif isinstance(x, Literal):
        #         return repr(x.value)
        #     else:
        #         return repr(x)

        p = build(parse("x is integer or x == 5"), table)
        print(p)
        print(p.fcn.typeConstraints(SymbolTable({"x": Union(boolean, integer, string)}), p.args))

