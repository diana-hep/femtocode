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
        if isinstance(param, NumEntries):
            sig.append(numbaSizeType)

        elif isinstance(param, Countdown):
            sig.append(numbaSizeType)

        elif isinstance(param, Index):
            sig.append(numbaSizeType)

        elif isinstance(param, Skip):
            sig.append(numbaSizeType)

        elif isinstance(param, (SizeArray, OutSizeArray)):
            sig.append(numbaSizeType)

        elif isinstance(param, (DataArray, OutDataArray)):
            sig.append(numba.from_dtype(numpy.dtype(param.dataType)))

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
    pass





class NativeAsyncExecutor(NativeExecutor):
    pass



