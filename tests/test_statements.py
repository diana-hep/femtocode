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

from femtocode.typesystem import *
from femtocode.asts.statementlist import *

import sys

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestStatements(unittest.TestCase):
    def runTest(self):
        pass

    def test_schemaToColumns(self):
        self.assertEqual(schemaToColumns("x", null), {})
        self.assertEqual(schemaToColumns("x", boolean), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", integer), {"x": Column("x", integer, None)})
        self.assertEqual(schemaToColumns("x", real), {"x": Column("x", real, None)})
        self.assertEqual(schemaToColumns("x", extended), {"x": Column("x", extended, None)})
        self.assertEqual(schemaToColumns("x", string), {"x": Column("x", string, Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", string("bytes", 5, 5)), {"x": Column("x", string("bytes", 5, 5), None)})
        self.assertEqual(schemaToColumns("x", string("unicode", 5, 5)), {"x": Column("x", string("unicode", 5, 5), Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", collection(boolean)), {"x": Column("x", boolean, Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", collection(null)), {})
        self.assertEqual(schemaToColumns("x", collection(boolean, 5, 5)), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", vector(boolean, 5)), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", vector(collection(boolean), 5)), {"x": Column("x", boolean, Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", collection(collection(boolean))), {"x": Column("x", boolean, Column("x.@rep", integer(0, 2), None)), "x.@rep": Column("x.@rep", integer(0, 2), None)})
        self.assertEqual(schemaToColumns("x", collection(vector(boolean, 5))), {"x": Column("x", boolean, Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", record(one=integer, two=real, three=string)), {"x.one": Column("x.one", integer, None), "x.two": Column("x.two", real, None), "x.three": Column("x.three", string, Column("x.three.@rep", integer(0, 1), None)), "x.three.@rep": Column("x.three.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", collection(record(one=integer, two=real, three=string))), {"x.one": Column("x.one", integer, Column("x.@rep", integer(0, 1), None)), "x.two": Column("x.two", real, Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None), "x.three": Column("x.three", string, Column("x.three.@rep", integer(0, 2), None)), "x.three.@rep": Column("x.three.@rep", integer(0, 2), None)})




        print("")
        print("\n".join(n + ": " + repr(c) for n, c in schemaToColumns("x", collection(record(one=integer, two=real, three=string))).items()))



