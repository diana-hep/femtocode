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

import json

try:
    import numpy
except ImportError as err:
    class FakeNumpy(object):
        def __getattr__(self, x):
            raise err
    numpy = FakeNumpy()

import femtocode.run._numpyengine as _numpyengine
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.asts.statementlist import ColumnName
from femtocode.compiler import Dataset
from femtocode.compiler import toPython

def NumpyDataset(**schemas):
    out = Dataset(**schemas)
    out.engine = NumpyEngine()
    return out

class NumpyEngine(object):
    def run(self, compiled):
        if isinstance(compiled, string_types):
            compiled = json.loads(compiled)

        dtypes = {}
        for name, schemaJson in compiled["inputs"].items() + compiled["temporaries"].items():
            schema = Schema.fromJson(schemaJson)
            if isinstance(schema, Boolean):
                dtype = numpy.bool_
            elif isinstance(schema, Number) and schema.whole:
                dtype = numpy.int64
            elif isinstance(schema, Number):
                dtype = numpy.float64
            elif isinstance(schema, String) and schema.charset == "bytes":
                dtype = numpy.int8
            elif isinstance(schema, String) and schema.charset == "unicode":
                dtype = numpy.unicode_
            else:
                assert False, "unexpected column schema: {0} {1}".format(type(schema), schema)
            dtypes[name] = dtype

        if compiled["source"]["type"] == "literal" and compiled["result"]["type"] == "toPython":
            numEntries = compiled["source"]["numEntries"]
            stripes = {}
            for name in compiled["inputs"]:
                stripes[name] = numpy.array(compiled["source"]["stripes"][name], dtype=dtypes[name])

            for name in compiled["temporaries"]:
                sizeName = ColumnName.parse(name).size()
                if sizeName in compiled["temporaries"]:
                    raise NotImplementedError
                else:
                    size = compiled["source"]["numEntries"]

                stripes[name] = numpy.empty(size, dtype=dtypes[name])

            for statement in compiled["statements"]:
                fcn = getattr(_numpyengine, "numpy_" + statement["fcn"])
                fcn(*([size] + [stripes[x] for x in statement["args"]] + [stripes[statement["to"]]]))

            schema = Schema.fromJson(compiled["result"]["ref"]["schema"])
            columns = dict((ColumnName.parse(n), None) for n in stripes)   # FIXME: faked; remove this dependency!
            stripes2 = dict((ColumnName.parse(n), s) for n, s in stripes.items())
            indexes = dict((ColumnName.parse(n), 0) for n in stripes)
            name = ColumnName(compiled["result"]["ref"]["data"])

            return [toPython.assemble(schema, columns, stripes2, indexes, name) for i in xrange(numEntries)]

        else:
            raise NotImplementedError
