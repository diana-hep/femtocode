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
import math

from femtocode.asts import parsingtree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

class LispyTree(object): pass

class BuiltinFunction(Function):
    order = 0

    def __repr__(self):
        return "BuiltinFunction[\"{0}\"]".format(self.name)

    def __lt__(self, other):
        if isinstance(other, BuiltinFunction):
            return self.name < other.name
        else:
            return self.order < other.order

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash((self.order,))

    def buildTyped(self, args, frame):
        raise ProgrammingError("missing implementation")

    def typingToColumnar(args, typeframe, colframe):
        raise ProgrammingError("missing implementation")

    def generate(self, args):
        raise ProgrammingError("missing implementation")

class UserFunction(Function):
    order = 1

    def __init__(self, names, defaults, body, original=None):
        self.names = tuple(names)
        self.defaults = tuple(defaults)
        self.body = body
        self.original = original

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

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, self.names, self.defaults)

class Ref(LispyTree):
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

    def generate(self):
        if isinstance(self.name, int):
            return "$" + repr(self.name)
        else:
            return self.name

class Literal(LispyTree):
    order = 3

    def __init__(self, value, original=None):
        self.value = value
        self.original = original
        if self.value is None:
            self.schema = null
        elif self.value is True or self.value is False:
            self.schema = boolean
        elif isinstance(self.value, (int, long, float)):
            self.schema = Number(self.value, self.value, not math.isinf(self.value) and round(self.value) == self.value)
        elif isinstance(self.value, bytes):
            self.schema = String("bytes", len(self.value), len(self.value))
        elif isinstance(self.value, string_types):
            self.schema = String("unicode", len(self.value), len(self.value))
        elif isinstance(self.value, Schema):
            self.schema = impossible
        else:
            raise ProgrammingError("missing implementation")

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

    def generate(self):
        return repr(self.value)

class Call(LispyTree):
    order = 4

    @staticmethod
    def build(fcn, args, original=None):
        if hasattr(fcn, "literaleval") and all(isinstance(x, Literal) for x in args):
            empty = SymbolTable()
            schema, typedargs, subempty = fcn.buildTyped(args, empty)
            if isinstance(schema, Impossible):
                if schema.reason is not None:
                    reason = "\n\n    " + schema.reason
                else:
                    reason = ""
                complain("Function \"{0}\" does not accept arguments with the given literal types:\n\n    {0}({1}){2}".format(fcn.name, ",\n    {0} ".format(" " * len(fcn.name)).join(pretty(x.schema, prefix="     " + " " * len(fcn.name)).lstrip() for x in typedargs), reason), original)
            else:
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

    def generate(self):
        if isinstance(self.fcn, UserFunction) and all(isinstance(x, int) for x in self.fcn.names):
            return self.fcn.body.generate()

        elif isinstance(self.fcn, UserFunction):
            return "{{{0} => {1}}}".format(", ".join(self.fcn.names, self.fcn.body.generate()))

        else:
            return self.fcn.generate(self.args)

def expandUserFunction(tree, frame):
    if isinstance(tree, BuiltinFunction):
        return tree

    elif isinstance(tree, UserFunction):
        names = tree.names
        defaults = [None if x is None else expandUserFunction(x, frame) for x in tree.defaults]
        subframe = frame.fork(dict((n, Ref(n)) for n in names))  # don't let shadowed variables get expanded
        body = expandUserFunction(tree.body, subframe)
        return UserFunction(names, defaults, body, tree.original)

    elif isinstance(tree, Ref):
        if frame.defined(tree.name):
            return frame[tree.name]
        else:
            raise ProgrammingError("{0} exists without any such name in the SymbolFrame {1}".format(tree, frame))

    elif isinstance(tree, Literal):
        return tree

    elif isinstance(tree, Call):
        return Call.build(expandUserFunction(tree.fcn, frame), [expandUserFunction(x, frame) for x in tree.args], tree.original)

    else:
        raise ProgrammingError("unrecognized functiontree: " + repr(tree))

def pos(tree):
    return {"lineno": tree.lineno, "col_offset": tree.col_offset}

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
        return UserFunction(params, [None] * arity, Call.build(fcn, [build(tree.value, frame)] + args, tree), tree)
        
    else:
        subframe = frame.fork()
        for i in xrange(1, arity + 1):
            subframe[i] = Ref(i, tree)
        return UserFunction(list(range(1, arity + 1)), [None] * arity, build(tree, subframe), tree)
    
def build(tree, frame):
    if isinstance(tree, parsingtree.Attribute):
        return Call.build(frame["."], [build(tree.value, frame), Literal(tree.attr, tree)], tree)

    elif isinstance(tree, parsingtree.BinOp):
        if isinstance(tree.op, parsingtree.Add):
            return Call.build(frame["+"], [build(tree.left, frame), build(tree.right, frame)], tree)
        elif isinstance(tree.op, parsingtree.Sub):
            return Call.build(frame["-"], [build(tree.left, frame), build(tree.right, frame)], tree)
        elif isinstance(tree.op, parsingtree.Mult):
            return Call.build(frame["*"], [build(tree.left, frame), build(tree.right, frame)], tree)
        elif isinstance(tree.op, parsingtree.Div):
            return Call.build(frame["/"], [build(tree.left, frame), build(tree.right, frame)], tree)
        elif isinstance(tree.op, parsingtree.Mod):
            return Call.build(frame["%"], [build(tree.left, frame), build(tree.right, frame)], tree)
        elif isinstance(tree.op, parsingtree.Pow):
            return Call.build(frame["**"], [build(tree.left, frame), build(tree.right, frame)], tree)
        elif isinstance(tree.op, parsingtree.FloorDiv):
            return Call.build(frame["//"], [build(tree.left, frame), build(tree.right, frame)], tree)
        else:
            raise ProgrammingError("unexpected binary operator: {0}".format(tree.op))

    elif isinstance(tree, parsingtree.BoolOp):
        # boolean operators flattened by normalizeLogic
        if isinstance(tree.op, parsingtree.And):
            return Call.build(frame["and"], [build(x, frame) for x in tree.values], tree)

        elif isinstance(tree.op, parsingtree.Or):
            return Call.build(frame["or"], [build(x, frame) for x in tree.values], tree)

        else:
            raise ProgrammingError("unexpected boolean operator: {0}".format(tree.op))

    elif isinstance(tree, parsingtree.Compare):
        # comparators flattened by normalizeLogic
        left = build(tree.left, frame)
        op = tree.ops[0]
        right = build(tree.comparators[0], frame)

        if isinstance(op, parsingtree.Eq):
            return Call.build(frame["=="], [left, right], op)

        elif isinstance(op, parsingtree.NotEq):
            return Call.build(frame["!="], [left, right], op)

        elif isinstance(op, parsingtree.Lt):
            return Call.build(frame["<"], [left, right], op)

        elif isinstance(op, parsingtree.LtE):
            return Call.build(frame["<="], [left, right], op)

        elif isinstance(op, parsingtree.Gt):
            # use "<" with reversed arguments
            return Call.build(frame["<"], [right, left], op)

        elif isinstance(op, parsingtree.GtE):
            # use "<=" with reversed arguments
            return Call.build(frame["<="], [right, left], op)

        elif isinstance(op, parsingtree.In):
            return Call.build(frame["in"], [left, right], op)

        elif isinstance(op, parsingtree.NotIn):
            return Call.build(frame["not in"], [left, right], op)

        else:
            raise ProgrammingError("unexpected comparison operator {0}".format(op))
            
    elif isinstance(tree, parsingtree.List):
        return Call.build(frame["[]"], [build(x, frame) for x in tree.elts])

    elif isinstance(tree, parsingtree.Name):
        if tree.id == "None":
            return Literal(None, tree)
        elif tree.id == "True":
            return Literal(True, tree)
        elif tree.id == "False":
            return Literal(False, tree)
        elif tree.id == "inf":
            return Literal(float("inf"), tree)
        elif frame.defined(tree.id):
            return frame[tree.id]
        else:
            complain("\"{0}\" is not (yet?) defined in this scope: define in the order of dependency, recursion is not allowed.".format(tree.id), tree)

    elif isinstance(tree, parsingtree.Num):
        return Literal(tree.n, tree)

    elif isinstance(tree, parsingtree.Str):
        return Literal(tree.s, tree)

    elif isinstance(tree, parsingtree.Subscript):
        result = build(tree.value, frame)
        if isinstance(tree.slice, parsingtree.Slice):
            if len(tree.slice.dims) == 0:
                raise ProgrammingError("unexpected subscript ExtSlice of zero dimensions in {0}".format(tree))
            args = []
            for slic in tree.slice.dims:
                if isinstance(slic, parsingtree.Slice):
                    lower = build(slic.lower, frame) if slic.lower is not None else Literal(None, slic)
                    upper = build(slic.upper, frame) if slic.upper is not None else Literal(None, slic)
                    step = build(slic.step, frame) if slic.step is not None else Literal(None, slic)
                    args.extend([lower, upper, step])
                elif isinstance(slic, parsingtree.Index):
                    value = build(slic.value, frame)
                    args.extend([value, value, Literal(0, slic)])
                else:
                    raise ProgrammingError("unexpected slice type in ExtSlice: {0}".format(slic))
            return Call.build(frame["[#:#:#,]"], [result] + args, tree)
            
        elif isinstance(tree.slice, parsingtree.ExtSlice):
            lower = build(tree.slice.lower, frame) if tree.slice.lower is not None else Literal(None, tree.slice)
            upper = build(tree.slice.upper, frame) if tree.slice.upper is not None else Literal(None, tree.slice)
            step = build(tree.slice.step, frame) if tree.slice.step is not None else Literal(None, tree.slice)
            return Call.build(frame["[#:#:#,]"], [result, lower, upper, step], tree)

        elif isinstance(tree.slice, parsingtree.Index):
            if isinstance(tree.slice.value, parsingtree.Tuple):
                if len(tree.slice.value.elts) == 0:
                    raise ProgrammingError("unexpected subscript tuple of length zero in {0}".format(tree))
                return Call.build(frame["[#,]"], [result] + [build(x, frame) for x in tree.slice.value.elts], tree)
            else:
                return Call.build(frame["[#,]"], [result, build(tree.slice.value, frame)], tree)

        else:
            raise ProgrammingError("unexpected subscript type: {0}".format(tree.slice))

    elif isinstance(tree, parsingtree.UnaryOp):
        if isinstance(tree.op, parsingtree.Not):
            return Call.build(frame["not"], [build(tree.operand, frame)], tree)
        elif isinstance(tree.op, parsingtree.UAdd):
            return Call.build(frame["u+"], [build(tree.operand, frame)], tree)
        elif isinstance(tree.op, parsingtree.USub):
            return Call.build(frame["u-"], [build(tree.operand, frame)], tree)
        else:
            raise ProgrammingError("unexpected unary operator: {0}".format(tree.op))

    elif isinstance(tree, parsingtree.Assignment):
        result = build(tree.expression, frame)
        if len(tree.lvalues) == 1:
            frame[tree.lvalues[0].id] = result
        elif len(tree.lvalues) > 1:
            for index, lvalue in enumerate(tree.lvalues):
                frame[lvalue.id] = Call.build(frame["[#,]"], [result, Literal(index)], lvalue)
        else:
            raise ProgrammingError("zero lvalues in assignment of {0}".format(tree.expression))

    elif isinstance(tree, parsingtree.AtArg):
        out = frame.get(1 if tree.num is None else tree.num)
        if out is None:
            complain("Function shortcuts ($n) can only be used in builtin functionals; write your function like {x => f(x)}.", tree)
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
                complain("Expression {0} is a value, not a function; it cannot be called.".format(fcn.generate()), tree)

            try:
                args = fcn.sortargs(tree.positional, dict((k.id, v) for k, v in zip(tree.names, tree.named)))
            except TypeError as err:
                complain(str(err), tree)

            builtArgs = [x if isinstance(x, (LispyTree, Function)) else buildOrElevate(x, frame, fcn.arity(i)) for i, x in enumerate(args)]

            if isinstance(fcn, UserFunction):
                return expandUserFunction(fcn.body, frame.fork(dict(zip(fcn.names, builtArgs))))
            else:
                return Call.build(fcn, builtArgs, tree)

    elif isinstance(tree, parsingtree.FcnDef):
        return UserFunction([x.id for x in tree.parameters],
                            [None if x is None else build(x, frame) for x in tree.defaults],
                            build(tree.body, frame.fork(dict((x.id, Ref(x.id)) for x in tree.parameters))),
                            tree)

    elif isinstance(tree, parsingtree.IfChain):
        args = []
        for predicate, consequent in zip(tree.predicates, tree.consequents):
            args.append(build(predicate, frame))
            args.append(build(parsingtree.normalizeLogic(predicate, negate=True), frame))
            args.append(build(consequent, frame))
        args.append(build(tree.alternate, frame))
        return Call.build(frame["if"], args, tree)

    elif isinstance(tree, parsingtree.TypeCheck):
        oftype = eval(compile(ast.Expression(buildSchema(tree.schema)), "<schema expression>", "eval"))
        return Call.build(frame["is"], [build(tree.expr, frame), Literal(oftype, tree.schema), Literal(tree.negate, tree)], tree)

    elif isinstance(tree, parsingtree.Suite):
        if len(tree.assignments) > 0:
            for assignment in tree.assignments:
                build(parsingtree.normalizeLogic(assignment), frame)
        return build(parsingtree.normalizeLogic(tree.expression), frame)

    else:
        raise ProgrammingError("unrecognized element in parsingtree: " + repr(tree))
