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

import importlib
import json
import threading

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.dataset import Dataset
from femtocode.defs import *
from femtocode import parser
from femtocode.lib import standard
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.util import *
from femtocode.version import version

class Query(Serializable):
    def __init__(self, dataset, libs, inputs, statements, actions, cancelled, crosscheck):
        self.dataset = dataset
        self.libs = libs
        self.inputs = inputs
        self.statements = statements
        self.actions = actions
        self.cancelled = cancelled
        self.crosscheck = crosscheck

    def __repr__(self):
        return "Query.fromJson({0})".format(self.toJson())

    @property
    def id(self):
        return "{0:016x}".format(hash(self) + 2**63)

    def __eq__(self, other):
        # doesn't include any part of the dataset other than the name, as well as the inputs, cancelled, or crosscheck
        return other.__class__ == Query and self.dataset.name == other.dataset.name and self.libs == other.libs and self.statements == other.statements and self.actions == other.actions

    def __hash__(self):
        # doesn't include any part of the dataset other than the name, as well as the inputs, cancelled, or crosscheck
        if not hasattr(self, "_hash"):
            self._hash = hash(("Query", self.dataset.name, self.libs, self.statements, tuple(self.actions)))
        return self._hash

    class DatasetName(Serializable):
        def __init__(self, name):
            self.name = name

        def toJson(self):
            return {"name": self.name}

        @staticmethod
        def fromJson(obj):
            assert isinstance(obj, dict)
            assert set(obj.keys()).difference(set(["_id"])) == set(["name"])
            return Query.DatasetName(obj["name"])

    def strip(self):
        return Query(self.dataset.strip(), self.libs, self.inputs, self.statements, self.actions, self.cancelled, self.crosscheck)

    def stripToName(self):
        return Query(Query.DatasetName(self.dataset.name), self.libs, self.inputs, self.statements, self.actions, False, self.crosscheck)

    def toJson(self):
        return {"dataset": self.dataset.toJson(),
                "libs": [lib.toJson() for lib in self.libs],
                "inputs": self.inputs,
                "statements": self.statements.toJson(),
                "actions": [action.toJson() for action in self.actions],
                "cancelled": self.cancelled,
                "crosscheck": self.crosscheck.toJson()}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["dataset", "inputs", "statements", "actions", "cancelled", "crosscheck"])

        if set(obj["dataset"].keys()).difference(set(["_id"])) == set(["name"]):
            dataset = Query.DatasetName.fromJson(obj["dataset"])
        else:
            dataset = Dataset.fromJson(obj["dataset"])

        libs = [Library.fromJson(lib) for lib in obj["libs"]]

        statements = statementlist.Statement.fromJson(obj["statements"])
        assert isinstance(statements, statementlist.Statements)

        actions = [statementlist.Statement.fromJson(action) for action in obj["actions"]]
        for action in actions:
            assert isinstance(action, statementlist.Action)
        
        return Query(dataset, libs, obj["inputs"], statements, actions, obj["cancelled"], Workflow.fromJson(obj["crosscheck"]))

class Workflow(Serializable):
    def __init__(self):
        assert False, "{0} is not a concrete class".format(self.__class__.__name__)

    def _compileInScope(self, code, symbolTable, typeTable):
        lt, _ = lispytree.build(parser.parse(code), symbolTable.fork())
        tt, _ = typedtree.build(lt, typeTable.fork())
        return lt, tt

    def _propagated(self, libs=()):
        symbolTable = SymbolTable(standard.table.asdict())
        for lib in libs:
            symbolTable = symbolTable.fork(lib.asdict())

        symbolTable = symbolTable.fork()
        typeTable = SymbolTable()
        for n, t in self.source().dataset.schema.items():
            symbolTable[n] = lispytree.Ref(n)
            typeTable[lispytree.Ref(n)] = t

        preactions = ()
        for step in self.steps():
            symbolTable, typeTable, preactions = step.propagate(symbolTable, typeTable, preactions)

        return symbolTable, typeTable, preactions

    def type(self, expression, libs=()):
        symbolTable, typeTable, preactions = self._propagated(libs)

        expr = parser.parse(expression)

        lt, _ = lispytree.build(expr, symbolTable)
        if isinstance(lt, lispytree.UserFunction):
            raise FemtocodeError("Expression is a user-defined function, which has no type.")

        tt, _ = typedtree.build(lt, typeTable)
        return tt.schema

    def typeString(self, expression, libs=(), highlight=lambda t: "", indent="  ", prefix=""):
        return pretty(self.type(expression, libs), highlight, indent, prefix)

    def typeCompareString(self, expr1, expr2, libs=(), header=None, between=lambda t1, t2: " " if t1 == t2 or t1 is None or t2 is None else ">", indent="  ", prefix="", width=None):
        return compare(self.type(expr1, libs), self.type(expr2, libs), header, between, indent, prefix, width)

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert "class" in obj

        mod = obj["class"][:obj["class"].rindex(".")]
        cls = obj["class"][obj["class"].rindex(".") + 1:]

        return getattr(importlib.import_module(mod), cls).fromJson(obj)

############### NotFirst and NotLast are mixins for all but the Source and all but the Goal
        
class NotFirst(object):
    def __init__(self, source):
        self._source = source

    def source(self):
        return self._source.source()

    def steps(self):
        return self._source.steps() + [self]

    def propagate(self, symbolTable, typeTable, preactions):
        return symbolTable, typeTable, preactions

class NotLast(object):
    # methods for creating all the intermediates and goals

    def define(self, **namesToCode):
        return Define(self, **namesToCode)

    def toPython(self, **namesToCode):
        return ToPython(self, **namesToCode)

############### Source, Intermediate, and Goal are the three types of Workflow transformation

class Source(NotLast, Workflow):
    def __init__(self, session, dataset):
        self.session = session
        self.dataset = dataset

    def source(self):
        return self

    def steps(self):
        return []

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["class"])
        return Source(None, None)

class Intermediate(NotFirst, NotLast, Workflow): pass

class Goal(NotFirst, Workflow):
    def compile(self, libs=()):
        if isinstance(libs, SymbolTable):
            libs = (libs,)

        source = self.source()
        symbolTable, typeTable, preactions = self._propagated(libs)

        replacements = {}
        refnumber = 0
        statements = statementlist.Statements()
        inputs = {}
        actions = []
        for preaction in preactions:
            refs = []
            for tt in preaction.typedTrees():
                ref, ss, ins, refnumber = statementlist.build(tt, source.dataset, replacements, refnumber)
                refs.append(ref)
                statements.extend(ss)
                inputs.update(ins)

            actions.append(preaction.finalize(refs))

        return Query(source.dataset, libs, inputs, statements, actions, False, self)

    def submit(self, ondone=None, onupdate=None, libs=(), debug=False):
        return self.source().session.submit(self.compile(libs), ondone, onupdate, debug)

############### Intermediates

class Define(Intermediate):
    def __init__(self, source, **namesToExprs):
        super(Define, self).__init__(source)
        self.namesToExprs = namesToExprs

    def propagate(self, symbolTable, typeTable, preactions):
        newSymbols = {}
        newTypes = {}
        for name, expr in self.namesToExprs.items():
            lt, tt = self._compileInScope(expr, symbolTable, typeTable)
            newSymbols[name] = lt
            newTypes[lt] = tt.schema

        return symbolTable.fork(newSymbols), typeTable.fork(newTypes), preactions

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "source": self.source.toJson(),
                "namesToExprs": self.namesToExprs}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["class", "source", "namesToExprs"])
        return Define(Workflow.fromJson(obj["source"]), **obj["namesToExprs"])

############### Goals

class ToPython(Goal):
    def __init__(self, source, **namesToExprs):
        super(ToPython, self).__init__(source)
        self.namesToExprs = namesToExprs

    def propagate(self, symbolTable, typeTable, preactions):
        namesToTypedTrees = []
        for name in sorted(self.namesToExprs):
            lt, tt = self._compileInScope(self.namesToExprs[name], symbolTable, typeTable)
            namesToTypedTrees.append((name, tt))

        preactions = preactions + (statementlist.ReturnPythonDataset.Pre("Entry", namesToTypedTrees),)
        return symbolTable, typeTable, preactions

    def toJson(self):
        return {"class": self.__class__.__module__ + "." + self.__class__.__name__,
                "source": self.source.toJson(),
                "namesToExprs": self.namesToExprs}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["class", "source", "namesToExprs"])
        return ToPython(Workflow.fromJson(obj["source"]), **obj["namesToExprs"])
