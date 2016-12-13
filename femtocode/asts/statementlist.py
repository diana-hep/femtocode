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
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

class Column(object):
    sizeSuffix = "@size"
    tagSuffix = "@tag"

    @staticmethod
    def posSuffix(n):
        return "@" + repr(n)

    def __init__(self, name, schema, size):
        self.name = name
        self.schema = schema
        self.size = size
        
    def __repr__(self):
        return "Column({0}, {1}, {2}, {3})".format(self.name, self.schema, self.size)

    def __eq__(self, other):
        return self.name == other.name and self.schema == other.schema and self.size == other.size

class SizeColumn(Column):
    def __init__(self, name, depth):
        super(SizeColumn, self).__init__(name, integer(0, almost(inf)), None)
        self.depth = depth

    def __repr__(self):
        return "SizeColumn({0}, {1})".format(self.name, self.depth)

class TagColumn(Column):
    def __init__(self, name, max):
        super(TagColumn, self).__init__(name, integer(0, max), None)

    def __repr__(self):
        return "TagColumn({0}, {1})".format(self.name, self.schema.max)

def schemaToColumns(name, schema, size=None, memo=None):
    if memo is None:
        memo = ()
    if schema.alias is not None:
        memo = memo + (schema,)

    if isinstance(schema, Null):
        return {}

    elif isinstance(schema, (Boolean, Number)):
        out = {name: Column(name, schema, size)}
        if size is not None:
            out[size.name] = size
        return out

    elif isinstance(schema, String):
        if schema.charset == "bytes" and schema.fewest == schema.most:
            return {name: Column(name, schema, size)}
        else:
            sizeName = name + "." + Column.sizeSuffix
            maxSize = 1 + (0 if size is None else size.schema.max)
            size = SizeColumn(sizeName, maxSize)
            return {sizeName: size, name: Column(name, schema, size)}

    elif isinstance(schema, Collection):
        if schema.fewest == schema.most:
            return schemaToColumns(name, schema.items, size, memo)

        elif schema.items in memo:
            sizeName = name + "." + Column.sizeSuffix
            size = SizeColumn(sizeName, almost(inf))
            return {sizeName: size, name: Column(name, schema.items, size)}

        else:
            sizeName = name + "." + Column.sizeSuffix
            maxSize = 1 + (0 if size is None else size.schema.max)
            size = SizeColumn(sizeName, maxSize)
            return schemaToColumns(name, schema.items, size, memo)

    elif isinstance(schema, Record):
        out = {}
        for n, t in schema.fields.items():
            out.update(schemaToColumns(name + "." + n, t, size, memo))
        return out

    elif isinstance(schema, Union):
        def compatible(x, y):
            if isinstance(x, Null) and isinstance(y, Null):
                return True
            elif isinstance(x, Boolean) and isinstance(y, Boolean):
                return True
            elif isinstance(x, Number) and isinstance(y, Number):
                return True
            elif isinstance(x, String) and x.charset == "bytes" and isinstance(y, String) and y.charset == "bytes":
                return True
            elif isinstance(x, String) and x.charset == "unicode" and isinstance(y, String) and y.charset == "unicode":
                return True
            elif isinstance(x, String) and isinstance(y, String):
                return False   # bytes and unicode or unicode and bytes
            elif isinstance(x, Collection) and isinstance(y, Collection):
                return compatible(x.items, y.items)
            elif isinstance(x, Record) and isinstance(y, Record):
                return set(x.fields.keys()) == set(y.fields.keys()) and \
                       all(compatible(x.fields[n], y.fields[n]) for n in x.fields)
            elif x.__class__ == y.__class__:
                raise ProgrammingError("missing case: {0} {1} {2}".format(type(x), x, y))
            else:
                return False

        classes = []
        for p1 in schema.possibilities:
            found = False
            for c in classes:
                for p2 in c:
                    if not found and compatible(p1, p2):
                        c.append(p1)
                        found = True
            if not found:
                classes.append([p1])
        
        flattened = []
        for c in classes:
            if isinstance(c[0], Null):
                flattened.append(null)
            elif isinstance(c[0], Boolean):
                flattened.append(boolean)
            elif isinstance(c[0], Number):
                flattened.append(Number(almost.min(*[p.min for p in c]), almost.max(*[p.max for p in c]), all(p.whole for p in c)))
            elif isinstance(c[0], String) and c[0].charset == "bytes":
                flattened.append(String("bytes", almost.min(*[p.fewest for p in c]), almost.max(*[p.most for p in c])))
            elif isinstance(c[0], String) and c[0].charset == "unicode":
                flattened.append(String("unicode", almost.min(*[p.fewest for p in c]), almost.max(*[p.most for p in c])))
            elif isinstance(c[0], Collection):
                flattened.append(Collection(union(*[p.items for p in c]), almost.min(*[p.fewest for p in c]), almost.max(*[p.most for p in c]), all(p.ordered for p in c)))
            elif isinstance(c[0], Record):
                flattened.append(Record(dict((n, union(*[p.fields[n] for p in c])) for n in c[0].fields)))
            else:
                raise ProgrammingError("missing case: {0} {1}".format(type(c[0]), c))

        if len(flattened) == 1:
            return schemaToColumns(name, flattened[0], size, memo)
        else:
            tagName = name + "." + Column.tagSuffix
            out = {tagName: TagColumn(tagName, len(flattened) - 1)}

            if any(p in memo for p in flattened):
                size = SizeColumn(name + "." + Column.sizeSuffix, almost(inf))
            for i, p in enumerate(flattened):
                if p not in memo:
                    out.update(schemaToColumns(name + "." + Column.posSuffix(i), p, size, memo))
            return out

    else:
        raise ProgrammingError("unexpected schema: {0}".format(schema))
