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
        def schemaToColumns2(name, schema):
            columns = schemaToColumns(name, schema)

            out = {}
            for n, c in columns.items():
                if isinstance(c, SizeColumn):
                    out[str(n)] = SizeColumn(str(c.name))
                elif isinstance(c, TagColumn):
                    out[str(n)] = TagColumn(str(c.name), c.possibilities)
                else:
                    out[str(n)] = Column(str(c.name), c.schema)
            return out

        self.assertEqual(schemaToColumns2("x", null), {})
        self.assertEqual(schemaToColumns2("x", boolean), {"x": Column("x", boolean)})
        self.assertEqual(schemaToColumns2("x", integer), {"x": Column("x", integer)})
        self.assertEqual(schemaToColumns2("x", real), {"x": Column("x", real)})
        self.assertEqual(schemaToColumns2("x", extended), {"x": Column("x", extended)})

        self.assertEqual(schemaToColumns2("x", string), {"x": Column("x", string), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", string("bytes", 5, 5)), {"x": Column("x", string("bytes", 5, 5))})
        self.assertEqual(schemaToColumns2("x", string("unicode", 5, 5)), {"x": Column("x", string("unicode", 5, 5)), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", collection(boolean)), {"x": Column("x", boolean), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", collection(null)), {"x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", collection(boolean, 5, 5)), {"x": Column("x", boolean)})
        self.assertEqual(schemaToColumns2("x", vector(boolean, 5)), {"x": Column("x", boolean)})
        self.assertEqual(schemaToColumns2("x", vector(collection(boolean), 5)), {"x": Column("x", boolean), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", collection(collection(boolean))), {"x": Column("x", boolean), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", collection(vector(boolean, 5))), {"x": Column("x", boolean), "x@size": SizeColumn("x@size")})

        self.assertEqual(schemaToColumns2("x", record(one=integer, two=real, three=string)),
                         {"x.one": Column("x.one", integer),
                          "x.two": Column("x.two", real),
                          "x.three": Column("x.three", string),
                          "x.three@size": SizeColumn("x.three@size")})
        self.assertEqual(schemaToColumns2("x", collection(record(one=integer, two=real, three=string))),
                         {"x.one": Column("x.one", integer),
                          "x.two": Column("x.two", real),
                          "x.three": Column("x.three", string),
                          "x.one@size": SizeColumn("x.one@size"),
                          "x.two@size": SizeColumn("x.two@size"),
                          "x.three@size": SizeColumn("x.three@size")})
        self.assertEqual(schemaToColumns2("x", collection(record(uno=boolean, dos=collection(record(tres=boolean, quatro=collection(boolean)))))),
                         {"x.uno": Column("x.uno", boolean),
                          "x.uno@size": SizeColumn("x.uno@size"),
                          "x.dos.tres": Column("x.dos.tres", boolean),
                          "x.dos.quatro": Column("x.dos.quatro", boolean),
                          "x.dos.tres@size": SizeColumn("x.dos.tres@size"),
                          "x.dos.quatro@size": SizeColumn("x.dos.quatro@size")})

        self.assertEqual(schemaToColumns2("x", union(null)), {})
        self.assertEqual(schemaToColumns2("x", union(boolean)), {"x": Column("x", boolean)})
        self.assertEqual(schemaToColumns2("x", union(integer(1, 2), integer(100, 200))), {"x": Column("x", integer(1, 200))})
        self.assertEqual(schemaToColumns2("x", union(real(almost(1), almost(2)), real(100, 200))), {"x": Column("x", real(almost(1), 200))})
        self.assertEqual(schemaToColumns2("x", union(extended(almost(-inf), almost(2)), real(100, inf))), {"x": Column("x", real(almost(-inf), inf))})
        self.assertEqual(schemaToColumns2("x", union(integer(1, 2), real(100, 200))), {"x": Column("x", real(1, 200))})

        self.assertEqual(schemaToColumns2("x", union(string("bytes", 5, 10), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 10)), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", union(string("bytes", 3, 3), string("bytes", 3, 3))), {"x": Column("x", string("bytes", 3, 3))})
        self.assertEqual(schemaToColumns2("x", union(string("unicode", 3, 3), string("unicode", 3, 3))), {"x": Column("x", string("unicode", 3, 3)), "x@size": SizeColumn("x@size")})

        self.assertEqual(schemaToColumns2("x", union(collection(integer(1, 2)), collection(real(100, 200)))), {"x": Column("x", real(1, 200)), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 6, 6))), {"x": Column("x", real(1, 200)), "x@size": SizeColumn("x@size")})
        self.assertEqual(schemaToColumns2("x", union(collection(integer(1, 2), 5, 5), collection(real(100, 200), 5, 5))), {"x": Column("x", real(1, 200))})

        self.assertEqual(schemaToColumns2("x", union(record(one=integer(1, 2), two=real(1, 2), three=string), record(one=integer(100, 200), two=real(100, 200), three=string))),
                         {"x.one": Column("x.one", integer(1, 200)),
                          "x.two": Column("x.two", real(1, 200)),
                          "x.three": Column("x.three", string),
                          "x.three@size": SizeColumn("x.three@size")})

        self.assertEqual(schemaToColumns2("x", union(null, boolean)), {"x@1": Column("x@1", boolean), "x@tag": TagColumn("x@tag", [null, boolean])})
        self.assertEqual(schemaToColumns2("x", union(null, integer(1, 2))), {"x@1": Column("x@1", integer(1, 2)), "x@tag": TagColumn("x@tag", [null, integer(1, 2)])})
        self.assertEqual(schemaToColumns2("x", union(boolean, integer(1, 2))), {"x@0": Column("x@0", boolean), "x@1": Column("x@1", integer(1, 2)), "x@tag": TagColumn("x@tag", [boolean, integer(1, 2)])})
        self.assertEqual(schemaToColumns2("x", union(string("bytes", 5, 5), string("unicode", 5, 5))), {"x@0": Column("x@0", string("bytes", 5, 5)), "x@1": Column("x@1", string("unicode", 5, 5)), "x@1@size": SizeColumn("x@1@size"), "x@tag": TagColumn("x@tag", [string("bytes", 5, 5), string("unicode", 5, 5)])})

        self.assertEqual(schemaToColumns2("x", union(collection(boolean), collection(string))), {
            "x@tag": TagColumn("x@tag", [collection(boolean), collection(string)]),
            "x@0": Column("x@0", boolean),
            "x@0@size": SizeColumn("x@0@size"),
            "x@1": Column("x@1", string),
            "x@1@size": SizeColumn("x@1@size")})

        self.assertEqual(schemaToColumns2("x", union(collection(boolean, 5, 5), collection(string, 5, 5))), {
            "x@tag": TagColumn("x@tag", [collection(boolean, 5, 5), collection(string, 5, 5)]),
            "x@0": Column("x@0", boolean),
            "x@1": Column("x@1", string),
            "x@1@size": SizeColumn("x@1@size")})
        
        self.assertEqual(schemaToColumns2("x", resolve([record("tree", left=union(boolean, "tree"), right=union(boolean, "tree"))])[0]), {
            "x": RecursiveColumn("x", resolve([record("tree", left=union(boolean, "tree"), right=union(boolean, "tree"))])[0])})

    def test_shredAndAssemble(self):
        def addData(columns):
            for c in columns.values():
                c.data = []
                c.pointer = 0
            return columns

        def shred(obj, schema, columns, name):
            if isinstance(name, string_types):
                name = ColumnName(name)

            self.assertIn(obj, schema)

            if isinstance(columns.get(name), RecursiveColumn):
                columns[name].data.append(obj)

            elif isinstance(schema, Null):
                pass

            elif isinstance(schema, (Boolean, Number)):
                self.assertIn(name, columns)
                columns[name].data.append(obj)

            elif isinstance(schema, String):
                self.assertIn(name, columns)
                columns[name].data.extend(list(obj))

                if schema.charset != "bytes" or schema.fewest != schema.most:
                    sizeName = name.size()
                    self.assertIn(sizeName, columns)
                    columns[sizeName].data.append(len(obj))

            elif isinstance(schema, Collection):
                if schema.fewest != schema.most:
                    size = len(obj)
                    for n, c in columns.items():
                        if n.startswith(name) and n.endswith(ColumnName.sizeSuffix):
                            c.data.append(size)

                items = schema.items
                for x in obj:
                    shred(x, items, columns, name)

            elif isinstance(schema, Record):
                for n, t in schema.fields.items():
                    self.assertTrue(hasattr(obj, n))
                    shred(getattr(obj, n), t, columns, name.rec(n))

            elif isinstance(schema, Union):
                tag = columns[name.tag()]
                for i, p in enumerate(tag.possibilities):
                    if obj in p:
                        tag.data.append(i)
                        shred(obj, p, columns, name.pos(i))
                        break

            else:
                raise ProgrammingError("unexpected type: {0} {1}".format(type(schema), schema))

        def assemble(schema, columns, name):
            if isinstance(name, string_types):
                name = ColumnName(name)

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
                if schema.charset == "bytes" and schema.fewest == schema.most:
                    size = schema.fewest
                else:
                    sizeCol = columns[name.size()]
                    size = sizeCol.data[sizeCol.pointer]
                    sizeCol.pointer += 1

                if schema.charset == "bytes":
                    if sys.version_info[0] >= 3:
                        out = bytes(col.data[col.pointer:col.pointer + size])
                    else:
                        out = b"".join(col.data[col.pointer:col.pointer + size])
                else:
                    out = u"".join(col.data[col.pointer:col.pointer + size])
                col.pointer += size
                return out

            elif isinstance(schema, Collection):
                if schema.fewest == schema.most:
                    size = schema.fewest
                else:
                    size = None
                    for n, c in columns.items():
                        if n.startswith(name) and n.endswith(ColumnName.sizeSuffix):
                            size = c.data[c.pointer]
                            c.pointer += 1
                    self.assertIsNotNone(size)

                items = schema.items
                return [assemble(items, columns, name) for i in xrange(size)]

            elif isinstance(schema, Record):
                names = sorted(schema.fields.keys())
                return namedtuple("tmp", names)(*[assemble(schema.fields[n], columns, name.rec(n)) for n in names])

            elif isinstance(schema, Union):
                tag = columns[name.tag()]
                pos = tag.data[tag.pointer]
                tag.pointer += 1
                return assemble(tag.possibilities[pos], columns, name.pos(pos))

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

        checkShredAndAssemble(null, [None, None, None, None, None])

        checkShredAndAssemble(collection(real), [[], [1.1], [2.2, 3.3], []])

        checkShredAndAssemble(collection(null), [[], [None], [None, None], [None, None, None]])

        checkShredAndAssemble(collection(null, 2, 2), [[None, None], [None, None], [None, None]])

        checkShredAndAssemble(collection(real, 1, 1), [[1.1], [2.2], [3.3], [4.4]])

        checkShredAndAssemble(collection(collection(real)), [[], [[1.1]], [[], [2.2, 3.3]]])

        checkShredAndAssemble(collection(collection(real, 1, 1)), [[], [[1.1]], [[2.2], [3.3]]])

        checkShredAndAssemble(collection(collection(real), 1, 1), [[[]], [[1.1]], [[2.2, 3.3]]])
        
        checkShredAndAssemble(string, [b"one", b"two", b"three"])

        checkShredAndAssemble(string("bytes", 3, 3), [b"one", b"two", b"thr"])

        checkShredAndAssemble(collection(string), [[], [b"one", b"two"], [b"three"]])

        checkShredAndAssemble(collection(string("bytes", 3, 3)), [[], [b"one", b"two"], [b"thr"]])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(record(a=real, b=real), [rec1(1.1, 2.2), rec1(3.3, 4.4)])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(record(a=real, b=string), [rec1(1.1, b"two"), rec1(3.3, b"four"), rec1(5.5, b"six")])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(record(a=real, b=string("bytes", 3, 3)), [rec1(1.1, b"two"), rec1(3.3, b"for"), rec1(5.5, b"six")])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(collection(record(a=real, b=string)), [[], [rec1(1.1, b"two")], [rec1(3.3, b"four"), rec1(5.5, b"six")]])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(collection(record(a=real, b=real)), [[], [rec1(1.1, 2.2), rec1(3.3, 4.4)]])

        rec1 = namedtuple("rec1", ["x", "y"])
        rec2 = namedtuple("rec2", ["a", "b"])
        checkShredAndAssemble(record(x=real, y=collection(record(a=real, b=collection(real)))),
                  [rec1(1, [rec2(2, [3, 4]), rec2(5, [])]),
                   rec1(6, [rec2(9, [10, 11])])])

        rec1 = namedtuple("rec1", ["x", "y"])
        rec2 = namedtuple("rec2", ["a", "b"])
        checkShredAndAssemble(record(x=real, y=collection(record(a=real, b=collection(real)), 1, 1)),
                  [rec1(1, [rec2(2, [3, 4])]),
                   rec1(6, [rec2(9, [10, 11])])])

        rec1 = namedtuple("rec1", ["x", "y"])
        rec2 = namedtuple("rec2", ["a", "b"])
        checkShredAndAssemble(record(x=real, y=collection(record(a=real, b=collection(real, 2, 2)))),
                  [rec1(1, [rec2(2, [3, 4]), rec2(5, [6, 7])]),
                   rec1(6, [rec2(9, [10, 11])])])

        rec1 = namedtuple("rec1", ["a", "b"])
        checkShredAndAssemble(record("rec1", a=real, b=collection("rec1")), [rec1(1.1, []), rec1(2.2, [rec1(3.3, [])])])

        checkShredAndAssemble(union(boolean, integer), [1, True, 2, False, 3])

        checkShredAndAssemble(collection(union(boolean, integer)), [[], [1], [True, 2], [False], [3, 4]])

        checkShredAndAssemble(collection(union(boolean, integer), 2, 2), [[1, 2], [3, True], [False, 4], [True, False]])

        checkShredAndAssemble(collection(union(integer, string)), [[], [1], [b"two", 3], [b"four"], [5, 6]])

        checkShredAndAssemble(collection(union(integer, string("bytes", 3, 3))), [[], [1], [b"two", 3], [b"for"], [5, 6]])

        rec1 = namedtuple("rec1", ["x", "y"])
        checkShredAndAssemble(union(integer, record(x=real, y=real)), [1, rec1(2.2, 3.3), 4, rec1(5.5, 6.6), 7])

        checkShredAndAssemble(union(real, collection(real)), [1.1, [2.2, 3.3], 4.4, [5.5, 6.6], 7.7])

        checkShredAndAssemble(union(real, collection(real, 2, 2)), [1.1, [2.2, 3.3], 4.4, [5.5, 6.6], 7.7])

        rec1 = namedtuple("rec1", ["x", "y"])
        checkShredAndAssemble(union(integer, collection(record(x=real, y=real))), [1, [], 2, [rec1(3.3, 4.4), rec1(5.5, 6.6)], 7])

        rec1 = namedtuple("rec1", ["x", "y"])
        checkShredAndAssemble(union(integer, collection(record(x=real, y=real), 1, 1)), [1, [rec1(3.3, 4.4)], 2, [rec1(5.5, 6.6)], 7])

        checkShredAndAssemble(union(null, real), [1.1, None, 2.2, None, 3.3])
