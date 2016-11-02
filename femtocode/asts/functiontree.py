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

import ast

from femtocode.asts import parsingtree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

# this kind of AST can include FunctionTree instances and Function instances
        
class FunctionTree(object):
    def schema(self, types):
        raise ProgrammingError("missing implementation")

class Ref(FunctionTree):
    order = 2

    def __init__(self, name, original=None):
        self.name = name
        self.original = original

    def __repr__(self):
        return "Ref({0})".format(self.name)

    def __lt__(self, other):
        if isinstance(other, Ref):
            return self.name < other.name
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Ref):
            return False
        else:
            return self.name == other.name

    def __hash__(self):
        return hash((Ref, self.name))

    def schema(self, types):
        if types.defined(self):
            return types[self]
        else:
            return types[self.name]

class Literal(FunctionTree):
    order = 3

    def __init__(self, value, original=None):
        self.value = value
        self.original = original

    def __repr__(self):
        return "Literal({0})".format(self.value)

    def __lt__(self, other):
        if isinstance(other, Literal):
            return self.value < other.value
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Literal):
            return False
        else:
            return self.value == other.value

    def __hash__(self):
        return hash((Literal, self.value))

    def schema(self, types):
        if isinstance(self.value, (int, long)):
            return integer(min=self.value, max=self.value)
        elif isinstance(self.value, float):
            return real(min=self.value, max=self.value)
        else:
            raise ProgrammingError("missing implementation")

class Call(FunctionTree):
    order = 4

    def __init__(self, fcn, args, original=None):
        self.fcn = fcn
        if self.fcn.commutative():
            self.args = tuple(sorted(args))
        else:
            self.args = tuple(args)
        self.original = original

    def __repr__(self):
        return "Call({0}, {1})".format(self.fcn, self.args)

    def __lt__(self, other):
        if isinstance(other, Call):
            if self.fcn == other.fcn:
                return self.args < other.args
            else:
                return self.fcn < other.fcn
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Call):
            return False
        else:
            return self.fcn == other.fcn and self.args == other.args

    def __hash__(self):
        return hash((Call, self.fcn, self.args))

    def schema(self, types):
        if types.defined(self):
            return types[self]
        else:
            try:
                return self.fcn.retschema(types, self.args)
            except TypeError as err:
                complain(str(err), self.original)

class TypeConstraint(FunctionTree):
    order = 5

    def __init__(self, instance, schema, original=None):
        self.instance = instance
        self.schema = schema
        self.original = original

    def __repr__(self):
        return "TypeConstraint({0}, {1})".format(self.instance, self.schema)

    def __lt__(self, other):
        if isinstance(other, TypeConstraint):
            if self.instance == other.instance:
                return self.schema < other.schema
            else:
                return self.instance < other.instance
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, TypeConstraint):
            return False
        else:
            return self.instance == other.instance and self.schema == other.schema

    def __hash__(self):
        return hash((TypeConstraint, self.instance, self.schema))

    def schema(self, types):
        return boolean

# these only live long enough to yield their schema; you won't find them in the tree
class Placeholder(FunctionTree):
    order = 6

    def __init__(self, schema):
        self.tpe = schema

    def __repr__(self):
        return "Placeholder({0})".format(self.tpe)

    def __lt__(self, other):
        if isinstance(other, Placeholder):
            return self.tpe < other.tpe
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Placeholder):
            return False
        else:
            return self.tpe == other.tpe

    def __hash__(self):
        return hash((Placeholder, self.tpe))

    def schema(self, types):
        return self.tpe

def pos(tree):
    return {"lineno": tree.lineno, "col_offset": tree.col_offset}

def negate(tree, values):
    if isinstance(tree, Call) and tree.fcn == values["not"]:
        return tree.args[0]
    else:
        # TODO: other cases; de Morgan's law, etc.
        return Call(values["not"], [tree], tree.original)

def resolve(tree, values):
    if isinstance(tree, BuiltinFunction):
        return tree

    elif isinstance(tree, UserFunction):
        names = tree.names
        defaults = [None if x is None else resolve(x, values) for x in tree.defaults]
        subframe = values.fork()
        for n, d in zip(names, defaults):
            subframe[n] = d
        body = resolve(tree.body, subframe)
        return UserFunction(names, defaults, body)

    elif isinstance(tree, Ref):
        if values.get(tree.name) is not None:
            return values[tree.name]
        else:
            return tree

    elif isinstance(tree, Literal):
        return tree

    elif isinstance(tree, Call):
        return Call(resolve(tree.fcn, values), [resolve(x, values) for x in tree.args], tree.original)

    elif isinstance(tree, TypeConstraint):
        return TypeConstraint(resolve(tree.instance, values), tree.schema, tree.original)

    elif isinstance(tree, Placeholder):
        return tree

    else:
        raise ProgrammingError("unrecognized functiontree: " + repr(tree))

def buildSchema(tree):
    if isinstance(tree, parsingtree.Attribute):
        complain("dot ('.') not allowed in schema expression", tree)

    elif isinstance(tree, parsingtree.BinOp):
        return ast.BinOp(buildSchema(tree.left), tree.op, buildSchema(tree.right), **pos(tree))

    elif isinstance(tree, parsingtree.BoolOp):
        if isinstance(tree.op, parsingtree.And):
            op = "and"
        elif isinstance(tree.op, parsingtree.Or):
            op = "or"
        complain(op + " not allowed in schema expression", tree)
        
    elif isinstance(tree, parsingtree.Compare):
        complain("boolean logic not allowed in schema expression")

    elif isinstance(tree, parsingtree.List):
        complain("square brackets ('[' ']') not allowed in schema expression")

    elif isinstance(tree, parsingtree.Name):
        if tree.id in concrete:
            return tree
        elif tree.id in parameterized:
            complain("type {0} in schema expression must be a function".format(tree.id))
        else:
            complain("unrecognized type \"{0}\" in schema expression".format(tree.id))

    elif isinstance(tree, parsingtree.Num):
        return tree

    elif isinstance(tree, parsingtree.Str):
        complain("quoted strings not allowed in schema expression")

    elif isinstance(tree, parsingtree.Subscript):
        complain("square brackets ('[' ']') not allowed in schema expression")

    elif isinstance(tree, parsingtree.UnaryOp):
        if isinstance(tree.op, parsingtree.Not):
            complain("negation ('not') not allowed in schema expression")
        elif isinstance(tree.op, parsingtree.UAdd):
            return ast.UnaryOp(tree.op, buildSchema(tree.operand), **pos(tree))
        elif isinstance(tree.op, parsingtree.USub):
            return ast.UnaryOp(tree.op, buildSchema(tree.operand), **pos(tree))
        raise ProgrammingError("unrecognized UnaryOp: " + repr(tree.op))

    elif isinstance(tree, parsingtree.Assignment):
        complain("assignment ('=') not allowed in schema expression", tree)

    elif isinstance(tree, parsingtree.AtArg):
        complain("shortcut arguments ('$') not allowed in schema expression", tree)

    elif isinstance(tree, parsingtree.FcnCall):
        if isinstance(tree.function, parsingtree.Name):
            if tree.function.id in parameterized:
                positional = [buildSchema(x) for x in tree.positional]
                keywords = [ast.keyword(k.id, buildSchema(v), **pos(v)) for k, v in zip(tree.names, tree.named)]
                return ast.Call(tree.function, positional, keywords, None, None, **pos(tree))
            elif tree.function.id in concrete:
                complain("type {0} in schema expression must not be a function".format(tree.function.id), tree)
            else:
                complain("unrecognized type function \"{0}\" in schema expression".format(tree.function.id), tree)
        else:
            complain("higher-order functions not allowed in schema expression", tree)

    elif isinstance(tree, parsingtree.FcnDef):
        complain("function declarations ('=>') not allowed in schema expression", tree)

    elif isinstance(tree, parsingtree.IfChain):
        complain("if-else not allowed in schema expression", tree)

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            complain("curly brackets ('{') not allowed in schema expression", tree)
        else:
            return buildSchema(tree.expression)

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))

def buildOrElevate(tree, values, arity):
    if arity is None or isinstance(tree, parsingtree.FcnDef):
        return build(tree, values)

    elif isinstance(tree, parsingtree.Attribute):
        fcn = values["." + tree.attr]
        params = list(xrange(arity))
        args = map(Ref, params)
        return UserFunction(params, [None] * arity, Call(fcn, [build(tree.value, values)] + args, tree))
        
    else:
        subframe = values.fork()
        for i in xrange(1, arity + 1):
            subframe[i] = Ref(i, tree)
        return UserFunction(list(range(1, arity + 1)), [None] * arity, build(tree, subframe))
    
def build(tree, values):
    if isinstance(tree, parsingtree.Attribute):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.BinOp):
        if isinstance(tree.op, parsingtree.Add):
            return Call(values["+"], [build(tree.left, values), build(tree.right, values)], tree)
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
            out = Call(values["and"], [], tree)
            for x in tree.values:
                y = build(x, values)
                if isinstance(y, Call) and y.fcn == values["and"]:
                    out.args = out.args + y.args
                else:
                    out.args = out.args + (y,)
            return out

        elif isinstance(tree.op, parsingtree.Or):
            out = Call(values["and"], [], tree)
            for x in tree.values:
                y = negate(build(x, values), values)
                if isinstance(y, Call) and y.fcn == values["and"]:
                    out.args = out.args + y.args
                else:
                    out.args = out.args + (y,)
            return out

        else:
            raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Compare):
        out = Call(values["and"], [], tree)
        left = build(tree.left, values)
        for op, right in zip(tree.ops, tree.comparators):
            right = build(right, values)
            if isinstance(op, parsingtree.Eq):
                if left == right:
                    pass
                elif isinstance(left, Literal) and isinstance(right, Literal):
                    return Call(values["and"], [], tree)
                elif isinstance(left, Literal):
                    if left.value is None:
                        arg = TypeConstraint(right, null)
                    elif left.value is True:
                        arg = right
                    elif left.value is False:
                        arg = negate(right, values)
                    elif isinstance(left.value, int):
                        arg = TypeConstraint(right, Integer(left.value, left.value))
                    elif isinstance(left.value, float):
                        arg = TypeConstraint(right, Real(left.value, left.value))
                    else:
                        ProgrammingError("missing implementation")
                elif isinstance(right, Literal):
                    if right.value is None:
                        arg = TypeConstraint(left, null)
                    elif right.value is True:
                        arg = left
                    elif right.value is False:
                        arg = negate(left, values)
                    elif isinstance(right.value, int):
                        arg = TypeConstraint(left, Integer(right.value, right.value))
                    elif isinstance(right.value, float):
                        arg = TypeConstraint(left, Real(right.value, right.value))
                    else:
                        ProgrammingError("missing implementation")
                else:
                    arg = Call(values["=="], [left, right], op)

            elif isinstance(op, parsingtree.NotEq):
                raise ProgrammingError("missing implementation")

            elif isinstance(op, parsingtree.Lt):
                raise ProgrammingError("missing implementation")

            elif isinstance(op, parsingtree.LtE):
                raise ProgrammingError("missing implementation")

            elif isinstance(op, parsingtree.Gt):
                raise ProgrammingError("missing implementation")

            elif isinstance(op, parsingtree.GtE):
                raise ProgrammingError("missing implementation")

            elif isinstance(op, parsingtree.In):
                raise ProgrammingError("missing implementation")

            elif isinstance(op, parsingtree.NotIn):
                raise ProgrammingError("missing implementation")

            else:
                raise ProgrammingError("missing implementation")

            left = right
            out.args = out.args + (arg,)

        return out
            
    elif isinstance(tree, parsingtree.List):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Name):
        if tree.id == "None":
            return Literal(None, tree)
        elif tree.id == "True":
            return Literal(True, tree)
        elif tree.id == "False":
            return Literal(False, tree)
        else:
            return values.get(tree.id, Ref(tree.id, tree))

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
            return negate(build(tree.operand, values), values)
        elif isinstance(tree.op, parsingtree.UAdd):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.USub):
            raise ProgrammingError("missing implementation")
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Assignment):
        result = build(tree.expression, values)
        if len(tree.lvalues) == 1:
            values[tree.lvalues[0].id] = result
        else:
            raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.AtArg):
        out = values.get(1 if tree.num is None else tree.num)
        if out is None:
            complain("function shortcuts ($n) can only be used in a builtin functional (.map, .filter); write your function longhand (x => f(x))", tree)
        return out

    elif isinstance(tree, parsingtree.FcnCall):
        if isinstance(tree.function, parsingtree.Attribute):
            fcn = values["." + tree.function.attr]
            try:
                args = fcn.sortargs(tree.positional, dict((k.id, v) for k, v in zip(tree.names, tree.named)))
            except TypeError as err:
                complain(str(err), tree)
            return Call(fcn, [build(tree.function.value, values)] + [buildOrElevate(x, values, fcn.arity(i + 1)) for i, x in enumerate(args)], tree)

        else:
            fcn = build(tree.function, values)
            if not isinstance(fcn, Function):
                complain("not a known function (declare in order of dependency; recursion is not allowed)", fcn.original)

            try:
                args = fcn.sortargs(tree.positional, dict((k.id, v) for k, v in zip(tree.names, tree.named)))
            except TypeError as err:
                complain(str(err), tree)

            if isinstance(fcn, UserFunction):
                return resolve(fcn.body, SymbolTable(dict(zip(fcn.names, [build(x, values) for x in args]))))
            else:
                return Call(fcn, [buildOrElevate(x, values, fcn.arity(i)) for i, x in enumerate(args)], tree)

    elif isinstance(tree, parsingtree.FcnDef):
        return UserFunction([x.id for x in tree.parameters], [None if x is None else build(x, values) for x in tree.defaults], build(tree.body, values))

    elif isinstance(tree, parsingtree.IfChain):
        args = []
        for p, c in zip(tree.predicates, tree.consequents):
            args.append(build(p, values))
            args.append(build(c, values.fork()))
        args.append(tree.alternate, values.fork())
        return Call(values["if"], args, tree)

    elif isinstance(tree, parsingtree.TypeCheck):
        schema = eval(compile(ast.Expression(buildSchema(tree.schema)), "<schema expression>", "eval"))
        return TypeConstraint(tree.expr, schema, tree)

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            for assignment in tree.assignments:
                build(assignment, values)
        return build(tree.expression, values)

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))
