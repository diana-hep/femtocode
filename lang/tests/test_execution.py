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
from femtocode.execution import Executor
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.testdataset import TestDataset
from femtocode.testdataset import TestSession
from femtocode.typesystem import *
import femtocode.asts.lispytree as lispytree
import femtocode.asts.statementlist as statementlist
import femtocode.asts.typedtree as typedtree

class TestExecution(unittest.TestCase):
    def runTest(self):
        pass

    def test_submit(self):
        session = TestSession()

        source = session.source("Test", x=integer, y=real)
        for i in xrange(100):
            source.dataset.fill({"x": i, "y": 0.2})

        sink = source.define(z = "x + y").toPython("Test", a = "z - 3", b = "z - 0.5").submit()

        self.assertEqual(source.dataset.numEntries, sink.numEntries)

        for old, new in zip(source.dataset, sink):
            self.assertAlmostEqual(old.x + old.y - 3, new.a)
            self.assertAlmostEqual(old.x + old.y - 0.5, new.b)
