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

import re
import json

import femtocode.asts.typedtree as typedtree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

class Serializable(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

    def toJsonFile(self, file):
        json.dump(file, self.toJson())

class ColumnName(Serializable):
    sizeSuffix = "@size"
    tagSuffix = "@tag"
    
    @staticmethod
    def parse(name):
        if name.endswith(ColumnName.sizeSuffix):
            issize = True
            name = name[:-len(ColumnName.sizeSuffix)]
        else:
            issize = False

        if name.endswith(ColumnName.tagSuffix):
            istag = True
            name = name[:-len(ColumnName.tagSuffix)]
        else:
            istag = False

        m = re.match("^([^@]*)@([0-9]+)$", name)
        if m is not None:
            name = m.group(1)
            pos = int(m.group(2))
        else:
            pos = None

        out = ColumnName(*name.split("."))
        if issize:
            out = out.size()
        if istag:
            out = out.tag()
        if pos is not None:
            out = out.pos(pos)
        return out

    def __init__(self, *seq):
        assert all(isinstance(x, string_types + (int, long)) for x in seq), "ColumnName parts must all be strings or integers, not {0}.".format(seq)
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

    def __lt__(self, other):
        if isinstance(other, ColumnName):
            for x, y in zip(self.seq, other.seq):
                if isinstance(x, string_types) and isinstance(y, string_types):
                    if x != y:
                        return x < y
                elif isinstance(x, int) and isinstance(y, int):
                    if x != y:
                        return x < y
                else:
                    return isinstance(x, int)
            return len(self.seq) < len(other.seq)

        else:
            raise TypeError("unorderable types: {0}() < {1}()".format(type(self), type(other)))

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
                assert False, "bad ColumnName"
        return out

    def toJson(self):
        return str(self)

    def startswith(self, other):
        if isinstance(other, string_types):
            return self.seq[0] == other

        elif isinstance(other, ColumnName):
            if len(self.seq) >= len(other.seq):
                return self.seq[:len(other.seq)] == other.seq
            else:
                return False
        else:
            assert False, "calling startswith on {0}".format(other)

    def endswith(self, other):
        if isinstance(other, string_types):
            return self.seq[-1] == other

        elif isinstance(other, ColumnName):
            if len(self.seq) >= len(other.seq):
                return self.seq[-len(other.seq):] == other.seq
            else:
                return False
        else:
            assert False, "calling endswith on {0}".format(other)

class Column(Serializable):
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema
        
    def __repr__(self):
        return "Column({0}, {1})".format(self.name, self.schema)

    def __str__(self):
        return str(self.name)

    def toJson(self):
        return self.name.toJson()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name and self.schema == other.schema

    def __hash__(self):
        return hash((self.__class__, self.name, self.schema))

class DataColumn(Column):
    def __repr__(self):
        return "DataColumn({0}, {1})".format(self.name, self.schema)

class SizeColumn(Column):
    def __init__(self, name):
        super(SizeColumn, self).__init__(name, integer(0, almost(inf)))

    def __repr__(self):
        return "SizeColumn({0})".format(self.name)

    def __eq__(self, other):
        return isinstance(other, SizeColumn) and self.name == other.name

    def __hash__(self):
        return hash((SizeColumn, self.name))

class TagColumn(Column):
    def __init__(self, name, possibilities):
        super(TagColumn, self).__init__(name, integer(0, len(possibilities)))
        self.possibilities = possibilities

    def __repr__(self):
        return "TagColumn({0}, {1})".format(self.name, self.possibilities)

def schemaToColumns(name, schema, hasSize=False):
    if isinstance(name, string_types):
        name = ColumnName(name)

    if isinstance(schema, Null):
        if hasSize:
            sizeName = name.size()
            return {sizeName: SizeColumn(sizeName)}
        else:
            return {}

    elif isinstance(schema, (Boolean, Number)):
        if hasSize:
            sizeName = name.size()
            return {name: DataColumn(name, schema), sizeName: SizeColumn(sizeName)}
        else:
            return {name: DataColumn(name, schema)}

    elif isinstance(schema, String):
        if not hasSize and schema.charset == "bytes" and schema.fewest == schema.most:
            return {name: DataColumn(name, schema)}
        else:
            sizeName = name.size()
            return {name: DataColumn(name, schema), sizeName: SizeColumn(sizeName)}

    elif isinstance(schema, Collection):
        if schema.fewest != schema.most:
            hasSize = True
        return schemaToColumns(name, schema.items, hasSize)

    elif isinstance(schema, Record):
        out = {}
        for n, t in schema.fields.items():
            out.update(schemaToColumns(name.rec(n), t, hasSize))

        collectiveSize = SizeColumn(name.size())

        def thislevel(name, schema):
            for n, t in schema.fields.items():
                if (isinstance(t, (Null, Boolean, Number)) or (isinstance(t, Union) and all(isinstance(p, Number) for p in t.possibilities))) and \
                       name.rec(n).size() in out:
                    out[name.rec(n).size()] = collectiveSize

                elif isinstance(t, Record):
                    thislevel(name.rec(n), t)

        thislevel(name, schema)

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
                assert False, "missing case: {0} {1} {2}".format(type(x), x, y)
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
                assert False, "missing case: {0} {1}".format(type(c[0]), c)

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
                out.update(schemaToColumns(name.pos(i), p, hasSize))
            return out

    else:
        assert False, "unexpected type: {0} {1}".format(type(schema), schema)

class Statement(Serializable): pass

class Statements(Statement, list):
    def __init__(self, *stmts):
        self.stmts = list(stmts)

    def __repr__(self):
        return "statementlist.Statements({0})".join(", ".join(self.stmts))

    def __str__(self):
        return "\n".join(str(x) for x in self.stmts)

    def toJson(self):
        return [x.toJson() for x in self.stmts]

    def __len__(self):
        return len(self.stmts)

    def __getitem__(self, key):
        return self.stmts[key]

    def __setitem__(self, key, value):
        self.stmts[key] = value

    def __delitem__(self, key):
        del self.stmts[key]

    def __iter__(self):
        return iter(self.stmts)

    def __reversed__(self):
        return Statements(*list(reversed(self.stmts)))

    def __contains__(self, item):
        return item in self.stmts

    def __add__(self, other):
        if isinstance(other, Statements):
            return Statements(*(self.stmts + other.stmts))
        else:
            return Statements(*(self.stmts + other))

    def __radd__(self, other):
        if isinstance(other, Statements):
            return Statements(*(other.stmts + self.stmts))
        else:
            return Statements(*(other + self.stmts))

    def __iadd__(self, other):
        self.stmts += other.stmts

    def __mul__(self, other):
        return Statements(*(self.stmts * other))

    def __rmul__(self, other):
        return Statements(*(other * self.stmts))

    def __imul__(self, other):
        self.stmts *= other

    def append(self, x):
        return self.stmts.append(x)

    def extend(self, x):
        if isinstance(x, Statements):
            return self.stmts.extend(x.stmts)
        else:
            return self.stmts.extend(x)

    def insert(self, i, x):
        return self.stmts.insert(i, x)

    def remove(self, x):
        return self.stmts.remove(x)

    def pop(self, *args):
        return self.stmts.pop(*args)

    def clear(self):
        return self.stmts.clear()

    def index(self, *args):
        return self.stmts.index(*args)

    def count(self, x):
        return self.stmts.count(x)

    def sort(self, *args):
        return self.stmts.sort(*args)

    def reverse(self):
        return self.stmts.reverse()

    def copy(self):
        return self.stmts.copy()

class Ref(Statement):
    def __init__(self, name, schema, data, size):
        self.name = name
        self.schema = schema
        self.data = data
        self.size = size

    def __repr__(self):
        return "statementlist.Ref({0}, {1}, {2}, {3})".format(self.name, self.schema, self.data, self.size)

    def __str__(self):
        if isinstance(self.name, int):
            name = "#" + repr(self.name)
        else:
            name = self.name
        if self.size is None:
            sized = ""
        else:
            sized = ", {0}".format(self.size.name)
        return "Ref({0}{1})".format(name, sized)

    def toJson(self):
        return {"schema": self.schema.toJson(),
                "data": self.data.toJson(),
                "size": None if self.size is None else self.size.toJson()}

    def __eq__(self, other):
        return isinstance(other, Ref) and self.name == other.name and self.schema == other.schema and self.data == other.data and self.size == other.size

    def __hash__(self):
        return hash((Ref, self.name, self.schema, self.data, self.size))

class Literal(Statement):
    def __init__(self, value, schema):
        self.value = value
        self.schema = schema

    def __repr__(self):
        return "statementlist.Literal({0}, {1})".format(self.value, self.schema)

    def __str__(self):
        return repr(self.value)

    def toJson(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value and self.schema == other.schema

    def __hash__(self):
        return hash((Literal, self.value, self.schema))

class Call(Statement):
    def __init__(self, column, fcnname, args):
        self.column = column
        self.fcnname = fcnname
        self.args = tuple(args)

    def __repr__(self):
        return "statementlist.Call({0}, {1}, {2})".format(self.column, self.fcnname, self.args)

    def __str__(self):
        return "{0} := {1}({2})".format(str(self.column), self.fcnname, ", ".join(map(str, self.args)))

    def toJson(self):
        return {"to": self.column.toJson(), "fcn": self.fcnname, "args": [x.toJson() for x in self.args]}

    def __eq__(self, other):
        return isinstance(other, Call) and self.column == other.column and self.fcnname == other.fcnname and self.args == other.args

    def __hash__(self):
        return hash((Call, self.column, self.fcnname, self.args))

class ExplodeSize(Call):
    def __init__(self, column, levels):
        self.column = column
        self.levels = levels

    @property
    def fcnname(self):
        return "explodesize"

    @property
    def args(self):
        return (self.levels,)

    def __repr__(self):
        return "statementlist.ExplodeSize({0}, {1})".format(self.column, self.levels)

    def __str__(self):
        return "{0} := {1}([{2}])".format(str(self.column), self.fcnname, ", ".join(map(str, self.levels)))

    def toJson(self):
        return {"to": self.column.toJson(), "fcn": self.fcnname, "levels": [x.toJson() for x in self.levels]}

class ExplodeData(Call):
    def __init__(self, column, data, size, levels):
        self.column = column
        self.data = data
        self.size = size
        self.levels = levels

    @property
    def fcnname(self):
        return "explodedata"

    @property
    def args(self):
        return (self.data, self.size, self.levels)

    def __repr__(self):
        return "statementlist.ExplodeData({0}, {1}, {2}, {3})".format(self.column, self.data, self.size, self.levels)

    def __str__(self):
        return "{0} := {1}({2}, {3}, [{4}])".format(str(self.column), self.fcnname, str(self.data), str(self.size), ", ".join(map(str, self.levels)))

    def toJson(self):
        return {"to": self.column.toJson(), "fcn": self.fcnname, "data": self.data.toJson(), "size": self.size.toJson(), "levels": [x.toJson() for x in self.levels]}

def exploderef(ref, replacements, refnumber, explosions):
    columnName = ColumnName("#" + repr(refnumber))

    statements = []

    if (ExplodeSize, explosions) in replacements:
        explodedSize = replacements[(ExplodeSize, explosions)]
    else:
        explodedSize = SizeColumn(columnName.size())
        replacements[(ExplodeSize, explosions)] = explodedSize
        statements.append(ExplodeSize(explodedSize, explosions))

    if (ExplodeData, ref.name, explosions) in replacements:
        explodedData = replacements[(ExplodeData, ref.name, explosions)]
    else:
        explodedData = DataColumn(columnName, ref.data.schema)
        replacements[(ExplodeData, ref.name, explosions)] = explodedData
        statements.append(ExplodeData(explodedData, ref.data, ref.size, explosions))

    if len(statements) == 0:
        return ref, [], refnumber
    else:
        return Ref(refnumber, ref.data.schema, explodedData, explodedSize), statements, refnumber + 1

def build(tree, columns, replacements=None, refnumber=0, explosions=()):
    if replacements is None:
        replacements = {}

    if (typedtree.TypedTree, tree) in replacements:
        return replacements[(typedtree.TypedTree, tree)], Statements(), refnumber

    elif isinstance(tree, typedtree.Ref):
        assert tree.framenumber is None, "should not encounter any deep references here"

        dataColumn = None
        sizeColumn = None
        for n, c in columns.items():
            if n.startswith(tree.name):
                if isinstance(c, DataColumn):
                    dataColumn = c
                elif isinstance(c, SizeColumn):
                    sizeColumn = c
        assert dataColumn is not None, "cannot find {0} dataColumn in columns: {1}".format(tree.name, columns.keys())

        ref = Ref(tree.name, tree.schema, dataColumn, sizeColumn)
        replacements[(typedtree.TypedTree, tree)] = ref
        return ref, Statements(), refnumber

    elif isinstance(tree, typedtree.Literal):
        replacements[(typedtree.TypedTree, tree)] = Literal(tree.value, tree.schema)
        return replacements[(typedtree.TypedTree, tree)], Statements(), refnumber

    elif isinstance(tree, typedtree.Call):
        return tree.fcn.buildstatements(tree, columns, replacements, refnumber, explosions)

    else:
        assert False, "unexpected in typedtree: {0}".format(tree)

# mix-in for most BuiltinFunctions
class BuildStatements(object):
    def buildstatements(self, call, columns, replacements, refnumber, explosions):
        args = []
        statements = Statements()
        sizeColumn = None
        for i, arg in enumerate(call.args):
            computed, ss, refnumber = build(arg, columns, replacements, refnumber, explosions)
            statements.extend(ss)

            if len(explosions) > 0:
                final, ss, refnumber = exploderef(computed, replacements, refnumber, explosions)
                statements.extend(ss)
            else:
                final = computed

            if i == 0:
                sizeColumn = final.size
            elif sizeColumn != final.size:
                raise ProgrammingError("all arguments in the default buildStatements must have identical size columns: {0} vs {1}".format(sizeColumn, final.size))

            args.append(final.data)

        columnName = ColumnName("#" + repr(refnumber))
        dataColumn = DataColumn(columnName, call.schema)
                
        ref = Ref(refnumber, call.schema, dataColumn, sizeColumn)

        refnumber += 1
        replacements[(typedtree.TypedTree, call)] = ref

        fcnname, fcnargs = self.kernel(args)
        statements.append(Call(dataColumn, fcnname, fcnargs))

        return ref, statements, refnumber
