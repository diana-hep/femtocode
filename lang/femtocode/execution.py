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

class Loop(object):
    def __init__(self, statements):
        self.name = statements[-1].column
        self.statements = statements
        self.inputs = sorted(set(sum([statement.args for statement in self.statements], ())).difference([statement.column for statement in self.statements]))

        goalStatement = filter(lambda x: x.column == self.name, self.statements)[0]
        if isinstance(goalStatement, statementlist.Call):
            self.sizeColumn = goalStatement.size
            self.schema = goalStatement.schema
        else:
            raise NotImplementedError

    def __repr__(self):
        return "<Loop {0}({1}) at {2:012x}>".format(self.name, ", ".join(map(str, self.inputs)), id(self))

    def __str__(self):
        return "\n".join(["Loop {0}({1})".format(self.name, ", ".join(map(str, self.inputs)))] + ["    " + str(x) for x in self.statements])

# FIXME: temporary size arrays have to be calculated outside of DependencyGraph, before all other arrays

class DependencyGraph(object):
    def __init__(self, goal, statements, inputs, lookup=None):
        self.goal = goal
        self.inputs = inputs
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

    def loops(self, divider, memo=None):
        if memo is None:
            memo = set()

        out = [Loop(self.linearize(divider, set()))]
        memo.add(out[0].name)
        for column in out[0].inputs:
            if column not in self.inputs and column not in memo:
                out.extend(self.lookup[column].loops(divider, memo))
        return out

class PythonCompiler(object):
    @staticmethod
    def _fakeLineNumbers(node):
        if isinstance(node, ast.AST):
            node.lineno = 1
            node.col_offset = 0
            for field in node._fields:
                PythonCompiler._fakeLineNumbers(getattr(node, field))

        elif isinstance(node, (list, tuple)):
            for x in node:
                PythonCompiler._fakeLineNumbers(x)

    @staticmethod
    def _compilePython(name, statements, params):
        if sys.version_info[0] <= 2:
            args = ast.arguments([ast.Name(n, ast.Param()) for n in params], None, None, [])
            fcn = ast.FunctionDef(name, args, statements, [])
        else:
            args = ast.arguments([ast.arg(n, None) for n in params], None, [], [], None, [])
            fcn = ast.FunctionDef(name, args, statements, [], None)

        moduleast = ast.Module([fcn])
        PythonCompiler._fakeLineNumbers(moduleast)

        modulecomp = compile(moduleast, "Femtocode", "exec")
        out = {}
        exec(modulecomp, out)
        return out[name]

    @staticmethod
    def compilePython(loop):
        validNames = {}
        def valid(n):
            if n not in validNames:
                validNames[n] = "v" + repr(len(validNames))
            return validNames[n]

        init = ast.Assign([ast.Name("i0", ast.Store())], ast.Num(0))

        whileloop = ast.While(ast.Compare(ast.Name("i0", ast.Load()), [ast.Lt()], [ast.Name("i0max", ast.Load())]), [], [])

        for statement in loop.statements:
            if statement.__class__ == statementlist.Call:
                args = [ast.Subscript(ast.Name(valid(x), ast.Load()), ast.Index(ast.Name("i0", ast.Load())), ast.Load()) for x in statement.args]
                expr = table[statement.fcnname].buildexec(args)

            else:
                expr = statement.buildexec(statement.args)

            whileloop.body.append(ast.Assign([ast.Name(valid(statement.column), ast.Store())], expr))

        whileloop.body.append(ast.Assign([ast.Subscript(ast.Name("out", ast.Load()), ast.Index(ast.Name("i0", ast.Load())), ast.Store())], ast.Name(valid(loop.name), ast.Load())))

        whileloop.body.append(ast.AugAssign(ast.Name("i0", ast.Store()), ast.Add(), ast.Num(1)))

        return PythonCompiler._compilePython(str(loop.name), [init, whileloop], [valid(x) for x in loop.inputs] + ["out", "i0max"])

class PythonExecutor(object):
    def __init__(self, goal, inputs, statements, divider):
        self.goal = goal
        self.inputs = [x if isinstance(x, ColumnName) else ColumnName.parse(x) for x in inputs]

        self.dataDependencies = DependencyGraph(self.goal.data, statements, self.inputs)

        self.loops = self.dataDependencies.loops(divider)
        self.lookup = dict((x.name, x) for x in self.loops)

        self.order = []
        done = set()
        def fill(loop):
            for param in loop.inputs:
                if param not in self.dataDependencies.inputs and param not in done:
                    fill(self.lookup[param])
            self.order.append(loop)
            done.add(loop.name)

        fill(self.lookup[self.dataDependencies.goal])

        self._compileLoops()

    def _compileLoops(self):
        for loop in self.order:
            loop.pyfcn = PythonCompiler.compilePython(loop)

    def _runloop(self, loop, args):
        loop.pyfcn(*args)

    def dataLengths(self, dataset, group):
        out = {}
        for loop in self.order:
            tmp = loop.name
            size = loop.sizeColumn
            assert not tmp.issize()   # REMEMBER!
            assert size is None or size.issize()

            if size is None:
                dataLength = group.numEntries
            elif not size.istmp():
                dataLength = group.segments[size.dropsize()].dataLength
            else:
                raise NotImplementedError   # FIXME; you'll run a counter over it, knowing its depth

            out[tmp] = dataLength

        return out

    def run(self, arrays, dataLengths):   # input arrays includes temporary size arrays
        arrays.update(dict((loop.name, [None] * dataLengths[loop.name]) for loop in self.order))
        for loop in self.order:
            inargs = [arrays[name] for name in loop.inputs]
            outarg = arrays[loop.name]
            i0max = dataLengths[loop.name]    # FIXME: wrong! for functions that end in a reduce
            self._runloop(loop, (inargs + [outarg, i0max]))

        lastsize = self.order[-1].sizeColumn
        if lastsize is not None:
            lastsize = arrays[lastsizename]

        return outarg, lastsize
