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

class FunctionTree(object):
    def schema(self, symbolFrame):
        raise ProgrammingError("missing implementation")
        
class Ref(FunctionTree):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "Ref({0})".format(self.name)
    def schema(self, symbolFrame):
        return symbolFrame[self.name]

class Literal(FunctionTree):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return "Literal({0})".format(self.value)
    def schema(self, symbolFrame):
        if isinstance(self.value, (int, long)):
            return integer(min=self.value, max=self.value)
        elif isinstance(self.value, float):
            return real(min=self.value, max=self.value)
        else:
            raise ProgrammingError("missing implementation")

class Call(FunctionTree):
    def __init__(self, fcn, args):
        self.fcn = fcn
        self.args = args
    def __repr__(self):
        return "Call({0}, {1})".format(self.fcn, self.args)
    def schema(self, symbolFrame):
        return self.fcn.retschema(symbolFrame, self.args)

class Def(FunctionTree):
    def __init__(self, names, defaults, body):
        self.names = names
        self.defaults = defaults
        self.body = body
    def __repr__(self):
        return "Def({0}, {1}, {2})".format(self.names, self.defaults, self.body)
    def argname(self, index):
        return self.names[index]
    def schema(self, symbolFrame):
        return Function([Unknown() for x in self.names], Unknown())
    def arity(self, index):
        return None  # TODO
    def retschema(self, symbolFrame, args):
        subframe = symbolFrame.fork()
        for name, arg in zip(self.names, args):
            subframe[name] = arg.schema(symbolFrame)
        return self.body.schema(subframe)

def buildOrElevate(tree, symbolFrame, arity):
    if arity is None or isinstance(tree, parsingtree.FcnDef):
        return build(tree, symbolFrame)
    else:
        subframe = symbolFrame.fork()
        for i in xrange(1, arity + 1):
            subframe[i] = Ref(i)
        return Def(list(range(1, arity + 1)), [None] * arity, build(tree, subframe))

def build(tree, symbolFrame):
    if isinstance(tree, parsingtree.Attribute):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.BinOp):
        if isinstance(tree.op, parsingtree.Add):
            return Call(symbolFrame["+"], [build(tree.left, symbolFrame), build(tree.right, symbolFrame)])
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
        return symbolFrame.get(tree.id, Ref(tree.id))

    elif isinstance(tree, parsingtree.Num):
        return Literal(tree.n)

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
        return symbolFrame[1 if tree.num is None else tree.num]

    elif isinstance(tree, parsingtree.FcnCall):
        if any(x is not None for x in tree.names):
            raise ProgrammingError("missing implementation")
        fcn = build(tree.function, symbolFrame)
        return Call(fcn, [buildOrElevate(x, symbolFrame, fcn.arity(i)) for i, x in enumerate(tree.positional)])

    elif isinstance(tree, parsingtree.FcnDef):
        return Def([x.id for x in tree.parameters], [None if x is None else build(x, symbolFrame) for x in tree.defaults], build(tree.body, symbolFrame))

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
