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

from femtocode.asts.typingtree import *
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
        p = build(parse("x"), table.fork({"x": Ref("x")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("x"): integer})))

        p = build(parse("x + 3"), table.fork({"x": Ref("x")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("x"): integer})))

        p = build(parse("y = x + 3; y + 1"), table.fork({"x": Ref("x")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("x"): integer})))

        p = build(parse("{x => x + 3}"), table.fork({"x": Ref("x")}))
        print(p)

        p = build(parse("def f(x): x + 3.14;\nf"), table)
        print(p)

        p = build(parse("def f(q): q + 3;  f(x)"), table.fork({"x": Ref("x")}))
        print(p)

        p = build(parse("xs.map({x => 3.14 + x})"), table.fork({"xs": Ref("xs")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("xs"): collection(integer)})))

        p = build(parse("xs.map(x => 3.14 + x)"), table.fork({"xs": Ref("xs")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("xs"): collection(integer)})))

        p = build(parse("xs.map(3.14 + $1)"), table.fork({"xs": Ref("xs")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("xs"): collection(integer)})))

        p = build(parse("xs.map(fcn = {x => 3.14 + x})"), table.fork({"xs": Ref("xs")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("xs"): collection(integer)})))

        try:
            build(parse("xs.map(wonky = {x => 3.14 + x}, fcn = {x => 3.14 + x})"), table.fork({"xs": Ref("xs")}))
        except FemtocodeError as err:
            print(err)

        try:
            build(parse("xs.map()"), table.fork({"xs": Ref("xs")}))
        except FemtocodeError as err:
            print(err)
        
        try:
            build(parse("xs.map({x => 3.14 + x}, {x => 3.14 + x})"), table.fork({"xs": Ref("xs")}))
        except FemtocodeError as err:
            print(err)

        p = build(parse("xs.map(3.14)"), table.fork({"xs": Ref("xs")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("xs"): collection(integer)})))

        p = build(parse("y = x + 3; y"), table.fork({"x": Ref("x")}))
        print(p)
        print(p.retschema(SymbolTable({Ref("x"): integer, Call(table["+"], [Literal(3), Ref("x")]): real})))

        print(build(parse("def f(x): {y => x + y}; f"), table))

        print(build(parse("def f(x): {y => x + y}; f(3)"), table))

        print(build(parse("def f(x, z=99): {y => x + y + z}; f(3)"), table))

        print(build(parse("y == 2"), table.fork({"y": Ref("y")})))

        print(build(parse("def f(x): x + 0.1; y == f(2)"), table.fork({"y": Ref("y")})))
