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

import llvmlite.binding
import numba
import numpy

from femtocode.asts import statementlist
from femtocode.dataset import ColumnName
from femtocode.execution import Loop
from femtocode.execution import DependencyGraph
from femtocode.execution import Compiler
from femtocode.execution import Executor

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
    def toJson(self):
        llvmname, compiledobj = NativeCompiler.serialize(self.fcn)
        return {"module": self.__class__.__module__,
                "class": self.__class__.__name__,
                "name": llvmname,
                "code": base64.b64encode(compiledobj)}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()) == set(["module", "class", "name", "code"])
        assert isinstance(obj["module"], string_types)
        assert isinstance(obj["class"], string_types)

        if obj["module"] == CompiledLoopFunction.__module__ and obj["class"] == CompiledLoopFunction.__name__:
            assert isinstance(obj["name"], string_types)
            assert isinstance(obj["code"], string_types)
            return DeserializedLoopFunction(NativeCompiler.deserialize(obj["name"], base64.b64decode(obj["code"])), obj["name"], obj["code"])
        else:
            return getattr(importlib.import_module(obj["module"]), obj["class"]).fromJson(obj)

class DeserializedLoopFunction(CompiledLoopFunction):
    def __init__(self, fcn, llvmname, compiledobj):
        self.fcn = fcn
        self.llvmname = llvmname
        self.compiledobj = compiledobj

    def toJson(self):
        return {"module": CompiledLoopFunction.__module__,
                "class": CompiledLoopFunction.__name__,
                "name": self.llvmname,
                "code": base64.b64encode(self.compiledobj)}

    def __call__(self, *args, **kwds):
        closure = ()
        return self.fcn(ctypes.cast(id(closure), PyObjectPtr), ctypes.cast(id(args), PyObjectPtr), ctypes.cast(id(kwds), PyObjectPtr))

class NativeExecutor(Executor):
    def __init__(self, query):
        super(NativeExecutor, self).__init__(query)

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
