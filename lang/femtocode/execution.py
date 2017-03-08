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
from femtocode.dataset import sizeType
from femtocode.lib.standard import table
from femtocode.py23 import *
from femtocode.typesystem import *

class Loop(object):
    def __init__(self, size):
        self.size = size
        self.targets = []
        self.statements = []

    def __repr__(self):
        return "<Loop over {0} at 0x{1:012x}>".format(str(self.size), id(self))

    def __str__(self):
        return "\n".join(["Loop over {0} params {1}".format(self.size, ", ".join(map(str, self.params())))] + ["    " + str(x) for x in self.statements])

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
        return out[name]

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
    
class Executor(object):
    def __init__(self, query):
        self.query = query
        self.targetsToEndpoints, self.lookup, self.required = DependencyGraph.wholedag(self.query)

        self.loops = DependencyGraph.loops(self.targetsToEndpoints.values())
        self.order = DependencyGraph.order(self.loops, self.query.actions, self.required)
        self.compileLoops()

    def compileLoops(self):
        for i, loops in enumerate(self.loops.values()):
            for j, loop in enumerate(loops):
                fcnname = "f{0}_{1}_{2}".format(self.query.id, i, j)
                loop.pythonfcn, loop.imax = Compiler.compileToPython(fcnname, loop)

    def runloop(self, loop, args):
        loop.pythonfcn(*args)

    def initialize(self):
        action = self.query.actions[-1]   # the tally is only affected by the last action
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"
        return action.initialize()

    def finalize(self, tally):
        action = self.query.actions[-1]   # the tally is only affected by the last action
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"
        return action.finalize(tally)

    def update(self, tally, subtally):
        action = self.query.actions[-1]   # the tally is only affected by the last action
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"
        return action.update(tally, subtally)
        
    def inarrays(self, group):
        out = {}
        for column in self.required:
            if column.issize():
                out[column] = group.segments[column.dropsize()].size
            else:
                out[column] = group.segments[column].data
        return out

    def temporaries(self):
        return [(target, graph.size) for target, graph in self.targetsToEndpoints.items() if not target.issize()]

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
        return dict((data, [None] * lengths[data]) for data, size in self.temporaries())

    def runloops(self, group, lengths, arrays):
        out = None
        for loopOrAction in self.order:
            if isinstance(loopOrAction, Loop):
                loop = loopOrAction
                imax = [group.numEntries if loop.size is None else lengths[loop.size]]
                args = [arrays[x] for x in loop.params() + loop.targets]
                self.runloop(loop, [imax] + args)

            else:
                action = loopOrAction
                out = action.act(group, lengths, arrays)

        return out

    def run(self, group, tally):
        inarrays = self.inarrays(group)

        lengths = {}
        for data, size in self.temporaries():
            if size is not None:
                lengths[size] = self.length(size, None, group, None)

        sizearrays = self.sizearrays(group, inarrays)

        for data, size in self.temporaries():
            lengths[data] = self.length(data, size, group, sizearrays)

        workarrays = self.workarrays(group, lengths)

        arrays = {}
        arrays.update(inarrays)
        arrays.update(sizearrays)
        arrays.update(workarrays)

        subtally = self.runloops(group, lengths, arrays)
        return self.update(tally, subtally)





#####################################################################
## Test them here (to avoid stale bytecode during development)

import ctypes

import llvmlite.binding
import numba
import numpy

class PyTypeObject(ctypes.Structure):
    _fields_ = ("ob_refcnt", ctypes.c_int), ("ob_type", ctypes.c_void_p), ("ob_size", ctypes.c_int), ("tp_name", ctypes.c_char_p)

class PyObject(ctypes.Structure):
    _fields_ = ("ob_refcnt", ctypes.c_int), ("ob_type", ctypes.POINTER(PyTypeObject))

PyObjectPtr = ctypes.POINTER(PyObject)

llvmlite.binding.initialize()
llvmlite.binding.initialize_native_target()
llvmlite.binding.initialize_native_asmprinter()

class NativeCompiler(Compiler):
    @staticmethod
    def compileToNative(fcnname, loop, columns):
        pythonfcn, imax = NativeCompiler.compileToPython(fcnname, loop)

        sig = (numba.int64[:],)

        for column in loop.params():
            if column.issize():
                sig = sig + (numba.from_dtype(numpy.dtype(sizeType))[:],)
            else:
                sig = sig + (numba.from_dtype(numpy.dtype(columns[column].dataType))[:],)

        tmptypes = {}
        for column in loop.targets:
            if column.issize():
                sig = sig + (numba.from_dtype(numpy.dtype(sizeType))[:],)
                tmptypes[column] = numpy.dtype(sizeType)

            else:
                statement = filter(lambda x: isinstance(x, statementlist.Call) and x.column == column, loop.statements)[0]
                if isinstance(statement.schema, Number) and statement.schema.whole:
                    sig = sig + (numba.int64[:],)
                    tmptypes[column] = numpy.int64

                elif isinstance(statement.schema, Number):
                    sig = sig + (numba.float64[:],)
                    tmptypes[column] = numpy.float64

                else:
                    raise NotImplementedError

        return numba.jit([sig], nopython=True)(pythonfcn), imax, tmptypes

    @staticmethod
    def serialize(nativefcn):
        assert len(nativefcn.overloads) == 1, "expected function to have exactly one signature"
        cres = nativefcn.overloads.values()[0]
        llvmnames = [x.name for x in cres.library._final_module.functions if x.name.startswith("cpython.")]
        assert len(llvmnames) == 1, "expected only one function from dynamically generated Python"
        return (llvmnames[0], cres.library._compiled_object)

    @staticmethod
    def deserialize(llvmname, compiledobj):
        # insignificant compared with 2 ms
        def object_compiled_hook(ll_module, buf):
            pass
        def object_getbuffer_hook(ll_module):
            return compiledobj
        NativeCompiler.llvmengine.set_object_cache(object_compiled_hook, object_getbuffer_hook)

        # actually loads compiled code
        NativeCompiler.llvmengine.finalize_object()

        # find the function within the compiled code
        fcnptr = NativeCompiler.llvmengine.get_function_address(llvmname)

        # interpret it as a Python function
        cpythonfcn = ctypes.CFUNCTYPE(PyObjectPtr, PyObjectPtr, PyObjectPtr, PyObjectPtr)(fcnptr)

        # the cpython.* function takes Python pointers to closure, args, kwds and unpacks them
        def wrapped(*args, **kwds):
            closure = ()
            return cpythonfcn(ctypes.cast(id(closure), PyObjectPtr), ctypes.cast(id(args), PyObjectPtr), ctypes.cast(id(kwds), PyObjectPtr))

        return wrapped

    @staticmethod
    def newengine():
        # 2 ms, which is dominant, but more importantly it needs to persist
        target = llvmlite.binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        backing_mod = llvmlite.binding.parse_assembly("")
        return llvmlite.binding.create_mcjit_compiler(backing_mod, target_machine)

# you should *probably* make sure that access to this is from a single thread...
NativeCompiler.llvmengine = NativeCompiler.newengine()

class NativeExecutor(Executor):
    def __init__(self, query):
        super(NativeExecutor, self).__init__(query)

    def compileLoops(self):
        self.tmptypes = {}
        for i, loops in enumerate(self.loops.values()):
            for j, loop in enumerate(loops):
                fcnname = "f{0}_{1}_{2}".format(self.query.id, i, j)
                loop.nativefcn, loop.imax, tmptypes = NativeCompiler.compileToNative(fcnname, loop, self.query.dataset.columns)
                self.tmptypes.update(tmptypes)

                llvmname, compiledobj = NativeCompiler.serialize(loop.nativefcn)
                loop.nativefcn = NativeCompiler.deserialize(llvmname, compiledobj)

    def runloop(self, loop, args):
        imax = numpy.array(args[0], dtype=numpy.int64)
        loop.nativefcn(*([imax] + args[1:]))

    def inarrays(self, group):
        return dict((n, numpy.array(a)) for n, a in super(NativeExecutor, self).inarrays(group).items())

    def sizearrays(self, group, inarrays):
        return dict((n, numpy.array(a)) for n, a in super(NativeExecutor, self).sizearrays(group, inarrays).items())

    def workarrays(self, group, lengths):
        return dict((data, numpy.empty(lengths[data], dtype=self.tmptypes[data])) for data, size in self.temporaries())
