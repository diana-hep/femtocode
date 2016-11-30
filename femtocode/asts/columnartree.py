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

import femtocode.asts.lispytree as lispytree
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
    def __init__(self, schema, fcn, args):
        super(DerivedData, self).__init__(schema)
        self.fcn = fcn
        self.args = args

class LiteralData(Data):
    def __init__(self, schema, value):
        super(LiteralData, self).__init__(schema)
        self.value = value

def columnarSchemaToInputs(schema, path=()):
    if isinstance(schema, ColumnarNull):
        return []

    elif isinstance(schema, (ColumnarBoolean, ColumnarNumber, ColumnarStringFixed)):
        data = InputData(schema, path)
        schema.data = data
        return [data]

    elif isinstance(schema, ColumnarString):
        first = InputData(ColumnarNumber(0, almost(inf), True, []), path + (Data.first,))
        size = InputData(ColumnarNumber(schema.fewest, schema.most, True, []), path + (Data.size,))
        data = InputData(schema, path)
        schema.first = first
        schema.size = size
        schema.data = data
        return [first, size, data]

    elif isinstance(schema, ColumnarCollectionFixed):
        return columnarSchemaToInputs(schema.items)

    elif isinstance(schema, ColumnarCollection):
        first = InputData(ColumnarNumber(0, almost(inf), True, []), path + (Data.first,))
        size = InputData(ColumnarNumber(schema.fewest, schema.most, True, []), path + (Data.size,))
        schema.first = first
        schema.size = size
        return [first, size] + columnarSchemaToInputs(schema.items)

    elif isinstance(schema, ColumnarRecord):
        out = []
        for name in sorted(schema.fields):
            out.extend(columnarSchemaToInputs(schema.fields[name], path + (name,)))
        return out

    elif isinstance(schema, ColumnarUnion):
        tag = InputData(ColumnarNumber(0, len(schema.possibilities), True, []), path + (Data.tag,))
        schema.tag = tag
        out = [tag]
        for i, possibility in enumerate(schema.possibilities):
            data.extend(columnarSchemaToInputs(possibility, path + (repr(i),)))
        return out

def typingToColumnar(tree, typeframe, colframe):
    if isinstance(tree, lispytree.Ref):
        if colframe.defined(tree):
            return colframe[tree]
        else:
            raise ProgrammingError("{0} was defined when building lispytree but is not defined at the stage of building columns".format(tree))

    elif isinstance(tree, lispytree.Literal):
        return LiteralData(schemaToColumnar(tree.schema), tree.value)

    elif isinstance(tree, lispytree.Call):
        if isinstance(tree.fcn, lispytree.BuiltinFunction):
            return tree.fcn.typingToColumnar(tree.args, typeframe, colframe)

        else:
            ### UserFunctions should already have been expanded.
            ### They appear in arguments to functions like .map, not directly in lispytree.Call
            # if isinstance(tree.fcn, lispytree.UserFunction):
            #     subframe = colframe.fork()
            #     for name, arg in zip(tree.fcn.names, tree.args):
            #         subframe[name] = typingToColumnar(arg, colframe, typeframe)
            #     return typingToColumnar(tree.fcn.body, subframe, typeframe)
            raise ProgrammingError("unexpected in lispytree function: {0}".format(tree.fcn))

    else:
        raise ProgrammingError("unexpected in lispytree: {0}".format(tree))
