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
import sys

from femtocode.asts import statementlist
from femtocode.typesystem import *
from femtocode.lib.standard import table

#### temporarily load numba for testing

import numba

def fakeLineNumbers(node):
    if isinstance(node, ast.AST):
        node.lineno = 1
        node.col_offset = 0
        for field in node._fields:
            fakeLineNumbers(getattr(node, field))

    elif isinstance(node, (list, tuple)):
        for x in node:
            fakeLineNumbers(x)

def makeFunction(name, statements, params):
    if sys.version_info[0] <= 2:
        args = ast.arguments([ast.Name(n, ast.Param()) for n in params], None, None, [])
        fcn = ast.FunctionDef(name, args, statements, [])
    else:
        args = ast.arguments([ast.arg(n, None) for n in params], None, [], [], None, [])
        fcn = ast.FunctionDef(name, args, statements, [], None)

    moduleast = ast.Module([fcn])
    fakeLineNumbers(moduleast)

    modulecomp = compile(moduleast, "Femtocode", "exec")
    out = {}
    exec(modulecomp, out)
    return out[name]





statements = statementlist.Statement.fromJson([
    {"to": "#0", "fcn": "+", "args": ["x", "y"]},
    {"to": "#1", "fcn": "-", "args": ["#0", "z"]}
    ])
result = statementlist.Statement.fromJson({"name": "#1", "schema": "real", "data": "#1", "size": None})


