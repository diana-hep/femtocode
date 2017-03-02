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

from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.version import version
import femtocode.asts.lispytree as lispytree
import femtocode.asts.statementlist as statementlist
import femtocode.asts.typedtree as typedtree
import femtocode.lib.standard as standard
import femtocode.parser as parser

class Workflow(object):
    def type(self, expression, libs=()):
        symbolTable = SymbolTable(standard.table.asdict())
        for lib in libs:
            symbolTable = symbolTable.fork(libs.asdict())
        symbolTable = symbolTable.fork()
        typeTable = SymbolTable()

        for n, t in self.source().dataset.schema.items():
            symbolTable[n] = lispytree.Ref(n)
            typeTable[lispytree.Ref(n)] = t

        targets, actions, result = (), (), None
        for step in self.steps():
            targets, actions, result, symbolTable = step.propagate(targets, actions, results, symbolTable)

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
        self.source = source

    def source(self):
        return self.source.source()

    def steps(self):
        return self.source.steps() + [self]

    def propagate(self):
        return targets, actions, result, symbolTable

class NotLast(object):
    # and a lot more transformation methods
    def col(self, **namesToCode):
        return Col(self, **namesToCode)

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
        pass

############### Intermediates

class Col(Intermediate):
    def __init__(self, source, **namesToCode):
        super(Col, self).__init__(source)
        self.namesToCode = namesToCode

############### Goals

class TestGoal(Goal):   # temporary
    def __init__(self, var):
        self.var = var
