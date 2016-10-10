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

import femtocode.parser
from femtocode.asts import parsingtree
from femtocode.defs import BuiltinFunction
from femtocode.py23 import *
from femtocode.typesystem import *

def complain(message, p):
    femtocode.parser.complain(message, p.source, p.pos, p.lineno, p.col_offset, p.fileName, 1)

class FunctionTree(object):
    def typify(self, schema):
        raise NotImplementedError

class Ref(FunctionTree):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "Ref({0})".format(self.name)
    def typify(self, schema):
        out = Ref(self.name)
        out.schema = schema
        return out

class Literal(FunctionTree):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return "Literal({0})".format(self.value)
    def typify(self, schema):
        out = Literal(self.value)
        out.schema = schema
        return out

class Call(FunctionTree):
    def __init__(self, fcn, args):
        self.fcn = fcn
        self.args = args
    def __repr__(self):
        return "Call({0}, {1})".format(self.fcn, self.args)
    def typify(self, schema):
        out = Call(self.fcn, self.args)
        out.schema = schema
        return out

class Def(FunctionTree):
    def __init__(self, params, body):
        self.params = params
        self.body = body
    def __repr__(self):
        return "Def({0}, {1})".format(self.params, self.body)
    def typify(self, schema):
        out = Def(self.params, self.body)
        out.schema = schema
        return out

class Unpack(FunctionTree):
    def __init__(self, structure, index):
        self.structure = structure
        self.index = index
    def __repr__(self):
        return "Unpack({0}, {1})".format(self.structure, self.index)
    def typify(self, schema):
        out = Unpack(self.structure, self.index)
        out.schema = schema
        return out

def flatten(tree, op):
    if isinstance(tree, parsingtree.BinOp) and isinstance(tree.op, op):
        return flatten(tree.left, op) + flatten(tree.right, op)
    else:
        return [tree]

def convert(parsing, builtin, stack, **options):
    if isinstance(parsing, parsingtree.Attribute):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.BinOp):
        args = flatten(parsing, parsing.op.__class__)

        if isinstance(parsing.op, parsingtree.Add):
            return Call(builtin.get("+"), [convert(a, builtin, stack, **options) for a in args])
        elif isinstance(parsing.op, parsingtree.Sub):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.Mult):
            return Call(builtin.get("*"), [convert(a, builtin, stack, **options) for a in args])
        elif isinstance(parsing.op, parsingtree.Div):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.Mod):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.Pow):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.FloorDiv):
            raise NotImplementedError
        else:
            raise TypeError("unrecognized BinOp.op: " + repr(parsing.op))

        raise NotImplementedError

    elif isinstance(parsing, parsingtree.BoolOp):
        if isinstance(parsing.op, parsingtree.And):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.Or):
            raise NotImplementedError
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Compare):
        if isinstance(parsing.op, parsingtree.Eq):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.NotEq):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.Lt):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.LtE):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.Gt):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.GtE):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.In):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.NotIn):
            raise NotImplementedError
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.List):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Name):
        if not stack.defined(parsing.id):
            complain(parsing.id + " not defined in this scope (curly brackets)", parsing)
        else:
            x = stack.get(parsing.id)
            if isinstance(x, Schema):
                return Ref(parsing.id)
            else:
                return x

    elif isinstance(parsing, parsingtree.Num):
        return Literal(parsing.n)

    elif isinstance(parsing, parsingtree.Str):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Subscript):
        if isinstance(parsing.op, parsingtree.Slice):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.ExtSlice):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.Index):
            raise NotImplementedError
        elif isinstance(parsing, parsingtree.Tuple):
            raise NotImplementedError
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.UnaryOp):
        if isinstance(parsing.op, parsingtree.Not):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.UAdd):
            raise NotImplementedError
        elif isinstance(parsing.op, parsingtree.USub):
            raise NotImplementedError
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Suite):
        if len(parsing.assignments) > 0:
            for assignment in parsing.assignments:
                convert(assignment, builtin, stack, **options)
        return convert(parsing.expression, builtin, stack, **options)

    elif isinstance(parsing, parsingtree.AtArg):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Assignment):
        result = convert(parsing.expression, builtin, stack, **options)

        if len(parsing.lvalues) == 1:
            name = parsing.lvalues[0].id
            if stack.definedHere(name):
                complain(name + " is already defined in this scope (curly brackets)", parsing.lvalues[0])
            stack.append(name, result)

        else:
            for index, lvalue in enumerate(parsing.lvalues):
                name = lvalue.id
                if stack.definedHere(name):
                    complain(name + " is already defined in this scope (curly brackets)", lvalue)
                stack.append(name, Unpack(result, index))

    elif isinstance(parsing, parsingtree.FcnCall):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.FcnDef):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.IfChain):
        raise NotImplementedError

    else:
        raise TypeError("unrecognized element in parsingtree: " + repr(parsing))
    




from femtocode.parser import parse
from femtocode.lib.standard import table

stack = table.child()
stack.append("hello", real)

print convert(parse("x = 1; x + x"), table, stack.child())
