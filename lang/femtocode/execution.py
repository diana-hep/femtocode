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
import sys

from femtocode.asts import statementlist
from femtocode.dataset import ColumnName
from femtocode.lib.standard import table
from femtocode.py23 import *
from femtocode.typesystem import *

class Loop(object):
    def __init__(self, statements):
        self.name = statements[-1].column
        self.statements = statements

        params = set()
        for statement in self.statements:
            for arg in statement.args:
                if isinstance(arg, ColumnName):
                    params.add(arg)

        for statement in self.statements:
            params.discard(statement.column)

        self.params = sorted(params)
        self.tosize = self.statements[-1].tosize

    def __repr__(self):
        return "<Loop of [{0}] at 0x{1:012x}>".format(", ".join([str(x.column) for x in self.statements]), id(self))

    def __str__(self):
        return "\n".join(["Loop {0}({1})".format(self.name, ", ".join(map(str, self.params)))] + ["    " + str(x) for x in self.statements])

class DependencyGraph(object):
    def __init__(self, target, query, lookup, required):
        self.target = target   # ColumnName, could be data or size
        self.query = query
        self.lookup = lookup
        self.lookup[self.target] = self
        self.required = required

        calls = filter(lambda x: isinstance(x, statementlist.Call) and x.column == target, self.query.statements)
        assert len(calls) == 1, "each new column must be defined exactly once"

        self.statement = calls[0]
        self.size = self.statement.tosize

        self.dependencies = []
        for c in self.statement.args:
            if isinstance(c, statementlist.Literal):
                pass

            elif isinstance(c, ColumnName):
                if c in self.query.dataset.columns:
                    self.required.add(c)

                elif c in self.lookup:
                    self.dependencies.append(self.lookup[c])

                else:
                    self.dependencies.append(DependencyGraph(c, self.query, self.lookup, self.required))

            else:
                assert False, "expected only Literals and ColumnNames in args, found {0}".format(c)

    def __repr__(self):
        return "<DependencyGraph of [{0}] at 0x{1:012x}>".format(", ".join(map(str, sorted(self.flattened()))), id(self))

    def pretty(self, indent=""):
        return "\n".join([indent + str(self.statement)] + [x.pretty(indent + "    ") for x in self.dependencies])

    def flattened(self):
        out = set([self.target])
        for x in self.dependencies:
            out.update(x.flattened())
        return out

    def overlap(self, other):
        return len(self.flattened().intersection(other.flattened())) > 0

    @staticmethod
    def cohorts(graphs):
        out = []
        for graph in graphs:
            found = False
            for previous in out:
                if any(graph.overlap(g) for g in previous):
                    previous.append(graph)
                    found = True
                    break
            if not found:
                out.append([graph])
        return out





    # def _samesize(self, size, memo):
    #     if self.target in memo:

    #     if self.size == size:
    #         segment = []
    #         endpoints = []
    #         for x in self.dependencies:
    #             seg, ends = x._samesize(size, memo)
    #             segment.extend(seg)
    #             endpoints.extend(ends)
    #         segment.append(self.statement)
    #         return segment, endpoints
    #     else:
    #         return [], [self]

    # @staticmethod
    # def segments(graphs):
    #     segments = []
    #     for graph in graphs:
    #         for previous in segments:
                













############################

from femtocode.workflow import Query
query = Query.fromJson({'statements': [{'to': '#0', 'args': ['x', 'y'], 'tosize': None, 'fcn': '+', 'schema': 'real'}, {'to': '#1', 'args': ['#0', 999], 'tosize': None, 'fcn': '-', 'schema': 'real'}, {'to': '#2', 'args': ['#0', 0.5], 'tosize': None, 'fcn': '-', 'schema': 'real'}], 'actions': [{'type': 'ReturnPythonDataset', 'targets': [{'size': None, 'data': '#1', 'name': '#1', 'schema': 'real'}, {'size': None, 'data': '#2', 'name': '#2', 'schema': 'real'}], 'structure': {'#2': 'b', '#1': 'a'}}], 'dataset': {'groups': [{'segments': {'y': {'sizeLength': 0, 'numEntries': 100, 'data': [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2], 'dataLength': 100, 'size': None}, 'x': {'sizeLength': 0, 'numEntries': 100, 'data': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99], 'dataLength': 100, 'size': None}}, 'numEntries': 100, 'id': 0}], 'numEntries': 0, 'name': 'Test', 'columns': {'y': {'dataType': 'float', 'data': 'y', 'size': None}, 'x': {'dataType': 'int', 'data': 'x', 'size': None}}, 'schema': {'y': 'real', 'x': 'integer'}}})

lookup = {}
required = set()
graphTargets = {}
for action in query.actions:
    for target in action.targets:
        graphTargets[target.data] = DependencyGraph(target.data, query, lookup, required)

for target, graph in graphTargets.items():
    print graph
    print graph.pretty()




        
class PythonExecutor(object):
    def __init__(self, query):
        self.query = query

    def arrays(self):
        return {}

    def run(self, arrays):
        return None
