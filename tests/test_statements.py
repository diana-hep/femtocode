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

from collections import namedtuple
import ast
import json
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

    def test_shredAndAssemble(self):
        def addData(columns):
            for c in columns.values():
                c.data = []
                c.pointer = 0
            return columns

        def shred(obj, schema, columns, name):
            self.assertIn(obj, schema)

            if isinstance(columns.get(name), RecursiveColumn):
                columns[name].data.append(obj)

            elif isinstance(schema, Null):
                pass

            elif isinstance(schema, (Boolean, Number)):
                self.assertIn(name, columns)
                columns[name].data.append(obj)

            elif isinstance(schema, String):
                sizeName = name + Column.sizeSuffix
                self.assertIn(name, columns)
                self.assertIn(sizeName, columns)

                columns[name].data.extend(list(obj))
                columns[sizeName].data.append(len(obj))

            elif isinstance(schema, Collection):
                size = len(obj)
                for n, c in columns.items():
                    if n.startswith(name) and n.endswith(Column.sizeSuffix):
                        c.data.append(size)

                items = schema.items
                for x in obj:
                    shred(x, items, columns, name)

            elif isinstance(schema, Record):
                for n, t in schema.fields.items():
                    self.assertTrue(hasattr(obj, n))
                    shred(getattr(obj, n), t, columns, name + "." + n)

            elif isinstance(schema, Union):
                tag = columns[name + Column.tagSuffix]
                for i, p in enumerate(tag.possibilities):
                    if obj in p:
                        tag.data.append(i)
                        shred(obj, p, columns, name + Column.posSuffix(i))
                        break

            else:
                raise ProgrammingError("unexpected type: {0} {1}".format(type(schema), schema))

        def assemble(schema, columns, name):
            if isinstance(columns.get(name), RecursiveColumn):
                col = columns[name]
                out = col.data[col.pointer]
                col.pointer += 1
                return out

            elif isinstance(schema, Null):
                return None

            elif isinstance(schema, (Boolean, Number)):
                col = columns[name]
                out = col.data[col.pointer]
                col.pointer += 1
                return out

            elif isinstance(schema, String):
                col = columns[name]
                sizeCol = columns[name + Column.sizeSuffix]

                size = sizeCol.data[sizeCol.pointer]
                sizeCol.pointer += 1
                out = "".join(col.data[col.pointer:col.pointer + size])
                col.pointer += size
                return out

            elif isinstance(schema, Collection):
                size = None
                for n, c in columns.items():
                    if n.startswith(name) and n.endswith(Column.sizeSuffix):
                        size = c.data[c.pointer]
                        c.pointer += 1
                self.assertIsNotNone(size)

                items = schema.items
                return [assemble(items, columns, name) for i in xrange(size)]

            elif isinstance(schema, Record):
                names = sorted(schema.fields.keys())
                return namedtuple("tmp", names)(*[assemble(schema.fields[n], columns, name + "." + n) for n in names])

            elif isinstance(schema, Union):
                tag = columns[name + Column.tagSuffix]
                pos = tag.data[tag.pointer]
                tag.pointer += 1
                return assemble(tag.possibilities[pos], columns, name + Column.posSuffix(pos))

            else:
                raise ProgrammingError("unexpected type: {0} {1}".format(type(schema), schema))

        def checkShred(schema, data, expect):
            schema = resolve([schema])[0]
            columns = addData(schemaToColumns("root", schema))
            for obj in data:
                shred(obj, schema, columns, "root")
            self.assertEqual(dict((k, v.data) for k, v in columns.items()), expect)

        def checkShredAndAssemble(schema, data, verbose=False):
            schema = resolve([schema])[0]
            columns = addData(schemaToColumns("root", schema))
            for obj in data:
                shred(obj, schema, columns, "root")

            num = len(data)
            out = [assemble(schema, columns, "root") for i in xrange(num)]

            if verbose:
                print("")
                print("Schema: {0}".format(pretty(schema)))
                print("Input: {0}".format(data))
                print("Columns:")
                for n in sorted(columns):
                    print("    {0}: {1}".format(json.dumps(n), columns[n].data))
            self.assertEqual(data, out)

        def lookShred(schema, data):
            schema = resolve([schema])[0]
            print("")
            print("Schema: {0}".format(pretty(schema)))
            print("Input: {0}".format(data))
            print("Columns:")
            columns = addData(schemaToColumns("root", schema))
            for n in sorted(columns):
                print("    {0}: {1}".format(json.dumps(n), columns[n]))
            for obj in data:
                shred(obj, schema, columns, "root")
            print("Contents:")
            for n in sorted(columns):
                print("    {0}: {1}".format(json.dumps(n), columns[n].data))

        checkShredAndAssemble(real, [1.1, 2.2, 3.3, 4.4, 5.5])

        checkShredAndAssemble(collection(real), [[], [1.1], [2.2, 3.3], []])

        checkShredAndAssemble(collection(collection(real)), [[], [[1.1]], [[], [2.2, 3.3]]])

        checkShredAndAssemble(string, [b"one", b"two", b"three"])

        checkShredAndAssemble(collection(string), [[], [b"one", b"two"], [b"three"]])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(record(a=real, b=real), [rec1(1.1, 2.2), rec1(3.3, 4.4)])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(record(a=real, b=string), [rec1(1.1, "two"), rec1(3.3, "four"), rec1(5.5, "six")])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(collection(record(a=real, b=string)), [[], [rec1(1.1, "two")], [rec1(3.3, "four"), rec1(5.5, "six")]])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(collection(record(a=real, b=real)), [[], [rec1(1.1, 2.2), rec1(3.3, 4.4)]])

        rec1 = namedtuple("rec1", ["x", "y"])
        rec2 = namedtuple("rec2", ["a", "b"])
        checkShredAndAssemble(record(x=real, y=collection(record(a=real, b=collection(real)))),
                  [rec1(1, [rec2(2, [3, 4]), rec2(5, [])]),
                   rec1(6, [rec2(9, [10, 11])])])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(record("rec1", a=real, b=collection("rec1")), [rec1(1.1, []), rec1(2.2, [rec1(3.3, [])])])

        checkShredAndAssemble(union(boolean, integer), [1, True, 2, False, 3])

        rec1 = namedtuple("rec1", ["x", "y"])
        checkShredAndAssemble(union(integer, record(x=real, y=real)), [1, rec1(2.2, 3.3), 4, rec1(5.5, 6.6), 7])

        checkShredAndAssemble(union(real, collection(real)), [1.1, [2.2, 3.3], 4.4, [5.5, 6.6], 7.7])

        rec1 = namedtuple("rec1", ["x", "y"])
        checkShredAndAssemble(union(integer, collection(record(x=real, y=real))), [1, [], 2, [rec1(3.3, 4.4), rec1(5.5, 6.6)], 7])

        checkShredAndAssemble(union(null, real), [1.1, None, 2.2, None, 3.3])


        # checkShred(real, [1.1, 2.2, 3.3, 4.4, 5.5], {
        #     "x": [1.1, 2.2, 3.3, 4.4, 5.5]})
        # checkShredAndAssemble(real, [1.1, 2.2, 3.3, 4.4, 5.5])

        # checkShred(collection(real), [[], [1.1], [2.2, 3.3], [], [], [4.4, 5.5]], {
        #     "x": [1.1, 2.2, 3.3, 4.4, 5.5],
        #     "x.@size": [0, 1, 2, 0, 0, 2]})
        # checkShredAndAssemble(collection(real), [[], [1.1], [2.2, 3.3], [], [], [4.4, 5.5]])

        # checkShred(collection(collection(real)), [[[1.1]], [[1.1], [2.2]], [[1.1, 2.2]]], {
        #     "x": [1.1, 1.1, 2.2, 1.1, 2.2],
        #     "x.@size": [1, 1, 2, 1, 1, 1, 2]})
        # checkShredAndAssemble(collection(collection(real)), [[[1.1]], [[1.1], [2.2]], [[1.1, 2.2]]])

        # checkShred(collection(collection(real)), [[], [[], [1.1]], [[1.1], [], [2.2]], [], [[], [1.1, 2.2], []], []], {
        #     "x": [1.1, 1.1, 2.2, 1.1, 2.2],
        #     "x.@size": [0, 2, 0, 1, 3, 1, 0, 1, 0, 3, 0, 2, 0, 0]})
        # checkShredAndAssemble(collection(collection(real)), [[], [[], [1.1]], [[1.1], [], [2.2]], [], [[], [1.1, 2.2], []], []])

        # rec1 = namedtuple("rec1", ["x", "y"])
        # rec2 = namedtuple("rec2", ["a", "b"])
        # checkShred(record(x=real, y=collection(record(a=real, b=collection(real)))),
        #           [rec1(1, [rec2(2, [3, 4]), rec2(5, [])]),
        #            rec1(6, [rec2(9, [10, 11])])], {
        #     "x.x": [1, 6],
        #     "x.y.@size": [2, 1],
        #     "x.y.a": [2, 5, 9],
        #     "x.y.b": [3, 4, 10, 11],
        #     "x.y.b.@size": [2, 0, 2]})

        # checkShredAndAssemble(record(x=real, y=collection(record(a=real, b=collection(real)))),
        #           [rec1(1, [rec2(2, [3, 4]), rec2(5, [])]),
        #            rec1(6, [rec2(9, [10, 11])])])

        # checkShredAndAssemble(collection("stuff", alias="stuff"), [[], [[], []], [[[], [], [[]]]]])


        # print schemaToColumns("", resolve([record("stuff", a=real, b=collection("stuff"))])[0])

        # rec1 = namedtuple("rec1", ["a", "b"])
        # lookShred(record("stuff", a=real, b=collection("stuff")), [rec1(1.1, []), rec1(2.2, [rec1(3.3, [])]), rec1(4.4, [rec1(5.5, [])])])
