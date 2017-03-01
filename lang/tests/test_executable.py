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
import re
import sys
import unittest

from femtocode.defs import SymbolTable
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.testdataset import TestDataset
from femtocode.typesystem import *
import femtocode.asts.executable as executable
import femtocode.asts.lispytree as lispytree
import femtocode.asts.statementlist as statementlist
import femtocode.asts.typedtree as typedtree

class TestExecutable(unittest.TestCase):
    def runTest(self):
        pass

    def test_compile(self):
        code = "x + y"
        schema = {"x": real, "y": real}
        dataset = TestDataset.fromSchema("Test", schema)
        for i in xrange(100):
            dataset.fill({"x": i + 0.1, "y": i + 1.1})

        lt, frame = lispytree.build(parse(code), table.fork(dict((n, lispytree.Ref(n)) for n in dataset.schema)))
        tt, frame = typedtree.build(lt, SymbolTable(dict((lispytree.Ref(n), t) for n, t in dataset.schema.items())))
        res, ss, _ = statementlist.build(tt, dataset)

        deps = executable.DependencyGraph(res.data, ss, list(schema))
        plan = executable.ExecutionPlan(deps, lambda start, end: False)

        print
        print plan.order
        print plan.tmp
        print dataset.groups[0]
