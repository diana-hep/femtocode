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

import femtocode.asts.typedtree as typedtree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

class ColumnName(object):
    sizeSuffix = "@size"
    tagSuffix = "@tag"
    
    def __init__(self, *seq):
        self.seq = seq

    def size(self):
        return ColumnName(*(self.seq + (self.sizeSuffix,)))

    def tag(self):
        return ColumnName(*(self.seq + (self.tagSuffix,)))

    def rec(self, fieldName):
        return ColumnName(*(self.seq + (fieldName,)))

    def pos(self, position):
        return ColumnName(*(self.seq + (position,)))

    def issize(self):
        return self.endswith(ColumnName.sizeSuffix)

    def istag(self):
        return self.endswith(ColumnName.tagSuffix)

    def __eq__(self, other):
        return isinstance(other, ColumnName) and self.seq == other.seq

    def __hash__(self):
        return hash((ColumnName, self.seq))

    def __repr__(self):
        return "ColumnName({0})".format(", ".join(map(json.dumps, self.seq)))

    def __str__(self):
        out = self.seq[0]
        for x in self.seq[1:]:
            if x == self.sizeSuffix:
                out = out + x
            elif x == self.tagSuffix:
                out = out + x
            elif isinstance(x, string_types):
                out = out + "." + x
            elif isinstance(x, int):
                out = out + "@" + repr(x)
            else:
                raise ProgrammingError("bad ColumnName")
        return out

    def startswith(self, other):
        if isinstance(other, string_types):
            return self.seq[0] == other

        elif isinstance(other, ColumnName):
            if len(self.seq) >= len(other.seq):
                return self.seq[:len(other.seq)] == other.seq
            else:
                return False
        else:
            raise ProgrammingError("calling startswith on {0}".format(other))

    def endswith(self, other):
        if isinstance(other, string_types):
            return self.seq[-1] == other

        elif isinstance(other, ColumnName):
            if len(self.seq) >= len(other.seq):
                return self.seq[-len(other.seq):] == other.seq
            else:
                return False
        else:
            raise ProgrammingError("calling endswith on {0}".format(other))

class Column(object):
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema
        
    def __repr__(self):
        return "Column({0}, {1})".format(self.name, self.schema)

    def __eq__(self, other):
        return self.name == other.name and self.schema == other.schema

class RecursiveColumn(Column):
    def __repr__(self):
        return "RecursiveColumn({0}, {1})".format(self.name, self.schema)

class SizeColumn(Column):
    def __init__(self, name):
        super(SizeColumn, self).__init__(name, integer(0, almost(inf)))

    def __repr__(self):
        return "SizeColumn({0})".format(self.name)

class TagColumn(Column):
    def __init__(self, name, possibilities):
        super(TagColumn, self).__init__(name, integer(0, len(possibilities)))
        self.possibilities = possibilities

    def __repr__(self):
        return "TagColumn({0}, {1})".format(self.name, self.possibilities)

def isMinimallyRecursive(schema, nested=None):
    if schema == nested:
        return True

    if nested is None:
        nested = schema

    if isinstance(schema, (Null, Boolean, Number, String)):
        return False

    elif isinstance(schema, Collection):
        return isMinimallyRecursive(schema.items, nested)

    elif isinstance(schema, Record):
        return any(isMinimallyRecursive(t, nested) for t in schema.fields.values())

    elif isinstance(schema, Union):
        return any(isMinimallyRecursive(p, nested) for p in schema.possibilities)

    else:
        raise ProgrammingError("unexpected type: {0} {1}".format(type(schema), schema))

def schemaToColumns(name, schema, hasSize=False):
    if isinstance(name, string_types):
        name = ColumnName(name)

    if isMinimallyRecursive(schema):
        if hasSize:
            sizeName = name.size()
            return {name: RecursiveColumn(name, schema), sizeName: SizeColumn(sizeName)}
        else:
            return {name: RecursiveColumn(name, schema)}

    elif isinstance(schema, Null):
        if hasSize:
            sizeName = name.size()
            return {sizeName: SizeColumn(sizeName)}
        else:
            return {}

    elif isinstance(schema, (Boolean, Number)):
        if hasSize:
            sizeName = name.size()
            return {name: Column(name, schema), sizeName: SizeColumn(sizeName)}
        else:
            return {name: Column(name, schema)}

    elif isinstance(schema, String):
        if not hasSize and schema.charset == "bytes" and schema.fewest == schema.most:
            return {name: Column(name, schema)}
        else:
            sizeName = name.size()
            return {name: Column(name, schema), sizeName: SizeColumn(sizeName)}

    elif isinstance(schema, Collection):
        return schemaToColumns(name, schema.items, hasSize or schema.fewest != schema.most)

    elif isinstance(schema, Record):
        out = {}
        for n, t in schema.fields.items():
            out.update(schemaToColumns(name.rec(n), t, hasSize))
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
            return schemaToColumns(name, flattened[0], hasSize)

        else:
            if hasSize:
                sizeName = name.size()
                out = {sizeName: SizeColumn(sizeName)}
            else:
                out = {}

            tagName = name.tag()
            out[tagName] = TagColumn(tagName, flattened)

            for i, p in enumerate(flattened):
                out.update(schemaToColumns(name.pos(i), p, False))
            return out

    else:
        raise ProgrammingError("unexpected type: {0} {1}".format(type(schema), schema))

class Statement(object): pass

# class Level(Statement):
#     @staticmethod
#     def deepest(one, two):
#         if len(one) <= len(two):
#             if one == two[:len(one)]:
#                 return two
#             else:
#                 raise ProgrammingError("cannot combine levels: {0} and {1}".format(one, two))
#         else:
#             if two == one[:len(two)]:
#                 return one
#             else:
#                 raise ProgrammingError("cannot combine levels: {0} and {1}".format(one, two))

#     def __init__(self, *sequence):
#         self.sequence = sequence

#     def __repr__(self):
#         return "Level{0}".format(self.sequence)

#     def __str__(self):
#         return "L" + repr(len(self.sequence))

#     def depth(self):
#         return len(self.sequence)
    
#     def __add__(self, other):
#         return Level(*(self.sequence + (other,)))

#     def __eq__(self, other):
#         return isinstance(other, Level) and self.sequence == other.sequence

#     def __hash__(self):
#         return hash((Level, self.sequence))

class Ref(Statement):
    @staticmethod
    def deeper(ref):
        if not isinstance(ref.schema, Collection):
            raise ProgrammingError("cannot go deeper into schema {0} (level {1})".format(ref.schema, ref.level))
        return Ref(ref.name, ref.schema.items, ref.level + 1, ref.columns)

    @staticmethod
    def shallower(ref, schema):
        if ref.level <= 1:
            raise ProgrammingError("cannot go shallower from schema {0} (level {1})".format(schema, ref.level))
        return Ref(ref.name, schema, ref.level - 1, ref.columns)

    def __init__(self, name, schema, level, columns):
        self.name = name
        self.schema = schema
        self.level = level
        self.columns = columns

    def __repr__(self):
        return "statementlist.Ref({0}, {1}, {2}, {3}, {4})".format(self.name, self.schema, self.level, self.columns)

    def __str__(self):
        if isinstance(self.name, int):
            return "#{0}[L{1}: {2}]".format(self.name, self.level, ", ".join(str(n) for n in self.columns))
        else:
            return "{0}[L{1}: {2}]".format(self.name, self.level, ", ".join(str(n) for n in self.columns))

    def __eq__(self, other):
        return isinstance(other, Ref) and self.name == other.name and self.schema == other.schema and self.level == other.level and self.columns == other.columns

    def __hash__(self):
        return hash((Ref, self.name, self.schema, self.level, tuple(sorted(self.columns.items()))))

class Literal(Statement):
    def __init__(self, value, schema):
        self.value = value
        self.schema = schema

    @property
    def level(self):
        return 0

    def __repr__(self):
        return "statementlist.Literal({0}, {1})".format(self.value, self.schema)

    def __str__(self):
        return "{0}[L{1}]".format(self.value, self.level)

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value and self.schema == other.schema

    def __hash__(self):
        return hash((Literal, self.value, self.schema))

class Call(Statement):
    def __init__(self, newref, fcnname, args):
        self.newref = newref
        self.fcnname = fcnname
        self.args = tuple(args)

    def __repr__(self):
        return "statementlist.Call({0}, {1}, {2})".format(self.newref, self.fcnname, self.args)

    def __str__(self):
        return "{0} := ({1} {2})".format(str(self.newref), self.fcnname, " ".join(map(str, self.args)))

    def __eq__(self, other):
        return isinstance(other, Call) and self.newref == other.newref and self.fcnname == other.fcnname and self.args == other.args

    def __hash__(self):
        return hash((Statement, self.newref, self.fcnname, self.args))

def build(tree, columns, replacements=None, refnumber=0):
    if replacements is None:
        replacements = {}

    if isinstance(tree, typedtree.Ref):
        if tree.framenumber is None:
            replacements[tree] = Ref(tree.name, tree.schema, 1, dict((n, c) for n, c in columns.items() if n.startswith(tree.name)))
        elif tree in replacements:
            pass
        else:
            raise ProgrammingError("should not encounter any deep references here")

        return replacements[tree], [], refnumber

    elif isinstance(tree, typedtree.Literal):
        replacements[tree] = Literal(tree.value, tree.schema)
        return replacements[tree], [], refnumber

    elif isinstance(tree, typedtree.Call):
        return tree.fcn.buildstatements(tree, columns, replacements, refnumber)

    else:
        raise ProgrammingError("unexpected in typedtree: {0}".format(tree))
