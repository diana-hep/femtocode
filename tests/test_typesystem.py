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
from collections import namedtuple

from femtocode.typesystem import *

class TestTypesystem(unittest.TestCase):
    def runTest(self):
        pass

    def test_constructors(self):
        self.assertEqual(impossible, Impossible())
        self.assertEqual(repr(impossible), "impossible")
        self.assertEqual(pretty(impossible), "impossible")
        self.assertTrue(impossible not in impossible)
        self.assertTrue(3.14 not in impossible)

        self.assertEqual(null, Null())
        self.assertEqual(repr(null), "null")
        self.assertEqual(pretty(null), "null")
        self.assertTrue(null in null)
        self.assertTrue(impossible not in null)
        self.assertTrue(None in null)
        self.assertTrue(3.14 not in null)

        self.assertEqual(boolean, Boolean())
        self.assertEqual(repr(boolean), "boolean")
        self.assertEqual(pretty(boolean), "boolean")
        self.assertTrue(boolean in boolean)
        self.assertTrue(null not in boolean)
        self.assertTrue(True in boolean)
        self.assertTrue(False in boolean)
        self.assertTrue(3.14 not in boolean)

        self.assertEqual(integer, Number(almost(-inf), almost(inf), True))
        self.assertEqual(real, Number(almost(-inf), almost(inf), False))
        self.assertEqual(extended, Number(-inf, inf, False))
        self.assertEqual(integer(almost(2), almost(11)), Number(3, 10, True))
        self.assertEqual(integer(almost(2.5), almost(10.5)), Number(3, 10, True))
        self.assertEqual(integer(2.5, 10.5), Number(3, 10, True))
        self.assertEqual(repr(integer), "integer")
        self.assertEqual(repr(integer(3)), "integer(min=3, max=almost(inf))")
        self.assertEqual(repr(integer(3, 10)), "integer(min=3, max=10)")
        self.assertEqual(repr(real), "real")
        self.assertEqual(repr(real(3)), "real(min=3.0, max=almost(inf))")
        self.assertEqual(repr(real(3, 10)), "real(min=3.0, max=10.0)")
        self.assertEqual(repr(extended), "extended")
        self.assertEqual(repr(extended(3)), "extended(min=3.0, max=inf)")
        self.assertEqual(repr(extended(3, 10)), "real(min=3.0, max=10.0)")
        self.assertEqual(pretty(integer), "integer")
        self.assertEqual(pretty(integer(3)), "integer(min=3, max=almost(inf))")
        self.assertEqual(pretty(integer(3, 10)), "integer(min=3, max=10)")
        self.assertEqual(pretty(real), "real")
        self.assertEqual(pretty(real(3)), "real(min=3.0, max=almost(inf))")
        self.assertEqual(pretty(real(3, 10)), "real(min=3.0, max=10.0)")
        self.assertEqual(pretty(extended), "extended")
        self.assertEqual(pretty(extended(3)), "extended(min=3.0, max=inf)")
        self.assertEqual(pretty(extended(3, 10)), "real(min=3.0, max=10.0)")
        self.assertTrue(null not in integer)
        self.assertTrue(boolean not in integer)
        self.assertTrue(integer in integer)
        self.assertTrue(integer in real)
        self.assertTrue(integer in extended)
        self.assertTrue(real not in integer)
        self.assertTrue(real in real)
        self.assertTrue(real in extended)
        self.assertTrue(extended not in integer)
        self.assertTrue(extended not in real)
        self.assertTrue(extended in extended)
        self.assertTrue(integer(3, 10) in integer)
        self.assertTrue(integer(3, 10) in real(3, 10))
        self.assertTrue(real(3, 10) in real(3, 10))
        self.assertTrue(real(3, 10) in real(3, 11))
        self.assertTrue(real(3, 10) in real(2, 10))
        self.assertTrue(real(3, almost(10)) in real(3, 10))
        self.assertTrue(real(almost(3), 10) in real(3, 10))
        self.assertTrue(real(almost(3), almost(10)) in real(3, 10))
        self.assertTrue(real(3, 11) not in real(3, 10))
        self.assertTrue(real(2, 10) not in real(3, 10))
        self.assertTrue(real(3, 10) not in real(3, almost(10)))
        self.assertTrue(real(3, 10) not in real(almost(3), 10))
        self.assertTrue(real(3, 10) not in real(almost(3), almost(10)))
        self.assertTrue(extended(-inf, 5) in extended)
        self.assertTrue(extended(5, inf) in extended)
        self.assertTrue(extended(almost(-inf), inf) in extended)
        self.assertTrue(extended(-inf, almost(inf)) in extended)
        self.assertTrue(-3 in integer)
        self.assertTrue(-3.14 not in integer)
        self.assertTrue(-3 not in integer(0))
        self.assertTrue(-3 in real)
        self.assertTrue(-3.14 in real)
        self.assertTrue(-3.14 not in real(0))
        self.assertTrue(2.9 not in real(3, 10))
        self.assertTrue(3 in real(3, 10))
        self.assertTrue(3.1 in real(3, 10))
        self.assertTrue(9.9 in real(3, 10))
        self.assertTrue(10 in real(3, 10))
        self.assertTrue(10.1 not in real(3, 10))
        self.assertTrue(2.9 not in real(almost(3), almost(10)))
        self.assertTrue(3 not in real(almost(3), almost(10)))
        self.assertTrue(3.1 in real(almost(3), almost(10)))
        self.assertTrue(9.9 in real(almost(3), almost(10)))
        self.assertTrue(10 not in real(almost(3), almost(10)))
        self.assertTrue(10.1 not in real(almost(3), almost(10)))
        self.assertTrue(-3 in extended)
        self.assertTrue(-3.14 in extended)
        self.assertTrue(-3.14 not in extended(0))
        self.assertTrue(float("inf") in extended)
        self.assertTrue(float("-inf") in extended)
        self.assertTrue(float("nan") not in extended)

        self.assertEqual(string, String("bytes", 0, almost(inf)))
        self.assertEqual(repr(string), "string")
        self.assertEqual(repr(string(fewest=1)), "string(fewest=1)")
        self.assertEqual(repr(string(most=5)), "string(most=5)")
        self.assertEqual(repr(string("unicode")), "string(\"unicode\")")
        self.assertEqual(repr(string("unicode", 1, 5)), "string(\"unicode\", fewest=1, most=5)")
        self.assertEqual(pretty(string), "string")
        self.assertEqual(pretty(string(fewest=1)), "string(fewest=1)")
        self.assertEqual(pretty(string(most=5)), "string(most=5)")
        self.assertEqual(pretty(string("unicode")), "string(\"unicode\")")
        self.assertEqual(pretty(string("unicode", 1, 5)), "string(\"unicode\", fewest=1, most=5)")
        self.assertTrue(null not in string)
        self.assertTrue(string in string)
        self.assertTrue(string("unicode") not in string)
        self.assertTrue(string not in string("unicode"))
        self.assertTrue(string(fewest=1) in string)
        self.assertTrue(string(most=1) in string)
        self.assertTrue(string(fewest=3, most=10) in string)
        self.assertTrue(string(fewest=3, most=10) in string(fewest=3, most=10))
        self.assertTrue(string(fewest=3, most=10) in string(fewest=2, most=10))
        self.assertTrue(string(fewest=3, most=10) in string(fewest=3, most=11))
        self.assertTrue(string not in string(fewest=1))
        self.assertTrue(string not in string(most=1))
        self.assertTrue(string not in string(fewest=3, most=10))
        self.assertTrue(string(fewest=2, most=10) not in string(fewest=3, most=10))
        self.assertTrue(string(fewest=3, most=11) not in string(fewest=3, most=10))
        self.assertTrue(b"hello" in string)
        self.assertTrue(u"hello" not in string)
        self.assertTrue(u"hello" in string("unicode"))
        self.assertTrue(b"hello" in string("bytes", 5, 5))
        self.assertTrue(b"hello" not in string("bytes", 4, 4))
        
        self.assertEqual(collection(real, most=0), empty)
        self.assertEqual(collection(string, most=0), empty)
        self.assertEqual(collection(real), Collection(real, 0, almost(inf), False))
        self.assertEqual(collection(real, 1), Collection(real, 1, almost(inf), False))
        self.assertEqual(collection(real, 1, 10), Collection(real, 1, 10, False))
        self.assertEqual(collection(real, ordered=True), Collection(real, 0, almost(inf), True))
        self.assertEqual(vector(real, 3), Collection(real, 3, 3, True))
        self.assertEqual(matrix(real, 2, 3), Collection(Collection(real, 3, 3, True), 2, 2, True))
        self.assertEqual(tensor(real, 1, 2, 3), Collection(Collection(Collection(real, 3, 3, True), 2, 2, True), 1, 1, True))
        self.assertEqual(repr(empty), "empty")
        self.assertEqual(repr(collection(real, most=0)), "empty")
        self.assertEqual(repr(collection(real)), "collection(real)")
        self.assertEqual(repr(vector(real, 3)), "vector(real, 3)")
        self.assertEqual(repr(matrix(real, 2, 3)), "matrix(real, 2, 3)")
        self.assertEqual(repr(tensor(real, 1, 2, 3)), "tensor(real, 1, 2, 3)")
        self.assertEqual(repr(collection(real, 3, 3, True)), "vector(real, 3)")
        self.assertEqual(repr(collection(collection(real, 3, 3, True), 2, 2, True)), "matrix(real, 2, 3)")
        self.assertEqual(repr(collection(collection(collection(real, 3, 3, True), 2, 2, True), 1, 1, True)), "tensor(real, 1, 2, 3)")
        self.assertEqual(repr(collection(real, 3, 3, False)), "collection(real, fewest=3, most=3)")
        self.assertEqual(repr(collection(collection(real, 3, 3, False), 2, 2, True)), "vector(collection(real, fewest=3, most=3), 2)")
        self.assertEqual(repr(collection(collection(collection(real, 3, 3, False), 2, 2, True), 1, 1, True)), "matrix(collection(real, fewest=3, most=3), 1, 2)")

        self.assertEqual(pretty(empty), """empty""")
        self.assertEqual(pretty(collection(real, most=0)), """empty""")
        self.assertEqual(pretty(collection(real)), """collection(
  real
  )""")
        self.assertEqual(pretty(vector(real, 3)), """vector(
  real,
  3)""")
        self.assertEqual(pretty(matrix(real, 2, 3)), """matrix(
  real,
  2, 3)""")
        self.assertEqual(pretty(tensor(real, 1, 2, 3)), """tensor(
  real,
  1, 2, 3)""")
        self.assertEqual(pretty(collection(real, 3, 3, True)), """vector(
  real,
  3)""")
        self.assertEqual(pretty(collection(collection(real, 3, 3, True), 2, 2, True)), """matrix(
  real,
  2, 3)""")
        self.assertEqual(pretty(collection(collection(collection(real, 3, 3, True), 2, 2, True), 1, 1, True)), """tensor(
  real,
  1, 2, 3)""")
        self.assertEqual(pretty(collection(real, 3, 3, False)), """collection(
  real,
  fewest=3, most=3)""")
        self.assertEqual(pretty(collection(collection(real, 3, 3, False), 2, 2, True)), """vector(
  collection(
    real,
    fewest=3, most=3),
  2)""")
        self.assertEqual(pretty(collection(collection(collection(real, 3, 3, False), 2, 2, True), 1, 1, True)), """matrix(
  collection(
    real,
    fewest=3, most=3),
  1, 2)""")

        self.assertTrue(null not in collection(real))
        self.assertTrue(collection(real) in collection(real))
        self.assertTrue(collection(real, ordered=True) in collection(real))
        self.assertTrue(collection(real) not in collection(real, ordered=True))
        self.assertTrue(collection(integer) in collection(real))
        self.assertTrue(collection(real) not in collection(integer))
        self.assertTrue(collection(real) not in collection(string))
        self.assertTrue(collection(real, fewest=1) in collection(real))
        self.assertTrue(collection(real, most=1) in collection(real))
        self.assertTrue(collection(real, fewest=3, most=10) in collection(real))
        self.assertTrue(collection(real, fewest=3, most=10) in collection(real, fewest=3, most=10))
        self.assertTrue(collection(real, fewest=3, most=10) in collection(real, fewest=2, most=10))
        self.assertTrue(collection(real, fewest=3, most=10) in collection(real, fewest=3, most=11))
        self.assertTrue(collection(real) not in collection(real, fewest=1))
        self.assertTrue(collection(real) not in collection(real, most=1))
        self.assertTrue(collection(real) not in collection(real, fewest=3, most=10))
        self.assertTrue(collection(real, fewest=2, most=10) not in collection(real, fewest=3, most=10))
        self.assertTrue(collection(real, fewest=3, most=11) not in collection(real, fewest=3, most=10))
        self.assertTrue(vector(real, 3) in collection(real, ordered=True))
        self.assertTrue(vector(real, 3) in collection(real))
        self.assertTrue(vector(real, 3) in collection(real, 2, 10))
        self.assertTrue(vector(real, 3) in collection(real, 3, 3))
        self.assertTrue(matrix(real, 2, 3) in collection(collection(real)))
        self.assertTrue(matrix(real, 2, 3) in collection(collection(real, 3, 3), 2, 2))
        self.assertTrue(tensor(real, 1, 2, 3) in collection(collection(collection(real))))
        self.assertTrue(tensor(real, 1, 2, 3) in collection(collection(collection(real, 3, 3), 2, 2), 1, 1))
        self.assertTrue(tensor(real, 1, 2, 3) in collection(collection(collection(real, ordered=True))))
        self.assertTrue(tensor(real, 1, 2, 3) in collection(collection(collection(real), ordered=True)))
        self.assertTrue(tensor(real, 1, 2, 3) in collection(collection(collection(real)), ordered=True))
        self.assertTrue(collection(real, ordered=True) not in vector(real, 3))
        self.assertTrue(collection(real) not in vector(real, 3))
        self.assertTrue(collection(real, 2, 10) not in vector(real, 3))
        self.assertTrue(collection(real, 3, 3) not in vector(real, 3))
        self.assertTrue(collection(real, 3, 3, ordered=True) in vector(real, 3))
        self.assertTrue(collection(collection(real)) not in matrix(real, 2, 3))
        self.assertTrue(collection(collection(real, 3, 3), 2, 2) not in matrix(real, 2, 3))
        self.assertTrue(collection(collection(real, 3, 3, ordered=True), 2, 2, ordered=True) in matrix(real, 2, 3))
        self.assertTrue(collection(collection(collection(real))) not in tensor(real, 1, 2, 3))
        self.assertTrue(collection(collection(collection(real, 3, 3), 2, 2), 1, 1) not in tensor(real, 1, 2, 3))
        self.assertTrue(collection(collection(collection(real, 3, 3, ordered=True), 2, 2, ordered=True), 1, 1, ordered=True) in tensor(real, 1, 2, 3))
        self.assertTrue(collection(collection(collection(real, ordered=True))) not in tensor(real, 1, 2, 3))
        self.assertTrue(collection(collection(collection(real), ordered=True)) not in tensor(real, 1, 2, 3))
        self.assertTrue(collection(collection(collection(real)), ordered=True) not in tensor(real, 1, 2, 3))
        self.assertTrue(None not in collection(real))
        self.assertTrue([] in collection(real))
        self.assertTrue([3] in collection(real))
        self.assertTrue([3.14] in collection(real))
        self.assertTrue([3.14] not in collection(integer))
        self.assertTrue({3} in collection(real))
        self.assertTrue({3.14} in collection(real))
        self.assertTrue({3.14} not in collection(integer))
        self.assertTrue({3} not in collection(real, ordered=True))
        self.assertTrue({3.14} not in collection(real, ordered=True))
        self.assertTrue([3] not in vector(real, 3))
        self.assertTrue([1, 2, 3] in vector(real, 3))
        self.assertTrue([[1, 2, 3], [4, 5, 6]] in matrix(real, 2, 3))
        self.assertTrue([[[99]]] in tensor(real, 1, 1, 1))

        self.assertEqual(record(one=integer, two=real, three=string), Record({"one": integer, "two": real, "three": string}))
        self.assertEqual(repr(record(one=integer, two=real, three=string)), "record(one=integer, three=string, two=real)")
        self.assertEqual(pretty(record(one=integer, two=real, three=string)), """record(
  one=integer,
  three=string,
  two=real
  )""")
        self.assertTrue(null not in record(one=integer, two=real, three=string))
        self.assertTrue(record(one=integer, two=real, three=string) in record(one=integer, two=real, three=string))
        self.assertTrue(record(one=integer, two=real, three=string) in record(one=integer, two=real))
        self.assertTrue(record(one=integer, two=real) not in record(one=integer, two=real, three=string))
        self.assertTrue(record(one=integer, two=real, THREE=string) not in record(one=integer, two=real, three=string))
        self.assertTrue(record(one=integer, two=real, THREE=string, three=string) in record(one=integer, two=real, three=string))
        self.assertTrue(None not in record(one=integer, two=real, three=string))
        self.assertTrue(namedtuple("tmp", ["one", "two", "three"])(1, 2.2, b"3") in record(one=integer, two=real, three=string))
        self.assertTrue(namedtuple("tmp", ["one", "two", "three", "four"])(1, 2.2, b"3", b"4") in record(one=integer, two=real, three=string))
        self.assertTrue(namedtuple("tmp", ["one", "two"])(1, 2.2) not in record(one=integer, two=real, three=string))

    def test_recursive(self):
        self.assertEqual(repr(resolve([record(a="placeholder", b=integer(alias="placeholder"))])[0]), "record(a=integer(alias=\"placeholder\"), b=\"placeholder\")")
        self.assertEqual(pretty(resolve([record(a="placeholder", b=integer(alias="placeholder"))])[0]), """record(
  a=integer(alias="placeholder"),
  b="placeholder"
  )""")

        un, deux = record(a="placeholder", b=integer(alias="placeholder")), record(a="placeholder", b="placeholder")
        one, two = resolve([un, deux])
        self.assertEqual(one, two)
        self.assertEqual(hash(one), hash(two))
        self.assertEqual(one, un)
        self.assertEqual(hash(one), hash(un))

        un = collection("recursive", alias="recursive")
        one = resolve([un])[0]
        self.assertEqual(one, one)
        self.assertEqual(one, one.items)
        self.assertEqual(hash(one), hash(one.items))
        self.assertEqual(one, un)
        self.assertEqual(one, un.items)
        self.assertEqual(hash(one), hash(un.items))

        self.assertEqual(repr(resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0]), "record(\"tree\", left=union(null, \"tree\"), right=union(null, \"tree\"))")
        self.assertEqual(pretty(resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0]), """record("tree", 
  left=union(
    null,
    "tree"
    ),
  right=union(
    null,
    "tree"
    )
  )""")

    def test_sets(self):
        self.assertEqual(impossible, union(impossible))
        self.assertEqual(impossible, union(impossible, impossible))
        self.assertEqual(impossible, union(impossible, impossible, impossible))
        self.assertEqual(impossible, intersection(impossible))
        self.assertEqual(impossible, intersection(impossible, impossible))
        self.assertEqual(impossible, intersection(impossible, impossible, impossible))
        self.assertEqual(impossible, difference(impossible, impossible))

        self.assertEqual(null, union(null))
        self.assertEqual(null, union(null, null))
        self.assertEqual(null, union(null, null, null))
        self.assertEqual(impossible, union(null, impossible))
        self.assertEqual(null, intersection(null))
        self.assertEqual(null, intersection(null, null))
        self.assertEqual(null, intersection(null, null, null))
        self.assertEqual(impossible, intersection(null, impossible))
        self.assertEqual(impossible, difference(null, null))
        self.assertEqual(impossible, difference(null, impossible))
        self.assertEqual(impossible, difference(impossible, null))

        self.assertEqual(boolean, union(boolean))
        self.assertEqual(boolean, union(boolean, boolean))
        self.assertEqual(boolean, union(boolean, boolean, boolean))
        self.assertEqual(impossible, union(boolean, impossible))
        self.assertEqual(Union([null, boolean]), union(null, boolean))
        self.assertEqual(boolean, intersection(boolean))
        self.assertEqual(boolean, intersection(boolean, boolean))
        self.assertEqual(boolean, intersection(boolean, boolean, boolean))
        self.assertEqual(impossible, intersection(boolean, impossible))
        self.assertEqual(impossible, intersection(null, boolean))
        self.assertEqual(impossible, difference(boolean, boolean))
        self.assertEqual(boolean, difference(boolean, null))
        self.assertEqual(null, difference(null, boolean))

        self.assertEqual(Union([integer, boolean]), union(boolean, integer))
        self.assertEqual(impossible, intersection(boolean, integer))
        self.assertEqual(boolean, difference(boolean, integer))
        self.assertEqual(integer, difference(integer, boolean))

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = integer(amin, amax)
                            b = integer(bmin, bmax)

                            c = union(a, b)
                            for value in range(1, 14):
                                if value in a or value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = intersection(a, b)
                            for value in range(1, 14):
                                if value in a and value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(a, b)
                            for value in range(1, 14):
                                if value in a and value not in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(b, a)
                            for value in range(1, 14):
                                if value in b and value not in a:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

        for amin in almost(-inf), -inf, almost(3), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in almost(3), 3, 4, 9, almost(10), 10, 11, almost(inf), inf:
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and not ((isinstance(amin, almost) or isinstance(amax, almost)) and amin.real == amax.real) and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = real(amin, amax)
                            b = real(bmin, bmax)

                            c = union(a, b)
                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in a or value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = intersection(a, b)
                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in a and value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(a, b)
                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in a and value not in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(b, a)
                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in b and value not in a:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = integer(amin, amax)
                            b = real(bmin, bmax)

                            c = union(a, b)

                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in a or value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = intersection(a, b)
                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in a and value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(a, b)
                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in a and value not in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(b, a)
                            for value in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                if value in b and value not in a:
                                    self.assertTrue(value in c)
                                # ## difference(real, integer) is conservative because it could result in a huge expression otherwise
                                # else:
                                #     self.assertTrue(value not in c)

        self.assertEqual(Union([string("bytes"), string("unicode")]), union(string("bytes"), string("unicode")))
        self.assertEqual(impossible, intersection(string("bytes"), string("unicode")))
        self.assertEqual(string("bytes"), difference(string("bytes"), string("unicode")))
        self.assertEqual(string("unicode"), difference(string("unicode"), string("bytes")))
        self.assertEqual(impossible, difference(string, string))
        self.assertEqual(impossible, difference(string("unicode"), string("unicode")))

        for amin in 0, 3:
            for bmin in 0, 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = string(fewest=amin, most=amax)
                            b = string(fewest=bmin, most=bmax)

                            c = union(a, b)
                            for value in ["x" * x for x in range(1, 14)]:
                                if value in a or value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = intersection(a, b)
                            for value in ["x" * x for x in range(1, 14)]:
                                if value in a and value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(a, b)
                            for value in ["x" * x for x in range(1, 14)]:
                                if value in a and value not in b:
                                    self.assertTrue(value in c)

                            c = difference(b, a)
                            for value in ["x" * x for x in range(1, 14)]:
                                if value in b and value not in a:
                                    self.assertTrue(value in c)

        self.assertEqual(Union([collection(integer), collection(string)]), union(collection(integer), collection(string)))
        self.assertEqual(Union([collection(integer(3, 10)), collection(integer(2, 6))]), union(collection(integer(3, 10)), collection(integer(2, 6))))
        self.assertEqual(Union([collection(integer(3, 10), 3, 10), collection(integer(2, 6), 2, 6)]), union(collection(integer(3, 10), 3, 10), collection(integer(2, 6), 2, 6)))
        self.assertEqual(Union([collection(integer(3, 10), ordered=True), collection(integer(2, 6), ordered=False)]), union(collection(integer(3, 10), ordered=True), collection(integer(2, 6), ordered=False)))
        self.assertEqual(collection(integer, ordered=False), union(collection(integer, ordered=True), collection(integer, ordered=False)))
        self.assertEqual(collection(integer, ordered=True), union(collection(integer, ordered=True), collection(integer, ordered=True)))
        self.assertEqual(Union([collection(integer), collection(integer(3, 10))]), union(collection(integer), collection(integer(3, 10))))
        self.assertEqual(collection(integer), union(collection(integer), empty))
        self.assertEqual(Union([collection(integer, 3, 10), empty]), union(collection(integer, 3, 10), empty))
        self.assertEqual(collection(integer, ordered=True), union(collection(integer, ordered=True), empty))
        self.assertEqual(collection(integer, ordered=False), union(collection(integer, ordered=False), empty))

        self.assertEqual(impossible, intersection(collection(integer), collection(string)))
        self.assertEqual(collection(integer(3, 6)), intersection(collection(integer(3, 10)), collection(integer(2, 6))))
        self.assertEqual(collection(integer(3, 6), 3, 6), intersection(collection(integer(3, 10), 3, 10), collection(integer(2, 6), 2, 6)))
        self.assertEqual(collection(integer(3, 6), ordered=False), intersection(collection(integer(3, 10), ordered=True), collection(integer(2, 6), ordered=False)))
        self.assertEqual(collection(integer(3, 6), ordered=True), intersection(collection(integer(3, 10), ordered=True), collection(integer(2, 6), ordered=True)))
        self.assertEqual(empty, intersection(collection(integer), empty))
        self.assertEqual(impossible, intersection(collection(integer, 3, 10), empty))

        self.assertEqual(collection(integer), difference(collection(integer), collection(string)))
        self.assertEqual(collection(string), difference(collection(string), collection(integer)))
        self.assertEqual(impossible, difference(collection(integer), collection(integer)))
        self.assertEqual(collection(integer(7, 10)), difference(collection(integer(3, 10)), collection(integer(2, 6))))
        self.assertEqual(Union([collection(integer(7, 10), 3, 10), collection(integer(3, 6), 7, 10)]), difference(collection(integer(3, 10), 3, 10), collection(integer(2, 6), 2, 6)))
        self.assertEqual(Union([collection(integer(min=23, max=27), most=2), collection(integer(min=23, max=27), fewest=8, most=10), collection(union(integer(min=20, max=22), integer(min=28, max=30)), most=10)]), difference(collection(integer(20, 30), 0, 10), collection(integer(23, 27), 3, 7)))
        self.assertEqual(collection(integer(7, 10), ordered=False), difference(collection(integer(3, 10), ordered=False), collection(integer(2, 6), ordered=True)))
        self.assertEqual(collection(integer(7, 10), ordered=True), difference(collection(integer(3, 10), ordered=True), collection(integer(2, 6), ordered=True)))
        self.assertEqual(collection(integer(7, 10), ordered=True), difference(collection(integer(3, 10), ordered=True), collection(integer(2, 6), ordered=False)))
        self.assertEqual(impossible, difference(empty, empty))
        self.assertEqual(empty, difference(empty, collection(integer)))
        self.assertEqual(collection(integer, fewest=1), difference(collection(integer), empty))

        for amin in 0, 3:
            for bmin in 0, 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = collection(string(fewest=amin, most=amax), fewest=amin, most=amax)
                            b = collection(string(fewest=bmin, most=bmax), fewest=bmin, most=bmax)

                            c = union(a, b)
                            for value in [["x" * x] * x for x in range(1, 14)]:
                                if value in a or value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = intersection(a, b)
                            for value in [["x" * x] * x for x in range(1, 14)]:
                                if value in a and value in b:
                                    self.assertTrue(value in c)
                                else:
                                    self.assertTrue(value not in c)

                            c = difference(a, b)
                            for value in [["x" * x] * x for x in range(1, 14)]:
                                if value in a and value not in b:
                                    self.assertTrue(value in c)

                            c = difference(b, a)
                            for value in [["x" * x] * x for x in range(1, 14)]:
                                if value in b and value not in a:
                                    self.assertTrue(value in c)

        self.assertEqual(record(one=integer, two=real, three=string), union(record(one=integer, two=real, three=string), record(one=integer, two=real, three=string)))
        self.assertEqual(Union([record(one=integer, two=real, three=string("bytes")), record(one=integer, two=real, three=string("unicode"))]), union(record(one=integer, two=real, three=string("bytes")), record(one=integer, two=real, three=string("unicode"))))
        self.assertEqual(Union([record(one=integer(0, 7), two=real, three=string), record(one=integer(3, 10), two=real, three=string)]), union(record(one=integer(0, 7), two=real, three=string), record(one=integer(3, 10), two=real, three=string)))
        self.assertEqual(Union([record(one=integer, two=real, three=string), record(one=integer, two=real, three=string, four=string)]), union(record(one=integer, two=real, three=string), record(one=integer, two=real, three=string, four=string)))

        self.assertEqual(record(one=integer, two=real, three=string), intersection(record(one=integer, two=real, three=string), record(one=integer, two=real, three=string)))
        self.assertEqual(record(one=integer(3, 7), two=real, three=string), intersection(record(one=integer(3, 10), two=real, three=string), record(one=integer(0, 7), two=real, three=string)))
        self.assertEqual(record(one=integer(3, 7), two=real(3, 7), three=string), intersection(record(one=integer(3, 10), two=real(3, 10), three=string), record(one=integer(0, 7), two=real(0, 7), three=string)))
        self.assertEqual(impossible, intersection(record(one=integer, two=real, three=string("bytes")), record(one=integer, two=real, three=string("unicode"))))

        self.assertEqual(impossible, difference(record(one=integer, two=real, three=string), record(one=integer, two=real, three=string)))
        self.assertEqual(record(one=integer, two=real, three=string("bytes")), difference(record(one=integer, two=real, three=string("bytes")), record(one=integer, two=real, three=string("unicode"))))
        self.assertEqual(record(one=integer, two=real, three=string("unicode")), difference(record(one=integer, two=real, three=string("unicode")), record(one=integer, two=real, three=string("bytes"))))
        self.assertEqual(record(one=integer(0, 5), two=real, three=string), difference(record(one=integer(0, 5), two=real, three=string), record(one=integer(6, 10), two=real, three=string)))
        self.assertEqual(record(one=integer(0, 5), two=real, three=string("bytes")), difference(record(one=integer(0, 5), two=real, three=string("bytes")), record(one=integer(6, 10), two=real, three=string("unicode"))))
        self.assertEqual(record(one=integer(6, 10), two=real, three=string("unicode")), difference(record(one=integer(6, 10), two=real, three=string("unicode")), record(one=integer(0, 5), two=real, three=string("bytes"))))
        self.assertEqual(record(one=integer(0, 5), two=real, three=string), difference(record(one=integer(0, 10), two=real, three=string), record(one=integer(6, 10), two=real, three=string)))
        self.assertEqual(Union([record(one=integer(0, 5), two=real, three=string("bytes")), record(one=integer(6, 10), two=real, three=string("bytes"))]), difference(record(one=integer(0, 10), two=real, three=string("bytes")), record(one=integer(6, 10), two=real, three=string("unicode"))))
        self.assertEqual(Union([record(one=integer(min=0, max=5), three=string, two=real(min=0, max=10)), record(one=integer(min=6, max=10), three=string, two=real(min=0, max=almost(6.0)))]), difference(record(one=integer(0, 10), two=real(0, 10), three=string), record(one=integer(6, 10), two=real(6, 10), three=string)))

        self.assertEqual(intersection(integer, union(integer, string)), integer)
        self.assertEqual(intersection(union(integer, string), integer), integer)
        self.assertEqual(intersection(record(f=integer), record(f=union(integer, string))), record(f=integer))
        self.assertEqual(intersection(record(f=union(integer, string)), record(f=integer)), record(f=integer))


    def test_inference(self):
        self.assertEqual(infer(impossible, "==", 5), impossible)
        self.assertEqual(infer(impossible, "!=", 5), impossible)

        self.assertEqual(infer(null, "==", None), null)
        self.assertEqual(infer(null, "==", 5), impossible)
        self.assertEqual(infer(null, "!=", None), impossible)
        self.assertEqual(infer(null, "!=", 5), null)

        # no intervals on booleans: "x == True" will be converted into "x" before typecheck
        self.assertEqual(infer(boolean, "==", True), boolean)
        self.assertEqual(infer(boolean, "==", False), boolean)
        self.assertEqual(infer(boolean, "!=", True), boolean)
        self.assertEqual(infer(boolean, "!=", False), boolean)
        self.assertEqual(infer(boolean, "==", 5), impossible)
        self.assertEqual(infer(boolean, "!=", 5), boolean)

        self.assertEqual(infer(union(null, boolean), "==", True), boolean)
        self.assertEqual(infer(union(null, boolean), "==", False), boolean)
        self.assertEqual(infer(union(null, boolean), "==", None), null)
        self.assertEqual(infer(union(null, boolean), "==", 5), impossible)

        self.assertEqual(infer(union(null, boolean), "!=", True), union(null, boolean))
        self.assertEqual(infer(union(null, boolean), "!=", False), union(null, boolean))
        self.assertEqual(infer(union(null, boolean), "!=", None), boolean)
        self.assertEqual(infer(union(null, boolean), "!=", 5), union(null, boolean))

        self.assertEqual(infer(integer, "==", 5), integer(5, 5))
        self.assertEqual(infer(integer(0, 10), "==", 5), integer(5, 5))
        self.assertEqual(infer(integer(10, 20), "==", 5), impossible)
        self.assertEqual(infer(integer, "!=", 5), union(integer(max=4), integer(min=6)))
        self.assertEqual(infer(integer(0, 10), "!=", 5), union(integer(0, 4), integer(6, 10)))
        self.assertEqual(infer(integer(10, 20), "!=", 5), integer(10, 20))

        self.assertEqual(infer(real, "==", 5), integer(5, 5))
        self.assertEqual(infer(real, "==", 3.14), real(3.14, 3.14))
        self.assertEqual(infer(real(0, 10), "==", 5), integer(5, 5))
        self.assertEqual(infer(real(0, 10), "==", 3.14), real(3.14, 3.14))
        self.assertEqual(infer(real(10, 20), "==", 5), impossible)
        self.assertEqual(infer(real(0, 10), "==", 10), integer(10, 10))
        self.assertEqual(infer(real(0, almost(10)), "==", 10), impossible)
        self.assertEqual(infer(union(real(0, 7), integer(5, 10)), "==", 6), integer(6, 6))

        self.assertEqual(infer(real, "!=", 5), union(real(max=almost(5)), real(min=almost(5))))
        self.assertEqual(infer(real, "!=", 3.14), union(real(max=almost(3.14)), real(min=almost(3.14))))
        self.assertEqual(infer(real(0, 10), "!=", 5), union(real(0, almost(5)), real(almost(5), 10)))
        self.assertEqual(infer(real(0, 10), "!=", 3.14), union(real(0, almost(3.14)), real(almost(3.14), 10)))
        self.assertEqual(infer(real(10, 20), "!=", 5), real(10, 20))
        self.assertEqual(infer(real(0, 10), "!=", 10), real(0, almost(10)))
        self.assertEqual(infer(real(0, almost(10)), "!=", 10), real(0, almost(10)))
        self.assertEqual(infer(union(real(0, 7), integer(5, 10)), "!=", 6), union(real(min=0.0, max=almost(6.0)), real(min=almost(6.0), max=7.0), integer(min=8, max=10)))

        self.assertEqual(infer(string, "==", b"hello"), string("bytes", 5, 5))
        self.assertEqual(infer(string, "==", u"hello"), impossible)
        self.assertEqual(infer(string("unicode"), "==", u"hello"), string("unicode", 5, 5))
        self.assertEqual(infer(string, "!=", b"hello"), string)
        self.assertEqual(infer(string, "!=", u"hello"), string)
        self.assertEqual(infer(string("unicode"), "!=", u"hello"), string("unicode"))

        self.assertEqual(infer(collection(real), "==", []), empty)
        self.assertEqual(infer(collection(real), "==", [3.14]), collection(real(3.14, 3.14), 1, 1))
        self.assertEqual(infer(collection(real), "==", [2.71, 3.14]), collection(union(real(2.71, 2.71), real(3.14, 3.14)), 2, 2))
        self.assertEqual(infer(collection(real), "==", [1, 2, 3]), collection(integer(1, 3), 3, 3))
        self.assertEqual(infer(collection(real), "==", [2, 4, 6]), collection(union(integer(2, 2), integer(4, 4), integer(6, 6)), 3, 3))
        self.assertEqual(infer(collection(real(0, 5)), "==", [2.71, 3.14]), collection(union(real(2.71, 2.71), real(3.14, 3.14)), 2, 2))
        self.assertEqual(infer(collection(real(3, 5)), "==", [2.71, 3.14]), impossible)
        self.assertEqual(infer(collection(real, 0, 5), "==", [2.71, 3.14]), collection(union(real(2.71, 2.71), real(3.14, 3.14)), 2, 2))
        self.assertEqual(infer(collection(real, 3, 5), "==", [2.71, 3.14]), impossible)

        self.assertEqual(infer(collection(real), "!=", []), collection(real, fewest=1))
        self.assertEqual(infer(collection(real), "!=", [3.14]), collection(real))
        self.assertEqual(infer(collection(real), "!=", [2.71, 3.14]), collection(real))
        self.assertEqual(infer(collection(real(0, 5)), "!=", [2.71, 3.14]), collection(real(0, 5)))
        self.assertEqual(infer(collection(real(3, 5)), "!=", [2.71, 3.14]), collection(real(3, 5)))
        self.assertEqual(infer(collection(real, 0, 5), "!=", [2.71, 3.14]), collection(real, 0, 5))
        self.assertEqual(infer(collection(real, 3, 5), "!=", [2.71, 3.14]), collection(real, 3, 5))

        self.assertEqual(infer(record(f=union(integer, string)), "==", namedtuple("tmp", ["f"])(3)), record(f=integer(3, 3)))
        self.assertEqual(infer(record(f=union(integer, string)), "==", namedtuple("tmp", ["f"])(b"hey")), record(f=string("bytes", 3, 3)))
        self.assertEqual(infer(record(one=integer, two=real, three=string), "==", namedtuple("tmp", ["one", "two", "three"])(1, 2.2, b"3")), record(one=integer(1, 1), two=real(2.2, 2.2), three=string(fewest=1, most=1)))
        tree = namedtuple("tree", ["left", "right"])
        self.assertEqual(infer(resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0], "==", tree(tree(None, None), tree(None, tree(None, None)))), record(left=record(left=null, right=null), right=record(right=record(left=null, right=null), left=null)))

        self.assertEqual(infer(record(f=union(integer, string)), "!=", namedtuple("tmp", ["f"])(3)), record(f=union(integer, string)))
        self.assertEqual(infer(record(f=union(integer, string)), "!=", namedtuple("tmp", ["f"])(b"hey")), record(f=union(integer, string)))
        self.assertEqual(infer(record(one=integer, two=real, three=string), "!=", namedtuple("tmp", ["one", "two", "three"])(1, 2.2, b"3")), record(one=integer, two=real, three=string))
        tree = namedtuple("tree", ["left", "right"])
        self.assertEqual(infer(resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0], "!=", tree(tree(None, None), tree(None, tree(None, None)))), resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0])

        self.assertEqual(infer(union(vector(real, 3), vector(real, 4)), "==", [1, 2, 3]), vector(integer(1, 3), 3))
        self.assertEqual(infer(union(vector(real, 3), vector(real, 4)), "==", [1, 2, 3, 4]), vector(integer(1, 4), 4))

        self.assertEqual(infer(real, ">", 3), real(almost(3), almost(inf)))
        self.assertEqual(infer(real, ">=", 3), real(3, almost(inf)))
        self.assertEqual(infer(real, "<", 3), real(almost(-inf), almost(3)))
        self.assertEqual(infer(real, "<=", 3), real(almost(-inf), 3))

        self.assertEqual(infer(real(-10, -5), ">", 3), impossible)
        self.assertEqual(infer(real(-10, -5), ">=", 3), impossible)
        self.assertEqual(infer(real(5, 10), "<", 3), impossible)
        self.assertEqual(infer(real(5, 10), "<=", 3), impossible)

        self.assertEqual(infer(extended(3, inf), ">", 3), extended(almost(3), inf))
        self.assertEqual(infer(extended(3, inf), ">=", 3), extended(3, inf))
        self.assertEqual(infer(extended(-inf, 3), "<", 3), extended(-inf, almost(3)))
        self.assertEqual(infer(extended(-inf, 3), "<=", 3), extended(-inf, 3))

        self.assertEqual(infer(extended(almost(3), inf), ">", 3), extended(almost(3), inf))
        self.assertEqual(infer(extended(almost(3), inf), ">=", 3), extended(almost(3), inf))
        self.assertEqual(infer(extended(-inf, almost(3)), "<", 3), extended(-inf, almost(3)))
        self.assertEqual(infer(extended(-inf, almost(3)), "<=", 3), extended(-inf, almost(3)))

        self.assertEqual(infer(string, "size>", 3), string(fewest=4))
        self.assertEqual(infer(string, "size>=", 3), string(fewest=3))
        self.assertEqual(infer(string, "size<", 3), string(most=2))
        self.assertEqual(infer(string, "size<=", 3), string(most=3))

        self.assertEqual(infer(string(fewest=3), "size>", 3), string(fewest=4))
        self.assertEqual(infer(string(fewest=3), "size>=", 3), string(fewest=3))
        self.assertEqual(infer(string(most=3), "size<", 3), string(most=2))
        self.assertEqual(infer(string(most=3), "size<=", 3), string(most=3))

        self.assertEqual(infer(string(most=3), "size>", 3), impossible)
        self.assertEqual(infer(string(most=3), "size>=", 3), string(fewest=3, most=3))
        self.assertEqual(infer(string(fewest=3), "size<", 3), impossible)
        self.assertEqual(infer(string(fewest=3), "size<=", 3), string(fewest=3, most=3))

        self.assertEqual(infer(collection(real), "size>", 3), collection(real, fewest=4))
        self.assertEqual(infer(collection(real), "size>=", 3), collection(real, fewest=3))
        self.assertEqual(infer(collection(real), "size<", 3), collection(real, most=2))
        self.assertEqual(infer(collection(real), "size<=", 3), collection(real, most=3))

        self.assertEqual(infer(collection(real, fewest=3), "size>", 3), collection(real, fewest=4))
        self.assertEqual(infer(collection(real, fewest=3), "size>=", 3), collection(real, fewest=3))
        self.assertEqual(infer(collection(real, most=3), "size<", 3), collection(real, most=2))
        self.assertEqual(infer(collection(real, most=3), "size<=", 3), collection(real, most=3))

        self.assertEqual(infer(collection(real, most=3), "size>", 3), impossible)
        self.assertEqual(infer(collection(real, most=3), "size>=", 3), collection(real, fewest=3, most=3))
        self.assertEqual(infer(collection(real, fewest=3), "size<", 3), impossible)
        self.assertEqual(infer(collection(real, fewest=3), "size<=", 3), collection(real, fewest=3, most=3))

        self.assertEqual(infer(union(collection(real, ordered=True), collection(string, ordered=False)), "ordered", None), collection(real, ordered=True))
        self.assertEqual(infer(union(collection(real, ordered=True), collection(string, ordered=False)), "notordered", None), collection(string, ordered=False))
