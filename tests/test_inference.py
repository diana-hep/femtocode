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
from femtocode.inference import *

class TestInference(unittest.TestCase):
    def runTest(self):
        pass

    def test_literal(self):
        self.assertEqual(literal(impossible, "==", 5), impossible)
        self.assertEqual(literal(impossible, "!=", 5), impossible)

        self.assertEqual(literal(null, "==", None), null)
        self.assertEqual(literal(null, "==", 5), impossible)
        self.assertEqual(literal(null, "!=", None), impossible)
        self.assertEqual(literal(null, "!=", 5), null)

        # no intervals on booleans: "x == True" will be converted into "x" before typecheck
        self.assertEqual(literal(boolean, "==", True), boolean)
        self.assertEqual(literal(boolean, "==", False), boolean)
        self.assertEqual(literal(boolean, "!=", True), boolean)
        self.assertEqual(literal(boolean, "!=", False), boolean)
        self.assertEqual(literal(boolean, "==", 5), impossible)
        self.assertEqual(literal(boolean, "!=", 5), boolean)

        self.assertEqual(literal(union(null, boolean), "==", True), boolean)
        self.assertEqual(literal(union(null, boolean), "==", False), boolean)
        self.assertEqual(literal(union(null, boolean), "==", None), null)
        self.assertEqual(literal(union(null, boolean), "==", 5), impossible)

        self.assertEqual(literal(union(null, boolean), "!=", True), union(null, boolean))
        self.assertEqual(literal(union(null, boolean), "!=", False), union(null, boolean))
        self.assertEqual(literal(union(null, boolean), "!=", None), boolean)
        self.assertEqual(literal(union(null, boolean), "!=", 5), union(null, boolean))

        self.assertEqual(literal(integer, "==", 5), integer(5, 5))
        self.assertEqual(literal(integer(0, 10), "==", 5), integer(5, 5))
        self.assertEqual(literal(integer(10, 20), "==", 5), impossible)
        self.assertEqual(literal(integer, "!=", 5), union(integer(max=4), integer(min=6)))
        self.assertEqual(literal(integer(0, 10), "!=", 5), union(integer(0, 4), integer(6, 10)))
        self.assertEqual(literal(integer(10, 20), "!=", 5), integer(10, 20))

        self.assertEqual(literal(real, "==", 5), integer(5, 5))
        self.assertEqual(literal(real, "==", 3.14), real(3.14, 3.14))
        self.assertEqual(literal(real(0, 10), "==", 5), integer(5, 5))
        self.assertEqual(literal(real(0, 10), "==", 3.14), real(3.14, 3.14))
        self.assertEqual(literal(real(10, 20), "==", 5), impossible)
        self.assertEqual(literal(real(0, 10), "==", 10), integer(10, 10))
        self.assertEqual(literal(real(0, almost(10)), "==", 10), impossible)
        self.assertEqual(literal(union(real(0, 7), integer(5, 10)), "==", 6), integer(6, 6))

        self.assertEqual(literal(real, "!=", 5), union(real(max=almost(5)), real(min=almost(5))))
        self.assertEqual(literal(real, "!=", 3.14), union(real(max=almost(3.14)), real(min=almost(3.14))))
        self.assertEqual(literal(real(0, 10), "!=", 5), union(real(0, almost(5)), real(almost(5), 10)))
        self.assertEqual(literal(real(0, 10), "!=", 3.14), union(real(0, almost(3.14)), real(almost(3.14), 10)))
        self.assertEqual(literal(real(10, 20), "!=", 5), real(10, 20))
        self.assertEqual(literal(real(0, 10), "!=", 10), real(0, almost(10)))
        self.assertEqual(literal(real(0, almost(10)), "!=", 10), real(0, almost(10)))
        self.assertEqual(literal(union(real(0, 7), integer(5, 10)), "!=", 6), union(real(min=0.0, max=almost(6.0)), real(min=almost(6.0), max=7.0), integer(min=8, max=10)))

        self.assertEqual(literal(string, "==", b"hello"), string("bytes", 5, 5))
        self.assertEqual(literal(string, "==", u"hello"), impossible)
        self.assertEqual(literal(string("unicode"), "==", u"hello"), string("unicode", 5, 5))
        self.assertEqual(literal(string, "!=", b"hello"), string)
        self.assertEqual(literal(string, "!=", u"hello"), string)
        self.assertEqual(literal(string("unicode"), "!=", u"hello"), string("unicode"))

        self.assertEqual(literal(collection(real), "==", []), empty)
        self.assertEqual(literal(collection(real), "==", [3.14]), collection(real(3.14, 3.14), 1, 1))
        self.assertEqual(literal(collection(real), "==", [2.71, 3.14]), collection(union(real(2.71, 2.71), real(3.14, 3.14)), 2, 2))
        self.assertEqual(literal(collection(real), "==", [1, 2, 3]), collection(integer(1, 3), 3, 3))
        self.assertEqual(literal(collection(real), "==", [2, 4, 6]), collection(union(integer(2, 2), integer(4, 4), integer(6, 6)), 3, 3))
        self.assertEqual(literal(collection(real(0, 5)), "==", [2.71, 3.14]), collection(union(real(2.71, 2.71), real(3.14, 3.14)), 2, 2))
        self.assertEqual(literal(collection(real(3, 5)), "==", [2.71, 3.14]), impossible)
        self.assertEqual(literal(collection(real, 0, 5), "==", [2.71, 3.14]), collection(union(real(2.71, 2.71), real(3.14, 3.14)), 2, 2))
        self.assertEqual(literal(collection(real, 3, 5), "==", [2.71, 3.14]), impossible)

        self.assertEqual(literal(collection(real), "!=", []), collection(real, fewest=1))
        self.assertEqual(literal(collection(real), "!=", [3.14]), collection(real))
        self.assertEqual(literal(collection(real), "!=", [2.71, 3.14]), collection(real))
        self.assertEqual(literal(collection(real(0, 5)), "!=", [2.71, 3.14]), collection(real(0, 5)))
        self.assertEqual(literal(collection(real(3, 5)), "!=", [2.71, 3.14]), collection(real(3, 5)))
        self.assertEqual(literal(collection(real, 0, 5), "!=", [2.71, 3.14]), collection(real, 0, 5))
        self.assertEqual(literal(collection(real, 3, 5), "!=", [2.71, 3.14]), collection(real, 3, 5))

        self.assertEqual(literal(record(f=union(integer, string)), "==", namedtuple("tmp", ["f"])(3)), record(f=integer(3, 3)))
        self.assertEqual(literal(record(f=union(integer, string)), "==", namedtuple("tmp", ["f"])(b"hey")), record(f=string("bytes", 3, 3)))
        self.assertEqual(literal(record(one=integer, two=real, three=string), "==", namedtuple("tmp", ["one", "two", "three"])(1, 2.2, b"3")), record(one=integer(1, 1), two=real(2.2, 2.2), three=string(fewest=1, most=1)))
        tree = namedtuple("tree", ["left", "right"])
        self.assertEqual(literal(resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0], "==", tree(tree(None, None), tree(None, tree(None, None)))), record(left=record(left=null, right=null), right=record(right=record(left=null, right=null), left=null)))

        self.assertEqual(literal(record(f=union(integer, string)), "!=", namedtuple("tmp", ["f"])(3)), record(f=union(integer, string)))
        self.assertEqual(literal(record(f=union(integer, string)), "!=", namedtuple("tmp", ["f"])(b"hey")), record(f=union(integer, string)))
        self.assertEqual(literal(record(one=integer, two=real, three=string), "!=", namedtuple("tmp", ["one", "two", "three"])(1, 2.2, b"3")), record(one=integer, two=real, three=string))
        tree = namedtuple("tree", ["left", "right"])
        self.assertEqual(literal(resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0], "!=", tree(tree(None, None), tree(None, tree(None, None)))), resolve([record("tree", left=union(null, "tree"), right=union(null, "tree"))])[0])

        self.assertEqual(literal(union(vector(real, 3), vector(real, 4)), "==", [1, 2, 3]), vector(integer(1, 3), 3))
        self.assertEqual(literal(union(vector(real, 3), vector(real, 4)), "==", [1, 2, 3, 4]), vector(integer(1, 4), 4))

        self.assertEqual(literal(real, ">", 3), real(almost(3), almost(inf)))
        self.assertEqual(literal(real, ">=", 3), real(3, almost(inf)))
        self.assertEqual(literal(real, "<", 3), real(almost(-inf), almost(3)))
        self.assertEqual(literal(real, "<=", 3), real(almost(-inf), 3))

        self.assertEqual(literal(real(-10, -5), ">", 3), impossible)
        self.assertEqual(literal(real(-10, -5), ">=", 3), impossible)
        self.assertEqual(literal(real(5, 10), "<", 3), impossible)
        self.assertEqual(literal(real(5, 10), "<=", 3), impossible)

        self.assertEqual(literal(extended(3, inf), ">", 3), extended(almost(3), inf))
        self.assertEqual(literal(extended(3, inf), ">=", 3), extended(3, inf))
        self.assertEqual(literal(extended(-inf, 3), "<", 3), extended(-inf, almost(3)))
        self.assertEqual(literal(extended(-inf, 3), "<=", 3), extended(-inf, 3))

        self.assertEqual(literal(extended(almost(3), inf), ">", 3), extended(almost(3), inf))
        self.assertEqual(literal(extended(almost(3), inf), ">=", 3), extended(almost(3), inf))
        self.assertEqual(literal(extended(-inf, almost(3)), "<", 3), extended(-inf, almost(3)))
        self.assertEqual(literal(extended(-inf, almost(3)), "<=", 3), extended(-inf, almost(3)))

        self.assertEqual(literal(string, "size>", 3), string(fewest=4))
        self.assertEqual(literal(string, "size>=", 3), string(fewest=3))
        self.assertEqual(literal(string, "size<", 3), string(most=2))
        self.assertEqual(literal(string, "size<=", 3), string(most=3))

        self.assertEqual(literal(string(fewest=3), "size>", 3), string(fewest=4))
        self.assertEqual(literal(string(fewest=3), "size>=", 3), string(fewest=3))
        self.assertEqual(literal(string(most=3), "size<", 3), string(most=2))
        self.assertEqual(literal(string(most=3), "size<=", 3), string(most=3))

        self.assertEqual(literal(string(most=3), "size>", 3), impossible)
        self.assertEqual(literal(string(most=3), "size>=", 3), string(fewest=3, most=3))
        self.assertEqual(literal(string(fewest=3), "size<", 3), impossible)
        self.assertEqual(literal(string(fewest=3), "size<=", 3), string(fewest=3, most=3))

        self.assertEqual(literal(collection(real), "size>", 3), collection(real, fewest=4))
        self.assertEqual(literal(collection(real), "size>=", 3), collection(real, fewest=3))
        self.assertEqual(literal(collection(real), "size<", 3), collection(real, most=2))
        self.assertEqual(literal(collection(real), "size<=", 3), collection(real, most=3))

        self.assertEqual(literal(collection(real, fewest=3), "size>", 3), collection(real, fewest=4))
        self.assertEqual(literal(collection(real, fewest=3), "size>=", 3), collection(real, fewest=3))
        self.assertEqual(literal(collection(real, most=3), "size<", 3), collection(real, most=2))
        self.assertEqual(literal(collection(real, most=3), "size<=", 3), collection(real, most=3))

        self.assertEqual(literal(collection(real, most=3), "size>", 3), impossible)
        self.assertEqual(literal(collection(real, most=3), "size>=", 3), collection(real, fewest=3, most=3))
        self.assertEqual(literal(collection(real, fewest=3), "size<", 3), impossible)
        self.assertEqual(literal(collection(real, fewest=3), "size<=", 3), collection(real, fewest=3, most=3))

        self.assertEqual(literal(union(collection(real, ordered=True), collection(string, ordered=False)), "ordered", None), collection(real, ordered=True))
        self.assertEqual(literal(union(collection(real, ordered=True), collection(string, ordered=False)), "notordered", None), collection(string, ordered=False))
