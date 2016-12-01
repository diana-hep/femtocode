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

import femtocode.asts.lispytree as lispytree
import femtocode.asts.typedtree as typedtree
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
        p = lispytree.build(parse("x"), table.fork({"x": lispytree.Ref("x")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer}))[0].schema)

        p = lispytree.build(parse("x + 3"), table.fork({"x": lispytree.Ref("x")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer}))[0].schema)

        p = lispytree.build(parse("y = x + 3; y + 1"), table.fork({"x": lispytree.Ref("x")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer}))[0].schema)

        p = lispytree.build(parse("{x => x + 3}"), table.fork({"x": lispytree.Ref("x")}))
        print(p)

        p = lispytree.build(parse("def f(x): x + 3.14;\nf"), table)
        print(p)

        p = lispytree.build(parse("def f(q): q + 3;  f(x)"), table.fork({"x": lispytree.Ref("x")}))
        print(p)

        p = lispytree.build(parse("xs.map({x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("xs.map(x => 3.14 + x)"), table.fork({"xs": lispytree.Ref("xs")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("xs.map(3.14 + $1)"), table.fork({"xs": lispytree.Ref("xs")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("xs.map(fcn = {x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        try:
            lispytree.build(parse("xs.map(wonky = {x => 3.14 + x}, fcn = {x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))
        except FemtocodeError as err:
            print(err)

        try:
            lispytree.build(parse("xs.map()"), table.fork({"xs": lispytree.Ref("xs")}))
        except FemtocodeError as err:
            print(err)
        
        try:
            lispytree.build(parse("xs.map({x => 3.14 + x}, {x => 3.14 + x})"), table.fork({"xs": lispytree.Ref("xs")}))
        except FemtocodeError as err:
            print(err)

        p = lispytree.build(parse("xs.map(3.14)"), table.fork({"xs": lispytree.Ref("xs")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("xs"): collection(integer)}))[0].schema)

        p = lispytree.build(parse("y = x + 3; y"), table.fork({"x": lispytree.Ref("x")}))
        print(p)
        print(typedtree.build(p, SymbolTable({lispytree.Ref("x"): integer, lispytree.Call(table["+"], [lispytree.Literal(3), lispytree.Ref("x")]): real}))[0].schema)

        print(lispytree.build(parse("def f(x): {y => x + y}; f"), table))

        print(lispytree.build(parse("def f(x): {y => x + y}; f(3)"), table))

        print(lispytree.build(parse("def f(x, z=99): {y => x + y + z}; f(3)"), table))

        print(lispytree.build(parse("y == 2"), table.fork({"y": lispytree.Ref("y")})))

        print(lispytree.build(parse("def f(x): x + 0.1; y == f(2)"), table.fork({"y": lispytree.Ref("y")})))

        try:
            lispytree.build(parse("def f(x): x; g(2)"), table)
        except FemtocodeError as err:
            print(err)

        try:
            lispytree.build(parse("g = 8; g(2)"), table)
        except FemtocodeError as err:
            print(err)

    def test_simple2(self):
        lt = lispytree.build(parse("a = x + y; b = a + y + z; c = xs.map(x => x + x + a + a + b).map(y => y + 2); c"), table.fork(dict((v, lispytree.Ref(v)) for v in ("x", "y", "z", "xs"))))
        tt = typedtree.build(lt, SymbolTable(dict([(lispytree.Ref(v), real) for v in ("x", "y", "z")] + [(lispytree.Ref("xs"), collection(real))])))[0]

        def walk(tree, indent=""):
            if isinstance(tree, typedtree.Ref):
                print("{0}Ref@{1} {2} {3} {4}".format(indent, id(tree), tree.name, tree.framenumber, tree.schema))

            elif isinstance(tree, typedtree.Literal):
                print("{0}Literal@{1} {2} {3}".format(indent, id(tree), tree.value, tree.schema))

            elif isinstance(tree, typedtree.Call):
                print("{0}Call@{1} {2} {3}".format(indent, id(tree), tree.fcn, tree.schema))
                for arg in tree.args:
                    walk(arg, indent + "    ")

            elif isinstance(tree, typedtree.UserFunction):
                print("{0}UserFunction@{1} {2} {3}".format(indent, id(tree), tree.refs, tree.schema))
                walk(tree.body, indent + "    ")

            else:
                print("WTF {0} {1}".format(type(tree), tree))

        print("")
        walk(tt)

        print("")
        uniques = {}
        typedtree.fillUniquesSet(tt, uniques)
        ttunique = typedtree.treeOfUniques(tt, uniques)
        walk(ttunique)

        def walk2(tree, indent=""):
            if isinstance(tree, typedtree.Ref):
                print("{0}Ref {1} {2} {3}".format(indent, tree.name, tree.framenumber, tree.dependencies))

            elif isinstance(tree, typedtree.Literal):
                print("{0}Literal {1} {2}".format(indent, tree.value, tree.dependencies))

            elif isinstance(tree, typedtree.Call):
                print("{0}Call {1} {2}".format(indent, tree.fcn.name, tree.dependencies))
                for arg in tree.args:
                    walk2(arg, indent + "    ")

            elif isinstance(tree, typedtree.UserFunction):
                print("{0}UserFunction {1}".format(indent, tree.refs))
                walk2(tree.body, indent + "    ")

            else:
                print("WTF {0} {1}".format(type(tree), tree))
        
        print("")
        typedtree.assignDependencies(ttunique)
        walk2(ttunique)
