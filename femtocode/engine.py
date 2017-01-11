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
import ctypes
import glob
import os.path

from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.asts.statementlist import ColumnName

class DefaultEngine(object):
    EntryCount = ctypes.c_uint64
    ItemCount = ctypes.c_uint64
    ArrayIndex = ctypes.c_uint64
    LevelIndex = ctypes.c_uint32
    ColumnIndex = ctypes.c_uint32
    NumBytes = ctypes.c_uint32

    def gettype(self, name, schema):
        if name.endswith(ColumnName.sizeSuffix):
            return self.ItemCount
        elif isinstance(schema, Boolean):
            return ctypes.c_bool
        elif isinstance(schema, Number) and schema.whole:
            return ctypes.c_int64
        elif isinstance(schema, Number):
            return ctypes.c_double
        elif isinstance(schema, String):
            return ctypes.c_char
        else:
            assert False, "unexpected column schema: {0} {1}".format(type(schema), schema)

    def explodesize(self, numEntries, levels, stripes, femtocoderun, exploded):
        assert not any("#" in level for level in levels), "explodesize must not be called on temporary stripes: {0}".format(levels)

        numEntries = self.EntryCount(numEntries)
        numLevels = self.LevelIndex(len(levels))

        uniqueSizeColumns = list(set(levels))
        numSizeColumns = self.ColumnIndex(len(uniqueSizeColumns))

        levelToColumnIndex = (self.ColumnIndex * len(levels))(*[uniqueSizeColumns.index(x) for x in levels])

        sizeColumnsType = (ctypes.POINTER(self.ItemCount) * len(uniqueSizeColumns))
        sizeColumns = sizeColumnsType(*[ctypes.cast(ctypes.pointer(stripes[x]), sizeColumnsType._type_) for x in uniqueSizeColumns])

        return femtocoderun.explodesize(numEntries, numLevels, numSizeColumns, levelToColumnIndex, sizeColumns, exploded)

    def explodedata(self, numEntries, levels, data, datasize, stripes, femtocoderun, exploded):
        numEntries = self.EntryCount(numEntries)
        numLevels = self.LevelIndex(len(levels))

        uniqueSizeColumns = list(set(levels))
        numSizeColumns = self.ColumnIndex(len(uniqueSizeColumns))

        levelToColumnIndex = (self.ColumnIndex * len(levels))(*[uniqueSizeColumns.index(x) for x in levels])

        sizeColumnsType = (ctypes.POINTER(self.ItemCount) * len(uniqueSizeColumns))
        sizeColumns = sizeColumnsType(*[ctypes.cast(ctypes.pointer(stripes[x]), sizeColumnsType._type_) for x in uniqueSizeColumns])

        dataSizeColumn = self.ColumnIndex(uniqueSizeColumns.index(datasize))
        dataArray = stripes[data]
        datumBytes = self.NumBytes(ctypes.sizeof(dataArray._type_))

        return femtocoderun.explodedata(numEntries, numLevels, numSizeColumns, levelToColumnIndex, sizeColumns, dataSizeColumn, datumBytes, dataArray, exploded)

    def run(self, query):
        location = glob.glob(os.path.join(os.path.split(os.path.split(__file__)[0])[0], "femtocoderun*.so"))[0]
        femtocoderun = ctypes.cdll.LoadLibrary(location)

        if isinstance(query, string_types):
            query = json.loads(query)

        if query["source"]["type"] == "literal" and query["result"]["type"] == "toPython":
            numEntries = query["source"]["numEntries"]
            stripes = {}
            for name, schemaJson in query["inputs"].items():
                lst = query["source"]["stripes"][name]
                stripes[name] = (self.gettype(name, Schema.fromJson(schemaJson)) * len(lst))(*lst)

            for statement in query["statements"]:
                if statement["fcn"] == "explodesize":
                    size = self.explodesize(query["source"]["numEntries"], statement["levels"], stripes, femtocoderun, ctypes.c_size_t(0))

                elif statement["fcn"] == "explodedata":
                    size = self.explodedata(query["source"]["numEntries"], statement["levels"], statement["data"], statement["size"], stripes, femtocoderun, ctypes.c_size_t(0))

                else:
                    size = None
                    for arg in statement["args"]:
                        if size is None:
                            size = len(stripes[arg])
                        else:
                            assert size == len(stripes[arg]), "All arguments of an ordinary function must have equal sizes: {0} vs {1}.".format(size, len(stripes[arg]))

                name = statement["to"]
                stripes[name] = (self.gettype(name, Schema.fromJson(query["temporaries"][name])) * size)()

            for statement in query["statements"]:
                if statement["fcn"] == "explodesize":
                    self.explodesize(query["source"]["numEntries"], statement["levels"], stripes, femtocoderun, stripes[statement["to"]])

                elif statement["fcn"] == "explodedata":
                    self.explodedata(query["source"]["numEntries"], statement["levels"], statement["data"], statement["size"], stripes, femtocoderun, stripes[statement["to"]])

                else:
                    fcn = getattr(femtocoderun, statement["fcn"])
                    fcn(*([size] + [stripes[x] for x in statement["args"]] + [stripes[statement["to"]]]))
            
            schema = Schema.fromJson(query["result"]["ref"]["schema"])
            stripes2 = dict([(ColumnName.parse(n), s) for n, s in stripes.items()])
            if query["result"]["ref"]["size"] is not None:
                stripes2[ColumnName(query["result"]["ref"]["data"]).size()] = stripes[query["result"]["ref"]["size"]]  # link the result to its size
            columns = stripes2   # FIXME: faked; remove this dependency!
            indexes = dict((n, 0) for n in stripes2)
            name = ColumnName(query["result"]["ref"]["data"])
            
            for i in xrange(numEntries):
                yield assemble(schema, columns, stripes2, indexes, name)

        else:
            raise NotImplementedError

def shred(datum, schema, columns, stripes, name):   # NB: columns is ONLY used by Union
    if datum not in schema:
        raise FemtocodeError("Datum {0} is not an instance of schema:\n\n{1}".format(datum, pretty(schema, prefix="    ")))

    if isinstance(schema, Null):
        pass

    elif isinstance(schema, (Boolean, Number)):
        stripes[name].append(datum)

    elif isinstance(schema, String):
        stripes[name].extend(list(datum))
        if schema.charset != "bytes" or schema.fewest != schema.most:
            sizeName = name.size()
            stripes[sizeName].append(len(datum))

    elif isinstance(schema, Collection):
        if schema.fewest != schema.most:
            size = len(datum)
            for n, s in stripes.items():
                if n.startswith(name) and n.endswith(ColumnName.sizeSuffix):
                    s.append(size)
        items = schema.items
        for x in datum:
            shred(x, items, columns, stripes, name)

    elif isinstance(schema, Record):
        for n, t in schema.fields.items():
            shred(getattr(datum, n), t, columns, stripes, name.rec(n))

    elif isinstance(schema, Union):
        ctag = columns[name.tag()]
        for i, p in enumerate(ctag.possibilities):
            if datum in p:
                stripes[name.tag()].append(i)
                shred(datum, p, columns, stripes, name.pos(i))
                break

    else:
        assert False, "unexpected type: {0} {1}".format(type(schema), schema)

def assemble(schema, columns, stripes, indexes, name):   # NB: columns is ONLY used by Union
    if isinstance(schema, Null):
        return None

    elif isinstance(schema, (Boolean, Number)):
        stripe = stripes[name]
        out = stripe[indexes[name]]
        indexes[name] += 1

        if isinstance(schema, Boolean):
            return bool(out)
        elif schema.whole:
            return int(out)
        else:
            return float(out)

    elif isinstance(schema, String):
        stripe = stripes[name]
        index = indexes[name]
        if schema.charset == "bytes" and schema.fewest == schema.most:
            size = schema.fewest
        else:
            sizeName = name.size()
            sizeStripe = stripes[sizeName]
            size = sizeStripe.data[indexes[sizeName]]
            indexes[sizeName] += 1

        start = index
        end = index + size

        if schema.charset == "bytes":
            if sys.version_info[0] >= 3:
                out = bytes(stripe[start:end])
            else:
                out = b"".join(stripe[start:end])
        else:
            out = u"".join(stripe[start:end])

        indexes[name] += 1
        return out

    elif isinstance(schema, Collection):
        if schema.fewest == schema.most:
            size = schema.fewest
        else:
            size = None
            for n, s in stripes.items():
                if n.startswith(name) and n.endswith(ColumnName.sizeSuffix):
                    size = s[indexes[n]]
                    indexes[n] += 1
            assert size is not None, "Misaligned collection index"

        items = schema.items
        return [assemble(items, columns, stripes, indexes, name) for i in xrange(size)]

    elif isinstance(schema, Record):
        ns = list(schema.fields.keys())
        return namedtuple("tmp", ns)(*[assemble(schema.fields[n], columns, stripes, indexes, name.rec(n)) for n in ns])

    elif isinstance(schema, Union):
        tagName = name.tag()
        stag = stripes[tagName]
        pos = stag[indexes[tagName]]
        indexes[tagName] += 1
        return assemble(columns[tagName].possibilities[pos], columns, stripes, name.pos(pos))

    else:
        assert False, "unexpected type: {0} {1}".format(type(schema), schema)
