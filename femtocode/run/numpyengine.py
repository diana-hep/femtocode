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

from femtocode.compiler import *
from femtocode.run._numpyengine import *
from femtocode.typesystem import *

class NumpyEngine(Engine):
    pass


class NumpyDataset(Dataset):
    def __init__(self, **schemas):
        super(NumpyDataset, self).__init__(schemas, columns)
        self.pages = dict((n, NumpyPage(c)) for n, c in self.columns.items())
        self.entries = 0

class NumpyPage(object):
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
            assert False, "unexpected type in Column: {0} {1}".format(type(column.schema), column.schema)

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
        assert self.data is not None, "should not allocate array of NULLs"
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
