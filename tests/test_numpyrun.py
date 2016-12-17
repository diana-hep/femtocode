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

import numpy

from femtocode.run.numpyengine import *

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestNumpyRun(unittest.TestCase):
    def runTest(self):
        pass

    def test_cython(self):
        in1 = numpy.array([i/100.0 for i in xrange(100)], dtype=numpy.double)
        in2 = numpy.array([1.0 - i/100.0 for i in xrange(100)], dtype=numpy.double)
        out = numpy.array([999.999 for i in xrange(100)], dtype=numpy.double)
        print
        print in1
        print in2
        print out
        plus(in1, in2, out)
        print out
