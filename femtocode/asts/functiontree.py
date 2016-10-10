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
        raise ProgrammingError("missing implementation")

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

def convert(tree, builtin, stack, **options):
    if isinstance(tree, parsingtree.Attribute):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.BinOp):
        args = flatten(tree, tree.op.__class__)

        if isinstance(tree.op, parsingtree.Add):
            return Call(builtin.get("+"), [convert(a, builtin, stack, **options) for a in args])
        elif isinstance(tree.op, parsingtree.Sub):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.Mult):
            return Call(builtin.get("*"), [convert(a, builtin, stack, **options) for a in args])
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
        if not stack.defined(tree.id):
            complain(tree.id + " not defined in this scope (curly brackets)", tree)
        else:
            x = stack.get(tree.id)
            if isinstance(x, Schema):
                return Ref(tree.id)
            else:
                return x

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

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            for assignment in tree.assignments:
                convert(assignment, builtin, stack, **options)
        return convert(tree.expression, builtin, stack, **options)

    elif isinstance(tree, parsingtree.AtArg):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Assignment):
        result = convert(tree.expression, builtin, stack, **options)

        if len(tree.lvalues) == 1:
            name = tree.lvalues[0].id
            if stack.definedHere(name):
                complain(name + " is already defined in this scope (curly brackets)", tree.lvalues[0])
            stack.append(name, result)

        else:
            for index, lvalue in enumerate(tree.lvalues):
                name = lvalue.id
                if stack.definedHere(name):
                    complain(name + " is already defined in this scope (curly brackets)", lvalue)
                stack.append(name, Unpack(result, index))

    elif isinstance(tree, parsingtree.FcnCall):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.FcnDef):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.IfChain):
        raise ProgrammingError("missing implementation")

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))
    
def typify(tree, schema, **options):
    if isinstance(tree, Ref):
        if schema.defined(tree.name):
            return tree.typify(schema.get(tree.name))
        else:
            raise ProgrammingError("Ref created without input datum")

    elif isinstance(tree, Literal):
        if isinstance(tree.value, (int, long)):
            return tree.typify(integer(min=tree.value, max=tree.value))
        elif isinstance(tree.value, float):
            return tree.typify(real(min=tree.value, max=tree.value))
        else:
            raise ProgrammingError("missing implementation")

    elif isinstance(tree, Call):
        return tree.typify(tree.fcn.typifyArgs(args, typify))

    elif isinstance(tree, Def):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, Unpack):
        raise ProgrammingError("missing implementation")

    else:
        raise ProgrammingError("unrecognized element in functiontree: " + repr(tree))







from femtocode.parser import parse
from femtocode.lib.standard import table

stack = table.child()
stack.append("hello", real)

print typify(convert(parse("x = 1; x + x"), table, stack.child()), stack)
