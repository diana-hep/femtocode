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
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.defs import SymbolTable
from femtocode.inference import *
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.py23 import *
from femtocode.typesystem import *

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

    # def test_simple2(self):
    #     columns = {}
    #     columns.update(statementlist.schemaToColumns("x", real))
    #     columns.update(statementlist.schemaToColumns("y", real))
    #     columns.update(statementlist.schemaToColumns("z", real))
    #     columns.update(statementlist.schemaToColumns("xs", collection(real)))

    #     lt = lispytree.build(parse("xs.map($1 + x).map($1 + y).map($1 + z)"), table.fork(dict((v, lispytree.Ref(v)) for v in ("x", "y", "z", "xs"))))[0]
    #     tt = typedtree.build(lt, SymbolTable(dict([(lispytree.Ref(v), real) for v in ("x", "y", "z")] + [(lispytree.Ref("xs"), collection(real))])))[0]
    #     result, ss, _ = statementlist.build(tt, columns)

    #     print("")
    #     for statement in ss:
    #         print(statement)
    #     print("-> " + str(result))

    #     lt = lispytree.build(parse("a = x + y; b = a + y + z; xs.map(x => x + a + a + b).map(y => y + 2)"), table.fork(dict((v, lispytree.Ref(v)) for v in ("x", "y", "z", "xs"))))[0]
    #     tt = typedtree.build(lt, SymbolTable(dict([(lispytree.Ref(v), real) for v in ("x", "y", "z")] + [(lispytree.Ref("xs"), collection(real))])))[0]
    #     result, ss, _ = statementlist.build(tt, columns)

    #     print("")
    #     for statement in ss:
    #         print(statement)
    #     print("-> " + str(result))

    #     columns = {}
    #     columns.update(statementlist.schemaToColumns("xss", collection(collection(real))))
    #     columns.update(statementlist.schemaToColumns("ys", collection(real)))

    #     lt = lispytree.build(parse("xss.map(xs => ys.map(y => xs.map(x => x + y)))"), table.fork(dict((v, lispytree.Ref(v)) for v in ("xss", "ys"))))[0]
    #     tt = typedtree.build(lt, SymbolTable({lispytree.Ref("xss"): collection(collection(real)), lispytree.Ref("ys"): collection(real)}))[0]
    #     result, ss, _ = statementlist.build(tt, columns)

    #     print("")
    #     for statement in ss:
    #         print(statement)
    #     print("-> " + str(result))
