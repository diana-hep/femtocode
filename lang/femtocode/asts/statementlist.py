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

class Explode(Call):
    def __init__(self, column, data, size, numLevels):
        self.column = column
        self.data = data
        self.size = size
        self.numLevels = numLevels

    @property
    def fcnname(self):
        return "explode"

    @property
    def args(self):
        return (self.data, self.size, self.numLevels)

    def __repr__(self):
        return "statementlist.Explode({0}, {1}, {2}, {3})".format(self.column, self.data, self.size, self.numLevels)

    def __str__(self):
        return "{0} := {1}({2}, {3}, {4})".format(str(self.column), self.fcnname, str(self.data), str(self.size), self.numLevels)

    def toJson(self):
        return {"to": self.column.toJson(), "fcn": self.fcnname, "data": self.data.toJson(), "size": self.size.toJson(), "numLevels": self.numLevels}

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
    if ref.size is None and len(set(explosions)) == 1:
        statements = []

        if (Explode, ref.name, explosions) in replacements:
            explodedData = replacements[(Explode, ref.name, explosions)]
        else:
            columnName = ColumnName("#" + repr(refnumber))
            explodedData = DataColumn(columnName, ref.data.schema)
            replacements[(Explode, ref.name, explosions)] = explodedData
            statements.append(Explode(explodedData, ref.data, explosions[0], len(explosions)))

        return Ref(refnumber, ref.data.schema, explodedData, explosions[0]), statements, refnumber + 1

    elif set([ref.size]) == set(explosions):
        return ref, [], refnumber

    else:
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
