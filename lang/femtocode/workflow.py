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
import threading

from femtocode.dataset import Dataset
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.version import version
from femtocode.util import *
import femtocode.asts.lispytree as lispytree
import femtocode.asts.statementlist as statementlist
import femtocode.asts.typedtree as typedtree
import femtocode.lib.standard as standard
import femtocode.parser as parser

class Query(Serializable):
    def __init__(self, dataset, statements, actions):
        self.dataset = dataset
        self.statements = statements
        self.actions = actions

    def __repr__(self):
        return "Query.fromJson({0})".format(self.toJson())

    @property
    def id(self):
        if not hasattr(self, "_id"):
            self._id = "{0:016x}".format(hash(self) + 2**63)
        return self._id

    def __eq__(self, other):
        return other.__class__ == Query and self.dataset == other.dataset and self.statements == other.statements and self.actions == other.actions

    def __hash__(self):
        return hash(("Query", self.dataset, self.statements, tuple(self.actions)))

    def toJson(self):
        return {"dataset": self.dataset.toJson(),
                "statements": self.statements.toJson(),
                "actions": [action.toJson() for action in self.actions]}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()) == set(["dataset", "statements", "actions"])

        dataset = Dataset.fromJson(obj["dataset"])

        statements = statementlist.Statement.fromJson(obj["statements"])
        assert isinstance(statements, statementlist.Statements)

        actions = [statementlist.Statement.fromJson(action) for action in obj["actions"]]
        for action in actions:
            assert isinstance(action, statementlist.Action)

        return Query(dataset, statements, actions)

class Workflow(object):
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

    def typeCompareString(self, expr1, expr2, libs=None, header=None, between=lambda t1, t2: " " if t1 == t2 or t1 is None or t2 is None else ">", indent="  ", prefix="", width=None):
        return compare(self.type(expr1, libs), self.type(expr2, libs), header, between, indent, prefix, width)
    
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

    def toPython(self, datasetName, **namesToCode):
        return ToPython(self, datasetName, **namesToCode)

############### Source, Intermediate, and Goal are the three types of Workflow transformation

class Source(NotLast, Workflow):
    def __init__(self, session, dataset):
        self.session = session
        self.dataset = dataset

    def source(self):
        return self

    def steps(self):
        return []

class Intermediate(NotFirst, NotLast, Workflow): pass

class Goal(NotFirst, Workflow):
    def compile(self, libs=()):
        source = self.source()
        symbolTable, typeTable, preactions = self._propagated(libs)

        replacements = {}
        refnumber = 0
        statements = statementlist.Statements()
        actions = []
        for preaction in preactions:
            refs = []
            for tt in preaction.typedTrees():
                ref, ss, refnumber = statementlist.build(tt, source.dataset, replacements, refnumber)
                statements.extend(ss)
                refs.append(ref)

            actions.append(preaction.finalize(refs))

        return Query(source.dataset, statements, actions)

    def submit(self, callback=None, libs=()):
        return self.source().session.submit(self.compile(libs), callback)

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

############### Goals

class ToPython(Goal):
    def __init__(self, source, datasetName, **namesToExprs):
        super(ToPython, self).__init__(source)
        self.datasetName = datasetName
        self.namesToExprs = namesToExprs

    def propagate(self, symbolTable, typeTable, preactions):
        namesToTypedTrees = []
        for name in sorted(self.namesToExprs):
            lt, tt = self._compileInScope(self.namesToExprs[name], symbolTable, typeTable)
            namesToTypedTrees.append((name, tt))

        preactions = preactions + (statementlist.ReturnPythonDataset.Pre(self.datasetName, namesToTypedTrees),)
        return symbolTable, typeTable, preactions
