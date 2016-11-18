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
import json
import math

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
    def __init__(self, alias=None):
        if alias is not None and not isinstance(alias, basestring):
            raise FemtocodeError("alias {0} must be None or a string".format(alias))
        self.alias = alias

    def __contains__(self, other):
        raise NotImplementedError

    def __lt__(self, other):
        if not isinstance(other, Schema):
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))
        return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash((self.order,))

    def __call__(self, alias=None):
        return self.__class__(alias)

class Impossible(Schema):   # results in a compilation error
    order = -1

    def __repr__(self):
        return "impossible"

    def __contains__(self, other):
        return False

impossible = Impossible()

class Null(Schema):
    order = 0

    def __repr__(self):
        return "null"

    def __contains__(self, other):
        return isinstance(other, Null) or other is None

null = Null()

class Boolean(Schema):
    order = 1

    def __repr__(self):
        return "boolean"

    def __contains__(self, other):
        return isinstance(other, Boolean) or other is True or other is False

boolean = Boolean()

class Number(Schema):
    order = 2

    def __init__(self, min=almost(-inf), max=almost(inf), whole=False, alias=None):
        if not isinstance(min, (int, long, float)):
            raise FemtocodeError("min ({0}) must be a number (or an almost(number))".format(min))
        if not isinstance(max, (int, long, float)):
            raise FemtocodeError("max ({0}) must be a number (or an almost(number))".format(max))
        if not isinstance(whole, bool):
            raise FemtocodeError("whole ({0}) must be boolean".format(whole))

        if whole:
            if min == -inf:
                raise FemtocodeError("for whole-numbered intervals, min ({0}) cannot be -inf; try almost(-inf)".format(min))
            if max == inf:
                raise FemtocodeError("for whole-numbered intervals, max ({0}) cannot be inf; try almost(inf)".format(max))
            if isinstance(min, almost) and min != almost(-inf) and round(min) == min.real:
                min = min.real + 1
            if isinstance(max, almost) and max != almost(inf) and round(max) == max.real:
                max = max.real - 1
            if round(min) != min.real:
                min = math.ceil(min)
            if round(max) != max.real:
                max = math.floor(max)

        if min > max:
            raise FemtocodeError("min ({0}) must not be greater than max ({1}){2}".format(min, max, " after adjustments for whole-numbered interval" if whole else ""))
        if min == max and isinstance(min, almost):
            raise FemtocodeError("min ({0}) and max ({1}) may only be equal to one another if they are closed endpoints (not almost(endpoint))".format(min, max))
            
        self.min = min
        self.max = max
        self.whole = whole
        super(Number, self).__init__(alias)

    def __repr__(self):
        if self.whole and self.min == almost(-inf) and self.max == almost(inf):
            return "integer"
        elif self.whole:
            return "integer(min={0}, max={1})".format(self.min, self.max)
        elif self.min == -inf and self.max == inf:
            return "extended"
        elif self.min == -inf or self.max == inf:
            return "extended(min={0}, max={1})".format(self.min, self.max)
        elif self.min == almost(-inf) and self.max == almost(inf):
            return "real"
        else:
            return "real(min={0}, max={1})"

    def __contains__(self, other):
        if isinstance(other, Number):
            ok = True

            if isinstance(self.min, almost) and not isinstance(other.min, almost):
                # for self to be the superset, its open min must be strictly below other's closed min
                ok = ok and self.min < other.min
            else:
                # any other case permits equality
                ok = ok and self.min <= other.min

            if isinstance(self.max, almost) and not isinstance(other.max, almost):
                # for self to be the superset, its open max must be strictly above other's closed max
                ok = ok and other.max < self.max
            else:
                # any other case permits equality
                ok = ok and other.max <= self.max

            if self.whole:
                # since self is only whole numbers, other must be whole numbers or a single whole value
                ok = ok and other.whole or (other.min == other.max and round(other.min) == other.min)

            return ok

        elif isinstance(other, Schema):
            return False

        elif isinstance(other, (int, long, float)):
            ok = True

            if isinstance(self.min, almost):
                ok = ok and self.min < other
            else:
                ok = ok and self.min <= other

            if isinstance(self.max, almost):
                ok = ok and other < self.max
            else:
                ok = ok and other <= self.max

            if self.whole:
                ok = ok and round(other) == other

            return ok

        else:
            return False

    def __lt__(self, other):
        if not isinstance(other, Schema):
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))
        if self.order == other.order:
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
        if not isinstance(other, Schema):
            return False
        return self.__class__ == other.__class__ and \
               self.min == other.min and \
               self.max == other.max and \
               self.whole == other.whole

    def __hash__(self):
        return hash((self.order, self.min, self.max, self.whole))

    def __call__(self, min=None, max=None, whole=None, alias=None):
        return self.__class__(self.min if min is None else min,
                              self.max if max is None else max,
                              self.whole if whole is None else whole,
                              alias)

integer = Number(almost(-inf), almost(inf), True)

real = Number(almost(-inf), almost(inf), False)

extended = Number(-inf, inf, False)

class String(Schema):
    order = 3

    def __init__(self, fewest=0, most=almost(inf), charset="bytes", alias=None):
        if not isinstance(fewest, (int, long)) or fewest < 0:
            raise FemtocodeError("fewest ({0}) must be a nonnegative integer".format(fewest))
        if not isinstance(most, (int, long)) and most != almost(inf):
            raise FemtocodeError("most ({0}) must be an integer or almost(inf)".format(most))
        if fewest > most:
            raise FemtocodeError("fewest ({0}) must not be greater than most ({1})".format(fewest, most))
        if charset not in ("bytes", "unicode"):
            raise FemtocodeError("charset {0} not recognized".format(json.dumps(charset)))

        self.fewest = fewest
        self.most = most
        self.charset = charset
        super(String, self).__init__(alias)

    def __repr__(self):
        args = []
        if not self.fewest == 0:
            args.append("fewest={0}".format(self.fewest))
        if not self.most == almost(inf):
            args.append("most={0}".format(self.most))
        if self.charset != "bytes":
            args.append("charset={0}".format(json.dumps(self.charset)))
        if len(args) == 0:
            return "string"
        else:
            return "string({0})".format(", ".join(args))

    # def __contains__(self, other):
    #     if isinstance(other, String):






    def __lt__(self, other):
        if not isinstance(other, Schema):
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))
        if self.order == other.order:
            if self.fewest == other.fewest:
                if self.most == other.most:
                    return self.charset < other.charset
                else:
                    return self.most < other.most
            else:
                return self.fewest < other.fewest
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               self.fewest == other.fewest and \
               self.most == other.most and \
               self.charset == other.charset

    def __hash__(self):
        return hash((self.order, self.fewest, self.most, self.charset))

    def __call__(self, fewest=None, most=None, charset=None, alias=None):
        return self.__class__(self.fewest if fewest is None else fewest,
                              self.most if most is None else most,
                              self.charset if charset is None else charset,
                              alias)

string = String(0, almost(inf), "bytes")

class Tensor(Schema):
    order = 4

    def __init__(self, items, dimensions, alias=None):
        if not isinstance(items, (Schema, basestring)):
            raise FemtocodeError("items ({0}) must be a Schema or an alias string".format(items))
        if isinstance(dimensions, (list, tuple)):
            dimensions = tuple(dimensions)
        else:
            dimensions = (dimensions,)
        if not all(isinstance(x, (int, long)) and x > 0 for x in dimensions):
            raise FemtocodeError("all elements of dimensions ({0}) must be positive integers".format(dimensions))

        self.items = items
        self.dimensions = dimensions
        super(Tensor, self).__init__(alias)

    def __repr__(self):
        return "tensor({0}, {1})".format(self.items, ", ".join(map(repr, self.dimensions)))

    def __lt__(self, other):
        if not isinstance(other, Schema):
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))
        if self.order == other.order:
            if self.items == other.items:
                return self.dimensions < other.dimensions
            else:
                return self.items < other.items
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               self.items == other.items and \
               self.dimensions == other.dimensions

    def __hash__(self):
        return hash((self.order, self.items, self.dimensions))

    def __call__(self, items=None, *dimensions):
        if len(dimensions) > 0 and isinstance(dimensions[-1], (Schema, basestring)):
            alias = alias[-1]
            dimensions = dimensions[:-1]
        else:
            alias = None
        return self.__class__(self.items if items is None else items,
                              self.dimensions if dimensions is None else dimensions,
                              alias)

def tensor(items, *dimensions):
    if len(dimensions) > 0 and isinstance(dimensions[-1], (Schema, basestring)):
        alias = alias[-1]
        dimensions = dimensions[:-1]
    else:
        alias = None
    return Tensor(items, dimensions, alias)
    
class Collection(Schema):
    order = 5

    def __init__(self, items, fewest=0, most=almost(inf), alias=None):
        if not isinstance(items, (Schema, basestring)):
            raise FemtocodeError("items ({0}) must be a Schema or an alias string".format(items))
        if not isinstance(fewest, (int, long)) or fewest < 0:
            raise FemtocodeError("fewest ({0}) must be a nonnegative integer".format(fewest))
        if not isinstance(most, (int, long)) and most != almost(inf):
            raise FemtocodeError("most ({0}) must be an integer or almost(inf)".format(most))
        if fewest > most:
            raise FemtocodeError("fewest ({0}) must not be greater than most ({1})".format(fewest, most))

        self.items = items
        self.fewest = fewest
        self.most = most
        super(Collection, self).__init__(alias)

    def __repr__(self):
        args = [repr(self.items)]
        if not self.fewest == 0:
            args.append("fewest={0}".format(self.fewest))
        if not self.most == almost(inf):
            args.append("most={0}".format(self.most))
        return "collection({0})".format(", ".join(args))

    def __lt__(self, other):
        if not isinstance(other, Schema):
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))
        if self.order == other.order:
            if self.items == other.items:
                if self.fewest == other.fewest:
                    return self.most < other.most
                else:
                    return self.fewest < other.fewest
            else:
                return self.items < other.items
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               self.items == other.items and \
               self.fewest == other.fewest and \
               self.most == other.most

    def __hash__(self):
        return hash((self.order, self.items, self.fewest, self.most))

    def __call__(self, items=None, fewest=None, most=None, alias=None):
        return self.__class__(self.items if items is None else items,
                              self.fewest if fewest is None else fewest,
                              self.most if most is None else most,
                              alias)

def collection(items, fewest=0, most=almost(inf), alias=None):
    return Collection(items, fewest, most)

class Record(Schema):
    order = 6

    def __init__(self, fields, alias=None):
        if not isinstance(fields, dict):
            raise FemtocodeError("fields ({0}) must be a dictionary".format(fields))
        for n, t in fields.items():
            if not isinstance(n, basestring) or not isinstance(t, (Schema, basestring)):
                raise FemtocodeError("all fields ({0}: {1}) must map field names (string) to field types (Schema or alias string)".format(n, t))

        self.fields = fields
        super(Record, self).__init__(alias)

    def __repr__(self):
        return "record({0})".format(", ".join(n + " = " + repr(t) for n, t in self.fields.items()))

    def __lt__(self):
        if not isinstance(other, Schema):
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))
        if self.order == other.order:
            return self.fields < other.fields
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               self.fields == other.fields

    def __hash__(self):
        return hash((self.order, tuple(sorted(self.fields.items()))))

    def __call__(self, __alias__=None, **fields):
        return self.__class__(dict(self.fields, **fields), __alias__)

def record(__alias__=None, **fields):
    return Record(fields, __alias__)

class Union(Schema):
    order = 7

    def __init__(self, possibilities, alias=None):
        if not isinstance(possibilities, (list, tuple)):
            raise FemtocodeError("possibilities ({0}) must be a list or tuple".format(possibilities))
        for p in possibilities:
            if not isinstance(p, (Schema, basestring)):
                raise FemtocodeError("all possibilities ({0}) must be Schemas or alias strings".format(p))

        self.possibilities = tuple(possibilities)
        super(Union, self).__init__(alias)

    def __repr__(self):
        return "union({0})".format(", ".join(map(repr, possibilities)))

    def __lt__(self, other):
        if not isinstance(other, Schema):
            raise TypeError("unorderable types: {0}() < {1}()".format(self.__class__.__name__, type(other).__name__))
        if self.order == other.order:
            return self.possibilities < other.possibilities
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Schema):
            return False
        return self.order == other.order and \
               self.possibilities == other.possibilities

    def __hash__(self):
        return hash((self.order, self.possibilities))

    def __call__(self, *possibilities):
        return self.__class__(possibilities)
    
def union(*possibilities):
    if len(possibilities) == 0:
        raise TypeError("union() takes at least 1 argument (0 given)")

    elif len(possibilities) == 1:
        return possibilities[0]

    elif len(possibilities) > 2:
        # combine them in the order given by the user for more comprehensible error messages
        return union(union(possibilities[0], possibilities[1]), possibilities[2:])

    else:
        one, two = possibilities

        if isinstance(one, Impossible) or isinstance(two, Impossible):
            return impossible

        
        
