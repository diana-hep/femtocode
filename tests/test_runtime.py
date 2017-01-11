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

import os.path
import ctypes

from femtocode.compiler import Dataset
from femtocode.typesystem import *

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestRuntime(unittest.TestCase):
    def runTest(self):
        pass

    def test_plus(self):
        self.assertEqual(Dataset(x=integer, y=real).fromPython(x=list(range(10)), y=list(range(0, 1000, 100))).toPython("x + y").run(), [0.0, 101.0, 202.0, 303.0, 404.0, 505.0, 606.0, 707.0, 808.0, 909.0])

    def test_explode(self):
        print Dataset(xss=collection(collection(integer)), ys=collection(integer)).fromPython(xss=[[[100, 200], [300, 400], [500, 600]]], ys=[[1, 2, 3, 4]]).toPython("xss.map(xs => xs.map(x => ys.map(y => x + y)))").run()
