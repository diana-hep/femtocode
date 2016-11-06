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

import sys

from femtocode.defs import FemtocodeError
from femtocode.py23 import *

inf = float("inf")

# concrete = ("inf", "null", "boolean", "integer", "real", "string", "binary")
# parameterized = ("almost", "integer", "real", "binary", "record", "collection", "tensor", "union", "intersection", "complement")

class almost(float):
    """almost(x) -> open end of an interval

    Obeys open-closed arithmetic assuming that float(x) is the closed end of an interval.
    """

    @staticmethod
    def min(a, b):
        if a < b:
            return a
        elif b < a:
            return b
        elif not isinstance(a, almost):
            return a
        else:
            return b

    @staticmethod
    def max(a, b):
        if a > b:
            return a
        elif b > a:
            return b
        elif not isinstance(a, almost):
            return a
        else:
            return b

    def __eq__(self, other):
        if isinstance(other, almost):
            return self.real == other.real
        else:
            return False
    def __ne__(self, other):
        if isinstance(other, almost):
            return self.real != other.real
        else:
            return True
    def __hash__(self):
        return hash((almost, self.real))

    def __repr__(self):
        return "almost(" + repr(self.real) + ")"
    def __str__(self):
        return "almost(" + str(self.real) + ")"

    def __abs__(self):
        return almost(abs(self.real))
    def __pos__(self):
        return self
    def __neg__(self):
        return almost(-self.real)

    def __add__(self, other):
        return almost(self.real + other)
    def __radd__(other, self):
        return almost(self + other.real)
    def __sub__(self, other):
        return almost(self.real - other)
    def __rsub__(other, self):
        return almost(self - other.real)
    def __mul__(self, other):
        return almost(self.real * other)
    def __rmul__(other, self):
        return almost(self * other.real)
    def __pow__(self, other):
        return almost(self.real**other)
    def __rpow__(other, self):
        return almost(self**other.real)

    def __div__(self, other):
        return almost(self.real / other)
    def __rdiv__(other, self):
        return almost(self / other.real)
    def __truediv__(self, other):
        return almost(1.0*self.real / other)
    def __rtruediv__(other, self):
        return almost(1.0*self / other.real)
    def __floordiv__(self, other):
        return almost(self.real // other)
    def __rfloordiv__(other, self):
        return almost(self // other.real)

    def __mod__(self, other):
        return almost(self.real % other)
    def __rmod__(other, self):
        return almost(self % other.real)
    def __divmod__(self, other):
        a, b = divmod(self.real, other)
        return (almost(a), almost(b))
    def __rdivmod__(other, self):
        a, b = divmod(self, other.real)
        return (almost(a), almost(b))

# expressions must evaluate to concrete types, subclasses of Schema

class Schema(object):
    def __lt__(self, other):
        return self.order < other.order

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __hash__(self):
        return hash(self.__class__)

    def __call__(self, *args, **kwds):
        return self.__class__(*args, **kwds)

    def includes(self, value):
        raise NotImplementedError

class Impossible(Schema):    # bottom type; no values are possible
    order = 0
    
    def __repr__(self):
        return "impossible"

    def includes(self, value):
        return False

impossible = Impossible()

class Null(Schema):          # singleton type; only one possible value ("None", like Python)
    order = 1

    def __repr__(self):
        return "null"

    def includes(self, value):
        return value is None

null = Null()

class Boolean(Schema):
    order = 2

    def __repr__(self):
        return "boolean"

    def includes(self, value):
        return isinstance(value, bool)

boolean = Boolean()

class Number(Schema):
    order = 3

    def __init__(self, min=almost(-inf), max=almost(inf), whole=False):
        if not isinstance(min, (int, long, float)):
            raise FemtocodeError("min ({0}) must be a number (or 'almost')".format(min))
        if not isinstance(max, (int, long, float)):
            raise FemtocodeError("max ({0}) must be a number (or 'almost')".format(max))
        if not isinstance(whole, bool):
            raise FemtocodeError("whole ({0}) must be boolean".format(whole))
        if min > max:
            raise FemtocodeError("min ({0}) must not be greater than max ({1})".format(min, max))
        if min == max and isinstance(min, almost):
            raise FemtocodeError("min ({0}) and max ({1}) may only be equal to one another if they are closed endpoints (not 'almost')", min, max)
        if whole:
            if isinstance(min, almost) and min != almost(-inf):
                raise FemtocodeError("for whole numbered intervals, min ({0}) may only be 'almost' if it is almost(-inf)", min)
            if isinstance(max, almost) and max != almost(inf):
                raise FemtocodeError("for whole numbered intervals, max ({0}) may only be 'almost' if it is almost(inf)", max)
            if min == -inf:
                raise FemtocodeError("for whole numbered intervals, min ({0}) cannot be -inf; try almost(-inf)".format(min))
            if max == inf:
                raise FemtocodeError("for whole numbered intervals, max ({0}) cannot be inf; try almost(inf)".format(max))
        self.min = min
        self.max = max
        self.whole = whole

    def __repr__(self):
        if self.whole and (self.min == -inf or self.min == almost(-inf)) and (self.max == inf or self.max == almost(inf)):
            return "integer"
        elif self.whole:
            return "integer(min={0}, max={1})".format(self.min, self.max)
        elif self.min == -inf and self.max == inf:
            return "extended"
        elif self.min == -inf:
            return "extended(min=-inf, max={0})".format(self.max)
        elif self.max == inf:
            return "extended(min={0}, max=inf)".format(self.min)
        elif self.min == almost(-inf) and self.max == almost(inf):
            return "real"
        else:
            return "real(min={0}, max={1})"

    def __lt__(self, other):
        if isinstance(other, Number):
            if self.min == other.min:
                if self.max == other.max:
                    return self.whole < other.whole
                else:
                    return self.max < other.max
            else:
                return self.min < other.min
        else:
            return self.order < other.order

    def __eq__(self, other):
        if isinstance(other, Number):
            return self.min == other.min and self.max == other.max and self.whole == other.whole
        else:
            return False

    def __hash__(self):
        return hash((Number, self.min, self.max, self.whole))

    def includes(self, value):
        if isinstance(value, (int, long, float)):
            ok = True
            if isinstance(self.min, almost):
                ok = ok and (value > self.min):
            else:
                ok = ok and (value >= self.min)
            if isinstance(self.max, almost):
                ok = ok and (value < self.max)
            else:
                ok = ok and (value <= self.max)
            if self.whole:
                ok = ok and (round(value) == value)
            return ok

    def __call__(self, min=None, max=None, whole=None):
        return Number(self.min if min is None else min, self.max if max is None else max, self.whole if whole is None else whole)
                
integer = Number(min=almost(-inf), max=almost(inf), whole=True)

real = Number(min=almost(-inf), max=almost(inf), whole=False)

extended = Number(min=-inf, max=inf, whole=False)

class String(Schema):
    order = 4

    def __init__(self, fewest=0, most=almost(inf), charset="bytes"):
        if not isinstance(fewest, (int, long)) or fewest < 0:
            raise FemtocodeError("fewest {0} must be a nonnegative integer".format(fewest))
        if not (most == almost(inf) or isinstance(most, (int, long))) or most < 0:
            raise FemtocodeError("most {0} must be a nonnegative integer or almost(inf)".format(most))
        if fewest > most:
            raise FemtocodeError("fewest ({0}) must not be greater than most ({1})".format(fewest, most))
        if charset not in ("bytes", "unicode"):
            raise FemtocodeError("charset {0} not recognized".format(charset))
        self.fewest = fewest
        self.most = most
        self.charset = charset

    def __repr__(self):
        args = []

        if not (self.fewest == 0 and self.most == almost(inf)):
            args.append("fewest={0}, most={1}".format(self.fewest, self.most))

        if charset != "bytes":
            args.append("charset=\"bytes\"")

        if len(args) == 0:
            return "string"
        else:
            return "string(" + ", ".join(args) + ")"

    def includes(self, value):
        ok = True
        ok = ok and (len(value) >= self.fewest)
        ok = ok and (len(value) <= self.most)

        if self.charset == "bytes":
            ok = ok and isinstance(value, bytes)
        elif self.charset == "unicode":
            if sys.version_info[0] > 2:
                ok = ok and isinstance(value, str)
            else:
                ok = ok and isinstance(value, unicode)

        return ok

    def __call__(self, fewest=None, most=None, charset=None):
        return String(self.fewest if fewest is None else fewest, self.most if most is None else most, self.charset if charset is None else charset)





class Record(Schema):
    order = 7

    def __init__(self, **fields):
        self.fields = sorted(fields.items())

    def __repr__(self):
        return "record(" + ", ".join(n + "=" + repr(t) for n, t in self.fields) + ")"

    def __lt__(self, other):
        if isinstance(other, Record):
            return self.fields < other.fields
        else:
            return self.order < other.order








































# class Schema(object):
#     def __lt__(self, other):
#         return self.order < other.order

#     def __eq__(self, other):
#         return isinstance(other, self.__class__)

#     def __hash__(self):
#         return hash(self.__class__)

#     def __call__(self, *args, **kwds):
#         return self.__class__(*args, **kwds)

#     def union(self, other):
#         if isinstance(other, self.__class__):
#             return self
#         elif isinstance(other, Union):
#             if any(isinstance(x, self.__class__) for x in other.types):
#                 return other
#             else:
#                 return Union(self, *other.types)
#         else:
#             return Union(self, other)

#     def intersection(self, other):
#         if isinstance(other, self.__class__):
#             return self
#         elif isinstance(other, Union):
#             if any(isinstance(x, self.__class__) for x in other.types):
#                 return self
#             else:
#                 return impossible
#         else:
#             return impossible

# class Impossible(Schema):
#     order = 0

#     def __repr__(self):
#         return "impossible"

#     def union(self, other):
#         return other

#     def intersection(self, other):
#         return impossible

# impossible = Impossible()

# class Null(Schema):
#     order = 1

#     def __repr__(self):
#         return "null"
        
# null = Null()

# class Boolean(Schema):
#     order = 2

#     def __repr__(self):
#         return "boolean"

# boolean = Boolean()

# class Integer(Schema):
#     order = 3

#     def __init__(self, min=almost(-inf), max=almost(inf)):
#         if min > max:
#             raise FemtocodeError("min must not be greater than max")
#         if min != almost(-inf) and not isinstance(min, (int, long)):
#             raise FemtocodeError("min must be almost(-inf) or an integer")
#         if max != almost(inf) and not isinstance(max, (int, long)):
#             raise FemtocodeError("min must be almost(inf) or an integer")
#         self.min = min
#         self.max = max

#     def __repr__(self):
#         if self.min == almost(-inf) and self.max == almost(inf):
#             return "integer"
#         else:
#             return "integer(min={0}, max={1})".format(self.min, self.max)

#     def __lt__(self, other):
#         if isinstance(other, Integer):
#             if self.min == other.min:
#                 return self.max < other.max
#             else:
#                 return self.min < other.min
#         else:
#             return self.order < other.order

#     def __eq__(self, other):
#         if not isinstance(other, Integer):
#             return False
#         else:
#             return self.min == other.min and self.max == other.max

#     def __hash__(self):
#         return hash((Integer, self.min, self.max))

#     def union(self, other):
#         if isinstance(other, Integer):
#             a, b = sorted([self, other])
#             if a.max < b.min - 1:
#                 return Union(a, b)
#             else:
#                 return Integer(min(a.min, b.min), max(a.max, b.max))

#         elif isinstance(other, Real) and other.min <= self.min and self.max <= other.max:
#             return other

#         elif isinstance(other, Union):
#             ints = sorted([self] + [x for x in other.types if isinstance(x, Integer)])
#             out = [ints[0]]
#             for b in ints[1:]:
#                 if out[-1].max < b.min - 1:
#                     out.append(b)
#                 elif out[-1].max == b.min or out[-1].max == b.min - 1:
#                     out[-1] = Integer(out[-1].min, b.max)

#             nonints = sorted([x for x in other.types if not isinstance(x, Integer)])
#             if len(out) == 1 and len(nonints) == 0:
#                 return out[0]
#             else:
#                 return Union(*sorted(out + nonints))

#         else:
#             return Union(self, other)

#     def intersection(self, other):
#         if isinstance(other, (Integer, Real)):
#             othermin = other.min + 1 if isinstance(other.min, almost) else other.min
#             othermax = other.max - 1 if isinstance(other.max, almost) else other.max
#             if othermin > othermax:
#                 return impossible
#             other2 = other.__class__(othermin, othermax)

#             a, b = sorted([self, other2])
#             if a.max < b.min:
#                 return impossible
#             else:
#                 return Integer(max(a.min, b.min), min(a.max, b.max))

#         elif isinstance(other, Union):
#             ts = [self.intersection(t) for t in other.types]
#             return union(*ts)

#         else:
#             return impossible

# integer = Integer()

# class Real(Schema):
#     order = 4

#     def __init__(self, min=-inf, max=inf):
#         if min > max:
#             raise FemtocodeError("min must not be greater than max")
#         if min == max and isinstance(min, almost):
#             raise FemtocodeError("min and max may only be equal to one another if they are closed endpoints (not 'almost')")
#         if min != -inf and not isinstance(min, (int, long, float)):
#             raise FemtocodeError("min must be -inf or a float/almost endpoint")
#         if max != inf and not isinstance(max, (int, long, float)):
#             raise FemtocodeError("min must be inf or a float/almost endpoint")
#         self.min = min
#         self.max = max

#     def __repr__(self):
#         if self.min == -inf and self.max == inf:
#             return "real"
#         else:
#             return "real(min={0}, max={1})".format(self.min, self.max)

#     def __lt__(self, other):
#         if isinstance(other, Real):
#             if self.min == other.min:
#                 return self.max < other.max
#             else:
#                 return self.min < other.min
#         else:
#             return self.order < other.order

#     def __eq__(self, other):
#         if not isinstance(other, Real):
#             return False
#         else:
#             return self.min == other.min and self.max == other.max

#     def __hash__(self):
#         return hash((Real, self.min, self.max))

#     def union(self, other):
#         if isinstance(other, Real):
#             a, b = sorted([self, other])
#             if a.max < b.min - 1 or (a.max == b.min and isinstance(a.max, almost)):
#                 return Union(a, b)
#             else:
#                 return Real(almost.min(a.min, b.min), almost.max(a.max, b.max))

#         elif isinstance(other, Integer) and self.min <= other.min and other.max <= self.max:
#             return self

#         elif isinstance(other, Union):
#             reals = sorted([self] + [x for x in other.types if isinstance(x, Real)])
#             out = [reals[0]]
#             for b in reals[1:]:
#                 if out[-1].max < b.min:
#                     out.append(b)
#                 elif out[-1].max == b.min:
#                     out[-1] = Real(out[-1].min, b.max)

#             nonreals = sorted([x for x in other.types if not isinstance(x, Real)])
#             if len(out) == 1 and len(nonreals) == 0:
#                 return out[0]
#             else:
#                 return Union(*sorted(out + nonreals))

#         else:
#             return Union(self, other)

#     def intersection(self, other):
#         if isinstance(other, (Integer, Real)):
#             a, b = sorted([self, other])
#             if a.max < b.min:
#                 return impossible
#             elif isinstance(other, Real):
#                 return Real(max(a.min, b.min), min(a.max, b.max))
#             else:
#                 return Integer(max(a.min, b.min), min(a.max, b.max))

#         elif isinstance(other, Union):
#             return union(*[self.intersection(t) for t in other.types])

#         else:
#             return impossible

# real = Real()
        
# class String(Schema):
#     order = 5

#     def __repr__(self):
#         return "string"

# string = String()
        
# class Binary(Schema):
#     order = 6

#     def __init__(self, size=None):
#         self.size = size

#     def __repr__(self):
#         if size is None:
#             return "binary"
#         else:
#             return "binary({0})".format(self.size)

#     def __lt__(self, other):
#         if isinstance(other, Binary):
#             if self.size is None and other.size is None:
#                 return False
#             elif self.size is None:
#                 return False
#             elif other.size is None:
#                 return True
#             else:
#                 return self.size < other.size
#         else:
#             return self.order < other.order

#     def __eq__(self, other):
#         if not isinstance(other, Binary):
#             return False
#         else:
#             return self.size == other.size

#     def __hash__(self):
#         return hash((Binary, self.size))

#     def union(self, other):
#         if isinstance(other, Binary) and self.size == other.size:
#             return self
#         elif isinstance(other, Union):
#             if any(isinstance(x, Binary) and self.size == x.size for x in other.types):
#                 return other
#             else:
#                 return Union(self, *other.types)
#         else:
#             return Union(self, other)

#     def intersection(self, other):
#         if isinstance(other, self.Binary) and self.size == other.size:
#             return self
#         elif isinstance(other, Union):
#             if any(isinstance(x, self.Binary) and self.size == x.size for x in other.types):
#                 return self
#             else:
#                 return impossible
#         else:
#             return impossible

# binary = Binary()

# class Record(Schema):
#     order = 7

#     def __init__(self, **fields):
#         self.fields = sorted(fields.items())

#     def __repr__(self):
#         return "record(" + ", ".join(n + "=" + repr(t) for n, t in self.fields) + ")"

#     def __lt__(self, other):
#         if isinstance(other, Record):
#             return self.fields < other.fields
#         else:
#             return self.order < other.order

#     def __eq__(self, other):
#         if not isinstance(other, Record):
#             return False
#         else:
#             return self.fields == other.fields

#     def __hash__(self):
#         return hash((Record, self.fields))
    
# record = Record

# class Collection(Schema):
#     order = 8

#     def __init__(self, itemtype, fewest=0, most=almost(inf)):
#         self.itemtype = itemtype
#         if fewest > most:
#             raise FemtocodeError("fewest must not be greater than most")
#         if not isinstance(fewest, (int, long)) or fewest < 0:
#             raise FemtocodeError("fewest must be a non-negative integer")
#         if most != almost(inf) and not isinstance(most, (int, long)):
#             raise FemtocodeError("fewest must be almost(inf) or an integer")
#         self.fewest = fewest
#         self.most = most

#     def __repr__(self):
#         if self.fewest == 0 and self.most == almost(inf):
#             return "collection({0})".format(repr(self.itemtype))
#         else:
#             return "collection({0}, fewest={1}, most={2})".format(repr(self.itemtype), self.fewest, self.most)

#     def __lt__(self, other):
#         if isinstance(other, Collection):
#             if self.itemtype == other.itemtype:
#                 if self.fewest == other.fewest:
#                     return self.most < other.most
#                 else:
#                     return self.fewest < other.fewest
#             else:
#                 return self.itemtype < other.itemtype
#         else:
#             return self.order < other.order
                
#     def __eq__(self, other):
#         if not isinstance(other, Collection):
#             return False
#         else:
#             return self.itemtype == other.itemtype and self.fewest == other.fewest and self.most == other.most

#     def __hash__(self):
#         return hash((Collection, self.itemtype, self.fewest, self.most))

#     def union(self, other):
#         if isinstance(other, Collection):
#             subtype = self.itemtype.union(other.itemtype)
#             if (self.itemtype == subtype and other.itemtype == subtype) or \
#                    (isinstance(subtype, (Integer, Real))) or \
#                    (isinstance(subtype, Union) and all(isinstance(t, (Integer, Real)) for t in subtype.types)):
#                 size = Integer(self.fewest, self.most).union(Integer(other.fewest, other.most))
#                 if isinstance(size, Union):
#                     if len(size.types) != 2:
#                         raise ProgrammingError("union of two integer intervals should be a union of at most two intervals")
#                     one, two = size.types
#                     size = Integer(almost.min(one.min, two.min), almost.max(one.max, two.max))
#                 return Collection(subtype, size.min, size.max)
#             else:
#                 return Union(self, other)
#         elif isinstance(other, Union):
#             return Union(self, *other.types)
#         else:
#             return Union(self, other)

#     def intersection(self, other):
#         if isinstance(other, Collection):
#             subtype = self.itemtype.intersection(other.itemtype)
#             if (self.itemtype == subtype and other.itemtype == subtype) or \
#                    (isinstance(subtype, (Integer, Real))) or \
#                    (isinstance(subtype, Union) and all(isinstance(t, (Integer, Real)) for t in subtype.types)):
#                 size = Integer(self.fewest, self.most).intersection(Integer(other.fewest, other.most))
#                 if not isinstance(size, (Integer, Impossible)):
#                     raise ProgrammingError("intersection of two integer intervals should be an interval integer or impossible")
#                 if isinstance(subtype, Impossible) or isinstance(size, Impossible):
#                     return impossible
#                 else:
#                     return Collection(subtype, size.min, size.max)
#             else:
#                 return impossible
#         elif isinstance(other, Union):
#             return union(*[self.intersection(t) for t in other.types])
#         else:
#             return impossible

# collection = Collection

# class Tensor(Schema):
#     order = 9

#     def __init__(self, itemtype, dimensions):
#         self.itemtype = itemtype
#         if isinstance(dimensions, (list, tuple)):
#             self.dimensions = tuple(dimensions)
#         else:
#             self.dimensions = (dimensions,)

#     def __repr__(self):
#         if len(self.dimensions) == 1:
#             return "tensor({0}, dimensions={1})".format(repr(self.itemtype), self.dimensions[0])
#         else:
#             return "tensor({0}, dimensions={1})".format(repr(self.itemtype), self.dimensions)

#     def __lt__(self, other):
#         if isinstance(other, Tensor):
#             if self.itemtype == other.itemtype:
#                 return self.dimensions < other.dimensions
#             else:
#                 return self.itemtype < other.itemtype
#         else:
#             return self.order < other.order
                
#     def __eq__(self, other):
#         if not isinstance(other, Collection):
#             return False
#         else:
#             return self.itemtype == other.itemtype and self.dimensions == other.dimensions

#     def __hash__(self):
#         return hash((Tensor, self.itemtype, self.dimensions))

#     def union(self, other):
#         if isinstance(other, Tensor) and self.dimensions == other.dimensions:
#             subtype = self.itemtype.union(other.itemtype)
#             if (self.itemtype == subtype and other.itemtype == subtype) or \
#                    (isinstance(subtype, (Integer, Real))) or \
#                    (isinstance(subtype, Union) and all(isinstance(t, (Integer, Real)) for t in subtype.types)):
#                 return Tensor(subtype, self.dimensions)
#             else:
#                 return Union(self, other)
#         elif isinstance(other, Union):
#             return Union(self, *other.types)
#         else:
#             return Union(self, other)

#     def intersection(self, other):
#         if isinstance(other, Tensor) and self.dimensions == other.dimensions:
#             subtype = self.itemtype.intersection(other.itemtype)
#             if (self.itemtype == subtype and other.itemtype == subtype) or \
#                    (isinstance(subtype, (Integer, Real))) or \
#                    (isinstance(subtype, Union) and all(isinstance(t, (Integer, Real)) for t in subtype.types)):
#                 return Tensor(subtype, self.dimensions)
#             else:
#                 return Union(self, other)
#         elif isinstance(other, Union):
#             return union(*[self.intersection(t) for t in other.types])
#         else:
#             return impossible

# tensor = Tensor

# class Union(Schema):
#     order = 10

#     def __init__(self, *types):
#         if len(types) < 1:
#             raise FemtocodeError("Union requires at least one type")
#         self.types = sorted(types)

#     def __repr__(self):
#         return "union(" + ", ".join(repr(t) for t in self.types) + ")"

#     def __lt__(self, other):
#         if isinstance(other, Union):
#             return self.types < other.types
#         else:
#             return self.order < other.order
                
#     def __eq__(self, other):
#         if not isinstance(other, Union):
#             return False
#         else:
#             return self.types == other.types

#     def __hash__(self):
#         return hash((Union, self.types))

#     def union(self, other):
#         if isinstance(other, Union):
#             types = self.types + other.types
#         else:
#             types = list(self.types) + [other]
#         return union(*types)

# def union(*types):
#     if len(types) == 0:
#         return null
#     elif len(types) == 1:
#         return types[0]
#     else:
#         out = types[0]
#         for t in types[1:]:
#             out = out.union(t)
#         return out

# def intersection(*types):
#     if len(types) == 0:
#         return impossible
#     elif len(types) == 1:
#         return types[0]
#     else:
#         out = types[0]
#         for t in types[1:]:
#             out = out.intersection(t)
#         return out
