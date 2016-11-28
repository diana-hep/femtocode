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

def inheriting_lineno(px):
    out = {}
    if hasattr(px, "source"): out["source"] = px.source
    if hasattr(px, "pos"): out["pos"] = px.pos
    if hasattr(px, "lineno"): out["lineno"] = px.lineno
    if hasattr(px, "col_offset"): out["col_offset"] = px.col_offset
    if hasattr(px, "sourceName"): out["sourceName"] = px.sourceName
    if hasattr(px, "length"): out["length"] = px.length
    return out

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

def normalizeLogic(x, negate=False):
    # push 'not' down below 'and' and 'or' and remove double negatives, chained comparisons -> And/Or

    if isinstance(x, UnaryOp) and isinstance(x.op, Not):
        return normalizeLogic(x.operand, not negate)

    elif isinstance(x, BoolOp):
        if not negate:
            return BoolOp(x.op, [normalizeLogic(y, False) for y in x.values], **inheriting_lineno(x))
        elif isinstance(x.op, And):
            return BoolOp(Or(**inheriting_lineno(x.op)), [normalizeLogic(y, True) for y in x.values], **inheriting_lineno(x))
        elif isinstance(x.op, Or):
            return BoolOp(And(**inheriting_lineno(x.op)), [normalizeLogic(y, True) for y in x.values], **inheriting_lineno(x))
        else:
            raise Exception

    elif isinstance(x, Compare):
        comparisons = []
        left = normalizeLogic(x.left, False)
        for op, right in zip(x.ops, x.comparators):
            right = normalizeLogic(right, False)
            if negate:
                if isinstance(op, Eq):
                    op = NotEq(**inheriting_lineno(op))
                elif isinstance(op, NotEq):
                    op = Eq(**inheriting_lineno(op))
                elif isinstance(op, Lt):
                    op = GtE(**inheriting_lineno(op))
                elif isinstance(op, GtE):
                    op = Lt(**inheriting_lineno(op))
                elif isinstance(op, LtE):
                    op = Gt(**inheriting_lineno(op))
                elif isinstance(op, Gt):
                    op = LtE(**inheriting_lineno(op))
                elif isinstance(op, In):
                    op = NotIn(**inheriting_lineno(op))
                elif isinstance(op, NotIn):
                    op = In(**inheriting_lineno(op))
                else:
                    raise Exception
            comparisons.append(Compare(left, [op], [right], **inheriting_lineno(right)))
            left = right

        if len(comparisons) == 1:
            return comparisons[0]
        elif len(comparisons) > 1:
            if negate:
                return BoolOp(Or(**inheriting_lineno(x)), comparisons, **inheriting_lineno(x))
            else:
                return BoolOp(And(**inheriting_lineno(x)), comparisons, **inheriting_lineno(x))
        else:
            raise Exception

    elif isinstance(x, TypeCheck):
        if negate:
            return TypeCheck(x.expr, x.schema, not x.negate, **inheriting_lineno(x))
        else:
            return TypeCheck(x.expr, x.schema, x.negate, **inheriting_lineno(x))

    elif negate and isinstance(x, Name) and x.id == "True":
        return Name("False", x.ctx, **inheriting_lineno(x))

    elif negate and isinstance(x, Name) and x.id == "False":
        return Name("True", x.ctx, **inheriting_lineno(x))

    elif isinstance(x, Suite):
        return Suite([normalizeLogic(y, negate) for y in x.assignments], normalizeLogic(x.expression, negate), **inheriting_lineno(x))

    elif isinstance(x, Assignment):
        return Assignment(x.lvalues, normalizeLogic(x.expression, negate))

    elif isinstance(x, AST):
        out = x.__new__(x.__class__)
        for field in x._fields:
            setattr(out, field, normalizeLogic(getattr(x, field), False))
        for n, v in inheriting_lineno(x).items():
            setattr(out, n, v)

        if negate:
            return UnaryOp(Not(**inheriting_lineno(x)), out, **inheriting_lineno(x))
        else:
            return out

    elif isinstance(x, list):
        return [normalizeLogic(y, negate) for y in x]

    else:
        return x
