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

        self.assertEqual(schemaToColumns("x", record(one=integer, two=real, three=string)),
                         {"x.one": Column("x.one", integer, None),
                          "x.two": Column("x.two", real, None),
                          "x.three": Column("x.three", string, Column("x.three.@rep", integer(0, 1), None)),
                          "x.three.@rep": Column("x.three.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", collection(record(one=integer, two=real, three=string))),
                         {"x.one": Column("x.one", integer, Column("x.@rep", integer(0, 1), None)),
                          "x.two": Column("x.two", real, Column("x.@rep", integer(0, 1), None)),
                          "x.@rep": Column("x.@rep", integer(0, 1), None),
                          "x.three": Column("x.three", string, Column("x.three.@rep", integer(0, 2), None)),
                          "x.three.@rep": Column("x.three.@rep", integer(0, 2), None)})
        self.assertEqual(schemaToColumns("x", collection(record(uno=boolean, dos=collection(record(tres=boolean, quatro=collection(boolean)))))),
                         {"x.@rep": Column("x.@rep", integer(0, 1), None),
                          "x.uno": Column("x.uno", boolean, Column("x.@rep", integer(0, 1), None)),
                          "x.dos.@rep": Column("x.dos.@rep", integer(0, 2), None),
                          "x.dos.tres": Column("x.dos.tres", boolean, Column("x.dos.@rep", integer(0, 2), None)),
                          "x.dos.quatro.@rep": Column("x.dos.quatro.@rep", integer(0, 3), None),
                          "x.dos.quatro": Column("x.dos.quatro", boolean, Column("x.dos.quatro.@rep", integer(0, 3), None))})

        self.assertEqual(schemaToColumns("x", union(null)), {})
        self.assertEqual(schemaToColumns("x", union(boolean)), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", union(integer(1, 2), integer(100, 200))), {"x": Column("x", integer(1, 200), None)})
        self.assertEqual(schemaToColumns("x", union(real(almost(1), almost(2)), real(100, 200))), {"x": Column("x", real(almost(1), 200), None)})
        self.assertEqual(schemaToColumns("x", union(extended(almost(-inf), almost(2)), real(100, inf))), {"x": Column("x", real(almost(-inf), inf), None)})
        self.assertEqual(schemaToColumns("x", union(integer(1, 2), real(100, 200))), {"x": Column("x", real(1, 200), None)})

        self.assertEqual(schemaToColumns("x", union(string("bytes", 5, 10), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 10), Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", union(string("bytes", 3, 3), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 3), None)})
        self.assertEqual(schemaToColumns("x", union(string("unicode", 3, 3), string("unicode", 3, 3))), {"x": Column("x", string("unicode", 3, 3), Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})

        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2)), collection(real(100, 200)))), {"x": Column("x", real(1, 200), Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 6, 6))), {"x": Column("x", real(1, 200), Column("x.@rep", integer(0, 1), None)), "x.@rep": Column("x.@rep", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 5, 5))), {"x": Column("x", real(1, 200), None)})

        self.assertEqual(schemaToColumns("x", union(record(one=integer(1, 2), two=real(1, 2), three=string), record(one=integer(100, 200), two=real(100, 200), three=string))),
                         {"x.one": Column("x.one", integer(1, 200), None),
                          "x.two": Column("x.two", real(1, 200), None),
                          "x.three": Column("x.three", string, Column("x.three.@rep", integer(0, 1), None)),
                          "x.three.@rep": Column("x.three.@rep", integer(0, 1), None)})

        self.assertEqual(schemaToColumns("x", union(null, boolean)), {"x.@1": Column("x.@1", boolean, None), "x.@tag": Column("x.@tag", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", union(null, integer(1, 2))), {"x.@1": Column("x.@1", integer(1, 2), None), "x.@tag": Column("x.@tag", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", union(boolean, integer(1, 2))), {"x.@0": Column("x.@0", boolean, None), "x.@1": Column("x.@1", integer(1, 2), None), "x.@tag": Column("x.@tag", integer(0, 1), None)})
        self.assertEqual(schemaToColumns("x", union(string("bytes", 5, 5), string("unicode", 5, 5))), {"x.@0": Column("x.@0", string("bytes", 5, 5), None), "x.@1": Column("x.@1", string("unicode", 5, 5), Column("x.@1.@rep", integer(0, 1), None)), "x.@1.@rep": Column("x.@1.@rep", integer(0, 1), None), "x.@tag": Column("x.@tag", integer(0, 1), None)})

        self.assertEqual(schemaToColumns("x", union(collection(boolean), collection(string))), {
            "x.@tag": Column("x.@tag", integer(min=0, max=1), None),
            "x.@0": Column("x.@0", boolean, Column("x.@0.@rep", integer(0, 1), None)),
            "x.@0.@rep": Column("x.@0.@rep", integer(0, 1), None),
            "x.@1": Column("x.@1", string, Column("x.@1.@rep", integer(0, 2), None)),
            "x.@1.@rep": Column("x.@1.@rep", integer(0, 2), None)})

        self.assertEqual(schemaToColumns("x", union(collection(boolean, 5, 5), collection(string, 5, 5))), {
            "x.@tag": Column("x.@tag", integer(min=0, max=1), None),
            "x.@0": Column("x.@0", boolean, None),
            "x.@1": Column("x.@1", string, Column("x.@1.@rep", integer(0, 1), None)),
            "x.@1.@rep": Column("x.@1.@rep", integer(0, 1), None)})



        print("")
        print("\n".join(n + ": " + repr(c) for n, c in schemaToColumns("x", union(collection(boolean), collection(string))).items()))
