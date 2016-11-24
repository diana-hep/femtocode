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

from femtocode.typesystem import *

def literal(schema, operator, value):
    if isinstance(schema, Union):
        possibilities = []
        for p in schema.possibilities:
            result = literal(p, operator, value)
            if not isinstance(result, Impossible):
                possibilities.append(result)

        if len(possibilities) == 0:
            return impossible
        elif len(possibilities) == 1:
            return possibilities[0]
        else:
            return union(*possibilities)

    elif isinstance(schema, Impossible):
        if operator == "==":
            return impossible

        elif operator == "!=":
            return impossible

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Null):
        if value is None:
            if operator == "==":
                return null
            elif operator == "!=":
                return impossible
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

        else:
            if operator == "==":
                return impossible
            elif operator == "!=":
                return null
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Boolean):
        if isinstance(value, bool):
            if operator == "==":
                return boolean
            elif operator == "!=":
                return boolean       # it could be the other one
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

        else:
            if operator == "==":
                return impossible
            elif operator == "!=":
                return boolean
            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Number):
        if isinstance(value, (int, long, float)):
            if operator == "==":
                return intersection(schema, Number(value, value, round(value) == value))

            elif operator == "!=":
                return difference(schema, Number(value, value, False))

            elif operator == ">":
                return intersection(schema, Number(almost(value), inf, False))

            elif operator == ">=":
                return intersection(schema, Number(value, inf, False))

            elif operator == "<":
                return intersection(schema, Number(-inf, almost(value), False))

            elif operator == "<=":
                return intersection(schema, Number(-inf, value, False))

            else:
                raise ProgrammingError("unhandled operator: {0}".format(operator))

        else:
            return impossible

    elif isinstance(schema, String):
        if operator == "==":
            if isinstance(value, string_types):
                return intersection(schema, String("bytes" if isinstance(value, bytes) else "unicode", len(value), len(value)))
            else:
                return impossible

        elif operator == "!=":
            return schema

        elif operator in ("size==", "size!=", "size>", "size>=", "size<", "size<="):
            if isinstance(value, (int, long)):
                operator = {"size==": "==", "size!=": "!=", "size>": ">", "size>=": ">=", "size<": "<", "size<=": "<="}[operator]
                number = literal(Number(schema.fewest, schema.most, True), operator, value)
                if isinstance(number, Number):
                    return String(schema.charset, number.min, number.max)
                elif isinstance(number, Union):
                    return Union([String(schema.charset, p.min, p.max) for p in number.possibilities])
                elif isinstance(number, Impossible):
                    return impossible
                else:
                    raise ProgrammingError("literal(Number, \"{0}\", value) is {1}".format(operator, number))

            else:
                raise ProgrammingError("operator {0} unexpected for value {1}".format(operator, value))

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Collection):
        if operator == "==":
            if isinstance(value, (list, tuple, set)):
                if len(value) == 0:
                    return intersection(schema, empty)
                else:
                    return intersection(schema, Collection(union(*(literal(schema.items, operator, x) for x in value)), len(value), len(value), True))
            else:
                return impossible

        elif operator == "!=":
            if isinstance(value, (list, tuple, set)) and len(value) == 0:
                return difference(schema, empty)
            else:
                return schema

        elif operator in ("size==", "size!=", "size>", "size>=", "size<", "size<="):
            if isinstance(value, (int, long)):
                operator = {"size==": "==", "size!=": "!=", "size>": ">", "size>=": ">=", "size<": "<", "size<=": "<="}[operator]
                number = literal(Number(schema.fewest, schema.most, True), operator, value)
                if isinstance(number, Number):
                    return Collection(schema.items, number.min, number.max, schema.ordered)
                elif isinstance(number, Union):
                    return Union([Collection(schema.items, p.min, p.max, schema.ordered) for p in number.possibilities])
                elif isinstance(number, Impossible):
                    return impossible
                else:
                    raise ProgrammingError("literal(Number, \"{0}\", value) is {1}".format(operator, number))

            else:
                raise ProgrammingError("operator {0} unexpected for value {1}".format(operator, value))

        elif operator == "ordered":
            if schema.ordered:
                return schema
            else:
                return impossible

        elif operator == "notordered":
            if schema.ordered:
                return impossible
            else:
                return schema

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    elif isinstance(schema, Record):
        if operator == "==":
            if all(hasattr(value, n) for n in schema.fields):
                return intersection(schema, Record(dict((n, literal(t, operator, getattr(value, n))) for n, t in schema.fields.items())))
            else:
                return impossible

        elif operator == "!=":
            return schema

        else:
            raise ProgrammingError("unhandled operator: {0}".format(operator))

    else:
        raise ProgrammingError("unhandled schema: {0}".format(schema))





# def __add__(self, other):
#     if not isinstance(other, NumberType):
#         raise TypeError("cannot add %r and %r" % (self, other))

#     if (self.min == float("-inf") and other.min == float("inf")) or \
#        (self.min == float("-inf") and other.max == float("inf")) or \
#        (self.max == float("-inf") and other.min == float("inf")) or \
#        (self.max == float("-inf") and other.max == float("inf")) or \
#        (self.min == float("inf") and other.min == float("-inf")) or \
#        (self.min == float("inf") and other.max == float("-inf")) or \
#        (self.max == float("inf") and other.min == float("-inf")) or \
#        (self.max == float("inf") and other.max == float("-inf")):
#         raise TypeError("cannot add %r and %r" % (self, other))

#     if self.min == float("-inf") or other.min == float("-inf"):
#         newMin = float("-inf")
#     elif self.min == float("inf") or other.min == float("inf"):
#         newMin = float("inf")
#     elif self.min is almost("-inf") or other.min is almost("-inf"):
#         newMin = almost("-inf")
#     else:
#         newMin = self.min + other.min

#     if self.max == float("-inf") or other.max == float("-inf"):
#         newMax = float("-inf")
#     elif self.max == float("inf") or other.max == float("inf"):
#         newMax = float("inf")
#     elif self.max is almost("inf") or other.max is almost("inf"):
#         newMax = almost("inf")
#     else:
#         newMax = self.max + other.max

#     return NumberType(newMin, newMax, whole=self.whole and other.whole)

# def __sub__(self, other):
#     if not isinstance(other, NumberType):
#         raise TypeError("cannot subtract %r and %r" % (self, other))

#     if (self.min == float("-inf") and other.min == float("-inf")) or \
#        (self.min == float("-inf") and other.max == float("-inf")) or \
#        (self.max == float("-inf") and other.min == float("-inf")) or \
#        (self.max == float("-inf") and other.max == float("-inf")) or \
#        (self.min == float("inf") and other.min == float("inf")) or \
#        (self.min == float("inf") and other.max == float("inf")) or \
#        (self.max == float("inf") and other.min == float("inf")) or \
#        (self.max == float("inf") and other.max == float("inf")):
#         raise TypeError("cannot subtract %r and %r" % (self, other))

#     if self.min == float("-inf") or other.max == float("inf"):
#         newMin = float("-inf")
#     elif self.min == float("inf") or other.max == float("-inf"):
#         newMin = float("inf")
#     elif self.min is almost("-inf") or other.max is almost("inf"):
#         newMin = almost("-inf")
#     else:
#         newMin = self.min - other.max

#     if self.max == float("-inf") or other.min == float("inf"):
#         newMax = float("-inf")
#     elif self.max == float("inf") or other.min == float("-inf"):
#         newMax = float("inf")
#     elif self.max is almost("inf") or other.min is almost("-inf"):
#         newMax = almost("inf")
#     else:
#         newMax = self.max - other.min

#     return NumberType(newMin, newMax, whole=self.whole and other.whole)

# @staticmethod
# def __expandMinusPlus(interval):
#     if interval.min < 0.0 and 0.0 not in interval:
#         if interval.min == float("-inf") and interval.max == float("-inf"):
#             intervalMinus = [interval.min]
#         elif interval.min == float("-inf"):
#             intervalMinus = [interval.min, almost("-inf"), interval.max.real - 1.0, interval.max]
#         elif interval.min == almost("-inf"):
#             intervalMinus = [interval.min, interval.max.real - 1.0, interval.max]
#         else:
#             intervalMinus = [interval.min, (interval.min.real + interval.max.real)/2.0, interval.max]
#     elif interval.min < 0.0:
#         if interval.min.real == float("-inf"):
#             intervalMinus = [interval.min, -1.0, almost(0.0), 0.0]
#         else:
#             intervalMinus = [interval.min, interval.min.real/2.0, almost(0.0), 0.0]
#     elif interval.min == 0.0:
#         intervalMinus = [0.0]
#     else:
#         intervalMinus = []  # interval.min == almost(0.0) goes here

#     if interval.max > 0.0 and 0.0 not in interval:
#         if interval.max == float("inf") and interval.min == float("inf"):
#             intervalPlus = [interval.max]
#         elif interval.max == float("inf"):
#             intervalPlus = [interval.min, interval.min.real + 1.0, almost("inf"), interval.max]
#         elif interval.max == almost("inf"):
#             intervalPlus = [interval.min, interval.min.real + 1.0, interval.max]
#         else:
#             intervalPlus = [interval.min, (interval.min.real + interval.max.real)/2.0, interval.max]
#     elif interval.max > 0.0:
#         if interval.max.real == float("inf"):
#             intervalPlus = [0.0, almost(0.0), 1.0, interval.max]
#         else:
#             intervalPlus = [0.0, almost(0.0), interval.max.real/2.0, interval.max]
#     elif interval.max == 0.0:
#         intervalPlus = [0.0]
#     else:
#         intervalPlus = []  # interval.max == almost(0.0) goes here

#     return intervalMinus, intervalPlus

# @staticmethod
# def __minmaxFromCases(cases):
#     def compareMin(a, b):
#         if a.real < b.real:
#             return -1
#         elif a.real > b.real:
#             return 1
#         elif not isinstance(a, almost) and isinstance(b, almost):
#             return -1
#         elif isinstance(a, almost) and not isinstance(b, almost):
#             return 1
#         else:
#             return 0

#     newMin = min(cases, key=functools.cmp_to_key(compareMin))

#     def compareMax(a, b):
#         if a.real < b.real:
#             return -1
#         elif a.real > b.real:
#             return 1
#         elif isinstance(a, almost) and not isinstance(b, almost):
#             return -1
#         elif not isinstance(a, almost) and isinstance(b, almost):
#             return 1
#         else:
#             return 0

#     newMax = max(cases, key=functools.cmp_to_key(compareMax))

#     return newMin, newMax

# def __mul__(self, other):
#     if not isinstance(other, NumberType):
#         raise TypeError("cannot multiply %r and %r" % (self, other))

#     selfIntervalMinus, selfIntervalPlus = self.__expandMinusPlus(self)
#     otherIntervalMinus, otherIntervalPlus = self.__expandMinusPlus(other)

#     cases = []
#     for a in selfIntervalMinus:
#         for b in otherIntervalMinus:
#             if a == float("-inf") and b == 0.0:
#                 raise TypeError("cannot multiply -inf and 0 in %r and %r" % (self, other))

#             if a == 0.0 and b == float("-inf"):
#                 raise TypeError("cannot multiply -inf and 0 in %r and %r" % (self, other))

#             elif a == float("-inf"):
#                 cases.append(float("inf"))

#             elif b == float("-inf"):
#                 cases.append(float("inf"))

#             elif a == almost("-inf") and b == 0.0:
#                 cases.append(0.0)

#             elif a == almost("-inf") and b == almost(0.0):
#                 cases.append(almost(0.0))
#                 cases.append(almost("inf"))

#             elif a == 0.0 and b == almost("-inf"):
#                 cases.append(0.0)

#             elif a == almost(0.0) and b == almost("-inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("inf"))

#             else:
#                 cases.append(a * b)

#         for b in otherIntervalPlus:
#             if a == float("-inf") and b == 0.0:
#                 raise TypeError("cannot multiply -inf and 0 in %r and %r" % (self, other))

#             if a == 0.0 and b == float("inf"):
#                 raise TypeError("cannot multiply 0 and inf in %r and %r" % (self, other))

#             elif a == float("-inf"):
#                 cases.append(float("-inf"))

#             elif b == float("inf"):
#                 cases.append(float("-inf"))

#             elif a == almost("-inf") and b == 0.0:
#                 cases.append(0.0)

#             elif a == almost("-inf") and b == almost(0.0):
#                 cases.append(almost(0.0))
#                 cases.append(almost("-inf"))

#             elif a == 0.0 and b == almost("inf"):
#                 cases.append(0.0)

#             elif a == almost(0.0) and b == almost("inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("-inf"))

#             else:
#                 cases.append(a * b)

#     for a in selfIntervalPlus:
#         for b in otherIntervalMinus:
#             if a == float("inf") and b == 0.0:
#                 raise TypeError("cannot multiply 0 and inf in %r and %r" % (self, other))

#             if a == 0.0 and b == float("-inf"):
#                 raise TypeError("cannot multiply -inf and 0 in %r and %r" % (self, other))

#             elif a == float("inf"):
#                 cases.append(float("-inf"))

#             elif b == float("-inf"):
#                 cases.append(float("-inf"))

#             elif a == almost("inf") and b == 0.0:
#                 cases.append(0.0)

#             elif a == almost("inf") and b == almost(0.0):
#                 cases.append(almost(0.0))
#                 cases.append(almost("-inf"))

#             elif a == 0.0 and b == almost("-inf"):
#                 cases.append(0.0)

#             elif a == almost(0.0) and b == almost("-inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("-inf"))

#             else:
#                 cases.append(a * b)

#         for b in otherIntervalPlus:
#             if a == float("inf") and b == 0.0:
#                 raise TypeError("cannot multiply 0 and inf in %r and %r" % (self, other))

#             if a == 0.0 and b == float("inf"):
#                 raise TypeError("cannot multiply 0 and inf in %r and %r" % (self, other))

#             elif a == float("inf"):
#                 cases.append(float("inf"))

#             elif b == float("inf"):
#                 cases.append(float("inf"))

#             elif a == almost("inf") and b == 0.0:
#                 cases.append(0.0)

#             elif a == almost("inf") and b == almost(0.0):
#                 cases.append(almost(0.0))
#                 cases.append(almost("inf"))

#             elif a == 0.0 and b == almost("inf"):
#                 cases.append(0.0)

#             elif a == almost(0.0) and b == almost("inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("inf"))

#             else:
#                 cases.append(a * b)

#     assert not any(math.isnan(x) for x in cases)

#     newMin, newMax = self.__minmaxFromCases(cases)
#     return NumberType(newMin, newMax, whole=self.whole and other.whole)

# def __div__(self, other):
#     if not isinstance(other, NumberType):
#         raise TypeError("cannot divide %r and %r" % (self, other))

#     selfIntervalMinus, selfIntervalPlus = self.__expandMinusPlus(self)
#     otherIntervalMinus, otherIntervalPlus = self.__expandMinusPlus(other)

#     cases = []
#     for a in selfIntervalMinus:
#         for b in otherIntervalMinus:
#             if a == float("-inf") and b == float("-inf"):
#                 raise TypeError("cannot divide -inf and -inf in %r and %r" % (self, other))

#             elif a == float("-inf") and b == 0.0:
#                 # cases.append(float("-inf"))   # according to Java, but arguably an error
#                 raise TypeError("cannot divide -inf and 0 in %r and %r" % (self, other))

#             elif a == float("-inf"):
#                 cases.append(float("inf"))

#             elif a == almost("-inf") and b == float("-inf"):
#                 cases.append(0.0)

#             elif a == almost("-inf") and b == almost("-inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("inf"))

#             elif b == almost(0.0):
#                 cases.append(almost("inf"))

#             elif b == 0.0:
#                 cases.append(float("inf"))

#             else:
#                 cases.append(a / b)

#         for b in otherIntervalPlus:
#             if a == float("-inf") and b == float("inf"):
#                 raise TypeError("cannot divide -inf and inf in %r and %r" % (self, other))

#             elif a == float("-inf") and b == 0.0:
#                 # cases.append(float("-inf"))   # according to Java, but arguably an error
#                 raise TypeError("cannot divide -inf and 0 in %r and %r" % (self, other))

#             elif a == float("-inf"):
#                 cases.append(float("-inf"))

#             elif a == almost("-inf") and b == float("inf"):
#                 cases.append(0.0)

#             elif a == almost("-inf") and b == almost("inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("-inf"))

#             elif b == almost(0.0):
#                 cases.append(almost("-inf"))

#             elif b == 0.0:
#                 cases.append(float("-inf"))

#             else:
#                 cases.append(a / b)

#     for a in selfIntervalPlus:
#         for b in otherIntervalMinus:
#             if a == float("inf") and b == float("-inf"):
#                 raise TypeError("cannot divide -inf and inf in %r and %r" % (self, other))

#             elif a == float("inf") and b == 0.0:
#                 cases.append(float("inf"))   # according to Java, but arguably an error
#                 raise TypeError("cannot divide -inf and 0 in %r and %r" % (self, other))

#             elif a == float("inf"):
#                 cases.append(float("-inf"))

#             elif a == almost("inf") and b == float("-inf"):
#                 cases.append(0.0)

#             elif a == almost("inf") and b == almost("-inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("-inf"))

#             elif b == almost(0.0):
#                 cases.append(almost("-inf"))

#             elif b == 0.0:
#                 cases.append(float("-inf"))

#             else:
#                 cases.append(a / b)

#         for b in otherIntervalPlus:
#             if a == float("inf") and b == float("inf"):
#                 raise TypeError("cannot divide inf and inf in %r and %r" % (self, other))

#             elif a == float("inf") and b == 0.0:
#                 # cases.append(float("inf"))   # according to Java, but arguably an error
#                 raise TypeError("cannot divide inf and 0 in %r and %r" % (self, other))

#             elif a == float("inf"):
#                 cases.append(float("inf"))

#             elif a == almost("inf") and b == float("inf"):
#                 cases.append(0.0)

#             elif a == almost("inf") and b == almost("inf"):
#                 cases.append(almost(0.0))
#                 cases.append(almost("inf"))

#             elif b == almost(0.0):
#                 cases.append(almost("inf"))

#             elif b == 0.0:
#                 cases.append(float("inf"))

#             else:
#                 cases.append(a / b)

#     assert not any(math.isnan(x) for x in cases)

#     newMin, newMax = self.__minmaxFromCases(cases)
#     return NumberType(newMin, newMax, whole=self.whole and other.whole)

# def __pow__(self, other):
#     if not isinstance(other, NumberType):
#         raise TypeError("cannot raise %r to the %r power" % (self, other))

#     def hasNegative(interval):
#         if interval.whole:
#             if not isinstance(interval.min, almost):
#                 return interval.min <= -1
#             else:
#                 return interval.min < -1
#         else:
#             return interval.min < 0.0

#     def hasFiniteNegative(interval):
#         return hasNegative(interval) and interval.max != float("-inf")

#     def hasPositive(interval):
#         if interval.whole:
#             if not isinstance(interval.max, almost):
#                 return interval.max >= 1
#             else:
#                 return interval.max > 1
#         else:
#             return interval.max > 0.0

#     def hasFinitePositive(interval):
#         return hasPositive(interval) and interval.min != float("inf")

#     def hasInsideOfOne(interval):
#         if interval.min <= -1.0:
#             return interval.max > -1.0
#         else:
#             return interval.min < 1.0

#     def hasOutsideOfOne(interval):
#         return interval.min < -1.0 or interval.max > 1.0

#     def hasPositiveOddInteger(interval):
#         if interval.max.real == float("inf") and interval.min.real == float("inf"):
#             return False
#         elif interval.max.real == float("inf"):
#             return True
#         elif interval.min.real == float("-inf"):
#             if not isinstance(interval.max, almost):
#                 return interval.max >= 1.0
#             else:
#                 return interval.max > 1.0
#         else:
#             assert not math.isinf(interval.min) and not math.isinf(interval.max)
#             if interval.whole:
#                 for x in xrange(max(0, int(interval.min)), max(0, int(interval.max) + 1)):
#                     if isinstance(interval.min, almost) and x <= interval.min.real:
#                         continue
#                     if isinstance(interval.max, almost) and x >= interval.max.real:
#                         continue
#                     if x % 2 == 1:
#                         return True
#                 return False
#             else:
#                 for x in xrange(max(0, int(math.ceil(interval.min))), max(0, int(math.floor(interval.max)) + 1)):
#                     if isinstance(interval.min, almost) and x <= interval.min.real:
#                         continue
#                     if isinstance(interval.max, almost) and x >= interval.max.real:
#                         continue
#                     if x % 2 == 1:
#                         return True
#                 return False

#     def hasPositiveEvenInteger(interval):
#         if interval.max.real == float("inf") and interval.min.real == float("inf"):
#             return False
#         elif interval.max.real == float("inf"):
#             return True
#         elif interval.min.real == float("-inf"):
#             if not isinstance(interval.max, almost):
#                 return interval.max >= 2.0
#             else:
#                 return interval.max > 2.0
#         else:
#             assert not math.isinf(interval.min) and not math.isinf(interval.max)
#             if interval.whole:
#                 for x in xrange(max(0, int(interval.min)), max(0, int(interval.max) + 1)):
#                     if isinstance(interval.min, almost) and x <= interval.min.real:
#                         continue
#                     if isinstance(interval.max, almost) and x >= interval.max.real:
#                         continue
#                     if x % 2 == 0:
#                         return True
#                 return False
#             else:
#                 for x in xrange(max(1, int(math.ceil(interval.min))), max(1, int(math.floor(interval.max)) + 1)):
#                     if isinstance(interval.min, almost) and x <= interval.min.real:
#                         continue
#                     if isinstance(interval.max, almost) and x >= interval.max.real:
#                         continue
#                     if x % 2 == 0:
#                         return True
#                 return False

#     def hasNonInteger(interval):
#         return not interval.whole and (interval.max > interval.min or not interval.min.is_integer()) and (not math.isinf(interval.min) or not math.isinf(interval.max))

#     def hasPositiveNonInteger(interval):
#         return hasPositive(interval) and hasNonInteger(interval)

#     cases = []

#     if 0.0 in self and hasNegative(other):
#         cases.append(float("inf"))            # Java's behavior; Python raises ValueError

#     if float("inf") in other or float("-inf") in other:
#         if 1.0 in self or -1.0 in self:
#             # Java returns NaN; Python says it's 1 (math.pow) or -1 (** with negative base) for some reason
#             raise TypeError("cannot raise %r to the %r power (consider case x**y where x == 1 and y is infinite)" % (self, other))
#         if hasInsideOfOne(self):
#             if float("inf") in other:
#                 cases.append(0.0)             # Python and Java
#             if float("-inf") in other:
#                 cases.append(float("inf"))    # Python and Java
#         if hasOutsideOfOne(self):
#             if float("inf") in other:
#                 cases.append(float("inf"))    # Python and Java
#             if float("-inf") in other:
#                 cases.append(0.0)             # Python and Java

#     if float("inf") in self or float("-inf") in self:
#         if 0.0 in other:
#             cases.append(1.0)                 # Python and Java
#         if hasFiniteNegative(other):
#             cases.append(0.0)                 # Python and Java
#         if float("-inf") in self and hasPositiveOddInteger(other):
#             cases.append(float("-inf"))       # Python and Java
#         if float("inf") in self and hasFinitePositive(other):
#             cases.append(float("inf"))        # Python and Java
#         if hasPositiveEvenInteger(other) or hasPositiveNonInteger(other):
#             cases.append(float("inf"))        # Python and Java

#     if hasFiniteNegative(self) and hasNonInteger(other):
#         # Python raises ValueError; Java returns NaN
#         raise TypeError("cannot raise %r to the %r power (consider case x**y where x < 0 and y is not an integer)" % (self, other))

#     selfIntervalMinus, selfIntervalPlus = self.__expandMinusPlus(self)
#     otherIntervalMinus, otherIntervalPlus = self.__expandMinusPlus(other)

#     for x in selfIntervalMinus + selfIntervalPlus:
#         for y in otherIntervalMinus + otherIntervalPlus:
#             try:
#                 cases.append(x ** y)
#             except ZeroDivisionError:
#                 pass   # handled above
#             except OverflowError:
#                 if (abs(x) > 1.0 and y < 0.0) or (abs(x) < 1.0 and y > 0.0):
#                     cases.append(0.0)
#                 else:
#                     cases.append(float("inf"))

#     assert not any(math.isnan(x) for x in cases)

#     newMin, newMax = self.__minmaxFromCases(cases)
#     return NumberType(newMin, newMax, whole=self.whole and other.whole)

# def __mod__(self, other):
#     if not isinstance(other, NumberType):
#         raise TypeError("cannot take %r mod %r" % (self, other))

#     if float("inf") in self or float("-inf") in self:
#         raise TypeError("cannot take %r mod %r (consider case where dividend is infinite)" % (self, other))

#     if 0.0 in other:
#         raise TypeError("cannot take %r mod %r (consider case where divisor is zero)" % (self, other))

#     cases = []

#     if other.min >= 0.0:
#         if float("inf") in other:
#             cases.append(self.max)
#             if self.min >= 0.0:
#                 cases.append(self.min)
#             else:
#                 cases.append(0.0)
#                 cases.append(float("inf"))
#         if other.min < float("inf"):
#             if self.min >= 0.0 and self.max < other.min:
#                 cases.append(self.min)
#                 cases.append(self.max)
#             elif self.max <= 0.0 and self.min > -other.min:
#                 cases.append(self.min + other.min)
#                 cases.append(self.max + other.min)
#             else:
#                 cases.append(0.0)
#                 cases.append(almost(other.max.real))

#     if other.max <= 0.0:
#         if float("-inf") in other:
#             cases.append(self.min)
#             if self.max <= 0.0:
#                 cases.append(self.max)
#             else:
#                 cases.append(0.0)
#                 cases.append(float("-inf"))
#         if other.max > float("-inf"):
#             if self.max <= 0.0 and self.min > other.max:
#                 cases.append(self.max)
#                 cases.append(self.min)
#             elif self.min >= 0.0 and self.max < -other.max:
#                 cases.append(self.max + other.max)
#                 cases.append(self.min + other.min)
#             else:
#                 cases.append(0.0)
#                 cases.append(almost(other.min.real))

#     assert not any(math.isnan(x) for x in cases)

#     newMin, newMax = self.__minmaxFromCases(cases)
#     return NumberType(newMin, newMax, whole=self.whole and other.whole)

