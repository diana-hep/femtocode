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
    def retschema(self, frame):
        raise ProgrammingError("missing implementation")

class UserFunction(Function):
    order = 1

    def __init__(self, names, defaults, body):
        self.names = tuple(names)
        self.defaults = tuple(defaults)
        self.body = body

    def __repr__(self):
        return "UserFunction({0}, {1}, {2})".format(self.names, self.defaults, self.body)

    def __lt__(self, other):
        if isinstance(other, UserFunction):
            if self.names == other.names:
                if self.defaults == defaults:
                    return self.body < other.body
                else:
                    return self.defaults < other.defaults
            else:
                return self.names < other.names
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, UserFunction):
            return False
        else:
            return self.names == other.names and self.defaults == other.defaults and self.body == other.body

    def __hash__(self):
        return hash((self.order, self.names, self.defaults, self.body))

    def retschema(self, frame, args):
        subframe = frame.fork()
        for name, arg in zip(self.names, args):
            subframe[Ref(name)] = arg.retschema(frame)[0]
        return self.body.retschema(subframe)[0], subframe

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, self.names, self.defaults)

class Ref(FunctionTree):
    order = 2

    def __init__(self, name, original=None):
        self.name = name
        self.original = original

    def __repr__(self):
        return "Ref({0})".format(self.name)

    def __lt__(self, other):
        if isinstance(other, Ref):
            if isinstance(self.name, int) and isinstance(other.name, string_types):
                return True
            elif isinstance(self.name, string_types) and isinstance(other.name, int):
                return False
            else:
                return self.name < other.name
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Ref):
            return False
        else:
            return self.name == other.name

    def __hash__(self):
        return hash((self.order, self.name))

    def retschema(self, frame):
        if frame.defined(self):
            return frame[self], frame
        else:
            complain("\"{0}\" not defined (yet?) in this scope".format(self.name), self.original)

    def generate(self):
        if isinstance(self.name, int):
            return "$" + repr(self.name)
        else:
            return self.name

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
        return hash((self.order, self.value))

    def retschema(self, frame):
        if isinstance(self.value, (int, long)):
            return integer(min=self.value, max=self.value), frame
        elif isinstance(self.value, float):
            return real(min=self.value, max=self.value), frame
        else:
            raise ProgrammingError("missing implementation")

    def generate(self):
        return repr(self.value)

class Call(FunctionTree):
    order = 4

    @staticmethod
    def build(fcn, args, original=None):
        if hasattr(fcn, "literaleval") and all(isinstance(x, Literal) for x in args):
            return Literal(fcn.literaleval([x.value for x in args]), original)
        else:
            return Call(fcn, args, original)

    def __init__(self, fcn, args, original=None):
        self.fcn = fcn
        self.args = tuple(args)
        self.original = original

    def __repr__(self):
        return "Call({0}, {1})".format(self.fcn, self.args)

    def sortedargs(self):
        if self.fcn.commutative():
            return tuple(sorted(self.args))
        else:
            return self.args

    def __lt__(self, other):
        if isinstance(other, Call):
            if self.fcn == other.fcn:
                return self.sortedargs() < other.sortedargs()
            else:
                return self.fcn < other.fcn
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, Call):
            return False
        else:
            return self.fcn == other.fcn and self.sortedargs() == other.sortedargs()

    def __hash__(self):
        return hash((self.order, self.fcn, self.sortedargs()))

    def retschema(self, frame):
        if isinstance(self.fcn, UserFunction):
            out, subframe = self.fcn.retschema(frame, self.args)

        else:
            out, subframe = self.fcn.retschema(frame, self.args)

            if isinstance(out, Impossible):
                if out.reason is not None:
                    reason = "\n    " + out.reason
                complain("Function \"{0}\" does not accept arguments with the given types:\n\n    {0}({1})\n{2}".format(self.fcn.name, ",\n    {0} ".format(" " * len(self.fcn.name)).join(pretty(x.retschema(frame)[0], prefix="     " + " " * len(self.fcn.name)).lstrip() for x in self.args), reason), self.original)

            for expr, t in subframe.itemsHere():
                if isinstance(t, Impossible):
                    if t.reason is not None:
                        reason = "\n    " + out.reason
                        complain("Function \"{0}\" puts impossible constraints on {1}:\n\n    {0}({2})\n{3}".format(self.fcn.name, expr.generate(), ",\n    {0} ".format(" " * len(self.fcn.name)).join(pretty(x.retschema(frame.parent)[0], prefix="     " + " " * len(self.fcn.name)).lstrip() for x in self.args), reason), self.original)

        if frame.defined(self):
            out = intersection(frame[self], out)
            if isinstance(out, Impossible):
                reason = "\n    " + out.reason
                complain("Expression {0} previously constrained to be\n\n{1}\n    but new constraints on its arguments are incompatible with that.\n\n    {2}({3})\n{4}".format(self.generate(), pretty(frame[self], prefix="        "), self.fcn.name, ",\n    {0} ".format(" " * len(self.fcn.name)).join(pretty(x.retschema(frame)[0], prefix="     " + " " * len(self.fcn.name)).lstrip() for x in self.args), reason), self.original)

            subframe[self] = out
            
        return out, subframe

    def generate(self):
        if isinstance(self.fcn, UserFunction) and all(isinstance(x, int) for x in self.fcn.names):
            return self.fcn.body.generate()

        elif isinstance(self.fcn, UserFunction):
            return "{{{0} => {1}}}".format(", ".join(self.fcn.names, self.fcn.body.generate()))

        else:
            return self.fcn.generate(self.args)

class TypeConstraint(FunctionTree):
    order = 5

    def __init__(self, instance, oftype, original=None):
        self.instance = instance
        self.oftype = oftype
        self.original = original

    def __repr__(self):
        return "TypeConstraint({0}, {1})".format(self.instance, self.oftype)

    def __lt__(self, other):
        if isinstance(other, TypeConstraint):
            if self.instance == other.instance:
                return self.oftype < other.oftype
            else:
                return self.instance < other.instance
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, TypeConstraint):
            return False
        else:
            return self.instance == other.instance and self.oftype == other.oftype

    def __hash__(self):
        return hash((self.order, self.instance, self.oftype))

    def retschema(self, frame):
        subframe = frame.fork()
        if subframe.defined(self.instance):
            out = intersection(subframe[self.instance], self.oftype)
            if isinstance(out, Impossible):
                reason = "\n    " + out.reason
                complain("Expression {0} cannot be constrained to\n\n{1}\n\n    because it is already\n\n{2}\n{3}".format(self.instance.generate(), pretty(self.oftype, prefix="        "), pretty(subframe[self.instance], prefix="        "), reason), self.original)
            subframe[self.instance] = out

        else:
            subframe[self.instance] = self.oftype

        return boolean, subframe

    def generate(self):
        return "({0} is {1})".format(self.instance.generate(), repr(self.type))

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
        return hash((self.order, self.tpe))

    def retschema(self, frame):
        return self.tpe, frame

    def generate(self):
        return "???"

def pos(tree):
    return {"lineno": tree.lineno, "col_offset": tree.col_offset}

# def negate(tree, frame):
#     if isinstance(tree, Call) and tree.fcn == frame["not"]:
#         return tree.args[0]
#     elif isinstance(tree, Call) and tree.fcn == frame["and"]:
#         return Call(frame["or"], [negate(x, frame) for x in tree.args], tree.original)
#     elif isinstance(tree, Call) and tree.fcn == frame["or"]:
#         return Call(frame["and"], [negate(x, frame) for x in tree.args], tree.original)
#     else:
#         return Call(frame["not"], [tree], tree.original)

def expandUserFcns(tree, frame):
    if isinstance(tree, BuiltinFunction):
        return tree

    elif isinstance(tree, UserFunction):
        names = tree.names
        defaults = [None if x is None else expandUserFcns(x, frame) for x in tree.defaults]
        subframe = frame.fork()
        for n, d in zip(names, defaults):
            subframe[n] = d
        body = expandUserFcns(tree.body, subframe)
        return UserFunction(names, defaults, body)

    elif isinstance(tree, Ref):
        if frame.get(tree.name) is not None:
            return frame[tree.name]
        else:
            return tree

    elif isinstance(tree, Literal):
        return tree

    elif isinstance(tree, Call):
        return Call.build(expandUserFcns(tree.fcn, frame), [expandUserFcns(x, frame) for x in tree.args], tree.original)

    elif isinstance(tree, TypeConstraint):
        return TypeConstraint(expandUserFcns(tree.instance, frame), tree.schema, tree.original)

    elif isinstance(tree, Placeholder):
        return tree

    else:
        raise ProgrammingError("unrecognized functiontree: " + repr(tree))

def buildSchema(tree):
    if isinstance(tree, parsingtree.Attribute):
        complain("Dot ('.') not allowed in schema expression.", tree)

    elif isinstance(tree, parsingtree.BinOp):
        return ast.BinOp(buildSchema(tree.left), tree.op, buildSchema(tree.right), **pos(tree))

    elif isinstance(tree, parsingtree.BoolOp):
        if isinstance(tree.op, parsingtree.And):
            op = "and"
        elif isinstance(tree.op, parsingtree.Or):
            op = "or"
        complain(op + " not allowed in schema expression.", tree)
        
    elif isinstance(tree, parsingtree.Compare):
        complain("Boolean logic not allowed in schema expression.")

    elif isinstance(tree, parsingtree.List):
        complain("Square brackets ('[' ']') not allowed in schema expression.")

    elif isinstance(tree, parsingtree.Name):
        if tree.id in concrete:
            return tree
        elif tree.id in parameterized:
            complain("Type {0} in schema expression must be a function.".format(tree.id))
        else:
            complain("Unrecognized type \"{0}\" in schema expression.".format(tree.id))

    elif isinstance(tree, parsingtree.Num):
        return tree

    elif isinstance(tree, parsingtree.Str):
        complain("Quoted strings not allowed in schema expression.")

    elif isinstance(tree, parsingtree.Subscript):
        complain("Square brackets ('[' ']') not allowed in schema expression.")

    elif isinstance(tree, parsingtree.UnaryOp):
        if isinstance(tree.op, parsingtree.Not):
            complain("Negation ('not') not allowed in schema expression.")
        elif isinstance(tree.op, parsingtree.UAdd):
            return ast.UnaryOp(tree.op, buildSchema(tree.operand), **pos(tree))
        elif isinstance(tree.op, parsingtree.USub):
            return ast.UnaryOp(tree.op, buildSchema(tree.operand), **pos(tree))
        raise ProgrammingError("unrecognized UnaryOp: " + repr(tree.op))

    elif isinstance(tree, parsingtree.Assignment):
        complain("Assignment ('=') not allowed in schema expression.", tree)

    elif isinstance(tree, parsingtree.AtArg):
        complain("Shortcut arguments ('$') not allowed in schema expression.", tree)

    elif isinstance(tree, parsingtree.FcnCall):
        if isinstance(tree.function, parsingtree.Name):
            if tree.function.id in parameterized:
                positional = [buildSchema(x) for x in tree.positional]
                keywords = [ast.keyword(k.id, buildSchema(v), **pos(v)) for k, v in zip(tree.names, tree.named)]
                return ast.Call(tree.function, positional, keywords, None, None, **pos(tree))
            elif tree.function.id in concrete:
                complain("Type {0} in schema expression must not be a function.".format(tree.function.id), tree)
            else:
                complain("Unrecognized type function \"{0}\" in schema expression.".format(tree.function.id), tree)
        else:
            complain("Higher-order functions not allowed in schema expression.", tree)

    elif isinstance(tree, parsingtree.FcnDef):
        complain("Function declarations ('=>') not allowed in schema expression.", tree)

    elif isinstance(tree, parsingtree.IfChain):
        complain("If-else not allowed in schema expression.", tree)

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            complain("Curly brackets ('{') not allowed in schema expression.", tree)
        else:
            return buildSchema(tree.expression)

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))

def buildOrElevate(tree, frame, arity):
    if arity is None or isinstance(tree, parsingtree.FcnDef) or (isinstance(tree, parsingtree.Name) and frame.defined(tree.id) and isinstance(frame[tree.id], Function)):
        return build(tree, frame)

    elif isinstance(tree, parsingtree.Attribute):
        fcn = frame["." + tree.attr]
        params = list(xrange(arity))
        args = map(Ref, params)
        return UserFunction(params, [None] * arity, Call.build(fcn, [build(tree.value, frame)] + args, tree))
        
    else:
        subframe = frame.fork()
        for i in xrange(1, arity + 1):
            subframe[i] = Ref(i, tree)
        return UserFunction(list(range(1, arity + 1)), [None] * arity, build(tree, subframe))
    
def build(tree, frame):
    if isinstance(tree, parsingtree.Attribute):
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.BinOp):
        if isinstance(tree.op, parsingtree.Add):
            return Call.build(frame["+"], [build(tree.left, frame), build(tree.right, frame)], tree)
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
            out = Call(frame["and"], [], tree)
            for x in tree.values:
                y = build(x, frame)
                if isinstance(y, Call) and y.fcn == frame["and"]:
                    out.args = out.args + y.args
                else:
                    out.args = out.args + (y,)
            out.args = out.args
            return out

        elif isinstance(tree.op, parsingtree.Or):
            out = Call(frame["or"], [], tree)
            for x in tree.values:
                y = build(x, frame)
                if isinstance(y, Call) and y.fcn == frame["or"]:
                    out.args = out.args + y.args
                else:
                    out.args = out.args + (y,)
            out.args = out.args
            return out

        else:
            raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Compare):
        out = Call(frame["and"], [], tree)
        left = build(tree.left, frame)
        for op, right in zip(tree.ops, tree.comparators):
            right = build(right, frame)
            if isinstance(op, parsingtree.Eq):
                arg = None
                if isinstance(left, Literal) and not isinstance(right, Literal):
                    if left.value is True:
                        arg = right
                    elif left.value is False:
                        arg = Call(frame["not"], [right], right.original)
                elif not isinstance(left, Literal) and isinstance(right, Literal):
                    if right.value is True:
                        arg = left
                    elif right.value is False:
                        arg = Call(frame["not"], [left], left.original)
                if arg is None:
                    arg = Call.build(frame["=="], [left, right], op)

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

        if len(out.args) == 0:
            return Literal(True, tree)
        elif len(out.args) == 1:
            return out.args[0]
        else:
            out.args = out.args
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
            return frame.get(tree.id, Ref(tree.id, tree))

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
            return Call(frame["not"], [build(tree.operand, frame)], tree)
        elif isinstance(tree.op, parsingtree.UAdd):
            raise ProgrammingError("missing implementation")
        elif isinstance(tree.op, parsingtree.USub):
            raise ProgrammingError("missing implementation")
        raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.Assignment):
        result = build(tree.expression, frame)
        if len(tree.lvalues) == 1:
            frame[tree.lvalues[0].id] = result
        else:
            raise ProgrammingError("missing implementation")

    elif isinstance(tree, parsingtree.AtArg):
        out = frame.get(1 if tree.num is None else tree.num)
        if out is None:
            complain("Function shortcuts ($n) can only be used in a builtin functional (.map, .filter); write your function longhand (x => f(x)).", tree)
        return out

    elif isinstance(tree, parsingtree.FcnCall):
        if isinstance(tree.function, parsingtree.Attribute):
            fcn = frame["." + tree.function.attr]
            try:
                args = fcn.sortargs(tree.positional, dict((k.id, v) for k, v in zip(tree.names, tree.named)))
            except TypeError as err:
                complain(str(err), tree)
            return Call.build(fcn, [build(tree.function.value, frame)] + [buildOrElevate(x, frame, fcn.arity(i + 1)) for i, x in enumerate(args)], tree)

        else:
            fcn = build(tree.function, frame)
            if not isinstance(fcn, Function):
                complain("Not a known function (declare in order of dependency; recursion is not allowed).", fcn.original)

            try:
                args = fcn.sortargs(tree.positional, dict((k.id, v) for k, v in zip(tree.names, tree.named)))
            except TypeError as err:
                complain(str(err), tree)

            builtArgs = [x if isinstance(x, (FunctionTree, Function)) else buildOrElevate(x, frame, fcn.arity(i)) for i, x in enumerate(args)]

            if isinstance(fcn, UserFunction):
                return expandUserFcns(fcn.body, SymbolTable(dict(zip(fcn.names, builtArgs))))
            else:
                return Call.build(fcn, builtArgs, tree)

    elif isinstance(tree, parsingtree.FcnDef):
        return UserFunction([x.id for x in tree.parameters], [None if x is None else build(x, frame) for x in tree.defaults], build(tree.body, frame))

    elif isinstance(tree, parsingtree.IfChain):
        args = []
        for pred, cons in zip(tree.predicates, tree.consequents):
            args.append(build(pred, frame))
            args.append(build(cons, frame))
        args.append(build(tree.alternate, frame))

        return Call.build(frame["if"], args, tree)

    elif isinstance(tree, parsingtree.TypeCheck):
        schema = eval(compile(ast.Expression(buildSchema(tree.schema)), "<schema expression>", "eval"))
        return TypeConstraint(build(tree.expr, frame), schema, tree)

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            for assignment in tree.assignments:
                build(assignment, frame)
        return build(tree.expression, frame)

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))
