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
            dataset.fill({"x": i, "y": 0.2})

        group = dataset.groups[0]

        lt, frame = lispytree.build(parse(code), table.fork(dict((n, lispytree.Ref(n)) for n in dataset.schema)))
        tt, frame = typedtree.build(lt, SymbolTable(dict((lispytree.Ref(n), t) for n, t in dataset.schema.items())))
        goal, ss, _ = statementlist.build(tt, dataset)

        executor = executable.Executor(goal, list(schema), ss, lambda start, end: False)
        executor.compilePython()

        # do sizes first, which provide input to dataLengths
        dataLengths = executor.dataLengths(dataset, group)

        arrays = {}
        for name in executor.inputs:    # make sure there are no size columns in this loop!
            assert not name.issize()
            arrays[name] = group.segments[name].data

        data, size = executor.run(arrays, dataLengths)

        print
        print data
        print size
