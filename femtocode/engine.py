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
import os.path

from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.asts.statementlist import ColumnName

class DefaultEngine(object):
    def run(self, compiled):
        location = os.path.join(os.path.split(os.path.split(__file__)[0])[0], "femtocoderun.so")
        try:
            femtocoderun = ctypes.cdll.LoadLibrary(location)
        except OSError:
            raise ImportError("Could not load femtocoderun.so.\n\n    Expected path: {0}".format(location))

        if isinstance(compiled, string_types):
            compiled = json.loads(compiled)

        types = {}
        for name, schemaJson in list(compiled["inputs"].items()) + list(compiled["temporaries"].items()):
            schema = Schema.fromJson(schemaJson)
            if isinstance(schema, Boolean):
                types[name] = ctypes.c_bool
            elif isinstance(schema, Number) and schema.whole:
                types[name] = ctypes.c_int64
            elif isinstance(schema, Number):
                types[name] = ctypes.c_double
            elif isinstance(schema, String):
                types[name] = ctypes.c_char
            else:
                assert False, "unexpected column schema: {0} {1}".format(type(schema), schema)

        if compiled["source"]["type"] == "literal" and compiled["result"]["type"] == "toPython":
            numEntries = compiled["source"]["numEntries"]
            stripes = {}
            for name in compiled["inputs"]:
                lst = compiled["source"]["stripes"][name]
                stripes[name] = (types[name] * len(lst))(*lst)

            for name in compiled["temporaries"]:
                sizeName = ColumnName.parse(name).size()
                if sizeName in compiled["temporaries"]:
                    raise NotImplementedError
                else:
                    size = compiled["source"]["numEntries"]

                stripes[name] = (types[name] * size)()

            for statement in compiled["statements"]:
                fcn = getattr(femtocoderun, statement["fcn"])
                fcn(*([size] + [stripes[x] for x in statement["args"]] + [stripes[statement["to"]]]))

            schema = Schema.fromJson(compiled["result"]["ref"]["schema"])
            columns = dict((ColumnName.parse(n), None) for n in stripes)   # FIXME: faked; remove this dependency!
            stripes2 = dict((ColumnName.parse(n), s) for n, s in stripes.items())
            indexes = dict((ColumnName.parse(n), 0) for n in stripes)
            name = ColumnName(compiled["result"]["ref"]["data"])

            return [assemble(schema, columns, stripes2, indexes, name) for i in xrange(numEntries)]

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
