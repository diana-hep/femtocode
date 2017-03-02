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

from femtocode.dataset import Dataset
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.version import version
import femtocode.asts.lispytree as lispytree
import femtocode.asts.statementlist as statementlist
import femtocode.asts.typedtree as typedtree
import femtocode.lib.standard as standard
import femtocode.parser as parser

class Query(object):
    def __init__(self, dataset, targets, statements, actions):
        self.dataset = dataset
        self.targets = targets
        self.statements = statements
        self.actions = actions

    def __repr__(self):
        return "<Query on {0} at 0x{1:012x}>".format(self.dataset.name, id(self))

    def toJsonString(self):
        return json.dumps(self.toJson())

    def toJson(self):
        return {"dataset": self.dataset.toJson(),
                "targets": [target.toJson() for target in self.targets],
                "statements": self.statements.toJson(),
                "actions": [action.toJson() for action in self.actions]}

    @staticmethod
    def fromJsonString(string):
        return Query.fromJson(json.loads(string))

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()) == set(["dataset", "targets", "statements", "actions"])

        dataset = Dataset.fromJson(obj["dataset"])
        targets = [statementlist.Statement.fromJson(target) for target in obj["targets"]]
        statements = statementlist.Statement.fromJson(obj["statements"])
        actions = [Action.fromJson(action) for action in obj["actions"]]
        for target in targets:
            assert isinstance(target, statementlist.Ref)
        assert isinstance(statements, statementlist.Statements)

        return Query(dataset, targets, statements, actions)

class Workflow(object):
    def propagated(self, libs=()):
        symbolTable = SymbolTable(standard.table.asdict())
        for lib in libs:
            symbolTable = symbolTable.fork(lib.asdict())

        symbolTable = symbolTable.fork()
        typeTable = SymbolTable()
        for n, t in self.source().dataset.schema.items():
            symbolTable[n] = lispytree.Ref(n)
            typeTable[lispytree.Ref(n)] = t

        actions = ()
        for step in self.steps():
            print symbolTable
            symbolTable, actions = step.propagate(symbolTable, actions)

        return symbolTable, typeTable, actions

    def type(self, expression, libs=()):
        symbolTable, typeTable, actions = self.propagated(libs)

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

    def propagate(self, symbolTable, actions):
        return symbolTable, actions

class NotLast(object):
    # and a lot more transformation methods
    def define(self, **namesToCode):
        return Define(self, **namesToCode)

    def testGoal(self, expression):
        return TestGoal(self, expression)

############### Source, Intermediate, and Goal are the three types of Workflow transformation

class Source(NotLast, Workflow):
    def __init__(self, dataset):
        self.dataset = dataset

    def source(self):
        return self

    def steps(self):
        return []

class Intermediate(NotFirst, NotLast, Workflow): pass

class Goal(NotFirst, Workflow):
    def compile(self, libs=()):
        source = self.source()
        symbolTable, typeTable, actions = self.propagated(libs)
        
        typedtrees = []
        for target in self.targets():
            tt, typeTable = typedtree.build(target, typeTable)
            typedtrees.append(tt)

        replacements = {}
        refnumber = 0
        targets = []
        statements = statementlist.Statements()
        for tt in typedtrees:
            ref, ss, refnumber = statementlist.build(tt, source.dataset, replacements, refnumber)
            targets.append(ref)
            statements.extend(ss)

        return Query(source.dataset, targets, statements, list(actions))

############### Intermediates

class Define(Intermediate):
    def __init__(self, source, **namesToExprs):
        super(Define, self).__init__(source)
        self.namesToExprs = namesToExprs

    def propagate(self, symbolTable, actions):
        newSymbols = {}
        for name, expr in self.namesToExprs.items():
            lt, _ = lispytree.build(parser.parse(expr), symbolTable.fork())
            newSymbols[name] = lt

        return symbolTable.fork(newSymbols), actions

############### Goals

class TestGoal(Goal):   # temporary
    def __init__(self, source, expression):
        super(TestGoal, self).__init__(source)
        self.expression = expression

    def propagate(self, symbolTable, actions):
        lt, _ = lispytree.build(parser.parse(self.expression), symbolTable.fork())
        return symbolTable.fork({"@target": lt})

    def targets(self):
        return [lispytree.Ref("@target")]





###################################

from femtocode.testdataset import TestDataset

schema = {"x": integer, "y": real}
dataset = TestDataset.fromSchema("Test", schema)
for i in xrange(100):
    dataset.fill({"x": i, "y": 0.2})

source = Source(dataset)

print source.typeString("x + 2")
# print source.typeString("z")

intermediate = source.define(z = "x + y")

print intermediate.typeString("z + 2")

goal = source.define(z = "x + y").testGoal("z")
query = goal.compile()
