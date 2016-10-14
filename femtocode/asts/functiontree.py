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

from femtocode.asts import parsingtree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

# this kind of AST can include FunctionTree instances and Function instances
        
class FunctionTree(object):
    def schema(self, symbolFrame):
        raise ProgrammingError("missing implementation")

class Ref(FunctionTree):
    def __init__(self, name, original):
        self.name = name
        self.original = original
    def __repr__(self):
        return "Ref({0})".format(self.name)
    def __eq__(self, other):
        if not isinstance(other, Ref):
            return False
        else:
            return self.name == other.name
    def __hash__(self):
        return hash((Ref, self.name))
    def schema(self, symbolFrame):
        return symbolFrame[self.name]

class Literal(FunctionTree):
    def __init__(self, value, original):
        self.value = value
        self.original = original
    def __repr__(self):
        return "Literal({0})".format(self.value)
    def __eq__(self, other):
        if not isinstance(other, Literal):
            return False
        else:
            return self.value == other.value
    def __hash__(self):
        return hash((Literal, self.value))
    def schema(self, symbolFrame):
        if isinstance(self.value, (int, long)):
            return integer(min=self.value, max=self.value)
        elif isinstance(self.value, float):
            return real(min=self.value, max=self.value)
        else:
            raise ProgrammingError("missing implementation")

class Call(FunctionTree):
    def __init__(self, fcn, args, original):
        self.fcn = fcn
        self.args = args
        self.original = original
    def __repr__(self):
        return "Call({0}, {1})".format(self.fcn, self.args)
    def __eq__(self, other):
        if not isinstance(other, Call):
            return False
        else:
            return self.fcn == other.fcn and self.args == other.args
    def __hash__(self):
        return hash((Call, self.fcn, self.args))
    def schema(self, symbolFrame):
        try:
            return self.fcn.retschema(symbolFrame, self.args)
        except TypeError as err:
            complain(str(err), self.original)

# these only live long enough to yield their schema; you won't find them in the tree
class Placeholder(FunctionTree):
    def __init__(self, schema):
        self.tpe = schema
    def __repr__(self):
        return "Placeholder({0})".format(self.tpe)
    def __eq__(self, other):
        if not isinstance(other, Placeholder):
            return False
        else:
            return self.tpe == other.tpe
    def __hash__(self):
        return hash((Placeholder, self.tpe))
    def schema(self, symbolFrame):
        return self.tpe

def buildOrElevate(tree, symbolFrame, arity):
    if arity is None or isinstance(tree, parsingtree.FcnDef):
        return build(tree, symbolFrame)

    elif isinstance(tree, parsingtree.Attribute):
        fcn = symbolFrame["." + tree.attr]
        params = list(xrange(arity))
        args = map(Ref, params)
        return UserFunction(params, [None] * arity, Call(fcn, [build(tree.value, symbolFrame)] + args, tree))
        
    else:
        subframe = symbolFrame.fork()
        for i in xrange(1, arity + 1):
            subframe[i] = Ref(i, tree)
        return UserFunction(list(range(1, arity + 1)), [None] * arity, build(tree, subframe))

def build(tree, symbolFrame):
    if isinstance(tree, parsingtree.Attribute):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.BinOp):
        if isinstance(tree.op, parsingtree.Add):
            return Call(symbolFrame["+"], [build(tree.left, symbolFrame), build(tree.right, symbolFrame)], tree)
        elif isinstance(tree.op, parsingtree.Sub):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Mult):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Div):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Mod):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Pow):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.FloorDiv):
            raise ProgrammingError("missing implementation")
        else:
            raise ProgrammingError("unrecognized BinOp.op: " + repr(tree.op))

        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.BoolOp):
        if isinstance(tree.op, parsingtree.And):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Or):
            raise ProgrammingError("missing implementation")
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Compare):
        if isinstance(tree.op, parsingtree.Eq):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.NotEq):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Lt):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.LtE):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Gt):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.GtE):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.In):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.NotIn):
            raise ProgrammingError("missing implementation")
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.List):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Name):
        return symbolFrame.get(tree.id, Ref(tree.id, tree))

    elif isinstance(tree, parsingtree.Num):
        return Literal(tree.n, tree)

    elif isinstance(tree, parsingtree.Str):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Subscript):
        if isinstance(tree.op, parsingtree.Slice):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.ExtSlice):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Index):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree, parsingtree.Tuple):
            raise ProgrammingError("missing implementation")
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.UnaryOp):
        if isinstance(tree.op, parsingtree.Not):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.UAdd):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.USub):
            raise ProgrammingError("missing implementation")
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Assignment):
        result = build(tree.expression, symbolFrame)
        if len(tree.lvalues) == 1:
            symbolFrame[tree.lvalues[0].id] = result
        else:
            raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.AtArg):
        out = symbolFrame.get(1 if tree.num is None else tree.num)
        if out is None:
            complain("function shortcuts ($n) can only be used in a builtin functional (.map, .filter); write your function longhand (x => f(x))", tree)
        return out

    elif isinstance(tree, parsingtree.FcnCall):
        if isinstance(tree.function, parsingtree.Attribute):
            fcn = symbolFrame["." + tree.function.attr]
            try:
                args = fcn.sortargs(tree.positional, dict((k.id, v) for k, v in zip(tree.names, tree.named)))
            except TypeError as err:
                complain(str(err), tree)
            return Call(fcn, [build(tree.function.value, symbolFrame)] + [buildOrElevate(x, symbolFrame, fcn.arity(i + 1)) for i, x in enumerate(args)], tree)

        else:
            fcn = build(tree.function, symbolFrame)
            try:
                args = fcn.sortargs(tree.positional, dict((k.id, v) for k, v in zip(tree.names, tree.named)))
            except TypeError as err:
                complain(str(err), tree)
            return Call(fcn, [buildOrElevate(x, symbolFrame, fcn.arity(i)) for i, x in enumerate(args)], tree)

    elif isinstance(tree, parsingtree.FcnDef):
        return UserFunction([x.id for x in tree.parameters], [None if x is None else build(x, symbolFrame) for x in tree.defaults], build(tree.body, symbolFrame))

    elif isinstance(tree, parsingtree.IfChain):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.IsType):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            for assignment in tree.assignments:
                build(assignment, symbolFrame)
        return build(tree.expression, symbolFrame)

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))
