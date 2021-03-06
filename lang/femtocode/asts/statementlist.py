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

import ast
import json
import re
import sys

from femtocode.asts import typedtree
from femtocode.dataset import *
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.util import *

class Statement(Serializable):
    @staticmethod
    def fromJson(obj):
        def build(obj, path):
            if obj is None:
                return Literal(None, Null)

            elif isinstance(obj, bool):
                return Literal(obj, Boolean)

            elif isinstance(obj, int):
                return Literal(obj, integer(min=obj, max=obj))

            elif isinstance(obj, float):
                return Literal(obj, real(min=obj, max=obj))

            elif isinstance(obj, list):
                return Statements(*[build(x, path + "[{0}]".format(i)) for i, x in enumerate(obj)])

            elif isinstance(obj, dict):
                keys = set(obj.keys()).difference(set(["_id"]))

                if keys == set(["type", "targets", "structure"]):
                    if not isinstance(obj["type"], string_types):
                        raise FemtocodeError("Expected \"type\" of an action to be a string at JSON{0}\n\n    found {1}".format(path, json.dumps(obj["type"])))

                    if not isinstance(obj["targets"], list):
                        raise FemtocodeError("Expected \"targets\" of an action to be an array at JSON{0}\n\n    found {1}".format(path, json.dumps(obj["targets"])))

                    targets = []
                    for i, target in enumerate(obj["targets"]):
                        target = Statement.fromJson(target)
                        if not isinstance(target, Ref):
                            raise FemtocodeError("Expected all \"targets\" to be Refs at JSON{0}\n\n    found {1}".format(path + "[{0}]".format(i), json.dumps(target)))
                        targets.append(target)

                    return Action.fromJson(obj["type"], targets, obj["structure"], path)

                elif keys == set(["name", "schema", "data", "size"]):
                    return Ref(ColumnName.parse(obj["name"]), Schema.fromJson(obj["schema"]), ColumnName.parse(obj["data"]), None if obj["size"] is None else ColumnName.parse(obj["size"]))

                elif keys == set(["value", "schema"]):
                    return Literal(obj["value"], Schema.fromJson(obj["schema"]))

                elif "fcn" in keys:
                    if obj["fcn"] == "is":
                        if keys == set(["to", "fcn", "tosize", "arg", "fromtype", "totype", "negate"]):
                            return IsType(ColumnName.parse(obj["to"]),
                                          ColumnName.parse(obj["tosize"]),
                                          ColumnName.parse(obj["arg"]),
                                          Schema.fromJson(obj["fromtype"]),
                                          Schema.fromJson(obj["totype"]),
                                          obj["negate"])

                        else:
                            raise FemtocodeError("Expected keys \"to\", \"fcn\", \"tosize\", \"arg\", \"fromtype\", \"totype\", \"negate\" for function \"is\" at JSON{0}\n\n    found {1}".format(path, json.dumps(sorted(keys))))

                    elif obj["fcn"] == "$explode":
                        if keys == set(["to", "fcn", "data", "tosize", "schema"]):
                            return Explode(ColumnName.parse(obj["to"]),
                                           Schema.fromJson(obj["schema"]),
                                           ColumnName.parse(obj["data"]),
                                           ColumnName.parse(obj["tosize"]))   # not nullable
                        else:
                            raise FemtocodeError("Expected keys \"to\", \"fcn\", \"data\", \"tosize\", \"schema\" for function $explode at JSON{0}\n\n    found {1}".format(path, json.dumps(sorted(keys))))

                    elif obj["fcn"] == "$explodesize":
                        if keys == set(["to", "fcn", "explosions"]) and isinstance(obj["explosions"], list):
                            return ExplodeSize(ColumnName.parse(obj["to"]),
                                               tuple(ColumnName.parse(x) for x in obj["explosions"]))
                        else:
                            raise FemtocodeError("Expected keys \"to\", \"fcn\", \"explosions\" with \"explosions\" being a list for function $explodesize at JSON{0}\n\n    found {1}".format(path, json.dumps(sorted(keys))))

                    elif obj["fcn"] == "$explodedata":
                        if keys == set(["to", "fcn", "data", "fromsize", "explodesize", "explosions", "schema"]):
                            return ExplodeData(ColumnName.parse(obj["to"]),
                                               Schema.fromJson(obj["schema"]),
                                               ColumnName.parse(obj["data"]),
                                               ColumnName.parse(obj["fromsize"]),
                                               ColumnName.parse(obj["explodesize"]),
                                               tuple(ColumnName.parse(x) for x in obj["explosions"]))
                        else:
                            raise FemtocodeError("Expected keys \"to\", \"fcn\", \"data\", \"fromsize\", \"explodesize\", \"explosions\", \"schema\" with \"explosions\" being a list for function $explodedata at JSON{0}\n\n    found {1}".format(path, json.dumps(sorted(keys))))

                    elif keys == set(["to", "fcn", "args", "schema", "tosize"]) and isinstance(obj["args"], list):
                        args = []
                        for i, arg in enumerate(obj["args"]):
                            if isinstance(arg, string_types):
                                args.append(ColumnName.parse(arg))
                            else:
                                path = path + "[{0}]".format(i)
                                arg = build(arg, path)
                                if isinstance(arg, Literal):
                                    args.append(arg)
                                else:
                                    raise FemtocodeError("Expected column name or literal at JSON{0}\n\n    found {1}".format(path, arg))

                        return Call(ColumnName.parse(obj["to"]),
                                    Schema.fromJson(obj["schema"]),
                                    None if obj["tosize"] is None else ColumnName.parse(obj["tosize"]),
                                    obj["fcn"],
                                    args)
                        
                    else:
                        raise FemtocodeError("Expected keys \"to\", \"fcn\", \"args\", \"schema\" with \"args\" being a list for function {0} at JSON{1}\n\n    found {2}".format(obj["fcn"], path, json.dumps(sorted(keys))))

            else:
                raise FemtocodeError("Expected list or object at JSON{0}\n\n    found {1}".format(path, json.dumps(obj)))

        return build(obj, "")

class Statements(Statement):
    def __init__(self, *stmts):
        self.stmts = list(stmts)

    def __repr__(self):
        return "statementlist.Statements({0})".format(", ".join(map(repr, self.stmts)))

    def __str__(self):
        if len(self.stmts) > 0:
            return "\n".join(str(x) for x in self.stmts)
        else:
            return "(no statements)"

    def toJson(self):
        return [x.toJson() for x in self.stmts]

    def __getstate__(self):
        return self.stmts

    def __setstate__(self, state):
        self.stmts = state

    def __eq__(self, other):
        return other.__class__ == Statements and self.stmts == other.stmts

    def __hash__(self):
        return hash(("statementlist.Statements", tuple(self.stmts)))

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

    def columnNames(self):
        return sum([x.columnNames() for x in self.stmts], [])

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
        return {"name": str(self.name),
                "schema": self.schema.toJson(),
                "data": str(self.data),
                "size": None if self.size is None else str(self.size)}

    def __eq__(self, other):
        # equality includes the subtype, RefWithExplosions
        return isinstance(other, Ref) and self.name == other.name and self.schema == other.schema and self.data == other.data and self.size == other.size

    def __hash__(self):
        return hash(("statementlist.Ref", self.name, self.schema, self.data, self.size))

    def columnNames(self):
        return [self.name, self.data] + ([] if self.size is None else [self.size])

    def explosions(self):
        if self.size is None:
            return ()
        else:
            return self.explosions()

class RefWithExplosions(Ref):
    def __init__(self, name, schema, data, size, explosions):
        super(RefWithExplosions, self).__init__(name, schema, data, size)
        self._explosions = explosions

    def __repr__(self):
        return "statementlist.RefWithExplosions({0}, {1}, {2}, {3}, {4})".format(self.name, self.schema, self.data, self.size, self._explosions)

    def explosions(self):
        return self._explosions

class Literal(Statement):
    def __init__(self, value, schema):
        self.value = value
        self.schema = schema

    def __repr__(self):
        return "statementlist.Literal({0}, {1})".format(self.value, self.schema)

    def __str__(self):
        return repr(self.value)

    def toJson(self):
        if isinstance(self.schema, Null):
            return None

        elif isinstance(self.schema, Boolean):
            return True if self.value else False

        elif isinstance(self.schema, Number) and self.schema.whole:
            return int(self.value)

        elif isinstance(self.schema, Number):
            return float(self.value)

        else:
            return {"value": self.value, "schema": self.schema.toJson()}

    def __eq__(self, other):
        return other.__class__ == Literal and self.value == other.value and self.schema == other.schema

    def __hash__(self):
        return hash(("statementlist.Literal", self.value, self.schema))

    def columnNames(self):
        return []

    def buildexec(self):
        if isinstance(self.schema, Null):
            if sys.version_info[0] <= 2:
                return ast.Name("None", ast.Load())
            else:
                return ast.NameConstant(None)

        elif isinstance(self.schema, Boolean):
            if sys.version_info[0] <= 2:
                if self.value:
                    return ast.Name("True", ast.Load())
                else:
                    return ast.Name("False", ast.Load())
            else:
                if self.value:
                    return ast.NameConstant(True)
                else:
                    return ast.NameConstant(False)

        elif isinstance(self.schema, Number):
            return ast.Num(self.value)

        else:
            raise NotImplementedError   # have to think about this when the case comes up

class Call(Statement):
    def __init__(self, column, schema, tosize, fcnname, args):
        self.column = column
        self.schema = schema
        self.tosize = tosize
        self.fcnname = fcnname
        self.args = tuple(args)

    def __repr__(self):
        return "statementlist.Call({0}, {1}, {2}, {3}, {4})".format(self.column, self.schema, self.tosize, self.fcnname, self.args)

    def __str__(self):
        return "{0} := {1}({2}) as {3} sized by {4}".format(str(self.column), self.fcnname, ", ".join(map(str, self.args)), self.schema, self.tosize)

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "args": [str(x) if isinstance(x, ColumnName) else x.toJson() for x in self.args], "schema": self.schema.toJson(), "tosize": None if self.tosize is None else str(self.tosize)}

    def __eq__(self, other):
        return other.__class__ == Call and self.column == other.column and self.schema == other.schema and self.tosize == other.tosize and self.fcnname == other.fcnname and self.args == other.args

    def __hash__(self):
        return hash(("statementlist.Call", self.column, self.schema, self.tosize, self.fcnname, self.args))

    def columnNames(self):
        return [self.column] + list(self.args) + ([] if self.tosize is None else [self.tosize])

    def inputSizes(self, statements):
        return [] if self.tosize is None else [self.tosize]

    def plateauSize(self, statements):
        return self.tosize

class IsType(Call):
    def __init__(self, column, tosize, arg, fromtype, totype, negate):
        self.column = column
        self.tosize = tosize
        self.arg = arg
        self.fromtype = fromtype
        self.totype = totype
        self.negate = negate

    @property
    def fcnname(self):
        return "is"

    @property
    def schema(self):
        return boolean

    @property
    def args(self):
        return (self.arg,)

    def __repr__(self):
        return "statementlist.TypeCheck({0}, {1}, {2}, {3}, {4}, {5})".format(self.column, self.tosize, self.arg, self.fromtype, self.totype, self.negate)

    def __str__(self):
        return "{0} := {1}({2}, {3} -> {4}{5}) as {6}".format(str(self.column), self.fcnname, self.arg, self.fromtype, self.totype, " (negated)" if self.negate else "", self.schema)

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "tosize": str(self.tosize), "arg": str(self.arg), "fromtype": self.fromtype.toJson(), "totype": self.totype.toJson(), "negate": self.negate}

    def __eq__(self, other):
        return other.__class__ == IsType and self.column == other.column and self.tosize == other.tosize and self.arg == other.arg and self.fromtype == other.fromtype and self.totype == other.totype and self.negate == other.negate

    def __hash__(self):
        return hash(("statementlist.IsType", self.column, self.tosize, self.arg, self.fromtype, self.totype, self.negate))

    def columnNames(self):
        return [self.column, self.tosize, self.arg]

    def inputSizes(self, statements):
        return [self.tosize]

    def plateauSize(self, statements):
        return self.tosize

class Explode(Call):
    def __init__(self, column, schema, data, tosize):
        self.column = column
        self.schema = schema
        self.data = data
        self.tosize = tosize

    @property
    def fcnname(self):
        return "$explode"

    @property
    def args(self):
        return (self.data, self.tosize)

    def __repr__(self):
        return "statementlist.Explode({0}, {1}, {2}, {3})".format(self.column, self.schema, self.data, self.tosize)

    def __str__(self):
        return "{0} := {1}({2}, {3}) as {4}".format(str(self.column), self.fcnname, str(self.data), str(self.tosize), self.schema)

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "data": str(self.data), "tosize": str(self.tosize), "schema": self.schema.toJson()}

    def __eq__(self, other):
        return other.__class__ == Explode and self.column == other.column and self.schema == other.schema and self.data == other.data and self.tosize == other.tosize

    def __hash__(self):
        return hash(("statementlist.Explode", self.column, self.schema, self.data, self.tosize))

    def columnNames(self):
        return [self.column, self.data, self.tosize]

    def inputSizes(self, statements):
        return [self.tosize]

    def plateauSize(self, statements):
        return self.tosize

class ExplodeSize(Call):
    def __init__(self, column, explosions):
        self.column = column
        self.explosions = tuple(explosions)

    @property
    def fcnname(self):
        return "$explodesize"

    @property
    def args(self):
        return (self.explosions,)

    def __repr__(self):
        return "statementlist.ExplodeSize({0}, {1})".format(self.column, self.explosions)

    def __str__(self):
        return "{0} := {1}({2})".format(str(self.column), self.fcnname, ", ".join(map(str, self.explosions)))

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "explosions": [str(x) for x in self.explosions]}

    def __eq__(self, other):
        return other.__class__ == ExplodeSize and self.column == other.column and self.explosions == other.explosions

    def __hash__(self):
        return hash(("statementlist.ExplodeSize", self.column, self.explosions))

    def columnNames(self):
        return [self.column]

    def inputSizes(self, statements):
        return list(self.explosions)

    def plateauSize(self, statements):
        return self.column

class ExplodeData(Call):
    def __init__(self, column, schema, data, fromsize, explodesize, explosions):
        self.column = column
        self.schema = schema
        self.data = data
        self.fromsize = fromsize
        self.explodesize = explodesize
        self.explosions = explosions

    @property
    def fcnname(self):
        return "$explodedata"

    @property
    def args(self):
        return (self.data, self.fromsize, self.explodesize)

    def __repr__(self):
        return "statementlist.ExplodeData({0}, {1}, {2}, {3}, {4}, {5})".format(self.column, self.schema, self.data, self.fromsize, self.explodesize, self.explosions)

    def __str__(self):
        return "{0} := {1}({2}, {3}, {4}, ({5})) as {6}".format(str(self.column), self.fcnname, str(self.data), str(self.fromsize), self.explodesize, ", ".join(map(str, self.explosions)), self.schema)

    def toJson(self):
        return {"to": str(self.column), "fcn": self.fcnname, "data": str(self.data), "fromsize": str(self.fromsize), "explodesize": str(self.explodesize), "explosions": [str(x) for x in self.explosions], "schema": self.schema.toJson()}

    def __eq__(self, other):
        return other.__class__ == ExplodeData and self.column == other.column and self.schema == other.schema and self.data == other.data and self.fromsize == other.fromsize and self.explodesize == other.explodesize and self.explosions == other.explosions

    def __hash__(self):
        return hash(("statementlist.ExplodeData", self.column, self.schema, self.data, self.fromsize, self.explodesize, self.explosions))

    def columnNames(self):
        return [self.column, self.data, self.fromsize, self.explodesize]

    def inputSizes(self, statements):
        for statement in statements:
            if isinstance(statement, ExplodeSize) and statement.column == self.explodesize:
                return [self.fromsize] + list(statement.explosions) + list(self.explosions)
        assert False, "explodesize not found for explodedata"

    def plateauSize(self, statements):
        for statement in statements:
            if isinstance(statement, ExplodeSize) and statement.column == self.explodesize:
                return statement.plateauSize(statements)
        assert False, "explodesize not found for explodedata"

def exploderef(ref, replacements, refnumber, dataset, explosions):
    if len(explosions) == 0 or progressionOf(explosions, ref.size):
        return ref, Statements(), replacements, refnumber

    elif ref.size is None:
        statements = []

        if progression(explosions):
            explodedSize = explosions[-1].size()

            if (Explode, ref.name, explodedSize) in replacements:
                explodedData = replacements[(Explode, ref.name, explodedSize)]
            else:
                explodedData = ColumnName(refnumber)
                replacements[(Explode, ref.name, explodedSize)] = explodedData
                statements.append(Explode(explodedData, ref.schema, ref.data, explodedSize))

        else:
            if (ExplodeSize, explosions) in replacements:
                explodedSize = replacements[(ExplodeSize, explosions)]
            else:
                explodedSize = ColumnName(refnumber).size()
                replacements[(ExplodeSize, explosions)] = explodedSize
                statements.append(ExplodeSize(explodedSize, explosions))

            if (Explode, ref.name, explodedSize) in replacements:
                explodedData = replacements[(Explode, ref.name, explodedSize)]
            else:
                explodedData = ColumnName(refnumber)
                replacements[(Explode, ref.name, explodedSize)] = explodedData
                statements.append(Explode(explodedData, ref.schema, ref.data, explodedSize))

        return RefWithExplosions(refnumber, ref.schema, explodedData, explodedSize, explosions), statements, replacements, refnumber + 1

    else:
        statements = []

        if (ExplodeSize, explosions) in replacements:
            explodedSize = replacements[(ExplodeSize, explosions)]
        else:
            explodedSize = ColumnName(refnumber).size()
            replacements[(ExplodeSize, explosions)] = explodedSize
            statements.append(ExplodeSize(explodedSize, explosions))

        if (ExplodeData, ref.name, explosions, ref.explosions()) in replacements:
            explodedData = replacements[(ExplodeData, ref.name, explosions, ref.explosions())]
        elif ref.size != explodedSize:
            explodedData = ColumnName(refnumber)
            replacements[(ExplodeData, ref.name, explosions, ref.explosions())] = explodedData
            statements.append(ExplodeData(explodedData, ref.schema, ref.data, ref.size, explodedSize, ref.explosions()))

        else:
            explodedData = ref.data

        return RefWithExplosions(refnumber, ref.schema, explodedData, explodedSize, explosions), statements, replacements, refnumber + 1

def startswith(a, b):
    return len(a) >= len(b) and a[:len(b)] == b

def build(tree, dataset, replacements={}, refnumber=0, explosions=()):
    if (typedtree.TypedTree, tree) in replacements:
        for exp, ref in replacements[(typedtree.TypedTree, tree)].items():
            if startswith(explosions, exp):
                return ref, Statements(), {}, replacements, refnumber

    if isinstance(tree, typedtree.Ref):
        assert tree.framenumber is None, "should not encounter any deep references here"

        ref = Ref(tree.name, tree.schema, dataset.dataColumn(tree.name), dataset.sizeColumn(tree.name))
        replacements[(typedtree.TypedTree, tree)] = replacements.get((typedtree.TypedTree, tree), {})
        replacements[(typedtree.TypedTree, tree)][explosions] = ref
        if ref.data in dataset.columns:
            inputs = {ref.data: tree.schema}
        else:
            inputs = {}
        if ref.size is not None:
            for c in dataset.columns.values():
                if ref.size == c.size:
                    inputs[ref.size] = None

        return ref, Statements(), inputs, replacements, refnumber

    elif isinstance(tree, typedtree.Literal):
        literal = Literal(tree.value, tree.schema)
        replacements[(typedtree.TypedTree, tree)] = replacements.get((typedtree.TypedTree, tree), {})
        replacements[(typedtree.TypedTree, tree)][explosions] = literal
        return literal, Statements(), {}, replacements, refnumber

    elif isinstance(tree, typedtree.Call):
        return tree.fcn.buildstatements(tree, dataset, dict(replacements), refnumber, explosions)

    else:
        assert False, "unexpected type in typedtree: {0}".format(tree)

class FlatFunction(object):
    def _buildstatements_args(self, call):
        return call.args

    def _buildstatements_build(self, columnName, schema, sizeColumn, args, call):
        return Call(columnName, schema, sizeColumn, self.name, args)

    def buildstatements(self, call, dataset, replacements, refnumber, explosions):
        statements = Statements()
        inputs = {}
        argrefs = []
        for arg in self._buildstatements_args(call):
            argref, ss, ins, repl, refnumber = build(arg, dataset, dict(replacements), refnumber, explosions)
            argrefs.append(argref)
            statements.extend(ss)
            inputs.update(ins)
            replacements.update(repl)

        argexplosions = set(x.explosions() for x in argrefs if isinstance(x, Ref))
        argsizes = set(x.size for x in argrefs if isinstance(x, Ref))

        if len(argexplosions) == 1 and len(argsizes) == 1:
            passexp = list(argexplosions)[0]
            sizeColumn = list(argsizes)[0]

            columnName = ColumnName(refnumber)
            ref = RefWithExplosions(refnumber, call.schema, columnName, sizeColumn, passexp)

            refnumber += 1
            replacements[(typedtree.TypedTree, call)] = replacements.get((typedtree.TypedTree, call), {})
            replacements[(typedtree.TypedTree, call)][passexp] = ref
            statements.append(self._buildstatements_build(columnName, ref.schema, sizeColumn, [arg.data if isinstance(arg, Ref) else arg for arg in argrefs], call))

        else:
            args = []
            sizeColumnAssigned = False
            sizeColumn = None
            for argref in argrefs:
                if isinstance(argref, Ref):
                    final, ss, repl, refnumber = exploderef(argref, dict(replacements), refnumber, dataset, explosions)
                    statements.extend(ss)
                    replacements.update(repl)

                    if not sizeColumnAssigned:
                        sizeColumnAssigned = True
                        sizeColumn = final.size
                    else:
                        assert sizeColumn == final.size, "all arguments in a flat function must have identical size columns: {0} vs {1}".format(sizeColumn, final.size)

                    args.append(final.data)

                elif isinstance(argref, Literal):
                    args.append(argref)

                else:
                    assert False, "unexpected in argrefs: {0}".format(argref)

            columnName = ColumnName(refnumber)
            ref = RefWithExplosions(refnumber, call.schema, columnName, sizeColumn, explosions)

            refnumber += 1
            replacements[(typedtree.TypedTree, call)] = replacements.get((typedtree.TypedTree, call), {})
            replacements[(typedtree.TypedTree, call)][explosions] = ref
            statements.append(self._buildstatements_build(columnName, ref.schema, sizeColumn, args, call))

        return ref, statements, inputs, replacements, refnumber

class Action(Statement):
    @property
    def type(self):
        return self.__class__.__name__

    def __repr__(self):
        return "statementlist.Action.fromJson({0})".format(json.dumps(self.toJson()))

    def toJson(self):
        return {"type": self.type,
                "targets": [target.toJson() for target in self.targets],
                "structure": self.structure}

    def __eq__(self, other):
        return isinstance(other, Action) and self.type == other.type and self.targets == other.targets and self.structure == other.structure

    def __hash__(self):
        def hashready(x):
            if isinstance(x, dict):
                return tuple(sorted((hashready(k), hashready(v)) for k, v in x.items()))
            elif isinstance(x, list):
                return tuple(hashready(y) for y in x)
            else:
                return x

        return hash(("statementlist.Action", self.type, tuple(self.targets), hashready(self.structure)))

    @staticmethod
    def fromJson(tpe, targets, structure, path):
        if tpe == "ReturnPythonDataset":
            return ReturnPythonDataset.fromJson(targets, structure)
        else:
            raise FemtocodeError("Unrecognized action \"{0}\" at JSON{1}".format(tpe, path))
    
    def act(self, group, columns, columnLengths, lengths, arrays):
        raise NotImplementedError

class Aggregation(Action):
    def initialize(self):
        raise NotImplementedError

    def update(self, tally, subtally):
        raise NotImplementedError

class ReturnPythonDataset(Aggregation):
    class Pre(object):
        def __init__(self, datasetName, namesToTypedTrees):
            self.datasetName = datasetName
            self.namesToTypedTrees = namesToTypedTrees

        def typedTrees(self):
            return [tt for n, tt in self.namesToTypedTrees]

        def finalize(self, refs):
            return ReturnPythonDataset(self.datasetName, [(n, ref) for ref, (n, tt) in zip(refs, self.namesToTypedTrees)])

    class Segments(Serializable):
        def __init__(self, segs):
            self.segs = segs

        def toJson(self):
            return {"segs": dict((str(k), v.toJson()) for k, v in self.segs.items())}

        @staticmethod
        def fromJson(obj):
            from femtocode.testdataset import TestSegment
            return ReturnPythonDataset.Segments(dict((ColumnName.parse(k), TestSegment.fromJson(v)) for k, v in obj["segs"].items()))

    def tallyFromJson(self, obj):
        from femtocode.testdataset import TestDataset
        if "segs" in obj:
            return ReturnPythonDataset.Segments.fromJson(obj)
        else:
            return TestDataset.fromJson(obj)

    @staticmethod
    def fromJson(targets, structure):
        return ReturnPythonDataset(
            structure["datasetName"],
            [(structure["refsToNames"][ref.name], ref) for ref in targets])

    def __init__(self, datasetName, namesToRefs):
        self.datasetName = datasetName
        self.namesToRefs = namesToRefs

    @property
    def targets(self):
        return [r for n, r in self.namesToRefs]

    @property
    def structure(self):
        return {"datasetName": self.datasetName,
                "refsToNames": dict((str(r.name), n) for n, r in self.namesToRefs)}

    def columns(self):
        return [r.size for n, r in self.namesToRefs if isinstance(r, Ref) and r.size is not None] + [r.data for n, r in self.namesToRefs if isinstance(r, Ref)]

    def columnNames(self):
        return sum([x.columnNames() for x in self.namesToRefs.values()], [])

    def initialize(self):
        from femtocode.testdataset import TestDataset
        schema = dict((n, r.schema) for n, r in self.namesToRefs)
        return TestDataset.fromSchema(self.datasetName, **schema)

    def update(self, tally, subtally):
        numEntries = None
        for segment in subtally.segs.values():
            if numEntries is None:
                numEntries = segment.numEntries
            else:
                assert numEntries == segment.numEntries
        assert numEntries is not None

        tally.newGroup()
        tally.groups[-1].segments = subtally.segs
        tally.groups[-1].numEntries = numEntries

        tally.numEntries = sum(group.numEntries for group in tally.groups)
        return tally

    def act(self, group, columns, columnLengths, lengths, arrays):
        from femtocode.testdataset import TestSegment

        segments = {}
        for name, ref in self.namesToRefs:
            if not isinstance(name, ColumnName):
                name = ColumnName(name)

            for n, outputColumn in schemaToColumns(name, ref.schema, False).items():
                numEntries = group.numEntries
                dataLength, sizeLength = columnLengths[ref.size]
                data = arrays[ref.data]
                size = arrays[ref.size] if ref.size is not None else None

                if not isinstance(data, list):
                    data = data.tolist()   # because it's Numpy
                if size is not None and not isinstance(size, list):
                    size = size.tolist()   # because it's Numpy

                segments[n] = TestSegment(numEntries, dataLength, sizeLength, data, size)

        return ReturnPythonDataset.Segments(segments)
