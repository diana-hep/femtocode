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
import math
import re
import sys
import unittest

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.defs import SymbolTable
from femtocode.execution import Executor
from femtocode.lib.custom import *
from femtocode.parser import parse
from femtocode.testdataset import TestDataset
from femtocode.testdataset import TestSession
from femtocode.typesystem import *
from femtocode.workflow import *

session = TestSession()

numerical = session.source("Test", x=real)
for i in xrange(100):
    numerical.dataset.fill({"x": i * math.pi/2})

class TestLibCustom(unittest.TestCase):
    def runTest(self):
        pass

    def test_mysin(self):
        custom = CustomLibrary()
        custom.add(CustomFlatFunction("mysin", "math", "sin", lambda x: real))

        for entry in numerical.toPython(x = "x", a = "x - 3", b = "mysin(x)").submit(libs=[custom]):
            self.assertAlmostEqual(custom.table["mysin"].pythoneval([entry.x]), entry.b)
            self.assertAlmostEqual(math.sin(entry.x), entry.b)
