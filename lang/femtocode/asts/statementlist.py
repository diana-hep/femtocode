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
from femtocode.dataset import *

class Serializable(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

class Statement(Serializable): pass

class Statements(Statement, list):
    def __init__(self, *stmts):
        self.stmts = list(stmts)

    def __repr__(self):
        return "statementlist.Statements({0})".format(", ".join(map(repr, self.stmts)))

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
        if isinstance(name, ColumnName):
            self.name = name
        else:
            self.name = ColumnName(name)
        self.schema = schema
        self.data = data
        self.size = size

    def __repr__(self):
        return "statementlist.Ref({0}, {1}, {2}, {3})".format(self.name, self.schema, self.data, self.size)

    def toJson(self):
        return {"schema": self.schema.toJson(),
                "data": str(self.data),
                "size": None if self.size is None else str(self.size)}

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
        return {"value": self.value, "schema": self.schema.toJson()}

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
        return {"to": str(self.column), "fcn": self.fcnname, "args": [str(x) for x in self.args]}

    def __eq__(self, other):
        return isinstance(other, Call) and self.column == other.column and self.fcnname == other.fcnname and self.args == other.args

    def __hash__(self):
        return hash((Call, self.column, self.fcnname, self.args))

class Explode(Call):
    def __init__(self, column, data, size):
        self.column = column
        self.data = data
        self.size = size

    @property
    def fcnname(self):
        return "$explode"

    @property
    def args(self):
        return (self.data, self.size)

    def __repr__(self):
        return "statementlist.Explode({0}, {1}, {2})".format(self.column, self.data, self.size)

    def __str__(self):
        return "{0} := {1}({2}, {3})".format(str(self.column), self.fcnname, str(self.data), str(self.size))

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "data": str(self.data), "size": str(self.size)}

class ExplodeSize(Call):
    def __init__(self, column, levels):
        self.column = column
        self.levels = levels

    @property
    def fcnname(self):
        return "$explodesize"

    @property
    def args(self):
        return (self.levels,)

    def __repr__(self):
        return "statementlist.ExplodeSize({0}, {1})".format(self.column, self.levels)

    def __str__(self):
        return "{0} := {1}([{2}])".format(str(self.column), self.fcnname, ", ".join(map(str, self.levels)))

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "levels": [str(x) for x in self.levels]}

class ExplodeData(Call):
    def __init__(self, column, data, size, levels):
        self.column = column
        self.data = data
        self.size = size
        self.levels = levels

    @property
    def fcnname(self):
        return "$explodedata"

    @property
    def args(self):
        return (self.data, self.size, self.levels)

    def __repr__(self):
        return "statementlist.ExplodeData({0}, {1}, {2}, {3})".format(self.column, self.data, self.size, self.levels)

    def __str__(self):
        return "{0} := {1}({2}, {3}, [{4}])".format(str(self.column), self.fcnname, str(self.data), str(self.size), ", ".join(map(str, self.levels)))

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "data": str(self.data), "size": str(self.size), "levels": [str(x) for x in self.levels]}

def exploderef(ref, replacements, refnumber, dataset, sizes):
    if len(sizes) == 0:
        return ref, Statements(), refnumber

    elif ref.size is None and len(sizes) == 1:
        statements = []

        if (Explode, ref.name, sizes) in replacements:
            explodedData = replacements[(Explode, ref.name, sizes)]
        else:
            explodedData = ColumnName(refnumber)
            replacements[(Explode, ref.name, sizes)] = explodedData
            statements.append(Explode(explodedData, ref.data, sizes[0]))

        return Ref(refnumber, ref.schema, explodedData, sizes[0]), statements, refnumber + 1

    elif set([ref.size]) == set(sizes):
        return ref, [], refnumber

    else:
        statements = []

        if (ExplodeSize, sizes) in replacements:
            explodedSize = replacements[(ExplodeSize, sizes)]
        else:
            explodedSize = ColumnName(refnumber).size()
            replacements[(ExplodeSize, sizes)] = explodedSize
            statements.append(ExplodeSize(explodedSize, sizes))

        if (ExplodeData, ref.name, sizes) in replacements:
            explodedData = replacements[(ExplodeData, ref.name, sizes)]
        else:
            explodedData = ColumnName(refnumber)
            replacements[(ExplodeData, ref.name, sizes)] = explodedData
            statements.append(ExplodeData(explodedData, ref.data, ref.size, sizes))

        return Ref(refnumber, ref.schema, explodedData, explodedSize), statements, refnumber + 1

def build(tree, dataset, replacements=None, refnumber=0, explosions=()):
    if replacements is None:
        replacements = {}

    if (typedtree.TypedTree, tree) in replacements:
        return replacements[(typedtree.TypedTree, tree)], Statements(), refnumber

    elif isinstance(tree, typedtree.Ref):
        assert tree.framenumber is None, "should not encounter any deep references here"

        ref = Ref(tree.name, tree.schema, dataset.dataColumn(tree.name), dataset.sizeColumn(tree.name))
        replacements[(typedtree.TypedTree, tree)] = ref
        return ref, Statements(), refnumber

    elif isinstance(tree, typedtree.Literal):
        replacements[(typedtree.TypedTree, tree)] = Literal(tree.value, tree.schema)
        return replacements[(typedtree.TypedTree, tree)], Statements(), refnumber

    elif isinstance(tree, typedtree.Call):
        return tree.fcn.buildstatements(tree, dataset, replacements, refnumber, explosions)

    else:
        assert False, "unexpected type in typedtree: {0}".format(tree)

class FlatFunction(object):
    def buildstatements(self, call, dataset, replacements, refnumber, explosions):
        statements = Statements()
        argrefs = []
        for arg in call.args:
            argref, ss, refnumber = build(arg, dataset, replacements, refnumber, explosions)
            statements.extend(ss)
            argrefs.append(argref)

        sizes = []
        for explosion in explosions:
            size = None
            for argref in argrefs:
                if isinstance(explosion.schema, Record) and explosion.name.path == argref.data.path[:-1]:
                    size = dataset.sizeColumn(argref.data)
                    break
            if size is None:
                size = dataset.sizeColumn(explosion.name)
            if size is not None:
                sizes.append(size)
        sizes = tuple(sizes)

        args = []
        sizeColumn = None
        for i, argref in enumerate(argrefs):
            final, ss, refnumber = exploderef(argref, replacements, refnumber, dataset, sizes)
            statements.extend(ss)

            if i == 0:
                sizeColumn = final.size
            else:
                assert sizeColumn == final.size, "all arguments in a flat function must have identical size columns: {0} vs {1}".format(sizeColumn, final.size)

            args.append(final.data)

        columnName = ColumnName(refnumber)
        ref = Ref(refnumber, call.schema, columnName, sizeColumn)

        refnumber += 1
        replacements[(typedtree.TypedTree, call)] = ref
        statements.append(Call(columnName, self.name, args))

        return ref, statements, refnumber
