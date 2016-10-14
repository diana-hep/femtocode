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

from itertools import groupby

from femtocode.defs import FemtocodeError

inf = float("inf")

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
        return hash((self.real,))

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

    def union(self, other):
        if isinstance(other, self.__class__):
            return self
        elif isinstance(other, Union):
            if any(isinstance(x, self.__class__) for x in other.types):
                return other
            else:
                return Union(self, *other.types)
        else:
            return Union(self, other)

    def intersect(self, other):
        if isinstance(other, self.__class__):
            return self
        elif isinstance(other, Union):
            if any(isinstance(x, self.__class__) for x in other.types):
                return self
            else:
                return impossible
        else:
            return impossible

class Impossible(Schema):
    order = 0

    def __repr__(self):
        return "impossible"

    def __call__(self, *args, **kwds):
        return Impossible(*args, **kwds)

    def union(self, other):
        return other

    def intersect(self, other):
        return impossible

impossible = Impossible()

class NA(Schema):
    order = 1

    def __repr__(self):
        return "na"

    def __call__(self, *args, **kwds):
        return NA(*args, **kwds)
        
na = NA()

class Boolean(Schema):
    order = 2

    def __repr__(self):
        return "boolean"

    def __call__(self, *args, **kwds):
        return Boolean(*args, **kwds)

boolean = Boolean()

class Integer(Schema):
    order = 3

    def __init__(self, min=almost(-inf), max=almost(inf)):
        if min > max:
            raise FemtocodeError("min must not be greater than max")
        if min != almost(-inf) and not isinstance(min, (int, long)):
            raise FemtocodeError("min must be almost(-inf) or an integer")
        if max != almost(inf) and not isinstance(max, (int, long)):
            raise FemtocodeError("min must be almost(inf) or an integer")
        self.min = min
        self.max = max

    def __repr__(self):
        if self.min == almost(-inf) and self.max == almost(inf):
            return "integer"
        else:
            return "integer(min={0}, max={1})".format(self.min, self.max)

    def __call__(self, *args, **kwds):
        return Integer(*args, **kwds)

    def __lt__(self, other):
        if isinstance(other, Integer):
            if self.min == other.min:
                return self.max < other.max
            else:
                return self.min < other.min
        else:
            return self.order < other.order

    def union(self, other):
        if isinstance(other, Integer):
            a, b = sorted([self, other])
            if a.max < b.min - 1:
                return Union(a, b)
            else:
                return Integer(min(a.min, b.min), max(a.max, b.max))

        elif isinstance(other, Real) and other.min <= self.min and self.max <= other.max:
            return other

        elif isinstance(other, Union):
            ints = sorted([self] + [x for x in other.types if isinstance(x, Integer)])
            out = [ints[0]]
            for b in ints[1:]:
                if out[-1].max < b.min - 1:
                    out.append(b)
                elif out[-1].max == b.min or out[-1].max == b.min - 1:
                    out[-1] = Integer(out[-1].min, b.max)

            nonints = sorted([x for x in other.types if not isinstance(x, Integer)])
            if len(out) == 1 and len(nonints) == 0:
                return out[0]
            else:
                return Union(*sorted(out + nonints))

        else:
            return Union(self, other)

    def intersect(self, other):
        if isinstance(other, (Integer, Real)):
            othermin = other.min + 1 if isinstance(other.min, almost) else other.min
            othermax = other.max - 1 if isinstance(other.max, almost) else other.max
            if othermin > othermax:
                return impossible
            other2 = other.__class__(othermin, othermax)

            a, b = sorted([self, other2])
            if a.max < b.min:
                return impossible
            else:
                return Integer(max(a.min, b.min), min(a.max, b.max))

        elif isinstance(other, Union):
            ts = [self.intersect(t) for t in other.types]
            return union(*ts)

        else:
            return impossible

integer = Integer()

class Real(Schema):
    order = 4

    def __init__(self, min=-inf, max=inf):
        if min > max:
            raise FemtocodeError("min must not be greater than max")
        if min == max and isinstance(min, almost):
            raise FemtocodeError("min and max may only be equal to one another if they are closed endpoints (not 'almost')")
        if min != -inf and not isinstance(min, (int, long, float)):
            raise FemtocodeError("min must be -inf or a float/almost endpoint")
        if max != inf and not isinstance(max, (int, long, float)):
            raise FemtocodeError("min must be inf or a float/almost endpoint")
        self.min = min
        self.max = max

    def __repr__(self):
        if self.min == -inf and self.max == inf:
            return "real"
        else:
            return "real(min={0}, max={1})".format(self.min, self.max)

    def __call__(self, *args, **kwds):
        return Real(*args, **kwds)

    def __lt__(self, other):
        if isinstance(other, Real):
            if self.min == other.min:
                return self.max < other.max
            else:
                return self.min < other.min
        else:
            return self.order < other.order

    def union(self, other):
        if isinstance(other, Real):
            a, b = sorted([self, other])
            if a.max < b.min - 1 or (a.max == b.min and isinstance(a.max, almost)):
                return Union(a, b)
            else:
                return Real(almost.min(a.min, b.min), almost.max(a.max, b.max))

        elif isinstance(other, Integer) and self.min <= other.min and other.max <= self.max:
            return self

        elif isinstance(other, Union):
            reals = sorted([self] + [x for x in other.types if isinstance(x, Real)])
            out = [reals[0]]
            for b in reals[1:]:
                if out[-1].max < b.min:
                    out.append(b)
                elif out[-1].max == b.min:
                    out[-1] = Real(out[-1].min, b.max)

            nonreals = sorted([x for x in other.types if not isinstance(x, Real)])
            if len(out) == 1 and len(nonreals) == 0:
                return out[0]
            else:
                return Union(*sorted(out + nonreals))

        else:
            return Union(self, other)

    def intersect(self, other):
        if isinstance(other, (Integer, Real)):
            a, b = sorted([self, other])
            if a.max < b.min:
                return impossible
            elif isinstance(other, Real):
                return Real(max(a.min, b.min), min(a.max, b.max))
            else:
                return Integer(max(a.min, b.min), min(a.max, b.max))

        elif isinstance(other, Union):
            ts = [self.intersect(t) for t in other.types]
            return union(*ts)

        else:
            return impossible

real = Real()
        
class String(Schema):
    order = 5

    def __repr__(self):
        return "string"

    def __call__(self, *args, **kwds):
        return String(*args, **kwds)

string = String()
        
class Binary(Schema):
    order = 6

    def __init__(self, size=None):
        self.size = size

    def __repr__(self):
        if size is None:
            return "binary"
        else:
            return "binary({0})".format(self.size)

    def __call__(self, *args, **kwds):
        return Binary(*args, **kwds)

    def __lt__(self, other):
        if isinstance(other, Binary):
            if self.size is None and other.size is None:
                return False
            elif self.size is None:
                return False
            elif other.size is None:
                return True
            else:
                return self.size < other.size
        else:
            return self.order < other.order

    def union(self, other):
        if isinstance(other, Binary) and self.size == other.size:
            return self
        elif isinstance(other, Union):
            if any(isinstance(x, Binary) and self.size == x.size for x in other.types):
                return other
            else:
                return Union(self, *other.types)
        else:
            return Union(self, other)

    def intersect(self, other):
        if isinstance(other, self.Binary) and self.size == other.size:
            return self
        elif isinstance(other, Union):
            if any(isinstance(x, self.Binary) and self.size == x.size for x in other.types):
                return self
            else:
                return impossible
        else:
            return impossible

binary = Binary()

class Record(Schema):
    order = 7

    def __init__(self, **fields):
        self.fields = sorted(fields.items())

    def __repr__(self):
        return "record(" + ", ".join(n + "=" + repr(t) for n, t in self.fields) + ")"

    def __call__(self, *args, **kwds):
        return Record(*args, **kwds)
    
record = Record

class Collection(Schema):
    order = 8

    def __init__(self, itemtype, min=0, max=None):
        self.itemtype = itemtype
        self.min = min
        self.max = max

    def __repr__(self):
        if self.min == 0 and self.max is None:
            return "collection({0})".format(repr(self.itemtype))
        else:
            return "collection({0}, {1}, {2})".format(repr(self.itemtype), self.min, self.max)

    def __call__(self, *args, **kwds):
        return Collection(*args, **kwds)

    def __lt__(self, other):
        return self.order < other.order

collection = Collection

class Tensor(Schema):
    order = 9

    def __init__(self, itemtype, dimensions):
        self.itemtype = itemtype
        if isinstance(dimensions, (list, tuple)):
            self.dimensions = tuple(dimensions)
        else:
            self.dimensions = (dimensions,)

    def __repr__(self):
        if len(self.dimensions) == 1:
            return "tensor({0}, {1})".format(repr(self.itemtype), self.dimensions[0])
        else:
            return "tensor({0}, {1})".format(repr(self.itemtype), self.dimensions)

    def __call__(self, *args, **kwds):
        return Tensor(*args, **kwds)

tensor = Tensor

class Union(Schema):
    order = 10

    def __init__(self, *types):
        if len(types) < 1:
            raise FemtocodeError("Union requires at least one type")
        self.types = types

    def __repr__(self):
        return "union(" + ", ".join(repr(t) for t in self.types) + ")"

    def __call__(self, *args, **kwds):
        return Union(*args, **kwds)

    def union(self, other):
        if isinstance(other, Union):
            types = self.types + other.types
        else:
            types = list(self.types) + [other]
        return union(*types)

def union(*types):
    if len(types) == 0:
        return na
    elif len(types) == 1:
        return types[0]
    else:
        out = types[0]
        for t in types[1:]:
            out = out.union(t)
        return out

def intersect(*types):
    if len(types) == 0:
        return impossible
    elif len(types) == 1:
        return types[0]
    else:
        out = types[0]
        for t in types[1:]:
            out = out.intersect(t)
        return out
