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
import importlib
import sys

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.defs import *
from femtocode.typesystem import *
from femtocode.util import *

class CustomLibrary(Library):
    def __init__(self, *fcns):
        self.table = SymbolTable()   # the only Library with a per-instance table
        for fcn in fcns:
            self.add(fcn)

    def add(self, fcn):
        if isinstance(fcn, lispytree.BuiltinFunction):
            self.table[fcn.name] = fcn
        else:
            raise TypeError("CustomLibrary should contain only BuiltinFunctions.")

class CustomFlatFunction(statementlist.FlatFunction, lispytree.BuiltinFunction):
    def __init__(self, name, moduleName, callableName, typefcn, commutative=False, associative=False):
        self.name = name
        self.moduleName = moduleName
        self.callableName = callableName
        self.typefcn = typefcn
        self.commutative = commutative
        self.associative = associative

    def pythonast(self, args):
        return ast.Call(ast.Call(ast.Name("getattr", ast.Load()), [ast.Call(ast.Attribute(ast.Name("$importlib", ast.Load()), "import_module", ast.Load()), [ast.Str(self.moduleName)], [], None, None), ast.Str(self.callableName)], [], None, None), args, [], None, None)

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        try:
            out = self.typefcn(*[x.schema for x in typedargs])
        except Exception as err:
            return impossible("CustomFlatFunction.typefcn raised {0}: {1}".format(err.__class__.__name__, str(err))), typedargs, frame
        else:
            return out, typedargs, frame

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative):
        fcnname = newname()
        references[fcnname] = getattr(importlib.import_module(self.moduleName), self.callableName)
        return [Assign([target], Call(Name(fcnname, Load()), args, [], None, None))]
