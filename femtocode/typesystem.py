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

inf = float("inf")

class Type(object):
    def accepts(self, other):
        raise NotImplementedError

class Missing(Type):
    def __repr__(self):
        return "missing"
    def accepts(self, other):
        return isinstance(other, Missing)
    def __call__(self, *args, **kwds):
        return Missing(*args, **kwds)

missing = Missing()

class Boolean(Type):
    def __repr__(self):
        return "boolean"
    def accepts(self, other):
        return isinstance(other, Boolean)
    def __call__(self, *args, **kwds):
        return Boolean(*args, **kwds)

boolean = Boolean()

class Integer(Type):
    def __init__(self, min=-inf, max=inf):
        self.min = min
        self.max = max
    def __repr__(self):
        if self.min == -inf and self.max == inf:
            return "integer"
        else:
            return "integer({0}, {1})".format(self.min, self.max)
    def accepts(self, other):
        return isinstance(other, Integer)
    def __call__(self, *args, **kwds):
        return Integer(*args, **kwds)

integer = Integer()

class Real(Type):
    def __init__(self, inf=None, sup=None, min=None, max=None):
        if min is None and inf is None:
            self.min = None
            self.inf = float("-inf")
        elif min is None:
            self.min = None
            self.inf = inf
        elif inf is None:
            self.min = min
            self.inf = None
        else:
            raise TypeError("cannot specify both min and inf")
        if max is None and sup is None:
            self.max = None
            self.sup = float("inf")
        elif max is None:
            self.max = None
            self.sup = sup
        elif sup is None:
            self.max = max
            self.sup = None
        else:
            raise TypeError("cannot specify both max and sup")
    def __repr__(self):
        if self.inf == float("-inf") and self.sup == float("inf"):
            return "real"
        else:
            return "Real()"
    def accepts(self, other):
        return isinstance(other, (Integer, Real))
    def __call__(self, *args, **kwds):
        return Real(*args, **kwds)

real = Real()
        
class String(Type):
    def __repr__(self):
        return "string"
    def accepts(self, other):
        return isinstance(other, String)
    def __call__(self, *args, **kwds):
        return String(*args, **kwds)

string = String()
        
class Binary(Type):
    def __init__(self, size=None):
        self.size = size
    def __repr__(self):
        if size is None:
            return "binary"
        else:
            return "binary({0})".format(self.size)
    def accepts(self, other):
        return isinstance(other, Binary)
    def __call__(self, *args, **kwds):
        return Binary(*args, **kwds)

binary = Binary()

class Record(Type):
    def __init__(self, **fields):
        self.fields = sorted(fields.items())
    def __repr__(self):
        return "record(" + ", ".join(n + " = " + repr(t) for n, t in self.fields) + ")"
    def accepts(self, other):
        if not isinstance(other, Record):
            return False
        for n, t in self.fields:
            if n not in other.fields:
                return False
            if not t.accept(other[n]):
                return False
        return True
    def __call__(self, *args, **kwds):
        return Record(*args, **kwds)

record = Record

class Collection(Type):
    def __init__(self, itemtype, min=0, max=None):
        self.itemtype = itemtype
        self.min = min
        self.max = max
    def __repr__(self):
        if self.min == 0 and self.max is None:
            return "collection({0})".format(repr(self.itemtype))
        else:
            return "collection({0}, {1}, {2})".format(repr(self.itemtype), self.min, self.max)
    def accepts(self, other):
        return isinstance(other, Collection) and self.itemtype.accepts(other.itemtype)
    def __call__(self, *args, **kwds):
        return Collection(*args, **kwds)

collection = Collection

class Tensor(Type):
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
    def accepts(self, other):
        return isinstance(other, Tensor) and self.itemtype.accepts(other.itemtype) and self.dimensions == other.dimensions
    def __call__(self, *args, **kwds):
        return Tensor(*args, **kwds)

tensor = Tensor

class Union(Type):
    def __init__(self, *types):
        self.types = types
    def __repr__(self):
        return "union(" + ", ".join(repr(t) for t in self.types) + ")"
    def accepts(self, other):
        return any(t.accepts(other) for t in self.types)
    def __call__(self, *args, **kwds):
        return Union(*args, **kwds)

union = Union

class Function:
    def __init__(self, args, ret):
        self.args = args
        self.ret = ret
    def __repr__(self):
        return "function({0}, {1})".format(self.args, self.ret)
    def accepts(self, other):
        return isinstance(other, Function) and all(other.accepts(t) for t in self.types) and self.ret.accepts(other.ret)
    def __call__(self, *args, **kwds):
        return Function(*args, **kwds)

function = Function
