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

import cython

import numpy
cimport numpy

from femtocode.defs import *

cdef extern from "femtocoderun.h":
    ctypedef long EntryCount
    ctypedef long ItemCount
    ctypedef long ArrayIndex
    ctypedef int LevelIndex
    ctypedef int ColumnIndex
    ctypedef int NumBytes

    ArrayIndex explodesize(EntryCount numEntries,
                           LevelIndex numLevels,
                           ColumnIndex numSizeColumns,
                           ColumnIndex* levelToColumnIndex,
                           ItemCount** sizeColumns,
                           ItemCount* exploded)

    ArrayIndex explodedata(EntryCount numEntries,
                           LevelIndex numLevels,
                           ColumnIndex numSizeColumns,
                           ColumnIndex* levelToColumnIndex,
                           ItemCount** sizeColumns,
                           ColumnIndex dataSizeColumn,
                           NumBytes datumBytes,
                           void* data,
                           void* exploded)

    void plus_lll(ArrayIndex len, long* in1array, long* in2array, long* outarray)
    void plus_ldd(ArrayIndex len, long* in1array, double* in2array, double* outarray)
    void plus_ddd(ArrayIndex len, double* in1array, double* in2array, double* outarray)

cdef extern from "femtocoderun.c":
    ArrayIndex explodesize(EntryCount numEntries,
                           LevelIndex numLevels,
                           ColumnIndex numSizeColumns,
                           ColumnIndex* levelToColumnIndex,
                           ItemCount** sizeColumns,
                           ItemCount* exploded)

    ArrayIndex explodedata(EntryCount numEntries,
                           LevelIndex numLevels,
                           ColumnIndex numSizeColumns,
                           ColumnIndex* levelToColumnIndex,
                           ItemCount** sizeColumns,
                           ColumnIndex dataSizeColumn,
                           NumBytes datumBytes,
                           void* data,
                           void* exploded)

    void plus_lll(ArrayIndex len, long* in1array, long* in2array, long* outarray)
    void plus_ldd(ArrayIndex len, long* in1array, double* in2array, double* outarray)
    void plus_ddd(ArrayIndex len, double* in1array, double* in2array, double* outarray)

# @cython.boundscheck(False)
# @cython.wraparound(False)
# def numpy_explodesize(long numEntries, int numLevels, int numSizeColumns,
    



@cython.boundscheck(False)
@cython.wraparound(False)
def numpy_plus_lll(Py_ssize_t len,
    numpy.ndarray[long, ndim=1, mode="c"] in1 not None,
    numpy.ndarray[long, ndim=1, mode="c"] in2 not None,
    numpy.ndarray[long, ndim=1, mode="c"] out not None):
    plus_lll(len, &in1[0], &in2[0], &out[0])

@cython.boundscheck(False)
@cython.wraparound(False)
def numpy_plus_ldd(Py_ssize_t len,
    numpy.ndarray[long, ndim=1, mode="c"] in1 not None,
    numpy.ndarray[double, ndim=1, mode="c"] in2 not None,
    numpy.ndarray[double, ndim=1, mode="c"] out not None):
    plus_ldd(len, &in1[0], &in2[0], &out[0])

@cython.boundscheck(False)
@cython.wraparound(False)
def numpy_plus_ddd(Py_ssize_t len,
    numpy.ndarray[double, ndim=1, mode="c"] in1 not None,
    numpy.ndarray[double, ndim=1, mode="c"] in2 not None,
    numpy.ndarray[double, ndim=1, mode="c"] out not None):
    plus_ddd(len, &in1[0], &in2[0], &out[0])
