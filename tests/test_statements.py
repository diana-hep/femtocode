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
        self.assertEqual(schemaToColumns("x", boolean), {"x": Column("x", boolean, None, None)})
        self.assertEqual(schemaToColumns("x", integer), {"x": Column("x", integer, None, None)})
        self.assertEqual(schemaToColumns("x", real), {"x": Column("x", real, None, None)})
        self.assertEqual(schemaToColumns("x", extended), {"x": Column("x", extended, None, None)})

        self.assertEqual(schemaToColumns("x", string), {"x": Column("x", string, RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", string("bytes", 5, 5)), {"x": Column("x", string("bytes", 5, 5), None, None)})
        self.assertEqual(schemaToColumns("x", string("unicode", 5, 5)), {"x": Column("x", string("unicode", 5, 5), RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", collection(boolean)), {"x": Column("x", boolean, RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", collection(null)), {})
        self.assertEqual(schemaToColumns("x", collection(boolean, 5, 5)), {"x": Column("x", boolean, None, None)})
        self.assertEqual(schemaToColumns("x", vector(boolean, 5)), {"x": Column("x", boolean, None, None)})
        self.assertEqual(schemaToColumns("x", vector(collection(boolean), 5)), {"x": Column("x", boolean, RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", collection(collection(boolean))), {"x": Column("x", boolean, RepColumn("x.@rep", 2), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 2), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", collection(vector(boolean, 5))), {"x": Column("x", boolean, RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})

        self.assertEqual(schemaToColumns("x", record(one=integer, two=real, three=string)),
                         {"x.one": Column("x.one", integer, None, None),
                          "x.two": Column("x.two", real, None, None),
                          "x.three": Column("x.three", string, RepColumn("x.three.@rep", 1), GapColumn("x.three.@gap")),
                          "x.three.@rep": RepColumn("x.three.@rep", 1),
                          "x.three.@gap": GapColumn("x.three.@gap")})
        self.assertEqual(schemaToColumns("x", collection(record(one=integer, two=real, three=string))),
                         {"x.one": Column("x.one", integer, RepColumn("x.@rep", 1), GapColumn("x.@gap")),
                          "x.two": Column("x.two", real, RepColumn("x.@rep", 1), GapColumn("x.@gap")),
                          "x.@rep": RepColumn("x.@rep", 1),
                          "x.@gap": GapColumn("x.@gap"),
                          "x.three": Column("x.three", string, RepColumn("x.three.@rep", 2), GapColumn("x.three.@gap")),
                          "x.three.@rep": RepColumn("x.three.@rep", 2),
                          "x.three.@gap": GapColumn("x.three.@gap")})
        self.assertEqual(schemaToColumns("x", collection(record(uno=boolean, dos=collection(record(tres=boolean, quatro=collection(boolean)))))),
                         {"x.@rep": RepColumn("x.@rep", 1),
                          "x.@gap": GapColumn("x.@gap"),
                          "x.uno": Column("x.uno", boolean, RepColumn("x.@rep", 1), GapColumn("x.@gap")),
                          "x.dos.@rep": RepColumn("x.dos.@rep", 2),
                          "x.dos.@gap": GapColumn("x.dos.@gap"),
                          "x.dos.tres": Column("x.dos.tres", boolean, RepColumn("x.dos.@rep", 2), GapColumn("x.dos.@gap")),
                          "x.dos.quatro.@rep": RepColumn("x.dos.quatro.@rep", 3),
                          "x.dos.quatro.@gap": GapColumn("x.dos.quatro.@gap"),
                          "x.dos.quatro": Column("x.dos.quatro", boolean, RepColumn("x.dos.quatro.@rep", 3), GapColumn("x.dos.quatro.@gap"))})

        self.assertEqual(schemaToColumns("x", union(null)), {})
        self.assertEqual(schemaToColumns("x", union(boolean)), {"x": Column("x", boolean, None, None)})
        self.assertEqual(schemaToColumns("x", union(integer(1, 2), integer(100, 200))), {"x": Column("x", integer(1, 200), None, None)})
        self.assertEqual(schemaToColumns("x", union(real(almost(1), almost(2)), real(100, 200))), {"x": Column("x", real(almost(1), 200), None, None)})
        self.assertEqual(schemaToColumns("x", union(extended(almost(-inf), almost(2)), real(100, inf))), {"x": Column("x", real(almost(-inf), inf), None, None)})
        self.assertEqual(schemaToColumns("x", union(integer(1, 2), real(100, 200))), {"x": Column("x", real(1, 200), None, None)})

        self.assertEqual(schemaToColumns("x", union(string("bytes", 5, 10), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 10), RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", union(string("bytes", 3, 3), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 3), None, None)})
        self.assertEqual(schemaToColumns("x", union(string("unicode", 3, 3), string("unicode", 3, 3))), {"x": Column("x", string("unicode", 3, 3), RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})

        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2)), collection(real(100, 200)))), {"x": Column("x", real(1, 200), RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 6, 6))), {"x": Column("x", real(1, 200), RepColumn("x.@rep", 1), GapColumn("x.@gap")), "x.@rep": RepColumn("x.@rep", 1), "x.@gap": GapColumn("x.@gap")})
        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 5, 5))), {"x": Column("x", real(1, 200), None, None)})

        self.assertEqual(schemaToColumns("x", union(record(one=integer(1, 2), two=real(1, 2), three=string), record(one=integer(100, 200), two=real(100, 200), three=string))),
                         {"x.one": Column("x.one", integer(1, 200), None, None),
                          "x.two": Column("x.two", real(1, 200), None, None),
                          "x.three": Column("x.three", string, RepColumn("x.three.@rep", 1), GapColumn("x.three.@gap")),
                          "x.three.@rep": RepColumn("x.three.@rep", 1),
                          "x.three.@gap": GapColumn("x.three.@gap")})

        self.assertEqual(schemaToColumns("x", union(null, boolean)), {"x.@1": Column("x.@1", boolean, None, None), "x.@tag": TagColumn("x.@tag", 1)})
        self.assertEqual(schemaToColumns("x", union(null, integer(1, 2))), {"x.@1": Column("x.@1", integer(1, 2), None, None), "x.@tag": TagColumn("x.@tag", 1)})
        self.assertEqual(schemaToColumns("x", union(boolean, integer(1, 2))), {"x.@0": Column("x.@0", boolean, None, None), "x.@1": Column("x.@1", integer(1, 2), None, None), "x.@tag": TagColumn("x.@tag", 1)})
        self.assertEqual(schemaToColumns("x", union(string("bytes", 5, 5), string("unicode", 5, 5))), {"x.@0": Column("x.@0", string("bytes", 5, 5), None, None), "x.@1": Column("x.@1", string("unicode", 5, 5), RepColumn("x.@1.@rep", 1), GapColumn("x.@1.@gap")), "x.@1.@rep": RepColumn("x.@1.@rep", 1), "x.@1.@gap": GapColumn("x.@1.@gap"), "x.@tag": TagColumn("x.@tag", 1)})

        self.assertEqual(schemaToColumns("x", union(collection(boolean), collection(string))), {
            "x.@tag": TagColumn("x.@tag", 1),
            "x.@0": Column("x.@0", boolean, RepColumn("x.@0.@rep", 1), GapColumn("x.@0.@gap")),
            "x.@0.@rep": RepColumn("x.@0.@rep", 1),
            "x.@0.@gap": GapColumn("x.@0.@gap"),
            "x.@1": Column("x.@1", string, RepColumn("x.@1.@rep", 2), GapColumn("x.@1.@gap")),
            "x.@1.@rep": RepColumn("x.@1.@rep", 2),
            "x.@1.@gap": GapColumn("x.@1.@gap")})

        self.assertEqual(schemaToColumns("x", union(collection(boolean, 5, 5), collection(string, 5, 5))), {
            "x.@tag": TagColumn("x.@tag", 1),
            "x.@0": Column("x.@0", boolean, None, None),
            "x.@1": Column("x.@1", string, RepColumn("x.@1.@rep", 1), GapColumn("x.@1.@gap")),
            "x.@1.@rep": RepColumn("x.@1.@rep", 1),
            "x.@1.@gap": GapColumn("x.@1.@gap")})
        
        self.assertEqual(schemaToColumns("x", resolve([record("tree", left=union(boolean, "tree"), right=union(boolean, "tree"))])[0]), {
            "x.left.@tag": TagColumn("x.left.@tag", 1),
            "x.left.@0": Column("x.left.@0", boolean, RepColumn("x.left.@rep", almost(inf)), GapColumn("x.left.@gap")),
            "x.left.@rep": RepColumn("x.left.@rep", almost(inf)),
            "x.left.@gap": GapColumn("x.left.@gap"),
            "x.right.@tag": TagColumn("x.right.@tag", 1),
            "x.right.@0": Column("x.right.@0", boolean, RepColumn("x.right.@rep", almost(inf)), GapColumn("x.right.@gap")),
            "x.right.@rep": RepColumn("x.right.@rep", almost(inf)),
            "x.right.@gap": GapColumn("x.right.@gap")})

        self.assertEqual(schemaToColumns("x", resolve([record("tree", left=collection("tree"), right=collection("tree"))])[0]), {
            "x.left": Column("x.left", record("tree", left=collection("tree"), right=collection("tree")), RepColumn("x.left.@rep", almost(inf)), GapColumn("x.left.@gap")),
            "x.left.@rep": RepColumn("x.left.@rep", almost(inf)),
            "x.left.@gap": GapColumn("x.left.@gap"),
            "x.right": Column("x.right", record("tree", left=collection("tree"), right=collection("tree")), RepColumn("x.right.@rep", almost(inf)), GapColumn("x.right.@gap")),
            "x.right.@rep": RepColumn("x.right.@rep", almost(inf)),
            "x.right.@gap": GapColumn("x.right.@gap")})

        self.assertEqual(schemaToColumns("x", resolve([record("tree", left=collection(collection("tree")), right=collection("tree"))])[0]), {
            "x.left": Column("x.left", record("tree", left=collection(collection("tree")), right=collection("tree")), RepColumn("x.left.@rep", almost(inf)), GapColumn("x.left.@gap")),
            "x.left.@rep": RepColumn("x.left.@rep", almost(inf)),
            "x.left.@gap": GapColumn("x.left.@gap"),
            "x.right": Column("x.right", record("tree", left=collection(collection("tree")), right=collection("tree")), RepColumn("x.right.@rep", almost(inf)), GapColumn("x.right.@gap")),
            "x.right.@rep": RepColumn("x.right.@rep", almost(inf)),
            "x.right.@gap": GapColumn("x.right.@gap")})

    def test_shredAndAssemble(self):
        def addData(columns):
            for c in columns.values():
                c.data = []
            return columns

        def shred(obj, schema, level, repNumber, gapNumber, columns, name):
            self.assertIn(obj, schema)

            if isinstance(schema, Null):
                return level, 0

            elif isinstance(schema, (Boolean, Number)):
                self.assertIn(name, columns)
                col = columns[name]
                col.data.append(obj)
                if col.rep is not None and len(col.rep.data) < len(col.data):
                    col.rep.data.append(repNumber)
                    col.gap.data.append(gapNumber)
                return level, 0

            # elif isinstance(schema, String):
            #     pass

            elif isinstance(schema, Collection):
                if len(obj) == 0:
                    gapOut = gapNumber + 1
                else:
                    gapOut = 0

                items = schema.items
                for x in obj:
                    repNumber, gapNumber = shred(x, items, level + 1, repNumber, gapNumber, columns, name)

                return level, gapOut

            # else:
            #     pass

        def checkShred(schema, data, expect):
            schema = resolve([schema])[0]
            columns = addData(schemaToColumns("x", schema))
            gapNumber = 0
            for obj in data:
                repNumber, gapNumber = shred(obj, schema, 0, 0, gapNumber, columns, "x")
            self.assertEqual(dict((k, v.data) for k, v in columns.items()), expect)

        def lookShred(schema, data):
            schema = resolve([schema])[0]
            columns = addData(schemaToColumns("x", schema))
            gapNumber = 0
            for obj in data:
                repNumber, gapNumber = shred(obj, schema, 0, 0, gapNumber, columns, "x")
            print("")
            for n in sorted(columns):
                print("{0}: {1}".format(n, columns[n].data))

        checkShred(real, [1.1, 2.2, 3.3, 4.4, 5.5], {
            "x": [1.1, 2.2, 3.3, 4.4, 5.5]})

        checkShred(collection(real), [[], [1.1], [2.2, 3.3], [], [], [4.4, 5.5]], {
            "x": [1.1, 2.2, 3.3, 4.4, 5.5],
            "x.@gap": [1, 0, 0, 2, 0],
            "x.@rep": [0, 0, 1, 0, 1]})

        checkShred(collection(collection(real)), [[[1.1]], [[1.1], [2.2]], [[1.1, 2.2]]], {
            "x": [1.1, 1.1, 2.2, 1.1, 2.2],
            "x.@gap": [0, 0, 0, 0, 0],
            "x.@rep": [0, 0, 1, 0, 2]})

        lookShred(collection(collection(real)), [[[1.1]], [[1.1], [2.2]], [[1.1, 2.2]]])
