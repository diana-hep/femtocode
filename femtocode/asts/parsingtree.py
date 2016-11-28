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

from ast import AST
from ast import expr

# Use the Python AST directly
from ast import Add
from ast import And
from ast import Attribute
from ast import BinOp
from ast import BoolOp
from ast import Compare
from ast import Div
from ast import Eq
from ast import ExtSlice
from ast import FloorDiv
from ast import Gt
from ast import GtE
from ast import In
from ast import Index
from ast import List
from ast import Load
from ast import Lt
from ast import LtE
from ast import Mod
from ast import Mult
from ast import Name
from ast import Not
from ast import NotEq
from ast import NotIn
from ast import Num
from ast import Or
from ast import Param
from ast import Pow
from ast import Slice
from ast import Store
from ast import Str
from ast import Sub
from ast import Subscript
from ast import Tuple
from ast import UAdd
from ast import USub
from ast import UnaryOp

class Femtocode(AST): pass

class Suite(expr):
    _fields = ("assignments", "expression")
    def __init__(self, assignments, expression, **kwds):
        self.assignments = assignments
        self.expression = expression
        self.__dict__.update(kwds)

class AtArg(expr):
    _fields = ("num",)
    def __init__(self, num, **kwds):
        self.num = num
        self.__dict__.update(kwds)

class Assignment(expr):
    _fields = ("lvalues", "expression")
    def __init__(self, lvalues, expression, **kwds):
        self.lvalues = lvalues
        self.expression = expression
        self.__dict__.update(kwds)

class FcnCall(expr):
    _fields = ("function", "positional", "names", "named")
    def __init__(self, function, positional, names, named, **kwds):
        self.function = function
        self.positional = positional
        self.names = names
        self.named = named
        self.__dict__.update(kwds)

class FcnDef(expr):
    _fields = ("parameters", "defaults", "body")
    def __init__(self, parameters, defaults, body, **kwds):
        self.parameters = parameters
        self.defaults = defaults
        self.body = body
        self.__dict__.update(kwds)

class IfChain(expr):
    _fields = ("predicates", "consequents", "alternate")
    def __init__(self, predicates, consequents, alternate, **kwds):
        self.predicates = predicates
        self.consequents = consequents
        self.alternate = alternate
        self.__dict__.update(kwds)

class TypeCheck(expr):
    _fields = ("expr", "schema", "negate")
    def __init__(self, expr, schema, negate, **kwds):
        self.expr = expr
        self.schema = schema
        self.negate = negate
        self.__dict__.update(kwds)

def inherit_lineno(p0, px, alt=True):
    if isinstance(px, dict):
        p0.source = px["source"]
        p0.pos = px["pos"]
        p0.lineno = px["lineno"]
        p0.col_offset = px["col_offset"]
        p0.sourceName = px["sourceName"]
        p0.length = px["length"]
    else:
        p0.source = px.source
        p0.pos = px.pos
        p0.lineno = px.lineno
        p0.col_offset = px.col_offset
        p0.sourceName = px.sourceName
        p0.length = px.length
        if alt and hasattr(px, "alt"):
            p0.lineno = px.alt["lineno"]
            p0.col_offset = px.alt["col_offset"]

def unwrap_left_associative(args, alt=False):
    out = BinOp(args[0], args[1], args[2])
    inherit_lineno(out, args[0])
    args = args[3:]
    while len(args) > 0:
        out = BinOp(out, args[0], args[1])
        inherit_lineno(out, out.left)
        if alt:
            out.alt = {"lineno": out.lineno, "col_offset": out.col_offset}
            inherit_lineno(out, out.op)
        args = args[2:]
    return out

def unpack_trailer(atom, power_star):
    out = atom
    for trailer in power_star:
        if isinstance(trailer, FcnCall):
            trailer.function = out
            inherit_lineno(trailer, out)
            out = trailer
        elif isinstance(trailer, Attribute):
            trailer.value = out
            inherit_lineno(trailer, out, alt=False)
            if hasattr(out, "alt"):
                trailer.alt = out.alt
            out = trailer
        elif isinstance(trailer, Subscript):
            trailer.value = out
            inherit_lineno(trailer, out)
            out = trailer
        else:
            assert False
    return out

def negate(x):
    # push 'not' down below all 'and' and 'or' (also removing redundant double-negatives)

    if isinstance(x, UnaryOp) and isinstance(x.op, Not):
        return x.operand

    elif isinstance(x, BoolOp) and isinstance(x.op, And):
        op = Or()
        inherit_lineno(op, x.op)
        out = BoolOp(op, [negate(y) for y in x.values])
        inherit_lineno(out, x)
        return out

    elif isinstance(x, BoolOp) and isinstance(x.op, Or):
        op = And()
        inherit_lineno(op, x.op)
        out = BoolOp(op, [negate(y) for y in x.values])
        inherit_lineno(out, x)
        return out

    else:
        op = Not()
        inherit_lineno(op, x)
        out = UnaryOp(op, x)
        inherit_lineno(out, x)
        return out
