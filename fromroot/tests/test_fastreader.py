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

import unittest

import numpy

from femtocode.fromroot._fastreader import fillarrays

class TestFastReader(unittest.TestCase):
    def runTest(self):
        pass

    def test_fastReader(self):
        one = numpy.ones(10, dtype=numpy.double) * 1.1
        two = numpy.ones(10, dtype=numpy.uint64) * 2
        print(fillarrays("fileName", "treeName", [("one", one), ("two", two)]))
