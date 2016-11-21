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
        self.assertEqual(repr(real(3)), "real(min=3, max=almost(inf))")
        self.assertEqual(repr(real(3, 10)), "real(min=3, max=10)")
        self.assertEqual(repr(extended), "extended")
        self.assertEqual(repr(extended(3)), "extended(min=3, max=inf)")
        self.assertEqual(repr(extended(3, 10)), "real(min=3, max=10)")
        self.assertEqual(pretty(integer), "integer")
        self.assertEqual(pretty(integer(3)), "integer(min=3, max=almost(inf))")
        self.assertEqual(pretty(integer(3, 10)), "integer(min=3, max=10)")
        self.assertEqual(pretty(real), "real")
        self.assertEqual(pretty(real(3)), "real(min=3, max=almost(inf))")
        self.assertEqual(pretty(real(3, 10)), "real(min=3, max=10)")
        self.assertEqual(pretty(extended), "extended")
        self.assertEqual(pretty(extended(3)), "extended(min=3, max=inf)")
        self.assertEqual(pretty(extended(3, 10)), "real(min=3, max=10)")
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

        self.assertEqual(collection(real), Collection(real, 0, almost(inf), False))
        self.assertEqual(collection(real, 1), Collection(real, 1, almost(inf), False))
        self.assertEqual(collection(real, 1, 10), Collection(real, 1, 10, False))
        self.assertEqual(collection(real, ordered=True), Collection(real, 0, almost(inf), True))
        self.assertEqual(vector(real, 3), Collection(real, 3, 3, True))
        self.assertEqual(matrix(real, 2, 3), Collection(Collection(real, 3, 3, True), 2, 2, True))
        self.assertEqual(tensor(real, 1, 2, 3), Collection(Collection(Collection(real, 3, 3, True), 2, 2, True), 1, 1, True))
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
        self.assertTrue(namedtuple("tmp", ["one", "two", "three"])(1, 2.2, "3") in record(one=integer, two=real, three=string))
        self.assertTrue(namedtuple("tmp", ["one", "two", "three", "four"])(1, 2.2, "3", "4") in record(one=integer, two=real, three=string))
        self.assertTrue(namedtuple("tmp", ["one", "two"])(1, 2.2) not in record(one=integer, two=real, three=string))