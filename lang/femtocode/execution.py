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

# from femtocode.workflow import Query
# query = Query.fromJson({'statements': [{'to': '#0', 'args': ['x', 'y', '1'], 'tosize': None, 'fcn': '+', 'schema': 'real'}, {'to': '#1', 'args': ['x', 'y'], 'tosize': None, 'fcn': '+', 'schema': 'real'}, {'to': '#2', 'args': ['#1', '1'], 'tosize': None, 'fcn': '-', 'schema': 'real'}], 'actions': [{'type': 'ReturnPythonDataset', 'targets': [{'size': None, 'data': '#0', 'name': '#0', 'schema': 'real'}, {'size': None, 'data': '#2', 'name': '#2', 'schema': 'real'}], 'structure': {'#2': 'b', '#0': 'a'}}], 'dataset': {'groups': [{'segments': {'y': {'sizeLength': 0, 'numEntries': 100, 'data': [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2], 'dataLength': 100, 'size': None}, 'x': {'sizeLength': 0, 'numEntries': 100, 'data': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99], 'dataLength': 100, 'size': None}}, 'numEntries': 100, 'id': 0}], 'numEntries': 0, 'name': 'Test', 'columns': {'y': {'dataType': 'float', 'data': 'y', 'size': None}, 'x': {'dataType': 'int', 'data': 'x', 'size': None}}, 'schema': {'y': 'real', 'x': 'integer'}}})

class DependencyGraph(object):
    def __init__(self, target, query, lookup):
        self.target = target   # ColumnName, could be data or size
        self.query = query
        self.lookup = lookup
        self.lookup[self.target] = self

        calls = filter(lambda x: isinstance(x, statementlist.Call) and x.column == target, self.query.statements)

        self.dependencies = []
        self.statement = None
        self.size = None

        if len(calls) == 0:
            assert self.target in self.query.dataset.columns, "statement refers to unknown column {0}".format(self.target)
            self.size = self.query.dataset.sizeColumn(self.target)

        elif len(calls) == 1:
            self.statement = calls[0]
            self.size = self.statement.tosize

            for c in self.statement.args:
                if c in self.lookup:
                    self.dependencies.append(self.lookup[c])
                else:
                    self.dependencies.append(DependencyGraph(c, self.query, self.lookup))

        else:
            assert False, "each new column must be defined exactly once"

    def pretty(self, indent=""):
        return "\n".join([indent + (str(self.target) + " sized by " + str(self.size)) if self.statement is None else str(self.statement)] + [x.pretty(indent + "    ") for x in self.dependencies])

# lookup = {}
# dg = DependencyGraph(ColumnName("#0"), query, lookup)
# print dg.pretty()




        
class PythonExecutor(object):
    def __init__(self, query):
        self.query = query

    def arrays(self):
        return {}

    def run(self, arrays):
        return None
