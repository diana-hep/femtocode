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

from femtocode.run.numpyengine import *

import sys

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestNumpyEngine(unittest.TestCase):
    def runTest(self):
        pass

    def test_simple1(self):
        self.assertEqual(NumpyDataset(x=integer, y=real).fromPython(x=list(range(10)), y=list(range(0, 1000, 100))).toPython("x + y").run(), [0.0, 101.0, 202.0, 303.0, 404.0, 505.0, 606.0, 707.0, 808.0, 909.0])
