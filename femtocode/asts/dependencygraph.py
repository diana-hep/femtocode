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

import femtocode.asts.typingtree as typingtree
import femtocode.typesystem as typesystem

### Columnar typesystem for execution

class ColumnarSchema(object):
    pass

class ColumnarNull(ColumnarSchema):
    pass

class ColumnarBoolean(ColumnarSchema):
    pass

class ColumnarNumber(ColumnarSchema):
    def __init__(self, min, max, whole, guards):
        self.min = min
        self.max = max
        self.whole = whole
        self.guards = guards

class ColumnarStringFixed(ColumnarSchema):
    def __init__(self, size):
        self.size = size

class ColumnarString(ColumnarSchema):
    def __init__(self, charset, fewest, most):
        self.charset = charset
        self.fewest = fewest
        self.most = most

class ColumnarCollectionFixed(ColumnarSchema):
    def __init__(self, items, dims):
        self.items = items
        self.dims = dims

class ColumnarCollection(ColumnarSchema):
    def __init__(self, items, fewest, most):
        self.items = items
        self.fewest = fewest
        self.most = most
        
class ColumnarRecord(ColumnarSchema):
    def __init__(self, fields):
        self.fields = fields

class ColumnarUnion(ColumnarSchema):
    def __init__(self, possibilities):
        self.possibilities = possibilities

def schemaToColumnar(schema, memo=None):
    if memo is None:
        memo = set()

    if schema.alias is not None:
        if schema.alias in memo:
            raise FemtocodeError("Recursive types like \"{0}\" cannot be represented as columns.".format(schema.alias))
        else:
            memo.add(schema.alias)

    if isinstance(schema, typesystem.Null):
        return ColumnarNull()

    elif isinstance(schema, typesystem.Boolean):
        return ColumnarBoolean()

    elif isinstance(schema, typesystem.Number):
        return ColumnarNumber(schema.min, schema.max, schema.whole, [(schema.min, schema.max)])

    elif isinstance(schema, typesystem.String):
        if schema.charset == "bytes" and schema.fewest == schema.most:
            return ColumnarStringFixed(schema.fewest)
        else:
            return ColumnarString(schema.charset, schema.fewest, schema.most)

    elif isinstance(schema, typesystem.Collection):
        dims = []
        items = schema
        while isinstance(items, typesystem.Collection) and items.fewest == items.most:
            dims.append(items.fewest)
            items = items.items

        if len(dims) > 0:
            return ColumnarCollectionFixed(schemaToColumnar(items, memo), dims)
        else:
            return ColumnarCollection(schemaToColumnar(schema.items, memo), schema.fewest, schema.most)

    elif isinstance(schema, typesystem.Record):
        return ColumnarRecord(dict((n, schemaToColumnar(t, memo)) for n, t in schema.fields.items()))

    elif isinstance(schema, typesystem.Union):
        def updateNumbers(oldnumbers, newnumbers):
            return ColumnarNumber(almost.min(oldnumbers.min, newnumbers.min),
                                  almost.max(oldnumbers.max, newnumbers.max),
                                  oldnumbers.whole and newnumbers.whole,
                                  oldnumbers.guards + newnumbers.guards)

        def updateStrings(oldstrings, newstrings):
            if isinstance(oldstrings, ColumnarStringFixed) and isinstance(newstrings, ColumnarStringFixed) and oldstrings.size == newstrings.size:
                return newstrings
            elif isinstance(oldstrings, ColumnarStringFixed) and isinstance(newstrings, ColumnarStringFixed):
                return ColumnarString("bytes", min(oldstrings.size, newstrings.size), max(oldstrings.size, newstrings.size))
            elif isinstance(oldstrings, ColumnarStringFixed) and isinstance(newstrings, ColumnarString):
                return ColumnarString(newstrings.charset, min(oldstrings.size, newstrings.min), max(oldstrings.size, newstrings.max))
            elif isinstance(oldstrings, ColumnarString) and isinstance(newstrings, ColumnarStringFixed):
                return ColumnarString(oldstrings.charset, min(oldstrings.min, newstrings.size), max(oldstrings.max, newstrings.size))
            elif isinstance(oldstrings, ColumnarString) and isinstance(newstrings, ColumnarString):
                if oldstrings.charset == "unicode" or newstrings.charset == "unicode":
                    charset = "unicode"
                else:
                    charset = "bytes"
                return ColumnarString(charset, min(oldstrings.min, newstrings.min), max(oldstrings.max, newstrings.max))

        nulls = None
        booleans = None
        numbers = None
        strings = None
        collections = []
        records = []

        for possibility in schema.possibilities:
            if isinstance(possibility, typesystem.Null):
                nulls = schemaToColumnar(possibility, memo)

            elif isinstance(possibility, typesystem.Boolean):
                booleans = schemaToColumnar(possibility, memo)

            elif isinstance(possibility, typesystem.Number):
                if numbers is None:
                    numbers = schemaToColumnar(possibility, memo)
                else:
                    numbers = updateNumbers(numbers, schemaToColumnar(possibility, memo))

            elif isinstance(possibility, typesystem.String):
                if strings is None:
                    strings = schemaToColumnar(possibility, memo)
                else:
                    strings = updateStrings(strings, schemaToColumnar(possibility, memo))

            elif isinstance(possibility, typesystem.Collection):
                newcollection = schemaToColumnar(possibility, memo)
                found = False
                for oldcollection in collections:
                    if isinstance(oldcollection.items, ColumnarNull) and isinstance(newcollection.items, ColumnarNull):
                        items = oldcollection.items
                    elif isinstance(oldcollection.items, ColumnarBoolean) and isinstance(newcollection.items, ColumnarBoolean):
                        items = oldcollection.items
                    elif isinstance(oldcollection.items, ColumnarNumber) and isinstance(newcollection.items, ColumnarNumber):
                        items = updateNumbers(oldcollection.items, newcollection.items)
                    elif isinstance(oldcollection.items, ColumnarString) and isinstance(newcollection.items, ColumnarString):
                        items = updateStrings(oldcollection.items, newcollection.items)
                    else:
                        items = None

                    if items is not None and isinstance(oldcollection, ColumnarCollectionFixed) and isinstance(newcollection, ColumnarCollectionFixed) and oldcollection.dims == newcollection.dims:
                        oldcollection.items = items
                        found = True
                        break

                    elif items is not None and isinstance(oldcollection, ColumnarCollection) and isinstance(newcollection, ColumnarCollection):
                        oldcollection.items = items
                        oldcollection.fewest = min(oldcollection.fewest, newcollection.fewest)
                        oldcollection.most = max(oldcollection.most, newcollection.most)
                        found = True
                        break

                if not found:
                    collections.append(newcollection)

            elif isinstance(possibility, typesystem.Record):
                records.append(schemaToColumnar(possibility, memo))

            else:
                raise ProgrammingError("unexpected schema in schemaToColumnar union: {0}".format(schema))

        possibilities = []
        if nulls is None:
            possibilities.append(nulls)
        if booleans is None:
            possibilities.append(booleans)
        if numbers is None:
            possibilities.append(numbers)
        if strings is None:
            possibilities.append(strings)
        possibilities.extend(collections)
        possibilities.extend(records)

        return ColumnarUnion(possibilities)
        
    else:
        raise ProgrammingError("unexpected schema in schemaToColumnar: {0}".format(schema))

### Data representation

class Data(object):
    first = "@first"
    size = "@size"
    tag = "@tag"

    def __init__(self, schema):
        self.schema = schema

class InputData(Data):
    def __init__(self, schema, path):
        super(InputData, self).__init__(schema)
        self.path = path

class DerivedData(Data):
    def __init__(self, schema, dependencies, function):
        super(DerivedData, self).__init__(schema)
        self.dependencies = dependencies
        self.function = function

class Graph(object):
    def __init__(self):
        self.treeToData = {}

# def schemaToInputs(schema, prefix=InputData.root, memo=None):
#     if memo is None:
#         memo = set()

#     if schema.alias is not None:
#         if schema.alias in memo:
#             raise ProgrammingError("recursive types not implemented for input data")
#         else:
#             memo.add(schema.alias)

#     if isinstance(schema, Null):
#         return []

#     elif isinstance(schema, (Boolean, String)):
#         if schema.min == schema.max:


#         return [InputData(schema, prefix)]

#     elif isinstance(schema, Number):
#         if schema.min == schema.max:
#             return []
#         else:
#             return [InputData(schema, prefix)]

#     elif isinstance(schema, Collection):
#         if schema.fewest == schema.most:
#             return schemaToInputs(schema.items, prefix)
#         else:
#             return [InputData(integer(min=0), prefix + "." + InputData.first),
#                     InputData(integer(min=0, max=schema.most), prefix + "." + InputData.size)] + \
#                     schemaToInputs(schema.items, prefix)

#     elif isinstance(schema, Record):
#         return [InputData(schema.fields[n], prefix + "." + n) for n in sorted(schema.fields.keys())]

#     elif isinstance(schema, Union):
#         tag = {}
#         booleans = None
#         integers = None
#         extendeds = None
#         bytestrings = None
#         unicodestrings = None
#         groups = []

#         for possibility in sorted(schema.possibilities):
#             if isinstance(possibility, Null):
#                 tag[len(tag)] = possibility

#             elif isinstance(possibility, Boolean):
#                 booleans = len(tag)
#                 tag[len(tag)] = possibility

#             elif isinstance(possibility, Number) and possibility.whole:
#                 if integers is None:
#                     integers = len(tag)
#                     tag[len(tag)] = Number(possibility.min, possibility.max, True)
#                 else:
#                     tag[integers].min = almost.min(tag[integers].min, possibility.min)
#                     tag[integers].max = almost.max(tag[integers].max, possibility.max)

#             elif isinstance(possibility, Number):
#                 if extendeds is None:
#                     extendeds = len(tag)
#                     tag[len(tag)] = Number(possibility.min, possibility.max, False)
#                 else:
#                     tag[extendeds].min = almost.min(tag[extendeds].min, possibility.min)
#                     tag[extendeds].max = almost.max(tag[extendeds].max, possibility.max)

#             elif isinstance(possibility, String) and possibility.charset == "bytes":
#                 if bytestrings is None:
                    
