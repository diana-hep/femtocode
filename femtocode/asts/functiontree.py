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

class FunctionTree(object): pass
        
class Ref(FunctionTree):
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema
    def __repr__(self):
        return "Ref({0}, {1})".format(self.name, self.schema)

class Literal(FunctionTree):
    def __init__(self, value, schema):
        self.value = value
        self.schema = schema
    def __repr__(self):
        return "Literal({0})".format(self.value)

class Call(FunctionTree):
    def __init__(self, fcn, args):
        self.fcn = fcn
        self.args = args
    @property
    def schema(self):
        return self.fcn.retschema(self.args)
    def __repr__(self):
        return "Call({0}, {1})".format(self.fcn, self.args)

class Def(FunctionTree):
    def __init__(self, params, defaults, body):
        self.params = params
        self.defaults = defaults
        self.body = body
    @property
    def schema(self):
        return self.body.schema
    def __repr__(self):
        return "Def({0}, {1}, {2})".format(self.params, self.defaults, self.body)

def flatten(tree, op):
    if isinstance(tree, parsingtree.BinOp) and isinstance(tree.op, op):
        return flatten(tree.left, op) + flatten(tree.right, op)
    else:
        return [tree]

def build(tree, stack):
    if isinstance(tree, parsingtree.Attribute):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.BinOp):
        args = flatten(tree, tree.op.__class__)

        if isinstance(tree.op, parsingtree.Add):
            return Call(stack["+"], [build(x, stack) for x in args])
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
        result = stack.get(tree.id, Unknown)
        if result is None:
            complain(tree.id + " is not defined in this scope (curly brackets)", tree)
        elif isinstance(result, Schema):
            return Ref(tree.id, result)   # this is an input field; add a reference
        else:
            return result                 # this is an assignment; simply insert

    elif isinstance(tree, parsingtree.Num):
        if isinstance(tree.n, (int, long)):
            return Literal(tree.n, integer(min=tree.n, max=tree.n))
        elif isinstance(tree.n, float):
            return Literal(tree.n, real(min=tree.n, max=tree.n))
        else:
            raise ProgrammingError("non-numeric type in Num: " + repr(tree.n))

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
        result = build(tree.expression, stack)

        if len(tree.lvalues) == 1:
            name = tree.lvalues[0].id
            if stack.get(name) is not None:
                complain(name + " is already defined in this scope (curly brackets)", tree.lvalues[0])
            stack[name] = result

        else:
            raise ProgrammingError("missing implementation")

            # for index, lvalue in enumerate(tree.lvalues):
            #     name = lvalue.id
            #     if stack.definedHere(name):
            #         complain(name + " is already defined in this scope (curly brackets)", lvalue)
            #     stack[name] = Unpack(result, index)  # !!!

    elif isinstance(tree, parsingtree.AtArg):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.FcnCall):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.FcnDef):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.IfChain):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.IsType):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            for assignment in tree.assignments:
                build(assignment, stack)
        return build(tree.expression, stack)

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))






# class Ref(FunctionTree):
#     def __init__(self, name):
#         self.name = name
#     def __repr__(self):
#         return "Ref({0})".format(self.name)
#     def typify(self, schema):
#         out = Ref(self.name)
#         out.schema = schema
#         return out

# class Literal(FunctionTree):
#     def __init__(self, value):
#         self.value = value
#     def __repr__(self):
#         return "Literal({0})".format(self.value)
#     def typify(self, schema):
#         out = Literal(self.value)
#         out.schema = schema
#         return out

# class Call(FunctionTree):
#     def __init__(self, fcn, args):
#         self.fcn = fcn
#         self.args = args
#     def __repr__(self):
#         return "Call({0}, {1})".format(self.fcn, self.args)
#     def typify(self, targs, schema):
#         out = Call(self.fcn, targs)
#         out.schema = schema
#         return out

# class Def(FunctionTree):
#     def __init__(self, params, defaults, body):
#         self.params = params
#         self.defaults = defaults
#         self.body = body
#     def __repr__(self):
#         return "Def({0}, {1}, {2})".format(self.params, self.defaults, self.body)
#     def typify(self, tparams, tbody, schema):
#         out = Def(self.params, self.body)
#         out.tparams = tparams
#         out.schema = schema
#         return out

# def flatten(tree, op):
#     if isinstance(tree, parsingtree.BinOp) and isinstance(tree.op, op):
#         return flatten(tree.left, op) + flatten(tree.right, op)
#     else:
#         return [tree]

# def convert(tree, builtin, stack, **options):
#     if isinstance(tree, parsingtree.Attribute):
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.BinOp):
#         args = flatten(tree, tree.op.__class__)

#         if isinstance(tree.op, parsingtree.Add):
#             return Call(builtin.get("+"), [convert(a, builtin, stack, **options) for a in args])
#         elif isinstance(tree.op, parsingtree.Sub):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.Mult):
#             return Call(builtin.get("*"), [convert(a, builtin, stack, **options) for a in args])
#         elif isinstance(tree.op, parsingtree.Div):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.Mod):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.Pow):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.FloorDiv):
#             raise ProgrammingError("missing implementation")
#         else:
#             raise ProgrammingError("unrecognized BinOp.op: " + repr(tree.op))

#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.BoolOp):
#         if isinstance(tree.op, parsingtree.And):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.Or):
#             raise ProgrammingError("missing implementation")
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.Compare):
#         if isinstance(tree.op, parsingtree.Eq):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.NotEq):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.Lt):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.LtE):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.Gt):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.GtE):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.In):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.NotIn):
#             raise ProgrammingError("missing implementation")
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.List):
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.Name):
#         if not stack.defined(tree.id):
#             complain(tree.id + " not defined in this scope (curly brackets)", tree)
#         else:
#             x = stack.get(tree.id)
#             if isinstance(x, Schema):
#                 return Ref(tree.id)
#             else:
#                 return x   # could be an expression tree or a ParameterSymbol

#     elif isinstance(tree, parsingtree.Num):
#         return Literal(tree.n)

#     elif isinstance(tree, parsingtree.Str):
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.Subscript):
#         if isinstance(tree.op, parsingtree.Slice):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.ExtSlice):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.Index):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree, parsingtree.Tuple):
#             raise ProgrammingError("missing implementation")
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.UnaryOp):
#         if isinstance(tree.op, parsingtree.Not):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.UAdd):
#             raise ProgrammingError("missing implementation")
#         elif isinstance(tree.op, parsingtree.USub):
#             raise ProgrammingError("missing implementation")
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.Suite):
#         if len(tree.assignments) > 0:
#             for assignment in tree.assignments:
#                 convert(assignment, builtin, stack, **options)
#         return convert(tree.expression, builtin, stack, **options)

#     elif isinstance(tree, parsingtree.AtArg):
#         return ParameterSymbol(1 if tree.num is None else tree.num)

#     elif isinstance(tree, parsingtree.Assignment):
#         result = convert(tree.expression, builtin, stack, **options)

#         if len(tree.lvalues) == 1:
#             name = tree.lvalues[0].id
#             if stack.definedHere(name):
#                 complain(name + " is already defined in this scope (curly brackets)", tree.lvalues[0])
#             stack.append(name, result)

#         else:
#             for index, lvalue in enumerate(tree.lvalues):
#                 name = lvalue.id
#                 if stack.definedHere(name):
#                     complain(name + " is already defined in this scope (curly brackets)", lvalue)
#                 stack.append(name, Unpack(result, index))

#     elif isinstance(tree, parsingtree.FcnCall):
#         raise ProgrammingError("missing implementation")

#     elif isinstance(tree, parsingtree.FcnDef):
#         tparams = [x.id for x in tree.parameters]   # tree.parameters are all ast.Name
#         tdefaults = [None if x is None else convert(x, builtin, stack, **options) for x in tree.defaults]
#         frame = stack.child()
#         for name in tree.parameters:
#             frame.append(name.id, ParameterSymbol(name.id))
#         return Def(tparams, tdefaults, convert(tree.body, builtin, frame, **options))

#     elif isinstance(tree, parsingtree.IfChain):
#         raise ProgrammingError("missing implementation")

#     else:
#         raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))

# def typify(tree, stack, **options):
#     if isinstance(tree, Ref):
#         t = stack.get(tree.name)
#         if not isinstance(t, Schema):
#             raise ProgrammingError("Ref created without input datum")
#         return tree.typify(t, **options)

#     elif isinstance(tree, Literal):
#         if isinstance(tree.value, (int, long)):
#             return tree.typify(integer(min=tree.value, max=tree.value), **options)
#         elif isinstance(tree.value, float):
#             return tree.typify(real(min=tree.value, max=tree.value), **options)
#         else:
#             raise ProgrammingError("missing implementation")

#     elif isinstance(tree, Call):
#         return tree.fcn.typify(tree, stack, **options)

#     elif isinstance(tree, Def):
#         tbody = tree.body.typify()




#         return tree.typify(tparams, tret)

#     elif isinstance(tree, Unpack):
#         raise ProgrammingError("missing implementation")

#     else:
#         raise ProgrammingError("unrecognized element in functiontree: " + repr(tree))
