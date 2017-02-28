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
from femtocode.dataset import ColumnName
from femtocode.lib.standard import table
from femtocode.py23 import *
from femtocode.typesystem import *

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


statements = statementlist.Statement.fromJson([
    {"to": "#0", "fcn": "+", "args": ["a", "b"]},
    {"to": "#1", "fcn": "+", "args": ["c", "d"]},
    {"to": "#2", "fcn": "+", "args": ["e", "f"]},
    {"to": "#3", "fcn": "-", "args": ["#0", "#1"]},
    {"to": "#4", "fcn": "+", "args": ["#1", "#2"]},
    {"to": "#5", "fcn": "+", "args": ["#3", "#2"]},
    {"to": "#6", "fcn": "-", "args": ["#1", "#3"]},
    {"to": "#7", "fcn": "-", "args": ["#5", "#6"]},
    {"to": "#8", "fcn": "+", "args": ["#7", "#5"]},
    {"to": "#9", "fcn": "+", "args": ["#8", "#4"]},
    ])

class Kernel(object):
    def __init__(self, statements):
        self.name = statements[-1].column
        self.statements = statements
        self.inputs = sorted(set(sum([statement.args for statement in self.statements], ())).difference([statement.column for statement in self.statements]))

    def __repr__(self):
        return "<Kernel {0}({1}) at {2:012x}>".format(self.name, ", ".join(map(str, self.inputs)), id(self))

    def __str__(self):
        return "\n".join(["Kernel {0}({1})".format(self.name, ", ".join(map(str, self.inputs)))] + ["    " + str(x) for x in self.statements])

class DependencyGraph(object):
    def __init__(self, column, statements, inputs, lookup=None):
        if not isinstance(column, ColumnName):
            column = ColumnName.parse(column)
        self.column = column
        self.inputs = [x if isinstance(x, ColumnName) else ColumnName.parse(x) for x in inputs]
        if lookup is None:
            lookup = {}
        self.lookup = lookup

        m = filter(lambda x: x.column == column, statements)
        assert len(m) == 1, "each new column must be defined exactly once"

        self.statement = m[0]
        self.lookup[self.column] = self

        self.dependencies = []
        for c in self.statement.args:
            if c in self.lookup:
                self.dependencies.append(self.lookup[c])
            elif c not in inputs:
                self.dependencies.append(DependencyGraph(c, statements, inputs, self.lookup))

    def __repr__(self):
        return "<DependencyGraph {0} at {1:012x}>".format(self.column, id(self))

    def pretty(self, indent=""):
        return "\n".join([indent + str(self.statement)] + [x.pretty(indent + "    ") for x in self.dependencies])

    def linearize(self, stopat, memo):
        out = []
        memo.add(self.column)
        for node in self.dependencies:
            if node.column not in memo and not stopat(node):
                out.extend(node.linearize(stopat, memo))

        out.append(self.statement)
        return out

    def kernels(self, stopat, memo):
        out = [Kernel(self.linearize(stopat, set()))]
        memo.add(out[0].name)
        for column in out[0].inputs:
            if column not in self.inputs and column not in memo:
                out.extend(self.lookup[column].kernels(stopat, memo))
        return out

d = DependencyGraph("#9", statements, ["a", "b", "c", "d", "e", "f"])
print d.pretty()

print Kernel(d.linearize(lambda node: node.statement.fcnname == "-", set()))

print "\n".join(map(str, d.kernels(lambda node: node.statement.fcnname == "-", set())))
