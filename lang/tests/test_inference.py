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
import unittest

from femtocode.inference import *
from femtocode.typesystem import *

class TestInference(unittest.TestCase):
    def runTest(self):
        pass

    def test_add(self):
        for amin in almost(-inf), 3:
            for bmin in almost(-inf), 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = integer(amin, amax)
                            b = integer(bmin, bmax)
                            c = add(a, b)
                            if not isinstance(c, Impossible):
                                for x in range(1, 14):
                                    for y in range(1, 14):
                                        if x in a and y in b:
                                            self.assertTrue((x + y) in c)

        for amin in almost(-inf), -inf, almost(3), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in almost(3), 3, 4, 9, almost(10), 10, 11, almost(inf), inf:
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and not ((isinstance(amin, almost) or isinstance(amax, almost)) and amin.real == amax.real) and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = real(amin, amax)
                            b = real(bmin, bmax)
                            c = add(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x + y) in c)

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = integer(amin, amax)
                            b = real(bmin, bmax)
                            c = add(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x + y) in c)

    def test_subtract(self):
        for amin in almost(-inf), 3:
            for bmin in almost(-inf), 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = integer(amin, amax)
                            b = integer(bmin, bmax)
                            c = subtract(a, b)
                            if not isinstance(c, Impossible):
                                for x in range(1, 14):
                                    for y in range(1, 14):
                                        if x in a and y in b:
                                            self.assertTrue((x - y) in c)

        for amin in almost(-inf), -inf, almost(3), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in almost(3), 3, 4, 9, almost(10), 10, 11, almost(inf), inf:
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and not ((isinstance(amin, almost) or isinstance(amax, almost)) and amin.real == amax.real) and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = real(amin, amax)
                            b = real(bmin, bmax)
                            c = subtract(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x - y) in c)

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = integer(amin, amax)
                            b = real(bmin, bmax)
                            c = subtract(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x - y) in c)

    def test_multiply(self):
        for amin in almost(-inf), 3:
            for bmin in almost(-inf), 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = integer(amin, amax)
                            b = integer(bmin, bmax)
                            c = multiply(a, b)
                            if not isinstance(c, Impossible):
                                for x in range(1, 14):
                                    for y in range(1, 14):
                                        if x in a and y in b:
                                            self.assertTrue((x * y) in c)

        for amin in almost(-inf), -inf, almost(3), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in almost(3), 3, 4, 9, almost(10), 10, 11, almost(inf), inf:
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and not ((isinstance(amin, almost) or isinstance(amax, almost)) and amin.real == amax.real) and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = real(amin, amax)
                            b = real(bmin, bmax)
                            c = multiply(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x * y) in c)

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = integer(amin, amax)
                            b = real(bmin, bmax)
                            c = multiply(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x * y) in c)

    def test_divide(self):
        for amin in almost(-inf), 3:
            for bmin in almost(-inf), 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = integer(amin, amax)
                            b = integer(bmin, bmax)
                            c = divide(a, b)
                            if not isinstance(c, Impossible):
                                for x in range(1, 14):
                                    for y in range(1, 14):
                                        if x in a and y in b:
                                            self.assertTrue((1.0 * x / y) in c)

        for amin in almost(-inf), -inf, almost(3), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in almost(3), 3, 4, 9, almost(10), 10, 11, almost(inf), inf:
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and not ((isinstance(amin, almost) or isinstance(amax, almost)) and amin.real == amax.real) and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = real(amin, amax)
                            b = real(bmin, bmax)
                            c = divide(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((1.0 * x / y) in c)

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = integer(amin, amax)
                            b = real(bmin, bmax)
                            c = divide(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((1.0 * x / y) in c)

    def test_power(self):
        def powie(x, y):
            if math.isnan(x) and y == 0:
                return 1.0
            elif math.isnan(x) or math.isnan(y):
                return float("nan")
            elif x == 0 and y < 0:
                return float("inf")
            elif math.isinf(y):
                if x == 1 or x == -1:
                    return float("nan")
                elif abs(x) < 1:
                    if y > 0:
                        return 0.0
                    else:
                        return float("inf")
                else:
                    if y > 0:
                        return float("inf")
                    else:
                        return 0.0
            elif math.isinf(x):
                if y == 0:
                    return 1.0
                elif y < 0:
                    return 0.0
                else:
                    if x < 0 and round(y) == y and y % 2 == 1:
                        return float("-inf")
                    else:
                        return float("inf")
            elif x < 0 and round(y) != y:
                return float("nan")
            else:
                try:
                    return math.pow(x, y)
                except OverflowError:
                    if abs(y) < 1:
                        if x < 0:
                            return float("nan")
                        else:
                            return 1.0
                    else:
                        if (abs(x) > 1 and y < 0) or (abs(x) < 1 and y > 0):
                            return 0.0
                        else:
                            return float("inf")

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = integer(amin, amax)
                            b = integer(bmin, bmax)
                            c = power(a, b)
                            if not isinstance(c, Impossible):
                                for x in range(1, 14):
                                    for y in range(1, 14):
                                        if x in a and y in b:
                                            self.assertTrue(powie(x, y) in c)

        for amin in almost(-inf), -inf, almost(3), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in almost(3), 3, 4, 9, almost(10), 10, 11, almost(inf), inf:
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and not ((isinstance(amin, almost) or isinstance(amax, almost)) and amin.real == amax.real) and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = real(amin, amax)
                            b = real(bmin, bmax)
                            c = power(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue(powie(x, y) in c)

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = integer(amin, amax)
                            b = real(bmin, bmax)
                            c = power(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue(powie(x, y) in c)

    def test_modulo(self):
        for amin in almost(-inf), 3:
            for bmin in almost(-inf), 2, 3, 4, 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, 10, 11, 12, almost(inf):
                        if amin <= amax and bmin <= bmax:
                            a = integer(amin, amax)
                            b = integer(bmin, bmax)
                            c = modulo(a, b)
                            if not isinstance(c, Impossible):
                                for x in range(1, 14):
                                    for y in range(1, 14):
                                        if x in a and y in b:
                                            self.assertTrue((x % y) in c)

        for amin in almost(-inf), -inf, almost(3), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in almost(3), 3, 4, 9, almost(10), 10, 11, almost(inf), inf:
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and not ((isinstance(amin, almost) or isinstance(amax, almost)) and amin.real == amax.real) and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = real(amin, amax)
                            b = real(bmin, bmax)
                            c = modulo(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x % y) in c)

        for amin in almost(-inf), 3:
            for bmin in almost(-inf), -inf, 2, almost(3), 3, 4, almost(10), 10:
                for amax in 3, 4, 9, 10, 11, almost(inf):
                    for bmax in 2, 3, 4, 8, 9, almost(10), 10, 11, 12, almost(inf), inf:
                        if amin <= amax and \
                           bmin <= bmax and not ((isinstance(bmin, almost) or isinstance(bmax, almost)) and bmin.real == bmax.real):
                            a = integer(amin, amax)
                            b = real(bmin, bmax)
                            c = modulo(a, b)
                            if not isinstance(c, Impossible):
                                for x in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                    for y in -inf, 1, 2, 2.9, 3, 3.1, 4, 5, 6, 7, 8, 9, 9.9, 10, 10.1, 11, 12, 13, 14, inf:
                                        if x in a and y in b:
                                            self.assertTrue((x % y) in c)

    def test_lessthan(self):
        self.assertEqual(inequality("<", real(0, 1), real(2, 3)),         (boolean(True), real(0, 1), real(2, 3)))
        self.assertEqual(inequality("<", real(0, 1.5), real(1.5, 3)),     (boolean, real(0, 1.5), real(1.5, 3)))
        self.assertEqual(inequality("<", real(0, 2), real(1, 3)),         (boolean, real(0, 2), real(1, 3)))

        self.assertEqual(inequality("<", real(0, 3), real(2, 3)),         (boolean, real(0, almost(3)), real(2, 3)))
        self.assertEqual(inequality("<", real(0, 3), real(2, almost(3))), (boolean, real(0, almost(3)), real(2, almost(3))))
        self.assertEqual(inequality("<", real(0, 3), real(1, 2)),         (boolean, real(0, almost(2)), real(1, 2)))
        self.assertEqual(inequality("<", real(0, 3), real(1, almost(2))), (boolean, real(0, almost(2)), real(1, almost(2))))

        self.assertEqual(inequality("<", real(1, 2), real(1, 3)),         (boolean, real(1, 2), real(almost(1), 3)))
        self.assertEqual(inequality("<", real(1, 2), real(almost(1), 3)), (boolean, real(1, 2), real(almost(1), 3)))
        self.assertEqual(inequality("<", real(almost(1), 2), real(1, 3)), (boolean, real(almost(1), 2), real(almost(1), 3)))
        self.assertEqual(inequality("<", real(1, 2), real(0, 3)),         (boolean, real(1, 2), real(almost(1), 3)))

        self.assertEqual(inequality("<", real(1, 3), real(0, 2)),         (boolean, real(1, almost(2)), real(almost(1), 2)))
        self.assertEqual(inequality("<", real(almost(1), 3), real(0, 2)), (boolean, real(almost(1), almost(2)), real(almost(1), 2)))
        self.assertEqual(inequality("<", real(1, 3), real(0, almost(2))), (boolean, real(1, almost(2)), real(almost(1), almost(2))))

        self.assertEqual(inequality("<", real(2, 3), real(0, 1)), (impossible, None, None))

        values = [0, 0.001, 0.999, 1.0, 1.001, 1.999, 2.0, 2.001, 2.999, 3.0]
        edges = [0, almost(0), 1, almost(1), 2, almost(2), 3, almost(3)]
        for leftmin in edges:
            for leftmax in edges:
                try:
                    left = real(leftmin, leftmax)
                except FemtocodeError:
                    pass
                else:
                    for rightmin in edges:
                        for rightmax in edges:
                            try:
                                right = real(rightmin, rightmax)
                            except FemtocodeError:
                                pass
                            else:
                                boo, leftconstraint, rightconstraint = inequality("<", left, right)
                                if isinstance(boo, Impossible):
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    self.assertFalse(x < y)

                                else:
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    if x < y:
                                                        self.assertTrue(x in leftconstraint and y in rightconstraint)

    def test_lessequal(self):
        self.assertEqual(inequality("<=", real(0, 1), real(2, 3)),         (boolean(True), real(0, 1), real(2, 3)))
        self.assertEqual(inequality("<=", real(0, 1.5), real(1.5, 3)),     (boolean(True), real(0, 1.5), real(1.5, 3)))
        self.assertEqual(inequality("<=", real(0, 2), real(1, 3)),         (boolean, real(0, 2), real(1, 3)))

        self.assertEqual(inequality("<=", real(0, 3), real(2, 3)),         (boolean, real(0, 3), real(2, 3)))
        self.assertEqual(inequality("<=", real(0, 3), real(2, almost(3))), (boolean, real(0, almost(3)), real(2, almost(3))))
        self.assertEqual(inequality("<=", real(0, 3), real(1, 2)),         (boolean, real(0, 2), real(1, 2)))
        self.assertEqual(inequality("<=", real(0, 3), real(1, almost(2))), (boolean, real(0, almost(2)), real(1, almost(2))))

        self.assertEqual(inequality("<=", real(1, 2), real(1, 3)),         (boolean, real(1, 2), real(1, 3)))
        self.assertEqual(inequality("<=", real(1, 2), real(almost(1), 3)), (boolean, real(1, 2), real(almost(1), 3)))
        self.assertEqual(inequality("<=", real(almost(1), 2), real(1, 3)), (boolean, real(almost(1), 2), real(almost(1), 3)))
        self.assertEqual(inequality("<=", real(1, 2), real(0, 3)),         (boolean, real(1, 2), real(1, 3)))

        self.assertEqual(inequality("<=", real(1, 3), real(0, 2)),         (boolean, real(1, 2), real(1, 2)))
        self.assertEqual(inequality("<=", real(almost(1), 3), real(0, 2)), (boolean, real(almost(1), 2), real(almost(1), 2)))
        self.assertEqual(inequality("<=", real(1, 3), real(0, almost(2))), (boolean, real(1, almost(2)), real(1, almost(2))))

        self.assertEqual(inequality("<=", real(2, 3), real(0, 1)), (impossible, None, None))

        values = [0, 0.001, 0.999, 1.0, 1.001, 1.999, 2.0, 2.001, 2.999, 3.0]
        edges = [0, almost(0), 1, almost(1), 2, almost(2), 3, almost(3)]
        for leftmin in edges:
            for leftmax in edges:
                try:
                    left = real(leftmin, leftmax)
                except FemtocodeError:
                    pass
                else:
                    for rightmin in edges:
                        for rightmax in edges:
                            try:
                                right = real(rightmin, rightmax)
                            except FemtocodeError:
                                pass
                            else:
                                boo, leftconstraint, rightconstraint = inequality("<=", left, right)
                                if isinstance(boo, Impossible):
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    self.assertFalse(x <= y)

                                else:
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    if x <= y:
                                                        self.assertTrue(x in leftconstraint and y in rightconstraint)

    def test_greaterthan(self):
        self.assertEqual(inequality(">", real(2, 3), real(0, 1)),         (boolean(True), real(2, 3), real(0, 1)))
        self.assertEqual(inequality(">", real(1.5, 3), real(0, 1.5)),     (boolean, real(1.5, 3), real(0, 1.5)))
        self.assertEqual(inequality(">", real(1, 3), real(0, 2)),         (boolean, real(1, 3), real(0, 2)))

        values = [0, 0.001, 0.999, 1.0, 1.001, 1.999, 2.0, 2.001, 2.999, 3.0]
        edges = [0, almost(0), 1, almost(1), 2, almost(2), 3, almost(3)]
        for leftmin in edges:
            for leftmax in edges:
                try:
                    left = real(leftmin, leftmax)
                except FemtocodeError:
                    pass
                else:
                    for rightmin in edges:
                        for rightmax in edges:
                            try:
                                right = real(rightmin, rightmax)
                            except FemtocodeError:
                                pass
                            else:
                                boo, leftconstraint, rightconstraint = inequality(">", left, right)
                                if isinstance(boo, Impossible):
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    self.assertFalse(x > y)

                                else:
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    if x > y:
                                                        self.assertTrue(x in leftconstraint and y in rightconstraint)

    def test_greaterequal(self):
        self.assertEqual(inequality(">=", real(2, 3), real(0, 1)),         (boolean(True), real(2, 3), real(0, 1)))
        self.assertEqual(inequality(">=", real(1.5, 3), real(0, 1.5)),     (boolean(True), real(1.5, 3), real(0, 1.5)))
        self.assertEqual(inequality(">=", real(1, 3), real(0, 2)),         (boolean, real(1, 3), real(0, 2)))

        values = [0, 0.001, 0.999, 1.0, 1.001, 1.999, 2.0, 2.001, 2.999, 3.0]
        edges = [0, almost(0), 1, almost(1), 2, almost(2), 3, almost(3)]
        for leftmin in edges:
            for leftmax in edges:
                try:
                    left = real(leftmin, leftmax)
                except FemtocodeError:
                    pass
                else:
                    for rightmin in edges:
                        for rightmax in edges:
                            try:
                                right = real(rightmin, rightmax)
                            except FemtocodeError:
                                pass
                            else:
                                boo, leftconstraint, rightconstraint = inequality(">=", left, right)
                                if isinstance(boo, Impossible):
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    self.assertFalse(x >= y)

                                else:
                                    for x in values:
                                        if x in left:
                                            for y in values:
                                                if y in right:
                                                    if x >= y:
                                                        self.assertTrue(x in leftconstraint and y in rightconstraint)
