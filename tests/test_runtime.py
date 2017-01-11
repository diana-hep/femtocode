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
        self.assertEqual(list(Dataset(x=integer, y=real).fromPython(x=list(range(10)), y=list(range(0, 1000, 100))).toPython("x + y").run()), [0.0, 101.0, 202.0, 303.0, 404.0, 505.0, 606.0, 707.0, 808.0, 909.0])

    def test_explode(self):
        # scala> val xss = List(List(100, 200), List(300, 400), List(500, 600))
        # xss: List[List[Int]] = List(List(100, 200), List(300, 400), List(500, 600))

        # scala> val ys = List(1, 2, 3, 4)
        # ys: List[Int] = List(1, 2, 3, 4)

        # scala> xss.map(xs => xs.map(x => ys.map(y => x + y)))
        # res0: List[List[List[Int]]] = List(List(List(101, 102, 103, 104), List(201, 202, 203, 204)), List(List(301, 302, 303, 304), List(401, 402, 403, 404)), List(List(501, 502, 503, 504), List(601, 602, 603, 604)))
        self.assertEqual(list(Dataset(xss=collection(collection(integer)), ys=collection(integer)).fromPython(xss=[[[100, 200], [300, 400], [500, 600]]], ys=[[1, 2, 3, 4]]).toPython("xss.map(xs => xs.map(x => ys.map(y => x + y)))").run()), [[[[101, 102, 103, 104], [201, 202, 203, 204]], [[301, 302, 303, 304], [401, 402, 403, 404]], [[501, 502, 503, 504], [601, 602, 603, 604]]]])

        # scala> xss.map(xs => ys.map(y => xs.map(x => x + y)))
        # res1: List[List[List[Int]]] = List(List(List(101, 201), List(102, 202), List(103, 203), List(104, 204)), List(List(301, 401), List(302, 402), List(303, 403), List(304, 404)), List(List(501, 601), List(502, 602), List(503, 603), List(504, 604)))
        self.assertEqual(list(Dataset(xss=collection(collection(integer)), ys=collection(integer)).fromPython(xss=[[[100, 200], [300, 400], [500, 600]]], ys=[[1, 2, 3, 4]]).toPython("xss.map(xs => ys.map(y => xs.map(x => x + y)))").run()), [[[[101, 201], [102, 202], [103, 203], [104, 204]], [[301, 401], [302, 402], [303, 403], [304, 404]], [[501, 601], [502, 602], [503, 603], [504, 604]]]])
