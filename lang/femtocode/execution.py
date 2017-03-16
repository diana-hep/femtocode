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
import base64
import marshal
import sys
import types
import importlib
import traceback

from femtocode.asts import statementlist
from femtocode.dataset import ColumnName
from femtocode.dataset import sizeType
from femtocode.lib.standard import table
from femtocode.py23 import *
from femtocode.util import *
from femtocode.typesystem import *
from femtocode.workflow import Query

class Loop(Serializable):
    def __init__(self, size):
        self.size = size
        self.targets = []
        self.statements = []
        self.run = None

    def __repr__(self):
        return "<Loop over {0} at 0x{1:012x}>".format(str(self.size), id(self))

    def __str__(self):
        return "\n".join(["Loop over {0} params {1}".format(self.size, ", ".join(map(str, self.params())))] + ["    " + str(x) for x in self.statements])

    def toJson(self):
        return {"size": None if self.size is None else str(self.size),
                "targets": [str(x) for x in self.targets],
                "statements": [x.toJson() for x in self.statements],
                "run": None if self.run is None else self.run.toJson()}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()) == set(["size", "targets", "statements", "run"])
        assert obj["size"] is None or isinstance(obj["size"], string_types)
        assert isinstance(obj["targets"], list)
        assert all(isinstance(x, string_types) for x in obj["targets"])
        assert isinstance(obj["statements"], list)

        out = Loop(None if obj["size"] is None else ColumnName.parse(obj["size"]))
        out.targets = [ColumnName.parse(x) for x in obj["targets"]]
        out.statements = [statementlist.Statement.fromJson(x) for x in obj["statements"]]
        assert all(isinstance(x, statementlist.Call) for x in out.statements)
        out.run = None if obj["run"] is None else LoopFunction.fromJson(obj["run"])
        return out

    def newTarget(self, column):
        if column not in self.targets:
            self.targets.append(column)

    def newStatement(self, statement):
        if statement not in self.statements:
            self.statements.append(statement)

    def params(self):
        defines = set(x.column for x in self.statements)
        out = []
        for statement in self.statements:
            for arg in statement.args:
                if isinstance(arg, ColumnName) and arg not in defines and arg not in out:
                    out.append(arg)
        return out

    def __contains__(self, column):
        return any(x.column == column for x in self.statements)

class DependencyGraph(object):
    def __init__(self, target, query, lookup, required):
        self.target = target   # ColumnName, could be data or size
        self.query = query
        self.lookup = lookup
        self.lookup[self.target] = self
        self.required = required

        calls = filter(lambda x: isinstance(x, statementlist.Call) and x.column == target, self.query.statements)
        assert len(calls) == 1, "each new column must be defined exactly once"

        self.statement = calls[0]
        self.size = self.statement.tosize

        self.dependencies = []
        for c in self.statement.args:
            if isinstance(c, statementlist.Literal):
                pass

            elif isinstance(c, ColumnName):
                if c in self.query.dataset.columns:
                    self.required.add(c)

                elif c in self.lookup:
                    self.dependencies.append(self.lookup[c])

                else:
                    self.dependencies.append(DependencyGraph(c, self.query, self.lookup, self.required))

            else:
                assert False, "expected only Literals and ColumnNames in args, found {0}".format(c)

    def __repr__(self):
        return "<DependencyGraph of [{0}] at 0x{1:012x}>".format(", ".join(map(str, sorted(self.flattened()))), id(self))

    def pretty(self, indent=""):
        return "\n".join([indent + str(self.statement)] + [x.pretty(indent + "    ") for x in self.dependencies])

    def flattened(self):
        out = set([self.target])
        for x in self.dependencies:
            out.update(x.flattened())
        return out

    def overlap(self, other):
        return len(self.flattened().intersection(other.flattened())) > 0

    @staticmethod
    def wholedag(query):
        lookup = {}
        required = set()
        targetsToEndpoints = {}
        for action in query.actions:
            for target in action.columns():
                targetsToEndpoints[target] = DependencyGraph(target, query, lookup, required)
        return targetsToEndpoints, lookup, required

    @staticmethod
    def connectedSubgraphs(graphs):
        connectedSubgraphs = []
        for graph in graphs:
            found = False
            for previous in connectedSubgraphs:
                if any(graph.overlap(g) for g in previous):
                    previous.append(graph)
                    found = True
                    break
            if not found:
                connectedSubgraphs.append([graph])
        return connectedSubgraphs

    def _bucketfill(self, loop, endpoints, size):
        for dependency in self.dependencies:
            if dependency.size == size:
                if dependency.target not in loop:
                    dependency._bucketfill(loop, endpoints, size)
            else:
                endpoints.append(dependency)

        loop.newStatement(self.statement)

    @staticmethod
    def loops(graphs):
        loops = {}
        for startpoints in DependencyGraph.connectedSubgraphs(graphs):
            while len(startpoints) > 0:
                newloops = {}
                endpoints = []
                for graph in startpoints:
                    loop = newloops.get(graph.size, Loop(graph.size))
                    loop.newTarget(graph.target)
                    graph._bucketfill(loop, endpoints, graph.size)
                    newloops[graph.size] = loop

                for size, loop in newloops.items():
                    if size not in loops:
                        loops[size] = []
                    loops[size].append(loop)

                startpoints = []
                for x in endpoints:
                    if x not in startpoints:
                        startpoints.append(x)

        return loops

    @staticmethod
    def order(loops, actions, required):
        order = [x for x in actions if isinstance(x, statementlist.Aggregation)]
        targets = set(sum([x.columns() for x in actions], []))

        # FIXME: "Filter" type Actions should appear as far upstream in the order as possible

        while len(targets) > 0:
            for size in loops:
                for loop in loops[size]:
                    if loop not in order:
                        for target in loop.targets:
                            if target in targets:
                                order.insert(0, loop)  # put at beginning (working backward)
                                break

            targets = set(sum([loop.params() for loop in order if isinstance(loop, Loop)], []))
            for loop in order:
                for target in loop.targets:
                    targets.discard(target)
            for column in required:
                targets.discard(column)

        return order
        
class Compiler(object):
    @staticmethod
    def _fakeLineNumbers(node):
        if isinstance(node, ast.AST):
            node.lineno = 1
            node.col_offset = 0
            for field in node._fields:
                Compiler._fakeLineNumbers(getattr(node, field))

        elif isinstance(node, (list, tuple)):
            for x in node:
                Compiler._fakeLineNumbers(x)

    @staticmethod
    def _compileToPython(name, statements, params):
        if sys.version_info[0] <= 2:
            args = ast.arguments([ast.Name(n, ast.Param()) for n in params], None, None, [])
            fcn = ast.FunctionDef(name, args, statements, [])
        else:
            args = ast.arguments([ast.arg(n, None) for n in params], None, [], [], None, [])
            fcn = ast.FunctionDef(name, args, statements, [], None)

        moduleast = ast.Module([fcn])
        Compiler._fakeLineNumbers(moduleast)

        modulecomp = compile(moduleast, "Femtocode", "exec")
        out = {}
        exec(modulecomp, out)
        return LoopFunction(out[name])

    @staticmethod
    def compileToPython(fcnname, loop):
        validNames = {}
        def valid(n):
            if n not in validNames:
                validNames[n] = "v" + repr(len(validNames))
            return validNames[n]

        # i0 = 0; i0max = imax[0]
        imax = [loop.size]
        init = [ast.Assign([ast.Name("i0", ast.Store())], ast.Num(0)),
                ast.Assign([ast.Name("i0max", ast.Store())], ast.Subscript(ast.Name("imax", ast.Load()), ast.Index(ast.Num(0)), ast.Load()))]

        # while i0 < imax:
        whileloop = ast.While(ast.Compare(ast.Name("i0", ast.Load()), [ast.Lt()], [ast.Name("i0max", ast.Load())]), [], [])

        for statement in loop.statements:
            if isinstance(statement, statementlist.Explode):
                raise NotImplementedError

            elif isinstance(statement, statementlist.ExplodeSize):
                raise NotImplementedError

            elif isinstance(statement, statementlist.ExplodeData):
                raise NotImplementedError

            elif isinstance(statement, statementlist.Call):
                # f(x[i0], y[i0], 3.14, ...)
                astargs = []
                for arg in statement.args:
                    if isinstance(arg, ColumnName) and (arg in loop.targets or arg in loop.params()):
                        astargs.append(ast.Subscript(ast.Name(valid(arg), ast.Load()), ast.Index(ast.Name("i0", ast.Load())), ast.Load()))
                    elif isinstance(arg, ColumnName):
                        astargs.append(ast.Name(valid(arg), ast.Load()))
                    else:
                        astargs.append(arg.buildexec())

                expr = table[statement.fcnname].buildexec(astargs)

            else:
                assert False, "unrecognized statement: {0}".format(statement)

            if statement.column in loop.targets:
                # col[i0] = f...
                assignment = ast.Assign([ast.Subscript(ast.Name(valid(statement.column), ast.Load()), ast.Index(ast.Name("i0", ast.Load())), ast.Store())], expr)
            else:
                # col = f...
                assignment = ast.Assign([ast.Name(valid(statement.column), ast.Store())], expr)

            whileloop.body.append(assignment)

        # i0 += 1
        whileloop.body.append(ast.AugAssign(ast.Name("i0", ast.Store()), ast.Add(), ast.Num(1)))

        fcn = Compiler._compileToPython(fcnname, init + [whileloop], ["imax"] + [valid(x) for x in loop.params() + loop.targets])
        return fcn, imax

class LoopFunction(Serializable):
    def __init__(self, fcn):
        self.fcn = fcn

    def __call__(self, *args, **kwds):
        return self.fcn(*args, **kwds)

    def __getstate__(self):
        return self.fcn.func_name, marshal.dumps(self.fcn.func_code)

    def __setstate__(self, state):
        self.fcn = types.FunctionType(marshal.loads(state[1]), {}, state[0])

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "name": self.fcn.func_name,
                "code": base64.b64encode(marshal.dumps(self.fcn.func_code))}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()) == set(["class", "name", "code"])
        assert isinstance(obj["class"], string_types)
        assert "." in obj["class"]

        mod = obj["class"][:obj["class"].rindex(".")]
        cls = obj["class"][obj["class"].rindex(".") + 1:]

        if mod == LoopFunction.__module__ and cls == LoopFunction.__name__:
            assert isinstance(obj["name"], string_types)
            assert isinstance(obj["code"], string_types)
            return LoopFunction(types.FunctionType(marshal.loads(base64.b64decode(obj["code"])), {}, obj["name"]))
        else:
            return getattr(importlib.import_module(mod), cls).fromJson(obj)

class ExecutionFailure(Serializable):
    def __init__(self, exception, traceback):
        self.exception = exception
        self.traceback = traceback

    def __repr__(self):
        return "<ExecutionFailure: {0}>".format(str(self.exception))

    def __str__(self):
        if self.traceback is None:
            return repr(self)
        elif isinstance(self.traceback, string_types):
            return self.traceback
        else:
            return "".join(traceback.format_exception(self.exception.__class__, self.exception, self.traceback))

    def reraise(self):
        if isinstance(self.exception, string_types):
            raise StopIteration(self.exception)

        elif isinstance(self.traceback, string_types):
            raise RuntimeError("Remote exception: {0}\n\n{1}".format(str(self.exception), self.traceback))

        else:
            if sys.version_info[0] <= 2:
                raise self.exception.__class__, self.exception, self.traceback
            else:
                raise self.exception.with_traceback(self.traceback)

    def toJson(self):
        if self.traceback is None:
            traceback = None
        elif isinstance(self.traceback, string_types):
            traceback = self.traceback
        else:
            traceback = str(self.traceback)

        return {"class": self.exception.__class__.__name__,
                "message": str(self.exception),
                "traceback": traceback}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert "class" in obj
        assert "message" in obj
        assert "traceback" in obj
        return ExecutionFailure("{0}: {1}".format(obj["class"], obj["message"], obj["traceback"]))

    @staticmethod
    def failureJson(obj):
        return isinstance(obj, dict) and set(obj.keys()) == set(["class", "message", "traceback"])

class Executor(Serializable):
    def __init__(self, query):
        self.query = query
        targetsToEndpoints, lookup, self.required = DependencyGraph.wholedag(self.query)
        self.temporaries = sorted((target, graph.size) for target, graph in targetsToEndpoints.items() if not target.issize())

        loops = DependencyGraph.loops(targetsToEndpoints.values())
        self.order = DependencyGraph.order(loops, self.query.actions, self.required)
        self.compileLoops()

    def _copy(self):
        # reference that which is read-only, but actually copy what is mutable
        out = Executor.__new__(Executor)
        out.query = self.query._copy()
        out.required = self.required
        out.temporaries = self.temporaries
        out.order = self.order
        return out

    def toJson(self):
        return {"query": self.query.toJson(),
                "required": [str(x) for x in self.required],
                "temporaries": [(str(data), None if size is None else str(size)) for data, size in self.temporaries],
                "order": [{"loop": x.toJson()} if isinstance(x, Loop) else {"action": x.toJson()} for x in self.order]}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(["query", "required", "temporaries", "order"]).difference(set(obj.keys())) == set()
        assert isinstance(obj["required"], list)
        assert all(isinstance(x, string_types) for x in obj["required"])
        assert isinstance(obj["temporaries"], list)
        assert all(isinstance(k, string_types) and (v is None or isinstance(v, string_types)) for k, v in obj["temporaries"])
        assert isinstance(obj["order"], list)
        assert all(isinstance(x, dict) and len(x) == 1 and isinstance(x.keys()[0], string_types) for x in obj["order"])

        out = Executor.__new__(Executor)
        out.query = Query.fromJson(obj["query"])
        out.required = [ColumnName.parse(x) for x in obj["required"]]
        out.temporaries = [(ColumnName.parse(k), None if v is None else ColumnName.parse(v)) for k, v in obj["temporaries"]]
        out.order = [Loop.fromJson(x.values()[0]) if x.keys()[0] == "loop" else statementlist.Statement.fromJson(x.values()[0]) for x in obj["order"]]
        return out

    def compileLoops(self):
        for i, loop in enumerate(self.order):
            if isinstance(loop, Loop):
                fcnname = "f{0}_{1}".format(self.query.id, i)
                loop.run, loop.imax = Compiler.compileToPython(fcnname, loop)

    def inarraysFromTest(self, group):
        out = {}
        for column in self.required:
            if column.issize():
                out[column] = group.segments[column.dropsize()].size
            else:
                out[column] = group.segments[column].data
        return out

    def sizearrays(self, group, inarrays):
        return {}   # FIXME

    def length(self, column, size, group, sizearrays):
        if column.issize():
            raise NotImplementedError   # whatever its implementation, it can't use sizearrays

        elif size is None:
            return group.numEntries

        elif not size.istmp():
            return group.segments[size.dropsize()].dataLength

        else:
            raise NotImplementedError

    def workarrays(self, group, lengths):
        return dict((data, [None] * lengths[data]) for data, size in self.temporaries)

    def imax(self, imax):
        return imax

    def runloops(self, group, lengths, arrays):
        out = None
        for loopOrAction in self.order:
            if isinstance(loopOrAction, Loop):
                loop = loopOrAction
                imax = self.imax([group.numEntries if loop.size is None else lengths[loop.size]])
                args = [arrays[x] for x in loop.params() + loop.targets]
                loop.run(*([imax] + args))

            else:
                action = loopOrAction
                out = action.act(group, lengths, arrays)

        return out

    def run(self, inarrays, group):
        lengths = {}
        for data, size in self.temporaries:
            if size is not None:
                lengths[size] = self.length(size, None, group, None)

        sizearrays = self.sizearrays(group, inarrays)

        for data, size in self.temporaries:
            lengths[data] = self.length(data, size, group, sizearrays)

        workarrays = self.workarrays(group, lengths)

        arrays = {}
        arrays.update(inarrays)
        arrays.update(sizearrays)
        arrays.update(workarrays)

        return self.runloops(group, lengths, arrays)
