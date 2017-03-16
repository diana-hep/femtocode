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

import ctypes
import threading
import time

import llvmlite.binding
import numba
import numpy

from femtocode.asts import statementlist
from femtocode.dataset import ColumnName
from femtocode.execution import Loop
from femtocode.execution import LoopFunction
from femtocode.execution import DependencyGraph
from femtocode.execution import Compiler
from femtocode.execution import Executor
from femtocode.typesystem import *

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
        pythonfcn = pythonfcn.fcn

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
                    tmptypes[column] = numpy.dtype(numpy.int64)

                elif isinstance(statement.schema, Number):
                    sig = sig + (numba.float64[:],)
                    tmptypes[column] = numpy.dtype(numpy.float64)

                else:
                    raise NotImplementedError

        return CompiledLoopFunction(numba.jit([sig], nopython=True)(pythonfcn)), imax, tmptypes

    @staticmethod
    def serialize(nativefcn):
        assert len(nativefcn.overloads) == 1, "expected function to have exactly one signature"
        cres = nativefcn.overloads.values()[0]
        llvmnames = [x.name for x in cres.library._final_module.functions if x.name.startswith("cpython.")]
        assert len(llvmnames) == 1, "expected only one function from dynamically generated Python"
        return llvmnames[0], cres.library._compiled_object

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
        return cpythonfcn

    @staticmethod
    def newengine():
        # 2 ms, which is dominant, but more importantly it needs to persist
        target = llvmlite.binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        backing_mod = llvmlite.binding.parse_assembly("")
        return llvmlite.binding.create_mcjit_compiler(backing_mod, target_machine)

# you should *probably* make sure that access to this is from a single thread...
NativeCompiler.llvmengine = NativeCompiler.newengine()

class CompiledLoopFunction(LoopFunction):
    def __getstate__(self):
        return NativeCompiler.serialize(self.fcn)

    def __setstate__(self, state):
        self.llvmname, self.compiledobj = state
        self.fcn = NativeCompiler.deserialize(self.llvmname, self.compiledobj).fcn
        self.__class__ = DeserializedLoopFunction

    def toJson(self):
        llvmname, compiledobj = NativeCompiler.serialize(self.fcn)
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "name": llvmname,
                "code": base64.b64encode(compiledobj)}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()) == set(["class", "name", "code"])
        assert isinstance(obj["class"], string_types)
        assert "." in obj["class"]

        mod = obj["class"][:obj["class"].rindex(".")]
        cls = obj["class"][obj["class"].rindex(".") + 1:]

        if mod == CompiledLoopFunction.__module__ and cls == CompiledLoopFunction.__name__:
            assert isinstance(obj["name"], string_types)
            assert isinstance(obj["code"], string_types)
            return DeserializedLoopFunction(NativeCompiler.deserialize(obj["name"], base64.b64decode(obj["code"])), obj["name"], obj["code"])
        else:
            return getattr(importlib.import_module(mod), cls).fromJson(obj)

class DeserializedLoopFunction(CompiledLoopFunction):
    def __init__(self, fcn, llvmname, compiledobj):
        self.fcn = fcn
        self.llvmname = llvmname
        self.compiledobj = compiledobj

    def __getstate__(self):
        return self.llvmname, self.compiledobj

    def toJson(self):
        return {"class": CompiledLoopFunction.__module__ + "." + CompiledLoopFunction.__name__,
                "name": self.llvmname,
                "code": base64.b64encode(self.compiledobj)}

    def __call__(self, *args, **kwds):
        closure = ()
        return self.fcn(ctypes.cast(id(closure), PyObjectPtr), ctypes.cast(id(args), PyObjectPtr), ctypes.cast(id(kwds), PyObjectPtr))

class NativeExecutor(Executor):
    def __init__(self, query):
        super(NativeExecutor, self).__init__(query)

    # def _copy(self):
    #     # reference that which is read-only, but actually copy what is mutable
    #     out = super(NativeExecutor, self)._copy()
    #     out.__class__ = NativeExecutor
    #     out.tmptypes = self.tmptypes
    #     return out

    def toJson(self):
        out = super(NativeExecutor, self).toJson()
        out["tmptypes"] = dict((str(k), str(v)) for k, v in self.tmptypes.items())
        return out

    @staticmethod
    def fromJson(obj):
        assert "tmptypes" in obj
        assert isinstance(obj["tmptypes"], dict)
        assert all(isinstance(k, string_types) and isinstance(v, string_types) for k, v in obj["tmptypes"].items())

        out = Executor.fromJson(obj)
        out.__class__ = NativeExecutor
        out.tmptypes = dict((ColumnName.parse(k), numpy.dtype(v)) for k, v in obj["tmptypes"].items())
        return out

    def compileLoops(self):
        self.tmptypes = {}
        for i, loop in enumerate(self.order):
            if isinstance(loop, Loop):
                fcnname = "f{0}_{1}".format(self.query.id, i)
                loop.run, loop.imax, tmptypes = NativeCompiler.compileToNative(fcnname, loop, self.query.dataset.columns)
                self.tmptypes.update(tmptypes)

    def imax(self, imax):
        return numpy.array(imax, dtype=numpy.int64)

    def inarrays(self, group):
        return dict((n, numpy.array(a)) for n, a in super(NativeExecutor, self).inarrays(group).items())

    def sizearrays(self, group, inarrays):
        return dict((n, numpy.array(a)) for n, a in super(NativeExecutor, self).sizearrays(group, inarrays).items())

    def workarrays(self, group, lengths):
        return dict((data, numpy.empty(lengths[data], dtype=self.tmptypes[data])) for data, size in self.temporaries)

class NativeAsyncExecutor(NativeExecutor):
    def __init__(self, query, future):
        super(NativeAsyncExecutor, self).__init__(query)

        # all associated data are transient: they're lost if you serialize/deserialize
        self.future = future
        self.lock = threading.Lock()
        if self.future is not None:
            self.loadsDone = dict((group.id, False) for group in query.dataset.groups)
            self.computesDone = dict((group.id, False) for group in query.dataset.groups)
            self.startTime = time.time()
            self.computeTime = 0.0

            self.action = self.query.actions[-1]
            assert isinstance(self.action, statementlist.Aggregation), "last action must always be an aggregation"
            self.tally = self.action.initialize()

    # def _copy(self):
    #     # reference that which is read-only, but actually copy what is mutable
    #     out = super(NativeAsyncExecutor, self)._copy()
    #     out.__class__ = NativeAsyncExecutor
    #     return out

    def futureargs(self):
        return (sum(1.0 for x in self.loadsDone.values() if x) / len(self.loadsDone),
                sum(1.0 for x in self.computesDone.values() if x) / len(self.computesDone),
                self.query.cancelled or all(self.computesDone.values()),
                time.time() - self.startTime,
                self.computeTime,
                self.tally)

    def oneLoadDone(self, groupid):
        if self.future is not None:
            with self.lock:
                if not self.query.cancelled:
                    self.loadsDone[groupid] = True
                    futureargs = self.futureargs()

                else:
                    futureargs = None

            if futureargs is not None:
                self.future._update(*futureargs)

    def oneComputeDone(self, groupid, computeTime, subtally):
        if self.future is not None:
            with self.lock:
                if not self.query.cancelled:
                    self.computesDone[groupid] = True
                    self.computeTime += computeTime

                    self.tally = self.action.update(self.tally, subtally)

                    if all(self.computesDone.values()):
                        self.tally = self.action.finalize(self.tally)

                    futureargs = self.futureargs()

                else:
                    futureargs = None

            if futureargs is not None:
                self.future._update(*futureargs)

    def oneFailure(self, failure):
        with self.lock:
            self.query.cancelled = True
            self.tally = failure
            futureargs = self.futureargs()

        self.future._update(*futureargs)

    @staticmethod
    def fromJson(obj):
        out = NativeExecutor.fromJson(obj)
        out.__class__ = NativeAsyncExecutor
        out.lock = threading.Lock()
        out.future = None
        return out
