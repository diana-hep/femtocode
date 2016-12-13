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
    xrange = range

class TestStatements(unittest.TestCase):
    def runTest(self):
        pass

    def test_schemaToColumns(self):
        self.assertEqual(schemaToColumns("x", null), {})
        self.assertEqual(schemaToColumns("x", boolean), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", integer), {"x": Column("x", integer, None)})
        self.assertEqual(schemaToColumns("x", real), {"x": Column("x", real, None)})
        self.assertEqual(schemaToColumns("x", extended), {"x": Column("x", extended, None)})

        self.assertEqual(schemaToColumns("x", string), {"x": Column("x", string, SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})
        self.assertEqual(schemaToColumns("x", string("bytes", 5, 5)), {"x": Column("x", string("bytes", 5, 5), None)})
        self.assertEqual(schemaToColumns("x", string("unicode", 5, 5)), {"x": Column("x", string("unicode", 5, 5), SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})
        self.assertEqual(schemaToColumns("x", collection(boolean)), {"x": Column("x", boolean, SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})
        self.assertEqual(schemaToColumns("x", collection(null)), {})
        self.assertEqual(schemaToColumns("x", collection(boolean, 5, 5)), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", vector(boolean, 5)), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", vector(collection(boolean), 5)), {"x": Column("x", boolean, SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})
        self.assertEqual(schemaToColumns("x", collection(collection(boolean))), {"x": Column("x", boolean, SizeColumn("x.@size", 2)), "x.@size": SizeColumn("x.@size", 2)})
        self.assertEqual(schemaToColumns("x", collection(vector(boolean, 5))), {"x": Column("x", boolean, SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})

        self.assertEqual(schemaToColumns("x", record(one=integer, two=real, three=string)),
                         {"x.one": Column("x.one", integer, None),
                          "x.two": Column("x.two", real, None),
                          "x.three": Column("x.three", string, SizeColumn("x.three.@size", 1)),
                          "x.three.@size": SizeColumn("x.three.@size", 1)})
        self.assertEqual(schemaToColumns("x", collection(record(one=integer, two=real, three=string))),
                         {"x.one": Column("x.one", integer, SizeColumn("x.@size", 1)),
                          "x.two": Column("x.two", real, SizeColumn("x.@size", 1)),
                          "x.@size": SizeColumn("x.@size", 1),
                          "x.three": Column("x.three", string, SizeColumn("x.three.@size", 2)),
                          "x.three.@size": SizeColumn("x.three.@size", 2)})
        self.assertEqual(schemaToColumns("x", collection(record(uno=boolean, dos=collection(record(tres=boolean, quatro=collection(boolean)))))),
                         {"x.@size": SizeColumn("x.@size", 1),
                          "x.uno": Column("x.uno", boolean, SizeColumn("x.@size", 1)),
                          "x.dos.@size": SizeColumn("x.dos.@size", 2),
                          "x.dos.tres": Column("x.dos.tres", boolean, SizeColumn("x.dos.@size", 2)),
                          "x.dos.quatro.@size": SizeColumn("x.dos.quatro.@size", 3),
                          "x.dos.quatro": Column("x.dos.quatro", boolean, SizeColumn("x.dos.quatro.@size", 3))})

        self.assertEqual(schemaToColumns("x", union(null)), {})
        self.assertEqual(schemaToColumns("x", union(boolean)), {"x": Column("x", boolean, None)})
        self.assertEqual(schemaToColumns("x", union(integer(1, 2), integer(100, 200))), {"x": Column("x", integer(1, 200), None)})
        self.assertEqual(schemaToColumns("x", union(real(almost(1), almost(2)), real(100, 200))), {"x": Column("x", real(almost(1), 200), None)})
        self.assertEqual(schemaToColumns("x", union(extended(almost(-inf), almost(2)), real(100, inf))), {"x": Column("x", real(almost(-inf), inf), None)})
        self.assertEqual(schemaToColumns("x", union(integer(1, 2), real(100, 200))), {"x": Column("x", real(1, 200), None)})

        self.assertEqual(schemaToColumns("x", union(string("bytes", 5, 10), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 10), SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})
        self.assertEqual(schemaToColumns("x", union(string("bytes", 3, 3), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 3), None)})
        self.assertEqual(schemaToColumns("x", union(string("unicode", 3, 3), string("unicode", 3, 3))), {"x": Column("x", string("unicode", 3, 3), SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})

        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2)), collection(real(100, 200)))), {"x": Column("x", real(1, 200), SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})
        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 6, 6))), {"x": Column("x", real(1, 200), SizeColumn("x.@size", 1)), "x.@size": SizeColumn("x.@size", 1)})
        self.assertEqual(schemaToColumns("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 5, 5))), {"x": Column("x", real(1, 200), None)})

        self.assertEqual(schemaToColumns("x", union(record(one=integer(1, 2), two=real(1, 2), three=string), record(one=integer(100, 200), two=real(100, 200), three=string))),
                         {"x.one": Column("x.one", integer(1, 200), None),
                          "x.two": Column("x.two", real(1, 200), None),
                          "x.three": Column("x.three", string, SizeColumn("x.three.@size", 1)),
                          "x.three.@size": SizeColumn("x.three.@size", 1)})

        self.assertEqual(schemaToColumns("x", union(null, boolean)), {"x.@1": Column("x.@1", boolean, None), "x.@tag": TagColumn("x.@tag", 1)})
        self.assertEqual(schemaToColumns("x", union(null, integer(1, 2))), {"x.@1": Column("x.@1", integer(1, 2), None), "x.@tag": TagColumn("x.@tag", 1)})
        self.assertEqual(schemaToColumns("x", union(boolean, integer(1, 2))), {"x.@0": Column("x.@0", boolean, None), "x.@1": Column("x.@1", integer(1, 2), None), "x.@tag": TagColumn("x.@tag", 1)})
        self.assertEqual(schemaToColumns("x", union(string("bytes", 5, 5), string("unicode", 5, 5))), {"x.@0": Column("x.@0", string("bytes", 5, 5), None), "x.@1": Column("x.@1", string("unicode", 5, 5), SizeColumn("x.@1.@size", 1)), "x.@1.@size": SizeColumn("x.@1.@size", 1), "x.@tag": TagColumn("x.@tag", 1)})

        self.assertEqual(schemaToColumns("x", union(collection(boolean), collection(string))), {
            "x.@tag": TagColumn("x.@tag", 1),
            "x.@0": Column("x.@0", boolean, SizeColumn("x.@0.@size", 1)),
            "x.@0.@size": SizeColumn("x.@0.@size", 1),
            "x.@1": Column("x.@1", string, SizeColumn("x.@1.@size", 2)),
            "x.@1.@size": SizeColumn("x.@1.@size", 2)})

        self.assertEqual(schemaToColumns("x", union(collection(boolean, 5, 5), collection(string, 5, 5))), {
            "x.@tag": TagColumn("x.@tag", 1),
            "x.@0": Column("x.@0", boolean, None),
            "x.@1": Column("x.@1", string, SizeColumn("x.@1.@size", 1)),
            "x.@1.@size": SizeColumn("x.@1.@size", 1)})
        
        self.assertEqual(schemaToColumns("x", resolve([record("tree", left=union(boolean, "tree"), right=union(boolean, "tree"))])[0]), {
            "x.left.@tag": TagColumn("x.left.@tag", 1),
            "x.left.@0": Column("x.left.@0", boolean, SizeColumn("x.left.@size", almost(inf))),
            "x.left.@size": SizeColumn("x.left.@size", almost(inf)),
            "x.right.@tag": TagColumn("x.right.@tag", 1),
            "x.right.@0": Column("x.right.@0", boolean, SizeColumn("x.right.@size", almost(inf))),
            "x.right.@size": SizeColumn("x.right.@size", almost(inf))})

        self.assertEqual(schemaToColumns("x", resolve([record("tree", left=collection("tree"), right=collection("tree"))])[0]), {
            "x.left": Column("x.left", record("tree", left=collection("tree"), right=collection("tree")), SizeColumn("x.left.@size", almost(inf))),
            "x.left.@size": SizeColumn("x.left.@size", almost(inf)),
            "x.right": Column("x.right", record("tree", left=collection("tree"), right=collection("tree")), SizeColumn("x.right.@size", almost(inf))),
            "x.right.@size": SizeColumn("x.right.@size", almost(inf))})

        self.assertEqual(schemaToColumns("x", resolve([record("tree", left=collection(collection("tree")), right=collection("tree"))])[0]), {
            "x.left": Column("x.left", record("tree", left=collection(collection("tree")), right=collection("tree")), SizeColumn("x.left.@size", almost(inf))),
            "x.left.@size": SizeColumn("x.left.@size", almost(inf)),
            "x.right": Column("x.right", record("tree", left=collection(collection("tree")), right=collection("tree")), SizeColumn("x.right.@size", almost(inf))),
            "x.right.@size": SizeColumn("x.right.@size", almost(inf))})

    def test_shredAndAssemble(self):
        def addData(columns):
            for c in columns.values():
                c.data = []
                c.pointer = 0
            return columns

        def shred(obj, schema, columns, name):
            self.assertIn(obj, schema)

            if isinstance(schema, Null):
                pass

            elif isinstance(schema, (Boolean, Number)):
                self.assertIn(name, columns)
                col = columns[name]
                col.data.append(obj)

            # elif isinstance(schema, String):
            #     pass

            elif isinstance(schema, Collection):
                col = columns[name + "." + Column.sizeSuffix]
                col.data.append(len(obj))

                items = schema.items
                for x in obj:
                    shred(x, items, columns, name)

            # else:
            #     pass

        def assemble(schema, columns, name):
            if isinstance(schema, Null):
                return None

            elif isinstance(schema, (Boolean, Number)):
                col = columns[name]
                out = col.data[col.pointer]
                col.pointer += 1
                return out

            # elif isinstance(schema, String):
            #     pass

            elif isinstance(schema, Collection):
                col = columns[name + "." + Column.sizeSuffix]
                size = col.data[col.pointer]
                col.pointer += 1

                items = schema.items
                return [assemble(items, columns, name) for i in xrange(size)]

            # else:
            #     pass



        def checkShred(schema, data, expect):
            schema = resolve([schema])[0]
            columns = addData(schemaToColumns("x", schema))
            for obj in data:
                shred(obj, schema, columns, "x")
            self.assertEqual(dict((k, v.data) for k, v in columns.items()), expect)

        def checkShredAndAssemble(schema, data, verbose=False):
            schema = resolve([schema])[0]
            columns = addData(schemaToColumns("x", schema))
            for obj in data:
                shred(obj, schema, columns, "x")

            num = len(data)
            out = [assemble(schema, columns, "x") for i in xrange(num)]

            if verbose:
                print(out)
            self.assertEqual(data, out)

        def lookShred(schema, data):
            schema = resolve([schema])[0]
            columns = addData(schemaToColumns("x", schema))
            for obj in data:
                shred(obj, schema, columns, "x")
            print("")
            for n in sorted(columns):
                print("{0}: {1}".format(n, columns[n].data))

        checkShred(real, [1.1, 2.2, 3.3, 4.4, 5.5], {
            "x": [1.1, 2.2, 3.3, 4.4, 5.5]})
        checkShredAndAssemble(real, [1.1, 2.2, 3.3, 4.4, 5.5])

        checkShred(collection(real), [[], [1.1], [2.2, 3.3], [], [], [4.4, 5.5]], {
            "x": [1.1, 2.2, 3.3, 4.4, 5.5],
            "x.@size": [0, 1, 2, 0, 0, 2]})
        checkShredAndAssemble(collection(real), [[], [1.1], [2.2, 3.3], [], [], [4.4, 5.5]])

        checkShred(collection(collection(real)), [[[1.1]], [[1.1], [2.2]], [[1.1, 2.2]]], {
            "x": [1.1, 1.1, 2.2, 1.1, 2.2],
            "x.@size": [1, 1, 2, 1, 1, 1, 2]})
        checkShredAndAssemble(collection(collection(real)), [[[1.1]], [[1.1], [2.2]], [[1.1, 2.2]]])

        checkShred(collection(collection(real)), [[], [[], [1.1]], [[1.1], [], [2.2]], [], [[], [1.1, 2.2], []], []], {
            "x": [1.1, 1.1, 2.2, 1.1, 2.2],
            "x.@size": [0, 2, 0, 1, 3, 1, 0, 1, 0, 3, 0, 2, 0, 0]})
        checkShredAndAssemble(collection(collection(real)), [[], [[], [1.1]], [[1.1], [], [2.2]], [], [[], [1.1, 2.2], []], []])
