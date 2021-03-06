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

import math

from femtocode.typesystem import *

def _combineTwoUnions(one, two, operation):
    possibilities = []
    reason = None
    for p1 in one.possibilities:
        for p2 in two.possibilities:
            result = operation(p1, p2)
            if not isinstance(result, Impossible):
                possibilities.append(result)
            elif reason is None:
                reason = result.reason
                
    if len(possibilities) == 0:
        return impossible(reason)
    elif len(possibilities) == 1:
        return possibilities[0]
    else:
        return union(*possibilities)

def _combineFirstUnion(one, other, operation):
    possibilities = []
    reason = None
    for p in one.possibilities:
        result = operation(p, other)
        if not isinstance(result, Impossible):
            possibilities.append(result)
        elif reason is None:
            reason = result.reason

    if len(possibilities) == 0:
        return impossible(reason)
    elif len(possibilities) == 1:
        return possibilities[0]
    else:
        return union(*possibilities)

def _combineSecondUnion(other, two, operation):
    possibilities = []
    reason = None
    for p in two.possibilities:
        result = operation(other, p)
        if not isinstance(result, Impossible):
            possibilities.append(result)
        elif reason is None:
            reason = result.reason

    if len(possibilities) == 0:
        return impossible(reason)
    elif len(possibilities) == 1:
        return possibilities[0]
    else:
        return union(*possibilities)

def add(*args):
    assert len(args) > 0, "inference.add called with 0 arguments"
    if len(args) == 1:
        return args[0]
    elif len(args) > 2:
        return add(add(args[0], args[1]), *args[2:])
    else:
        one, two = args

        if isinstance(one, Union) and isinstance(two, Union):
            return _combineTwoUnions(one, two, add)

        elif isinstance(one, Union):
            return _combineFirstUnion(one, two, add)

        elif isinstance(two, Union):
            return _combineSecondUnion(one, two, add)

        elif isinstance(one, Number) and isinstance(two, Number):
            if (one.min == -inf and two.min == inf) or \
               (one.min == -inf and two.max == inf) or \
               (one.max == -inf and two.min == inf) or \
               (one.max == -inf and two.max == inf) or \
               (one.min == inf and two.min == -inf) or \
               (one.min == inf and two.max == -inf) or \
               (one.max == inf and two.min == -inf) or \
               (one.max == inf and two.max == -inf):
                return impossible("Indeterminate form (inf + -inf, from extended real type) is not allowed; constrain with if-else.")

            else:
                if one.min == -inf or two.min == -inf:
                    newmin = -inf
                elif one.min == inf or two.min == inf:
                    newmin = inf
                elif one.min == almost(-inf) or two.min == almost(-inf):
                    newmin = almost(-inf)
                else:
                    newmin = one.min + two.min

                if one.max == -inf or two.max == -inf:
                    newmax = -inf
                elif one.max == inf or two.max == inf:
                    newmax = inf
                elif one.max == almost(inf) or two.max == almost(inf):
                    newmax = almost(inf)
                else:
                    newmax = one.max + two.max

                return Number(newmin, newmax, one.whole and two.whole)

        else:
            assert False, "unhandled schemas: {0} {1}".format(one, two)

def subtract(*args):
    assert len(args) > 0, "inference.subtract called with 0 arguments"
    if len(args) == 1:
        return args[0]
    elif len(args) > 2:
        return subtract(subtract(args[0], args[1]), *args[2:])
    else:
        one, two = args

        if isinstance(one, Union) and isinstance(two, Union):
            return _combineTwoUnions(one, two, subtract)

        elif isinstance(one, Union):
            return _combineFirstUnion(one, two, subtract)

        elif isinstance(two, Union):
            return _combineSecondUnion(one, two, subtract)

        elif isinstance(one, Number) and isinstance(two, Number):
            if (one.min == -inf and two.min == -inf) or \
               (one.min == -inf and two.max == -inf) or \
               (one.max == -inf and two.min == -inf) or \
               (one.max == -inf and two.max == -inf) or \
               (one.min == inf and two.min == inf) or \
               (one.min == inf and two.max == inf) or \
               (one.max == inf and two.min == inf) or \
               (one.max == inf and two.max == inf):
                return impossible("Indeterminate form (inf - inf, from extended real type) is not allowed; constrain with if-else.")

            else:
                if one.min == -inf or two.max == inf:
                    newmin = -inf
                elif one.min == inf or two.max == -inf:
                    newmin = inf
                elif one.min == almost(-inf) or two.max == almost(inf):
                    newmin = almost(-inf)
                else:
                    newmin = one.min - two.max

                if one.max == -inf or two.min == inf:
                    newmax = -inf
                elif one.max == inf or two.min == -inf:
                    newmax = inf
                elif one.max == almost(inf) or two.min == almost(-inf):
                    newmax = almost(inf)
                else:
                    newmax = one.max - two.min

                return Number(newmin, newmax, one.whole and two.whole)

        else:
            assert False, "unhandled schemas: {0} {1}".format(one, two)

def _expandMinusPlus(interval, intermediate=False):
    if interval.min < 0.0 and 0.0 not in interval:
        if interval.min == -inf and interval.max == -inf:
            intervalMinus = (interval.min,)
        elif interval.min == -inf:
            intervalMinus = (interval.min, almost(-inf), interval.max.real - 1.0, interval.max)
        elif interval.min == almost(-inf):
            intervalMinus = (interval.min, interval.max.real - 1.0, interval.max)
        else:
            if intermediate:
                intervalMinus = (interval.min, (interval.min.real + interval.max.real)/2.0, interval.max)
            else:
                intervalMinus = (interval.min, interval.max)
    elif interval.min < 0.0:
        if interval.min.real == -inf:
            intervalMinus = (interval.min, -1.0, almost(0.0), 0.0)
        else:
            if intermediate:
                intervalMinus = (interval.min, interval.min.real/2.0, almost(0.0), 0.0)
            else:
                intervalMinus = (interval.min, almost(0.0), 0.0)
    elif interval.min == 0.0:
        intervalMinus = (0.0,)
    else:
        intervalMinus = ()  # interval.min == almost(0.0) goes here

    if interval.max > 0.0 and 0.0 not in interval:
        if interval.max == inf and interval.min == inf:
            intervalPlus = (interval.max,)
        elif interval.max == inf:
            intervalPlus = (interval.min, interval.min.real + 1.0, almost(inf), interval.max)
        elif interval.max == almost(inf):
            intervalPlus = (interval.min, interval.min.real + 1.0, interval.max)
        else:
            if intermediate:
                intervalPlus = (interval.min, (interval.min.real + interval.max.real)/2.0, interval.max)
            else:
                intervalPlus = (interval.min, interval.max)
    elif interval.max > 0.0:
        if interval.max.real == inf:
            intervalPlus = (0.0, almost(0.0), 1.0, interval.max)
        else:
            if intermediate:
                intervalPlus = (0.0, almost(0.0), interval.max.real/2.0, interval.max)
            else:
                intervalPlus = (0.0, almost(0.0), interval.max)
    elif interval.max == 0.0:
        intervalPlus = (0.0,)
    else:
        intervalPlus = ()  # interval.max == almost(0.0) goes here

    if intervalMinus == (0.0,):
        intervalMinus = ()
    if intervalPlus == (0.0,):
        intervalPlus = ()

    return intervalMinus, intervalPlus

def multiply(*args):
    assert len(args) > 0, "inference.multiply called with 0 arguments"
    if len(args) == 1:
        return args[0]
    elif len(args) > 2:
        return multiply(multiply(args[0], args[1]), *args[2:])
    else:
        one, two = args

        if isinstance(one, Union) and isinstance(two, Union):
            return _combineTwoUnions(one, two, multiply)

        elif isinstance(one, Union):
            return _combineFirstUnion(one, two, multiply)

        elif isinstance(two, Union):
            return _combineSecondUnion(one, two, multiply)

        elif isinstance(one, Number) and isinstance(two, Number):
            oneIntervalMinus, oneIntervalPlus = _expandMinusPlus(one)
            twoIntervalMinus, twoIntervalPlus = _expandMinusPlus(two)

            cases = []
            for a in oneIntervalMinus:
                for b in twoIntervalMinus:
                    if a == -inf and b == 0.0:
                        return impossible("Indeterminate form (-inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    if a == 0.0 and b == -inf:
                        return impossible("Indeterminate form (-inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    elif a == -inf:
                        cases.append(inf)

                    elif b == -inf:
                        cases.append(inf)

                    elif a == almost(-inf) and b == 0.0:
                        cases.append(0.0)

                    elif a == almost(-inf) and b == almost(0.0):
                        cases.append(almost(0.0))
                        cases.append(almost(inf))

                    elif a == 0.0 and b == almost(-inf):
                        cases.append(0.0)

                    elif a == almost(0.0) and b == almost(-inf):
                        cases.append(almost(0.0))
                        cases.append(almost(inf))

                    else:
                        cases.append(a * b)

                for b in twoIntervalPlus:
                    if a == -inf and b == 0.0:
                        return impossible("Indeterminate form (-inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    if a == 0.0 and b == inf:
                        return impossible("Indeterminate form (inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    elif a == -inf:
                        cases.append(-inf)

                    elif b == inf:
                        cases.append(-inf)

                    elif a == almost(-inf) and b == 0.0:
                        cases.append(0.0)

                    elif a == almost(-inf) and b == almost(0.0):
                        cases.append(almost(0.0))
                        cases.append(almost(-inf))

                    elif a == 0.0 and b == almost(inf):
                        cases.append(0.0)

                    elif a == almost(0.0) and b == almost(inf):
                        cases.append(almost(0.0))
                        cases.append(almost(-inf))

                    else:
                        cases.append(a * b)

            for a in oneIntervalPlus:
                for b in twoIntervalMinus:
                    if a == inf and b == 0.0:
                        return impossible("Indeterminate form (inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    if a == 0.0 and b == -inf:
                        return impossible("Indeterminate form (-inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    elif a == inf:
                        cases.append(-inf)

                    elif b == -inf:
                        cases.append(-inf)

                    elif a == almost(inf) and b == 0.0:
                        cases.append(0.0)

                    elif a == almost(inf) and b == almost(0.0):
                        cases.append(almost(0.0))
                        cases.append(almost(-inf))

                    elif a == 0.0 and b == almost(-inf):
                        cases.append(0.0)

                    elif a == almost(0.0) and b == almost(-inf):
                        cases.append(almost(0.0))
                        cases.append(almost(-inf))

                    else:
                        cases.append(a * b)

                for b in twoIntervalPlus:
                    if a == inf and b == 0.0:
                        return impossible("Indeterminate form (inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    if a == 0.0 and b == inf:
                        return impossible("Indeterminate form (inf * 0, from extended real type) is not allowed; constrain with if-else.")

                    elif a == inf:
                        cases.append(inf)

                    elif b == inf:
                        cases.append(inf)

                    elif a == almost(inf) and b == 0.0:
                        cases.append(0.0)

                    elif a == almost(inf) and b == almost(0.0):
                        cases.append(almost(0.0))
                        cases.append(almost(inf))

                    elif a == 0.0 and b == almost(inf):
                        cases.append(0.0)

                    elif a == almost(0.0) and b == almost(inf):
                        cases.append(almost(0.0))
                        cases.append(almost(inf))

                    else:
                        cases.append(a * b)

            assert not any(math.isnan(x) for x in cases), "nan encountered in multiply cases: {0}".format(cases)

            return Number(almost.min(*cases), almost.max(*cases), one.whole and two.whole)

        else:
            assert False, "unhandled schemas: {0} {1}".format(one, two)

def divide(*args):
    assert len(args) > 0, "inference.divide called with 0 arguments"
    if len(args) == 1:
        return args[0]
    elif len(args) > 2:
        return divide(divide(args[0], args[1]), *args[2:])
    else:
        one, two = args

        if isinstance(one, Union) and isinstance(two, Union):
            return _combineTwoUnions(one, two, divide)

        elif isinstance(one, Union):
            return _combineFirstUnion(one, two, divide)

        elif isinstance(two, Union):
            return _combineSecondUnion(one, two, divide)

        elif isinstance(one, Number) and isinstance(two, Number):
            oneIntervalMinus, oneIntervalPlus = _expandMinusPlus(one, True)
            twoIntervalMinus, twoIntervalPlus = _expandMinusPlus(two, True)

            cases = []
            for a in oneIntervalMinus:
                for b in twoIntervalMinus:
                    if a == -inf and b == -inf:
                        return impossible("Indeterminate form (-inf / -inf, from extended real type) is not allowed; constrain with if-else.")

                    elif a == -inf and b == 0.0:
                        cases.append(-inf)    # I agree with Java (not Python) that this is okay

                    elif a == 0.0 and b == 0.0:
                        return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                    elif a == -inf:
                        cases.append(inf)

                    elif a == almost(-inf) and b == -inf:
                        cases.append(0.0)

                    elif a == almost(-inf) and b == almost(-inf):
                        cases.append(almost(0.0))
                        cases.append(almost(inf))

                    elif b == almost(0.0):
                        cases.append(almost(inf))

                    elif b == 0.0:
                        cases.append(inf)

                    else:
                        cases.append(1.0 * a / b)

                for b in twoIntervalPlus:
                    if a == -inf and b == inf:
                        return impossible("Indeterminate form (-inf / inf, from extended real type) is not allowed; constrain with if-else.")

                    elif a == -inf and b == 0.0:
                        cases.append(-inf)    # I agree with Java (not Python) that this is okay

                    elif a == 0.0 and b == 0.0:
                        return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                    elif a == -inf:
                        cases.append(-inf)

                    elif a == almost(-inf) and b == inf:
                        cases.append(0.0)

                    elif a == almost(-inf) and b == almost(inf):
                        cases.append(almost(0.0))
                        cases.append(almost(-inf))

                    elif b == almost(0.0):
                        cases.append(almost(-inf))

                    elif b == 0.0:
                        cases.append(-inf)

                    else:
                        cases.append(1.0 * a / b)

            for a in oneIntervalPlus:
                for b in twoIntervalMinus:
                    if a == inf and b == -inf:
                        return impossible("Indeterminate form (inf / -inf, from extended real type) is not allowed; constrain with if-else.")

                    elif a == inf and b == 0.0:
                        cases.append(inf)    # I agree with Java (not Python) that this is okay

                    elif a == 0.0 and b == 0.0:
                        return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                    elif a == inf:
                        cases.append(-inf)

                    elif a == almost(inf) and b == -inf:
                        cases.append(0.0)

                    elif a == almost(inf) and b == almost(-inf):
                        cases.append(almost(0.0))
                        cases.append(almost(-inf))

                    elif b == almost(0.0):
                        cases.append(almost(-inf))

                    elif b == 0.0:
                        cases.append(-inf)

                    else:
                        cases.append(1.0 * a / b)

                for b in twoIntervalPlus:
                    if a == inf and b == inf:
                        return impossible("Indeterminate form (inf / inf, from extended real type) is not allowed; constrain with if-else.")

                    elif a == inf and b == 0.0:
                        cases.append(inf)    # I agree with Java (not Python) that this is okay

                    elif a == 0.0 and b == 0.0:
                        return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                    elif a == inf:
                        cases.append(inf)

                    elif a == almost(inf) and b == inf:
                        cases.append(0.0)

                    elif a == almost(inf) and b == almost(inf):
                        cases.append(almost(0.0))
                        cases.append(almost(inf))

                    elif b == almost(0.0):
                        cases.append(almost(inf))

                    elif b == 0.0:
                        cases.append(inf)

                    else:
                        cases.append(1.0 * a / b)

            assert not any(math.isnan(x) for x in cases), "nan encountered in divide cases: {0}".format(cases)

            return Number(almost.min(*cases), almost.max(*cases), False)

        else:
            assert False, "unhandled schemas: {0} {1}".format(one, two)

def floordivide(*args):
    assert len(args) > 0, "inference.floordivide called with 0 arguments"
    if len(args) == 1:
        return args[0]
    elif len(args) > 2:
        return floordivide(floordivide(args[0], args[1]), *args[2:])
    else:
        one, two = args

        if isinstance(one, Union) and isinstance(two, Union):
            return _combineTwoUnions(one, two, divide)

        elif isinstance(one, Union):
            return _combineFirstUnion(one, two, divide)

        elif isinstance(two, Union):
            return _combineSecondUnion(one, two, divide)

        elif isinstance(one, Number) and isinstance(two, Number):
            if isinstance(one, Number) and one.whole and isinstance(two, Number) and two.whole:
                oneIntervalMinus, oneIntervalPlus = _expandMinusPlus(one, True)
                twoIntervalMinus, twoIntervalPlus = _expandMinusPlus(two, True)

                cases = []
                for a in oneIntervalMinus:
                    for b in twoIntervalMinus:
                        if a == almost(-inf) and b == almost(-inf):
                            cases.append(almost(inf))
                            cases.append(0)

                        elif a == almost(-inf) and b.real == 0:
                            cases.append(almost(inf))

                        elif a == almost(-inf):
                            cases.append(almost(inf))

                        elif a.real == 0 and b == almost(-inf):
                            cases.append(0)

                        elif a.real == 0 and b.real == 0:
                            return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                        elif a.real == 0:
                            cases.append(0)

                        elif b == almost(-inf):
                            cases.append(0)

                        elif b.real == 0:
                            return impossible("Infinite value (inf, from extended real type) is not allowed in floor-division; constrain with if-else.")

                        else:
                            cases.append(a // b)

                    for b in twoIntervalPlus:
                        if a == almost(-inf) and b == almost(inf):
                            cases.append(almost(-inf))
                            cases.append(0)

                        elif a == almost(-inf) and b.real == 0:
                            cases.append(almost(-inf))

                        elif a == almost(-inf):
                            cases.append(almost(-inf))

                        elif a.real == 0 and b == almost(inf):
                            cases.append(0)

                        elif a.real == 0 and b.real == 0:
                            return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                        elif a.real == 0:
                            cases.append(0)

                        elif b == almost(inf):
                            cases.append(0)

                        elif b.real == 0:
                            return impossible("Infinite value (-inf, from extended real type) is not allowed in floor-division; constrain with if-else.")

                        else:
                            cases.append(a // b)

                for a in oneIntervalPlus:
                    for b in twoIntervalMinus:
                        if a == almost(inf) and b == almost(-inf):
                            cases.append(almost(-inf))
                            cases.append(0)

                        elif a == almost(inf) and b.real == 0:
                            cases.append(almost(-inf))

                        elif a == almost(inf):
                            cases.append(almost(-inf))

                        elif a.real == 0 and b == almost(-inf):
                            cases.append(0)

                        elif a.real == 0 and b.real == 0:
                            return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                        elif a.real == 0:
                            cases.append(0)

                        elif b == almost(-inf):
                            cases.append(0)

                        elif b.real == 0:
                            return impossible("Infinite value (-inf, from extended real type) is not allowed in floor-division; constrain with if-else.")

                        else:
                            cases.append(a // b)

                    for b in twoIntervalPlus:
                        if a == almost(inf) and b == almost(inf):
                            cases.append(almost(inf))
                            cases.append(0)

                        elif a == almost(inf) and b.real == 0:
                            cases.append(almost(inf))

                        elif a == almost(inf):
                            cases.append(almost(inf))

                        elif a.real == 0 and b == almost(inf):
                            cases.append(0)

                        elif a.real == 0 and b.real == 0:
                            return impossible("Indeterminate form (0 / 0) is not allowed; constrain with if-else.")

                        elif a.real == 0:
                            cases.append(0)

                        elif b == almost(inf):
                            cases.append(0)

                        elif b.real == 0:
                            return impossible("Infinite value (inf, from extended real type) is not allowed in floor-division; constrain with if-else.")

                        else:
                            cases.append(a // b)

                assert not any(math.isnan(x) for x in cases), "nan encountered in divide cases: {0}".format(cases)

                return Number(almost.min(*cases), almost.max(*cases), True)

            else:
                return impossible("Arguments of floor-division must be integers, not floating point numbers.")

        else:
            assert False, "unhandled schemas: {0} {1}".format(one, two)

def power(one, two):
    if isinstance(one, Union) and isinstance(two, Union):
        return _combineTwoUnions(one, two, power)

    elif isinstance(one, Union):
        return _combineFirstUnion(one, two, power)

    elif isinstance(two, Union):
        return _combineSecondUnion(one, two, power)

    elif isinstance(one, Number) and isinstance(two, Number):
        def hasNegative(interval):
            if interval.whole:
                if not isinstance(interval.min, almost):
                    return interval.min <= -1
                else:
                    return interval.min < -1
            else:
                return interval.min < 0.0

        def hasFiniteNegative(interval):
            return hasNegative(interval) and interval.max != -inf

        def hasPositive(interval):
            if interval.whole:
                if not isinstance(interval.max, almost):
                    return interval.max >= 1
                else:
                    return interval.max > 1
            else:
                return interval.max > 0.0

        def hasFinitePositive(interval):
            return hasPositive(interval) and interval.min != inf

        def hasInsideOfOne(interval):
            if interval.min <= -1.0:
                return interval.max > -1.0
            else:
                return interval.min < 1.0

        def hasOutsideOfOne(interval):
            return interval.min < -1.0 or interval.max > 1.0

        def hasPositiveOddInteger(interval):
            if interval.max.real == inf and interval.min.real == inf:
                return False
            elif interval.max.real == inf:
                return True
            elif interval.min.real == -inf:
                if not isinstance(interval.max, almost):
                    return interval.max >= 1.0
                else:
                    return interval.max > 1.0
            else:
                assert not math.isinf(interval.min) and not math.isinf(interval.max)
                if interval.whole:
                    for x in xrange(max(0, int(interval.min)), max(0, int(interval.max) + 1)):
                        if isinstance(interval.min, almost) and x <= interval.min.real:
                            continue
                        if isinstance(interval.max, almost) and x >= interval.max.real:
                            continue
                        if x % 2 == 1:
                            return True
                    return False
                else:
                    for x in xrange(max(0, int(math.ceil(interval.min))), max(0, int(math.floor(interval.max)) + 1)):
                        if isinstance(interval.min, almost) and x <= interval.min.real:
                            continue
                        if isinstance(interval.max, almost) and x >= interval.max.real:
                            continue
                        if x % 2 == 1:
                            return True
                    return False

        def hasPositiveEvenInteger(interval):
            if interval.max.real == inf and interval.min.real == inf:
                return False
            elif interval.max.real == inf:
                return True
            elif interval.min.real == -inf:
                if not isinstance(interval.max, almost):
                    return interval.max >= 2.0
                else:
                    return interval.max > 2.0
            else:
                assert not math.isinf(interval.min) and not math.isinf(interval.max)
                if interval.whole:
                    for x in xrange(max(0, int(interval.min)), max(0, int(interval.max) + 1)):
                        if isinstance(interval.min, almost) and x <= interval.min.real:
                            continue
                        if isinstance(interval.max, almost) and x >= interval.max.real:
                            continue
                        if x % 2 == 0:
                            return True
                    return False
                else:
                    for x in xrange(max(1, int(math.ceil(interval.min))), max(1, int(math.floor(interval.max)) + 1)):
                        if isinstance(interval.min, almost) and x <= interval.min.real:
                            continue
                        if isinstance(interval.max, almost) and x >= interval.max.real:
                            continue
                        if x % 2 == 0:
                            return True
                    return False

        def hasNonInteger(interval):
            return not interval.whole and (interval.max > interval.min or not interval.min.is_integer()) and (not math.isinf(interval.min) or not math.isinf(interval.max))

        def hasPositiveNonInteger(interval):
            return hasPositive(interval) and hasNonInteger(interval)

        cases = []

        if 0.0 in one and hasNegative(two):
            cases.append(inf)            # Java's behavior; Python raises ValueError

        if inf in two or -inf in two:
            if 1.0 in one or -1.0 in one:
                # Java returns NaN; Python says it's 1 (math.pow) or -1 (** with negative base) for some reason
                return impossible("Indeterminate form (1 ** inf, from extended real type) is not allowed; constrain with if-else.")
            if hasInsideOfOne(one):
                if inf in two:
                    cases.append(0.0)    # Python and Java
                if -inf in two:
                    cases.append(inf)    # Python and Java
            if hasOutsideOfOne(one):
                if inf in two:
                    cases.append(inf)    # Python and Java
                if -inf in two:
                    cases.append(0.0)    # Python and Java

        if inf in one or -inf in one:
            if 0.0 in two:
                cases.append(1.0)        # Python and Java
            if hasFiniteNegative(two):
                cases.append(0.0)        # Python and Java
            if -inf in one and hasPositiveOddInteger(two):
                cases.append(-inf)       # Python and Java
            if inf in one and hasFinitePositive(two):
                cases.append(inf)        # Python and Java
            if hasPositiveEvenInteger(two) or hasPositiveNonInteger(two):
                cases.append(inf)        # Python and Java

        if hasFiniteNegative(one) and hasNonInteger(two):
            # Python raises ValueError; Java returns NaN
            return impossible("Exponentiation of negative base by a non-integer power is not real or extended; constrain with if-else.")

        oneIntervalMinus, oneIntervalPlus = _expandMinusPlus(one)
        twoIntervalMinus, twoIntervalPlus = _expandMinusPlus(two)

        for x in oneIntervalMinus + oneIntervalPlus:
            for y in twoIntervalMinus + twoIntervalPlus:
                try:
                    cases.append(x ** y)
                except ZeroDivisionError:
                    pass   # handled above
                except OverflowError:
                    if (abs(x) > 1.0 and y < 0.0) or (abs(x) < 1.0 and y > 0.0):
                        cases.append(0.0)
                    else:
                        cases.append(inf)

        assert not any(math.isnan(x) for x in cases), "nan encountered in power cases: {0}".format(cases)

        return Number(almost.min(*cases), almost.max(*cases), one.whole and two.whole and two.min >= 0)
    
    else:
        assert False, "unhandled schemas: {0} {1}".format(one, two)

def modulo(one, two):
    if isinstance(one, Union) and isinstance(two, Union):
        return _combineTwoUnions(one, two, modulo)

    elif isinstance(one, Union):
        return _combineFirstUnion(one, two, modulo)

    elif isinstance(two, Union):
        return _combineSecondUnion(one, two, modulo)

    elif isinstance(one, Number) and isinstance(two, Number):
        if inf in one or -inf in one:
            return impossible("Infinite dividend (inf % something, from extended real type) is not allowed in modulo; constrain with if-else.")

        if 0.0 in two:
            return impossible("Zero divisor (something % 0) is not allowed in modulo; constrain with if-else.")

        cases = []

        if two.min >= 0.0:
            if inf in two:
                cases.append(one.max)
                if one.min >= 0.0:
                    cases.append(one.min)
                else:
                    cases.append(0.0)
                    cases.append(inf)
            if two.min < inf:
                if one.min >= 0.0 and one.max < two.min:
                    cases.append(one.min)
                    cases.append(one.max)
                elif one.max <= 0.0 and one.min > -two.min:
                    cases.append(one.min + two.min)
                    cases.append(one.max + two.min)
                else:
                    cases.append(0.0)
                    cases.append(almost(two.max.real))

        if two.max <= 0.0:
            if -inf in two:
                cases.append(one.min)
                if one.max <= 0.0:
                    cases.append(one.max)
                else:
                    cases.append(0.0)
                    cases.append(-inf)
            if two.max > -inf:
                if one.max <= 0.0 and one.min > two.max:
                    cases.append(one.max)
                    cases.append(one.min)
                elif one.min >= 0.0 and one.max < -two.max:
                    cases.append(one.max + two.max)
                    cases.append(one.min + two.min)
                else:
                    cases.append(0.0)
                    cases.append(almost(two.min.real))

        assert not any(math.isnan(x) for x in cases), "nan encountered in modulo cases: {0}".format(cases)

        return Number(almost.min(*cases), almost.max(*cases), one.whole and two.whole)

    else:
        assert False, "unhandled schemas: {0} {1}".format(one, two)

def inequality(operator, left, right):
    out = None
    reason = None
    leftconstraint = None
    rightconstraint = None

    # helper function to reduce duplicate code
    def update(triplet, out, reason, leftconstraint, rightconstraint):
        result, leftcons, rightcons = triplet

        if not isinstance(result, Impossible):
            if leftconstraint is None:
                leftconstraint = leftcons
            else:
                leftconstraint = union(leftconstraint, leftcons)

            if rightconstraint is None:
                rightconstraint = rightcons
            else:
                rightconstraint = union(rightconstraint, rightcons)

            if out is None:
                out = result
            else:
                out = union(out, result)

        elif reason is None:
            reason = result.reason

        return out, reason, leftconstraint, rightconstraint

    if isinstance(left, Union) and isinstance(right, Union):
        # build constraints from the union of all left possibilities with all right possibilities (all combinations)
        for p1 in left.possibilities:
            for p2 in right.possibilities:
                out, reason, leftconstraint, rightconstraint = update(inequality(operator, p1, p2), out, reason, leftconstraint, rightconstraint)

        if leftconstraint is None or rightconstraint is None:
            return impossible(reason), None, None
        else:
            return out, leftconstraint, rightconstraint

    elif isinstance(left, Union):
        # build constraints from the union of all left possibilities with the (single) right possibility
        for p1 in left.possibilities:
            out, reason, leftconstraint, rightconstraint = update(inequality(operator, p1, right), out, reason, leftconstraint, rightconstraint)

        if leftconstraint is None or rightconstraint is None:
            return impossible(reason), None, None
        else:
            return out, leftconstraint, rightconstraint
            
    elif isinstance(right, Union):
        # build constraints from the union of all right possibilities with the (single) left possibility
        reason = None
        for p2 in right.possibilities:
            out, reason, leftconstraint, rightconstraint = update(inequality(operator, left, p2), out, reason, leftconstraint, rightconstraint)

        if leftconstraint is None or rightconstraint is None:
            return impossible(reason), None, None
        else:
            return out, leftconstraint, rightconstraint

    elif operator == "!=":
        if isinstance(left, Null) and isinstance(right, Null):
            return impossible("The null type has only one value, so a null value will never be != a null value."), None, None

        elif isinstance(left, Boolean) and isinstance(right, Boolean):
            if left.just is True:                        # left is {True}
                if right.just is True:                   # right is {True}
                    return boolean(True), left, right
                elif right.just is False:                # right is {False}
                    return impossible("First argument is always True and second argument is always False."), None, None
                else:                                    # right is {True, False}
                    return boolean, left, left

            elif left.just is False:                     # left is {False}
                if right.just is True:                   # right is {True}
                    return impossible("First argument is always False and second argument is always True."), None, None
                elif right.just is False:                # right is {False}
                    return boolean(True), left, right
                else:                                    # right is {True, False}
                    return boolean, left, left

            else:                                        # left is {True, False}
                if right.just is True:                   # right is {True}
                    return boolean, right, right
                elif right.just is False:                # right is {False}
                    return boolean, right, right
                else:                                    # right is {True, False}
                    return boolean, left, right

        elif isinstance(left, Number) and isinstance(right, Number):
            if left.min == left.max:              # left is a constant
                if right.min == right.max:        # right is a constant
                    if left.min == right.min:     # they're the same constants
                        return impossible("Both arguments are the same constant; they will never be != each other."), None, None
                    else:
                        return boolean(True), left, right

                else:                             # left is a constant and right isn't
                    return boolean, left, difference(right, left)

            elif right.min == right.max:          # right is a constant and left isn't
                return boolean, difference(left, right), right

            else:                                 # if both are variable, no constraints are possible
                return boolean, left, right

        elif isinstance(left, String) and isinstance(right, String):
            # String cannot be parameterized in such a way as to constrict to a single value, so != is ineffective
            return boolean, left, right

        elif isinstance(left, Collection) and isinstance(right, Collection):
            # same for Collection
            return boolean, left, right

        elif isinstance(left, Record) and isinstance(right, Record):
            # same for Record
            return boolean, left, right

        else:
            # schemas are fundamentally different kinds; always unequal, constraints don't tighten
            return boolean(True), left, right

    elif isinstance(left, Number) and isinstance(right, Number):
        leftmin = left.min
        leftmax = left.max
        rightmin = right.min
        rightmax = right.max

        if operator == "<":
            if almost.max(left.max, right.max) == left.max:
                leftmax = almost(right.max)   # "almost" because of strict inequality

            if almost.min(left.min, right.min) == right.min:
                rightmin = almost(left.min)   # "almost" because of strict inequality

            if almost.min(left.max, right.min) == left.max and left.max != right.min:
                out = boolean(True)           # always satisfied
            else:
                out = boolean                 # sometimes satisfied (unless constructing a constraint raises FemtocodeError below)

            try:
                return out, left(leftmin, leftmax), right(rightmin, rightmax)
            except FemtocodeError:
                return impossible("First argument is never less than second argument."), None, None

        elif operator == "<=":
            if almost.max(left.max, right.max) == left.max:
                leftmax = right.max

            if almost.min(left.min, right.min) == right.min:
                rightmin = left.min

            if almost.min(left.max, right.min) == left.max:
                out = boolean(True)           # always satisfied
            else:
                out = boolean                 # sometimes satisfied (unless constructing a constraint raises FemtocodeError below)

            try:
                return out, left(leftmin, leftmax), right(rightmin, rightmax)
            except FemtocodeError:
                return impossible("First argument is never less than or equal to second argument."), None, None

        elif operator == ">":
            if almost.min(left.min, right.min) == left.min:
                leftmin = almost(right.min)   # "almost" because of strict inequality

            if almost.max(left.max, right.max) == right.max:
                rightmax = almost(left.max)   # "almost" because of strict inequality

            if almost.max(left.min, right.max) == left.min and left.min != right.max:
                out = boolean(True)           # always satisfied
            else:
                out = boolean                 # sometimes satisfied (unless constructing a constraint raises FemtocodeError below)

            try:
                return out, left(leftmin, leftmax), right(rightmin, rightmax)
            except FemtocodeError:
                return impossible("First argument is never greater than second argument."), None, None

        elif operator == ">=":
            if almost.min(left.min, right.min) == left.min:
                leftmin = right.min

            if almost.max(left.max, right.max) == right.max:
                rightmax = left.max

            if almost.max(left.min, right.max) == left.min:
                out = boolean(True)           # always satisfied
            else:
                out = boolean                 # sometimes satisfied (unless constructing a constraint raises FemtocodeError below)

            try:
                return out, left(leftmin, leftmax), right(rightmin, rightmax)
            except FemtocodeError:
                return impossible("First argument is never greater than or equal to second argument."), None, None

        else:
            assert False, "unexpected operator: {0}".format(operator)

    else:
        assert False, "unhandled schemas: {0} {1}".format(left, right)
