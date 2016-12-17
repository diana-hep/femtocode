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

try:
    import numpy
except ImportError as err:
    class FakeNumpy(object):
        def __getattr__(self, x):
            raise err
    numpy = FakeNumpy()

from femtocode.run.defs import *
from femtocode.typesystem import *
from femtocode.asts.statementlist import *

class NumpyDataset(Dataset):
    def __init__(self, **schemas):
        names = sorted(schemas.keys())
        Dataset.checknames(names)

        types = resolve([schemas[n] for n in names])

        columns = {}
        for n, t in zip(names, types):
            columns.update(schemaToColumns(n, t))
                
        columns = dict((n, NumpyColumn(c)) for n, c in columns.items())

        super(NumpyDataset, self).__init__(schemas, columns)

class NumpyColumn(object):
    def __init__(self, column):
        if isinstance(column.schema, Null):
            dtype = None
        elif isinstance(column.schema, Boolean):
            dtype = numpy.bool_
        elif isinstance(column.schema, Number) and column.schema.whole:
            dtype = numpy.int64
        elif isinstance(column.schema, Number):
            dtype = numpy.float64
        elif isinstance(column.schema, String) and column.schema.charset == "bytes":
            dtype = numpy.int8
        elif isinstance(column.schema, String) and column.schema.charset == "unicode":
            dtype = numpy.unicode_
        else:
            raise ProgrammingError("unexpected type in Column: {0} {1}".format(type(column.schema), column.schema))

        self.column = column
        self.growdata = []
        if dtype is not None:
            self.data = numpy.empty(0, dtype=dtype)
        else:
            self.data = None

    @property
    def schema(self):
        return self.column.schema

    def clear(self):
        self.data = numpy.empty(0, dtype=self.data.dtype)
        self.growdata = []

    def append(self, x):
        self.growdata.append(x)

    def finalize(self):
        if self.data is None:
            raise ProgrammingError("should not allocate array of NULLs")
        data = numpy.empty(len(self.data) + len(self.growdata), dtype=self.data.dtype)
        data[:len(self.data)] = self.data
        data[len(self.data):] = self.growdata
        self.data = data
        self.growdata = []

    def extend(self, other):
        if isinstance(other, numpy.ndarray) and len(other.shape) == 1 and self.dtype == other.dtype:
            data = numpy.empty(len(self.data) + len(other), dtype=self.dtype)
            data[:len(self.data)] = self.data
            data[len(self.data):] = other
            self.data = data

########################################################################

import cython

import numpy
cimport numpy

cdef extern from "stdint.h":
    ctypedef int int64_t

cdef extern from "femtocoderun.h":
    void plus_flatflat[IN1, IN2, OUT](int64_t len, IN1* in1array, IN2* in2array, OUT* outarray)

def plus(in1, in2, out):
    if isinstance(in1, numpy.ndarray) and isinstance(in2, numpy.ndarray) and isinstance(out, numpy.ndarray) and len(in1) == len(in2) == len(out):
        if in1.dtype == numpy.int64 and in2.dtype == numpy.int64 and out.dtype == numpy.int64:
            plus_flatflat_longlong(len(in1), in1, in2, out)
        elif in1.dtype == numpy.int64 and in2.dtype == numpy.float64 and out.dtype == numpy.float64:
            plus_flatflat_longdouble(len(in1), in1, in2, out)
        elif in1.dtype == numpy.float64 and in2.dtype == numpy.int64 and out.dtype == numpy.float64:
            plus_flatflat_doublelong(len(in1), in1, in2, out)
        elif in1.dtype == numpy.float64 and in2.dtype == numpy.float64 and out.dtype == numpy.float64:
            plus_flatflat_doubledouble(len(in1), in1, in2, out)
        else:
            raise ProgrammingError("bad numpy type combination: {0} {1} {2}".format(in1.dtype, in2.dtype, out.dtype))
    else:
        raise ProgrammingError("bad array input: {0} ({1}) {2} ({3}) {4} ({5})".format(in1, len(in1), in2, len(in2), out, len(out)))

@cython.boundscheck(False)
@cython.wraparound(False)
def plus_flatflat_longlong(Py_ssize_t len,
    numpy.ndarray[long, ndim=1, mode="c"] in1 not None,
    numpy.ndarray[long, ndim=1, mode="c"] in2 not None,
    numpy.ndarray[long, ndim=1, mode="c"] out not None):
    plus_flatflat[long, long, long](len, &in1[0], &in2[0], &out[0])

@cython.boundscheck(False)
@cython.wraparound(False)
def plus_flatflat_longdouble(Py_ssize_t len,
    numpy.ndarray[long, ndim=1, mode="c"] in1 not None,
    numpy.ndarray[double, ndim=1, mode="c"] in2 not None,
    numpy.ndarray[double, ndim=1, mode="c"] out not None):
    plus_flatflat[long, double, double](len, &in1[0], &in2[0], &out[0])

@cython.boundscheck(False)
@cython.wraparound(False)
def plus_flatflat_doublelong(Py_ssize_t len,
    numpy.ndarray[double, ndim=1, mode="c"] in1 not None,
    numpy.ndarray[long, ndim=1, mode="c"] in2 not None,
    numpy.ndarray[double, ndim=1, mode="c"] out not None):
    plus_flatflat[double, long, double](len, &in1[0], &in2[0], &out[0])

@cython.boundscheck(False)
@cython.wraparound(False)
def plus_flatflat_doubledouble(Py_ssize_t len,
    numpy.ndarray[double, ndim=1, mode="c"] in1 not None,
    numpy.ndarray[double, ndim=1, mode="c"] in2 not None,
    numpy.ndarray[double, ndim=1, mode="c"] out not None):
    plus_flatflat[double, double, double](len, &in1[0], &in2[0], &out[0])
