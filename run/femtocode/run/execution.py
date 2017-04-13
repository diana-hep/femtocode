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
import base64

import llvmlite.binding
import numba
import numpy

from femtocode.asts import statementlist
from femtocode.dataset import ColumnName
from femtocode.defs import *
from femtocode.execution import *
from femtocode.lib.standard import StandardLibrary
from femtocode.typesystem import *
from femtocode.testdataset import TestSession

# initialize all the parts of LLVM that Numba needs
numba.jit([(numba.float64[:],)], nopython=True)(lambda x: x[0])

class PyTypeObject(ctypes.Structure):
    _fields_ = ("ob_refcnt", ctypes.c_int), ("ob_type", ctypes.c_void_p), ("ob_size", ctypes.c_int), ("tp_name", ctypes.c_char_p)

class PyObject(ctypes.Structure):
    _fields_ = ("ob_refcnt", ctypes.c_int), ("ob_type", ctypes.POINTER(PyTypeObject))

PyObjectPtr = ctypes.POINTER(PyObject)

def compileToNative(loopFunction, inputs):
    numbaSizeType = numba.from_dtype(numpy.dtype(sizeType))[:]

    sig = []
    for param in loopFunction.parameters:
        if isinstance(param, Countdown):
            sig.append(numbaSizeType)

        elif isinstance(param, (SizeArray, OutSizeArray)):
            sig.append(numbaSizeType)

        elif isinstance(param, (DataArray, OutDataArray)):
            sig.append(numba.from_dtype(numpy.dtype(param.dataType))[:])

        else:
            assert False, "unexpected type: {0}".format(param)

    sig = tuple(sig)
    return numba.jit([sig], nopython=True)(loopFunction.fcn)

def serializeNative(nativefcn):
    assert len(nativefcn.overloads) == 1, "expected function to have exactly one signature"
    cres = nativefcn.overloads.values()[0]
    llvmnames = [x.name for x in cres.library._final_module.functions if x.name.startswith("cpython.")]
    assert len(llvmnames) == 1, "expected only one function from dynamically generated Python"
    return llvmnames[0], cres.library._compiled_object

def deserializeNative(llvmname, compiledobj):
    # 2 ms, which is dominant, but more importantly it needs to persist
    target = llvmlite.binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = llvmlite.binding.parse_assembly("")
    llvmengine = llvmlite.binding.create_mcjit_compiler(backing_mod, target_machine)

    # insignificant compared with 2 ms
    def object_compiled_hook(ll_module, buf):
        pass
    def object_getbuffer_hook(ll_module):
        return compiledobj
    llvmengine.set_object_cache(object_compiled_hook, object_getbuffer_hook)

    # actually loads compiled code
    llvmengine.finalize_object()

    # find the function within the compiled code
    fcnptr = llvmengine.get_function_address(llvmname)

    # interpret it as a Python function
    cpythonfcn = ctypes.CFUNCTYPE(PyObjectPtr, PyObjectPtr, PyObjectPtr, PyObjectPtr)(fcnptr)

    # make sure this engine gets persisted
    cpythonfcn.llvmengine = llvmengine

    # the cpython.* function takes Python pointers to closure, args, kwds and unpacks them
    return cpythonfcn

class CompiledLoopFunction(LoopFunction):
    def __getstate__(self):
        return serializeNative(self.fcn) + (self.parameters,)

    def __setstate__(self, state):
        self.llvmname, self.compiledobj, self.parameters = state
        self.fcn = deserializeNative(self.llvmname, self.compiledobj)
        self.__class__ = DeserializedLoopFunction

    def toJson(self):
        llvmname, compiledobj = NativeCompiler.serialize(self.fcn)
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "name": llvmname,
                "code": base64.b64encode(compiledobj),
                "parameters": [x.toJson() for x in self.parameters]}

    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["class", "name", "code", "parameters"])
        assert obj["class"] in (self.__class__.__module__ + "." + "CompiledLoopFunction",
                                self.__class__.__module__ + "." + "DeserializedLoopFunction")

        llvmname = obj["name"]
        compiledobj = base64.b64decode(obj["code"])
        fcn = deserializeNative(llvmname, compiledobj)
        parameters = [ParamNode.fromJson(x) for x in obj["parameters"]]
        return DeserializedLoopFunction(fcn, parameters, llvmname, compiledobj)

class DeserializedLoopFunction(CompiledLoopFunction):
    def __init__(self, fcn, parameters, llvmname, compiledobj):
        LoopFunction.__init__(self, fcn, parameters)
        self.llvmname = llvmname
        self.compiledobj = compiledobj
    
    def __call__(self, *args, **kwds):
        closure = ()
        return self.fcn(ctypes.cast(id(closure), PyObjectPtr), ctypes.cast(id(args), PyObjectPtr), ctypes.cast(id(kwds), PyObjectPtr))

    def __getstate__(self):
        return self.llvmname, self.compiledobj

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "name": self.llvmname,
                "code": base64.b64encode(self.compiledobj),
                "parameters": [x.toJson() for x in self.parameters]}

class NativeExecutor(Executor):
    def __init__(self, query, debug):
        super(NativeExecutor, self).__init__(query, debug)

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert obj["class"] == self.__class__.__module__ + "." + self.__class__.__name__
        obj["class"] = "femtocode.execution.Executor"
        out = Executor.fromJson(obj)
        out.__class__ = NativeExecutor
        return out

    def compileLoops(self, debug):
        fcntable = SymbolTable(StandardLibrary.table.asdict())
        for lib in self.query.libs:
            fcntable = fcntable.fork(lib.table.asdict())

        for i, loop in enumerate(self.order):
            if isinstance(loop, Loop):
                fcnname = "f{0}_{1}".format(self.query.id, i)
                loop.compileToPython(fcnname, self.query.inputs, fcntable, True, debug)

                if loop.prerun is not None:
                    fcn = compileToNative(loop.prerun, self.query.inputs)
                    loop.prerun = CompiledLoopFunction(fcn, loop.prerun.parameters)

                fcn = compileToNative(loop.run, self.query.inputs)
                loop.run = CompiledLoopFunction(fcn, loop.run.parameters)

    def makeArray(self, length, dataType, init):
        if init:
            return numpy.zeros(length, dtype=dataType)
        else:
            return numpy.empty(length, dtype=dataType)

class NativeAsyncExecutor(NativeExecutor):
    def __init__(self, query, future, debug):
        super(NativeAsyncExecutor, self).__init__(query, debug)

        # all associated data are transient: they're lost if you serialize/deserialize
        self.future = future
        if self.future is not None:
            self.loadsDone = dict((group.id, False) for group in query.dataset.groups)
            self.computesDone = dict((group.id, False) for group in query.dataset.groups)
            self.startTime = time.time()
            self.computeTime = 0.0

            self.action = self.query.actions[-1]
            assert isinstance(self.action, statementlist.Aggregation), "last action must always be an aggregation"
            self.tally = self.action.initialize()

    def futureargs(self):
        return (sum(1.0 for x in self.loadsDone.values() if x) / len(self.loadsDone),
                sum(1.0 for x in self.computesDone.values() if x) / len(self.computesDone),
                self.query.cancelled or all(self.computesDone.values()),
                time.time() - self.startTime,
                self.computeTime,
                self.tally)

    def oneLoadDone(self, groupid):
        if self.future is not None:
            with self.query.lock:
                if not self.query.cancelled:
                    self.loadsDone[groupid] = True
                    futureargs = self.futureargs()

                else:
                    futureargs = None

            if futureargs is not None:
                self.future._update(*futureargs)

    def oneComputeDone(self, groupid, computeTime, subtally):
        if self.future is not None:
            with self.query.lock:
                if not self.query.cancelled:
                    self.computesDone[groupid] = True
                    self.computeTime += computeTime

                    self.tally = self.action.update(self.tally, subtally)

                    futureargs = self.futureargs()

                else:
                    futureargs = None

            if futureargs is not None:
                self.future._update(*futureargs)

    def oneFailure(self, failure):
        with self.query.lock:
            self.query.cancelled = True
            self.tally = failure
            futureargs = self.futureargs()

        self.future._update(*futureargs)

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert obj["class"] == self.__class__.__module__ + "." + self.__class__.__name__
        obj["class"] = "femtocode.execution.Executor"
        out = Executor.fromJson(obj)
        out.__class__ = NativeAsyncExecutor
        return out

class NativeTestSession(TestSession):
    def _makeExecutor(self, query, debug):
        return NativeExecutor(query, debug)

    def _processArray(self, array, dataType):
        return numpy.array(array, dtype=dataType)
