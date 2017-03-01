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

class Kernel(object):
    def __init__(self, statements):
        self.name = statements[-1].column
        self.statements = statements
        self.inputs = sorted(set(sum([statement.args for statement in self.statements], ())).difference([statement.column for statement in self.statements]))

        goalStatement = filter(lambda x: x.column == self.name, self.statements)[0]
        if isinstance(goalStatement, Call):
            self.sizeColumn = goalStatement.size
            self.schema = goalStatement.schema
        else:
            raise NotImplementedError

    def __repr__(self):
        return "<Kernel {0}({1}) at {2:012x}>".format(self.name, ", ".join(map(str, self.inputs)), id(self))

    def __str__(self):
        return "\n".join(["Kernel {0}({1})".format(self.name, ", ".join(map(str, self.inputs)))] + ["    " + str(x) for x in self.statements])

class DependencyGraph(object):
    def __init__(self, goal, statements, inputs, lookup=None):
        if not isinstance(goal, ColumnName):
            goal = ColumnName.parse(goal)
        self.goal = goal
        self.inputs = [x if isinstance(x, ColumnName) else ColumnName.parse(x) for x in inputs]
        if lookup is None:
            lookup = {}
        self.lookup = lookup

        m = filter(lambda x: x.column == goal, statements)
        assert len(m) == 1, "each new column must be defined exactly once"

        self.statement = m[0]
        self.lookup[self.goal] = self

        self.dependencies = []
        for c in self.statement.args:
            if c in self.lookup:
                self.dependencies.append(self.lookup[c])
            elif c not in inputs:
                self.dependencies.append(DependencyGraph(c, statements, inputs, self.lookup))

    def __repr__(self):
        return "<DependencyGraph {0} at {1:012x}>".format(self.goal, id(self))

    def pretty(self, indent=""):
        return "\n".join([indent + str(self.statement)] + [x.pretty(indent + "    ") for x in self.dependencies])

    def linearize(self, divider, memo=None):
        if memo is None:
            memo = set()

        out = []
        memo.add(self.goal)
        for node in self.dependencies:
            if node.goal not in memo and not divider(self, node):
                out.extend(node.linearize(divider, memo))

        out.append(self.statement)
        return out

    def kernels(self, divider, memo=None):
        if memo is None:
            memo = set()

        out = [Kernel(self.linearize(divider, set()))]
        memo.add(out[0].name)
        for column in out[0].inputs:
            if column not in self.inputs and column not in memo:
                out.extend(self.lookup[column].kernels(divider, memo))
        return out

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
    
def kernelToFunction(kernel):
    validNames = {}
    def valid(n):
        if n not in validNames:
            validNames[n] = "v" + repr(len(validNames))
        return validNames[n]

    init = ast.Assign([ast.Name("i0", ast.Store())], ast.Num(0))

    loop = ast.While(ast.Compare(ast.Name("i0", ast.Load()), [ast.Lt()], [ast.Name("imax", ast.Load())]), [], [])

    for statement in kernel.statements:
        if statement.__class__ == statementlist.Call:
            args = [ast.Subscript(ast.Name(valid(x), ast.Load()), ast.Index(ast.Name("i0", ast.Load())), ast.Load()) for x in statement.args]
            expr = table[statement.fcnname].buildexec(args)

        else:
            expr = statement.buildexec(statement.args)

        loop.body.append(ast.Assign([ast.Name(valid(statement.column), ast.Store())], expr))

    loop.body.append(ast.Assign([ast.Subscript(ast.Name("out", ast.Load()), ast.Index(ast.Name("i0", ast.Load())), ast.Store())], ast.Name(valid(kernel.name), ast.Load())))

    loop.body.append(ast.AugAssign(ast.Name("i0", ast.Store()), ast.Add(), ast.Num(1)))

    out = makeFunction(str(kernel.name), [init, loop], [valid(x) for x in kernel.inputs] + ["out", "i0max"])
    out.kernel = kernel
    return out

class ExecutionPlan(object):
    def __init__(self, dependencyGraph, divider):
        self.dependencyGraph = dependencyGraph

        self.kernels = dependencyGraph.kernels(divider)
        self.functions = map(kernelToFunction, self.kernels)
        self.functionLookup = dict((x.kernel.name, x) for x in self.functions)

        self.tmps = []
        self.sizes = []
        self.order = []
        done = set()
        def fill(function):
            for param in function.kernel.inputs:
                if param not in self.dependencyGraph.inputs and param not in done:
                    fill(self.functionLookup[param])
            self.order.append(function)
            self.tmps.append(function.kernel.name)
            self.sizes.append(function.kernel.sizeColumn)
            done.add(function.kernel.name)

        fill(self.functionLookup[self.dependencyGraph.goal])

    # def run(self, arrays, dataset):
    #     tmparrays = {}
    #     for tmp in self.tmps:
    #         if tmp.issize():
    #             tmparrays[tmp] = [None] * numEntries
    #         else:
    #             dataset.sizeColumn()


    #             # tmparrays[tmp] = [None] * dataLengths[tmp]
                
