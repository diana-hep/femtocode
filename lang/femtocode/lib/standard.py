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
import json
import math
import sys
from functools import reduce

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.dataset import *
from femtocode.defs import *
from femtocode import inference
from femtocode.typesystem import *
from femtocode.util import *

def _buildargs(args, frame):
    return [typedtree.build(arg, frame)[0] for arg in args]

class StandardLibrary(Library):
    table = SymbolTable()

########################################################## Basic calculator

class Add(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "+"
    commutative = True
    associative = True

    def pythonast(self, args, tonative=False):
        return reduce(lambda x, y: ast.BinOp(x, ast.Add(), y), args)
        
    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("Addition (+) can only be used on numbers."), typedargs, frame
        else:
            return inference.add(*[x.schema for x in typedargs]), typedargs, frame

StandardLibrary.table[Add.name] = Add()

class Sub(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "-"

    def pythonast(self, args, tonative=False):
        return ast.BinOp(args[0], ast.Sub(), args[1])
        
    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("Subtraction (-) can only be used on numbers."), typedargs, frame
        else:
            return inference.subtract(*[x.schema for x in typedargs]), typedargs, frame

StandardLibrary.table[Sub.name] = Sub()

class UAdd(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "u+"

    def pythonast(self, args, tonative=False):
        return ast.UnaryOp(ast.UAdd(), args[0])

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if len(typedargs) != 1 or not isinstance(typedargs[0].schema, Number):
            return impossible("Unary plus (+) can only be used with a number."), typedargs, frame
        else:
            return typedargs[0].schema, typedargs, frame

StandardLibrary.table[UAdd.name] = UAdd()

class USub(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "u-"

    def pythonast(self, args, tonative=False):
        return ast.UnaryOp(ast.USub(), args[0])

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if len(typedargs) != 1 or not isinstance(typedargs[0].schema, Number):
            return impossible("Unary minus (-) can only be used with a number."), typedargs, frame
        else:
            return Number(-typedargs[0].schema.max, -typedargs[0].schema.min, typedargs[0].schema.whole), typedargs, frame

StandardLibrary.table[USub.name] = USub()

class Mult(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "*"
    commutative = True
    associative = True

    def pythonast(self, args, tonative=False):
        return reduce(lambda x, y: ast.BinOp(x, ast.Mult(), y), args)
        
    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("Multiplication (*) can only be used on numbers."), typedargs, frame
        else:
            return inference.multiply(*[x.schema for x in typedargs]), typedargs, frame

StandardLibrary.table[Mult.name] = Mult()

class Div(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "/"

    def pythonast(self, args, tonative=False):
        return ast.BinOp(args[0], ast.Div(), ast.Call(ast.Name("float", ast.Load()), [args[1]], [], None, None))

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("Division (/) can only be used on numbers."), typedargs, frame
        else:
            return inference.divide(typedargs[0].schema, typedargs[1].schema), typedargs, frame

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative):
        if tonative:
            # native arithmetic already returns inf/-inf on division by zero
            return super(Div, self).buildexec(target, schema, args, argschemas, newname, references, tonative)
        else:
            return statementsToAst("""
                try:
                    OUT = ARG0 / ARG1
                except ZeroDivisionError:
                    OUT = float("inf") * (1 if ARG0 > 0 else -1)
                """, OUT = target, ARG0 = args[0], ARG1 = args[1])

StandardLibrary.table[Div.name] = Div()

class FloorDiv(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "//"

    def pythonast(self, args, tonative=False):
        return ast.BinOp(args[0], ast.FloorDiv(), args[1])

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("Floor-division (//) can only be used on numbers."), typedargs, frame
        else:
            return inference.floordivide(typedargs[0].schema, typedargs[1].schema), typedargs, frame

StandardLibrary.table[FloorDiv.name] = FloorDiv()

class Pow(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "**"

    def pythonast(self, args, tonative=False):
        return ast.BinOp(args[0], ast.Pow(), args[1])

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("Power (**) can only be used on numbers."), typedargs, frame
        else:
            return inference.power(typedargs[0].schema, typedargs[1].schema), typedargs, frame

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative):
        if isinstance(args[1], ast.Num) and args[1].n == 0:
            if schema.whole:
                return statementsToAst("""OUT = 1""", OUT = target)
            else:
                return statementsToAst("""OUT = 1.0""", OUT = target)
                
        elif isinstance(args[1], ast.Num) and args[1].n == 0.5:
            return statementsToAst("""OUT = MATH.sqrt(ARG0)""", OUT = target, MATH=ast.Name("$math", ast.Load()), ARG0 = args[0])

        elif isinstance(args[1], ast.Num) and round(args[1].n) == args[1].n and args[1].n < 10:
            # TODO: this is an example of how ** can be optimized, but it is not proven to be optimal
            # another interesting implementation would be to create temporary variables and do the work in log_2(N) steps, rather than N
            x = newname()
            return statementsToAst("""
                X = ARG0
                OUT = xpow
                """, OUT = target, ARG0 = args[0],
                                   xpow = reduce(lambda x, y: ast.BinOp(x, ast.Mult(), y), [ast.Name(x, ast.Load()) for i in xrange(int(args[1].n))]),
                                   X = ast.Name(x, ast.Store()))

        elif tonative:
            return super(Pow, self).buildexec(target, schema, args, argschemas, newname, references, tonative)

        else:
            # make Python behave like low-level exponentiation
            x, y = newname(), newname()
            return statementsToAst("""
                X, Y = ARG0, ARG1
              
                if MATH.isnan(x) and y == 0:
                    OUT = 1.0
                elif MATH.isnan(x) or MATH.isnan(y):
                    OUT = float("nan")
                elif x == 0 and y < 0:
                    OUT = float("inf")
                elif MATH.isinf(y):
                    if x == 1 or x == -1:
                        OUT = float("nan")
                    elif abs(x) < 1:
                        if y > 0:
                            OUT = 0.0
                        else:
                            OUT = float("inf")
                    else:
                        if y > 0:
                            OUT = float("inf")
                        else:
                            OUT = 0.0
                elif MATH.isinf(x):
                    if y == 0:
                        OUT = 1.0
                    elif y < 0:
                        OUT = 0.0
                    else:
                        if x < 0 and round(y) == y and y % 2 == 1:
                            OUT = float("-inf")
                        else:
                            OUT = float("inf")
                elif x < 0 and round(y) != y:
                    OUT = float("nan")
                else:
                    try:
                        OUT = MATH.pow(x, y)
                    except OverflowError:
                        if abs(y) < 1:
                            if x < 0:
                                OUT = float("nan")
                            else:
                                OUT = 1.0
                        else:
                            if (abs(x) > 1 and y < 0) or (abs(x) < 1 and y > 0):
                                OUT = 0.0
                            else:
                                OUT = float("inf")
                """, OUT = target, MATH=ast.Name("$math", ast.Load()),
                                   ARG0 = args[0], ARG1 = args[1],
                                   x = ast.Name(x, ast.Load()), y = ast.Name(y, ast.Load()),
                                   X = ast.Name(x, ast.Store()), Y = ast.Name(y, ast.Store()))

StandardLibrary.table[Pow.name] = Pow()

class Mod(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "%"

    def pythonast(self, args, tonative=False):
        # Note: Numba knows that Python's % is modulo and not remainder (unlike C)
        return ast.BinOp(args[0], ast.Mod(), args[1])
        
    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("Modulo (%) can only be used on numbers."), typedargs, frame
        else:
            return inference.modulo(*[x.schema for x in typedargs]), typedargs, frame

StandardLibrary.table[Mod.name] = Mod()

########################################################## Predicates

class Eq(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "=="
    commutative = True

    def pythonast(self, args, tonative=False):
        return ast.Compare(args[0], [ast.Eq()], [args[1]])
        
    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        out = intersection(typedargs[0].schema, typedargs[1].schema)
        if isinstance(out, Impossible):
            return impossible("The argument types have no intersection (their values can never be equal)."), typedargs, frame
        else:
            return boolean, typedargs, frame.fork({args[0]: out, args[1]: out})

StandardLibrary.table[Eq.name] = Eq()

class NotEq(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "!="
    commutative = True

    def pythonast(self, args, tonative=False):
        return ast.Compare(args[0], [ast.NotEq()], [args[1]])

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)

        result, leftconstraint, rightconstraint = inference.inequality(self.name, typedargs[0].schema, typedargs[1].schema)
        if isinstance(result, Impossible):
            return result, typedargs, frame
        else:
            return result, typedargs, frame.fork({args[0]: leftconstraint, args[1]: rightconstraint})

StandardLibrary.table[NotEq.name] = NotEq()

class Inequality(statementlist.FlatFunction, lispytree.BuiltinFunction):

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not all(isNumber(ta.schema) for ta in typedargs):
            return impossible("{0} ({1}) can only be used on numbers.".format(self.longname, self.name)), typedargs, frame
        else:
            result, leftconstraint, rightconstraint = inference.inequality(self.name, typedargs[0].schema, typedargs[1].schema)
            if isinstance(result, Impossible):
                return result, typedargs, frame
            else:
                return result, typedargs, frame.fork({args[0]: leftconstraint, args[1]: rightconstraint})

class Lt(Inequality):
    name = "<"
    longname = "Less than"

    def pythonast(self, args, tonative=False):
        return ast.Compare(args[0], [ast.Lt()], [args[1]])
        
StandardLibrary.table[Lt.name] = Lt()

class LtE(Inequality):
    name = "<="
    longname = "Less than or equal to"

    def pythonast(self, args, tonative=False):
        return ast.Compare(args[0], [ast.LtE()], [args[1]])
        
StandardLibrary.table[LtE.name] = LtE()

class Gt(Inequality):
    name = ">"
    longname = "Greater than"

    def pythonast(self, args, tonative=False):
        return ast.Compare(args[0], [ast.Gt()], [args[1]])
        
StandardLibrary.table[Gt.name] = Gt()

class GtE(Inequality):
    name = ">="
    longname = "Greater than or equal to"

    def pythonast(self, args, tonative=False):
        return ast.Compare(args[0], [ast.GtE()], [args[1]])
        
StandardLibrary.table[GtE.name] = GtE()

class And(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "and"
    commutative = True
    associative = True

    def pythonast(self, args, tonative=False):
        return ast.BoolOp(ast.And(), args)
        
    def buildtyped(self, args, frame):
        subframe = frame.fork()
        subsubframes = []
        keys = set()

        for arg in args:
            # First pass gets all constraints in isolation.
            typedarg, subsubframe = typedtree.build(arg, subframe)
            keys = keys.union(subsubframe.keys(subframe))
            subsubframes.append(subsubframe)

        typedargs = []
        for i in xrange(len(args)):
            arg = args[i]
            tmpframe = subframe.fork()
            for k in keys:
                # Combine all constraints except the ones in 'arg' so that they can be used as preconditions,
                # regardless of the order in which the constraints are written.
                constraints = [f[k] for f in [subsubframes[j] for j in xrange(len(args)) if i != j] if f.defined(k)]
                if len(constraints) > 0:
                    constraint = intersection(*constraints)
                    if not isinstance(constraint, Impossible):
                        # Ignore the impossible ones for now; they'll come up again (with a more appropriate
                        # error message) below in arg.getschema(tmpframe).
                        tmpframe[k] = constraint

            # Check the type again, this time with all others as preconditions (regarless of order).
            typedargs.append(typedtree.build(arg, tmpframe)[0])

        for typedarg in typedargs:
            if not isinstance(typedarg.schema, Boolean):
                return impossible("Logical and can only be used on boolean arguments (use 'x != 0' if you want a zero value of 'x' to be 'False')."), typedargs, frame
            
        # 'and' constraints become intersections.
        for k in keys:
            constraints = [f[k] for f in subsubframes if f.defined(k)]
            if len(constraints) > 0:
                subframe[k] = intersection(*constraints)

        return boolean, typedargs, subframe

StandardLibrary.table[And.name] = And()

class Or(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "or"
    commutative = True
    associative = True

    def pythonast(self, args, tonative=False):
        return ast.BoolOp(ast.Or(), args)

    def buildtyped(self, args, frame):
        subframe = frame.fork()
        subsubframes = []
        keys = None

        typedargs = []
        for arg in args:
            typedarg, subsubframe = typedtree.build(arg, subframe)
            typedargs.append(typedarg)

            subsubframes.append(subsubframe)
            if keys is None:
                keys = subsubframe.keys(subframe)
            else:
                # Only apply a constraint if it is mentioned in all arguments of the 'or'.
                keys = keys.intersection(subsubframe.keys(subframe))

        # 'or' constraints become unions.
        for k in keys:
            subframe[k] = union(*[f[k] for f in subsubframes])

        for typedarg in typedargs:
            if not isinstance(typedarg.schema, Boolean):
                return impossible("Logical or can only be used on boolean arguments (use 'x != 0' if you want a zero value of 'x' to be 'False')."), typedargs, frame
                    
        return boolean, typedargs, subframe

StandardLibrary.table[Or.name] = Or()

class Not(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "not"

    def pythonast(self, args, tonative=False):
        return ast.UnaryOp(ast.Not(), args[0])

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)
        if not isinstance(typedargs[0].schema, Boolean):
            return impossible("Logical not can only be used on boolean arguments (use 'x != 0' if you want a zero value of 'x' to be 'False')."), typedargs, frame
        else:
            return boolean, typedargs, frame

StandardLibrary.table[Not.name] = Not()

########################################################## Type manipulations

class If(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "if"

    def pythonast(self, args, tonative=False):
        predicates = args[:-1][0::3]
        antipredicates = args[:-1][1::3]
        consequents = args[:-1][2::3]
        alternate = args[-1]
        return reduce(lambda x, y: ast.IfExp(y[0], y[1], x), reversed(list(zip(predicates, consequents))), alternate)

    def buildtyped(self, args, frame):
        predicates = args[:-1][0::3]
        antipredicates = args[:-1][1::3]
        consequents = args[:-1][2::3]
        alternate = args[-1]

        topframe = frame.fork()
        subframe = topframe
        typedargs = []
        outschemas = []
        for index, (predicate, antipredicate, consequent) in enumerate(zip(predicates, antipredicates, consequents)):
            try:
                typedpred, predframe = typedtree.build(predicate, subframe)
            except FemtocodeError as err:
                raise FemtocodeError("Error in \"if\" predicate. " + str(err))
            if not isinstance(typedpred.schema, Boolean):
                complain("If-predicate must be boolean (use 'x != 0' if you want a zero value of 'x' to be 'False'). Found\n\n{0}".format(",\n".join(pretty(typedpred.schema, prefix="    "))), predicate.original)

            try:
                typedanti, antiframe = typedtree.build(antipredicate, subframe)
            except FemtocodeError as err:
                if index == len(predicates) - 1:
                    which = "\"else\""
                else:
                    which = "\"elif\""
                raise FemtocodeError("Error while negating predicate for {0} clause. {1}".format(which, str(err)))

            if not isinstance(typedanti.schema, Boolean):
                complain("Negation of if-predicate must be boolean (use 'x != 0' if you want a zero value of 'x' to be 'False'). Found\n\n{0}".format(",\n".join(pretty(typedanti.schema, prefix="    "))), predicate.original)

            typedcons = typedtree.build(consequent, predframe)[0]

            typedargs.append(typedpred)
            typedargs.append(typedanti)
            typedargs.append(typedcons)
            outschemas.append(typedcons.schema)
            subframe = antiframe

        typedalt = typedtree.build(alternate, subframe)[0]
        typedargs.append(typedalt)
        outschemas.append(typedalt.schema)

        return union(*outschemas), typedargs, topframe

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative):
        predicates = args[:-1][0::3]
        antipredicates = args[:-1][1::3]
        consequents = args[:-1][2::3]
        alternate = args[-1]

        def isNone(expression):
            if sys.version_info[0] <= 2:
                return isinstance(expression, ast.Name) and expression.id == "None" and isinstance(expression.ctx, ast.Load)
            else:
                return isinstance(expression, ast.NameConstant) and expression.value is None
            
        def replaceNone(expression):
            return expression

        if isNullInt(schema):
            def replaceNone(expression):
                if isNone(expression):
                    return ast.Num(Number._intNaN)
                else:
                    return expression

        elif isNullFloat(schema):
            def replaceNone(expression):
                if isNone(expression):
                    return ast.Num(Number._floatNaN)
                else:
                    return expression

        chain = statementsToAst("""
            OUT = ALT
            """, OUT = target, ALT = replaceNone(alternate))

        for predicate, consequent in reversed(list(zip(predicates, consequents))):
            next = statementsToAst("""
                if PRED:
                    OUT = CONS
                else:
                    REPLACEME
                """, OUT = target, PRED = predicate, CONS = replaceNone(consequent))

            next[0].orelse = [chain[0]]   # replacing REPLACEME
            chain = next

        return chain

    def tosrc(self, args):
        predicates = args[0::3]
        consequents = args[2::3]
        alternate = args[-1]
        return " el".join("if ({0}) {{{1}}}".format(astToSource(p), astToSource(c)) for p, c in zip(predicates, consequents)) + " else {" + astToSource(alternate) + "}"
            
StandardLibrary.table[If.name] = If()

class Is(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "is"

    def pythoneval(self, args):
        if args[2]:
            return args[0] not in args[1]
        else:
            return args[0] in args[1]

    def buildtyped(self, args, frame):
        typedargs = _buildargs(args, frame)

        fromtype = typedargs[0].schema
        totype = typedargs[1].value   # literal type expression
        negate = typedargs[2].value   # literal boolean

        if negate:
            out = difference(fromtype, totype)
        else:
            out = intersection(fromtype, totype)

        if isinstance(out, Impossible):
            return impossible("Cannot constrain type:\n\n{0}".format(compare(fromtype, totype, header=("from", "excluding" if negate else "into"), between=lambda t1, t2: "|", prefix="    ")), out.reason), typedargs, frame

        return boolean(True) if fromtype == out else boolean, typedargs, frame.fork({args[0]: out})

    def _buildstatements_args(self, call):
        return [call.args[0]]

    def _buildstatements_build(self, columnName, schema, sizeColumn, args, call):
        fromtype = call.args[0].schema
        totype = call.args[1].value   # literal type expression
        negate = call.args[2].value   # literal boolean
        return statementlist.IsType(columnName, sizeColumn, args[0], fromtype, totype, negate)

    def buildstatements(self, call, dataset, replacements, refnumber, explosions):
        if call.schema == boolean(True):
            literal = statementlist.Literal(True, boolean(True))
            replacements[(typedtree.TypedTree, call)] = replacements.get((typedtree.TypedTree, call), {})
            replacements[(typedtree.TypedTree, call)][explosions] = literal
            return literal, statementlist.Statements(), {}, replacements, refnumber

        else:
            return super(Is, self).buildstatements(call, dataset, replacements, refnumber, explosions)

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative, fromtype, totype, negate):
        arg, = args

        if negate:
            restriction = difference(fromtype, totype)
        else:
            restriction = intersection(fromtype, totype)

        def numeric(restrict):
            if restrict.min == restrict.max:
                return ast.Compare(arg, [ast.Eq()], [ast.Num(restrict.min.real)])

            else:
                low = ast.Num(restrict.min.real)
                high = ast.Num(restrict.max.real)

                if isinstance(restrict.min, almost):
                    cmp1 = ast.Lt()
                else:
                    cmp1 = ast.LtE()

                if isinstance(restrict.max, almost):
                    cmp2 = ast.Lt()
                else:
                    cmp2 = ast.LtE()

                if restrict.whole and not isInt(fromtype) and not isNullInt(fromtype):
                    ops = [cmp1, ast.Eq(), cmp2]
                    comparators = [arg, ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "floor", ast.Load()), [arg], [], None, None), high]
                else:
                    ops = [cmp1, cmp2]
                    comparators = [arg, high]

                return ast.Compare(low, ops, comparators)

        expressions = []

        if isinstance(restriction, Number) and isNumber(fromtype):
            expressions.append(numeric(restriction))

        elif isinstance(restriction, Number) and isNullInt(fromtype):
            expressions.append(ast.BoolOp(ast.And(), [
                ast.Compare(arg, [ast.NotEq()], [ast.Num(Number._intNaN)]),
                numeric(restriction)
                ]))

        elif isinstance(restriction, Number) and isNullFloat(fromtype):
            expressions.append(ast.BoolOp(ast.And(), [
                ast.UnaryOp(ast.Not(), ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "isnan", ast.Load()), [arg], [], None, None)),
                numeric(restriction)
                ]))

        elif isinstance(restriction, Union) and isNumber(fromtype):
            for p in restriction.possibilities:
                expressions.append(numeric(p))

        elif isinstance(restriction, Union) and isNullInt(fromtype):
            for p in restriction.possibilities:
                if isinstance(p, Null):
                    expressions.append(ast.Compare(arg, [ast.Eq()], [ast.Num(Number._intNaN)]))
                else:
                    expressions.append(ast.BoolOp(ast.And(), [
                        ast.Compare(arg, [ast.NotEq()], [ast.Num(Number._intNaN)]),
                        numeric(p)
                        ]))

        elif isinstance(restriction, Union) and isNullFloat(fromtype):
            for p in restriction.possibilities:
                if isinstance(p, Null):
                    expressions.append(ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "isnan", ast.Load()), [arg], [], None, None))
                else:
                    expressions.append(ast.BoolOp(ast.And(), [
                        ast.UnaryOp(ast.Not(), ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "isnan", ast.Load()), [arg], [], None, None)),
                        numeric(p)
                        ]))

        else:
            raise NotImplementedException
        
        return statementsToAst("""
                OUT = RESTRICT
                """, OUT = target,
                     RESTRICT = expressions[0] if len(expressions) == 1 else ast.BoolOp(ast.Or(), expressions))
               
    def tosrc(self, args):
        return "(" + astToSource(args[0]) + " is " + astToSource(args[1]) + ")"

StandardLibrary.table[Is.name] = Is()

########################################################## Data structure manipulations

class Dot(lispytree.BuiltinFunction):
    name = "."

    def pythonast(self, args, tonative=False):
        return ast.Attribute(args[0], args[1])

    def buildtyped(self, args, frame):
        assert len(args) == 2 and isinstance(args[1].value, string_types), "dot (.) dereference operator got the wrong kinds of objects: {0}".format(", ".join(repr, args[0]))

        typedarg = typedtree.build(args[0], frame)[0]
        if isinstance(typedarg.schema, Record):
            if args[1].value in typedarg.schema.fields:
                schema = typedarg.schema.fields[args[1].value]
            else:
                schema = impossible("Record has no field named \"{0}\".".format(json.dumps(args[1].value)))
        else:
            schema = impossible("Dot (.) must be used on record types (first argument) only.")

        return schema, [typedarg, args[1]], frame

    def buildstatements(self, call, dataset, replacements, refnumber, explosions):
        argref, statements, inputs, repl, refnumber = statementlist.build(call.args[0], dataset, dict(replacements), refnumber, explosions)
        replacements.update(repl)

        field = call.args[1].value

        rename = argref.name.rec(field)
        if isinstance(argref, statementlist.RefWithExplosions):
            reref = statementlist.RefWithExplosions(rename, argref.schema.fields[field], dataset.dataColumn(rename), dataset.sizeColumn(rename), argref.explosions())
        else:
            reref = statementlist.Ref(rename, argref.schema.fields[field], dataset.dataColumn(rename), dataset.sizeColumn(rename))

        replacements[(typedtree.TypedTree, call)] = replacements.get((typedtree.TypedTree, call), {})
        replacements[(typedtree.TypedTree, call)][explosions] = reref

        if reref.data in dataset.columns:
            inputs[reref.data] = reref.schema
        if reref.size is not None:
            for c in dataset.columns.values():
                if reref.size == c.size:
                    inputs[reref.size] = None

        return reref, statements, inputs, replacements, refnumber

StandardLibrary.table[Dot.name] = Dot()

########################################################## Array methods

class Map(lispytree.BuiltinFunction):
    name = ".map"
            
    def arity(self, index, positional, named):
        if index == 1:
            return 1
        else:
            return None

    def buildtyped(self, args, frame):
        if len(args) != 2:
            return impossible("Exactly two arguments required."), [], frame

        typedarg0 = typedtree.build(args[0], frame)[0]
        if not isinstance(typedarg0.schema, Collection):
            return impossible("First argument must be a collection."), [], frame

        if not isinstance(args[1], Function):
            return impossible("Second argument must be a function."), [], frame

        fcn = lispytree.anyFunctionToUserFunction(args[1])

        typedarg1 = typedtree.buildUserFunction(fcn, [typedarg0.schema.items], frame)

        c = typedarg0.schema
        return collection(typedarg1.schema, c.fewest, c.most, c.ordered), [typedarg0, typedarg1], frame

    def buildstatements(self, call, dataset, replacements, refnumber, explosions):
        argref, statements, inputs, repl, refnumber = statementlist.build(call.args[0], dataset, dict(replacements), refnumber, explosions)
        replacements.update(repl)

        # the argument of the UserFunction is the values of the collection
        rename = argref.name.coll()
        extendedExplosions = explosions + (rename,)
        reref = statementlist.RefWithExplosions(rename, argref.schema.items, dataset.dataColumn(rename), dataset.sizeColumn(rename), extendedExplosions)
        
        if reref.data in dataset.columns:
            inputs = {reref.data: reref.schema}
        else:
            inputs = {}
        if reref.size is not None:
            for c in dataset.columns.values():
                if reref.size == c.size:
                    inputs[reref.size] = None

        replacements[(typedtree.TypedTree, call.args[1].refs[0])] = replacements.get((typedtree.TypedTree, call.args[1].refs[0]), {})
        replacements[(typedtree.TypedTree, call.args[1].refs[0])][extendedExplosions] = reref

        result, ss, ins, repl, refnumber = statementlist.build(call.args[1].body, dataset, dict(replacements), refnumber, extendedExplosions)
        statements.extend(ss)
        inputs.update(ins)
        replacements.update(repl)

        if not isinstance(reref.schema, Collection) and isinstance(result, statementlist.Ref) and result.explosions() != extendedExplosions:
            sizes = statementlist.explosionsToSizes(extendedExplosions, dataset)
            final, ss, repl, refnumber = statementlist.exploderef(result, dict(replacements), refnumber, dataset, sizes, extendedExplosions)
            statements.extend(ss)
            replacements.update(repl)
            outref = statementlist.RefWithExplosions(final.name, call.schema, final.data, final.size, explosions)

        elif isinstance(result, statementlist.Ref):
            outref = statementlist.RefWithExplosions(result.name, call.schema, result.data, result.size, explosions)
            
        else:
            outref = statementlist.Literal(result.value, call.schema)

        replacements[(typedtree.TypedTree, call)] = replacements.get((typedtree.TypedTree, call), {})
        replacements[(typedtree.TypedTree, call)][explosions] = outref

        return outref, statements, inputs, replacements, refnumber

    def tosrc(self, args):
        return astToSource(args[0]) + ".map(" + astToSource(args[1]) + ")"

    def sortargs(self, positional, named, original):
        return Function.sortargsWithNames(positional, named, ["fcn"], [None], original)

StandardLibrary.table[Map.name] = Map()

########################################################## Core math

class FlatReal1D(statementlist.FlatFunction, lispytree.BuiltinFunction):
    def buildtyped(self, args, frame):
        if len(args) != 1:
            return impossible("The {0} function takes only one argument.".format(self.name))

        typedargs = _buildargs(args, frame)
        if not isNumber(typedargs[0]):
            return impossible("The {0} function can only be used on numbers.".format(self.name))
        else:
            return self.image(typedargs[0])

    def image(self, domain):
        raise NotImplementedError

    def projection(self, endpoint):
        if isinstance(endpoint, almost):
            return almost(self.pythoneval([endpoint.real]))
        else:
            return self.pythoneval([endpoint])

    def imageFromTurningPoints(self, domain, turningPointAboveMin, turningPointBelowMax, wholeimage):
        if turningPointAboveMin > turningPointBelowMax:
            # monotonic on this interval
            one, two = self.projection(domain.min), self.projection(domain.max)
            if one < two:
                return real(one, two)
            else:
                return real(two, one)

        elif turningPointAboveMin == turningPointBelowMax:
            # monotonic to turning point
            one, two, three = self.projection(domain.min), self.projection(turningPointAboveMin), self.projection(domain.max)
            return real(almost.min(one, two, three), almost.max(one, two, three))

        else:
            # the whole image
            return wholeimage

class Abs(FlatReal1D):
    name = "abs"

    def pythonast(self, args, tonative=False):
        return ast.Call(ast.Name("abs", ast.Load()), args, [], None, None)

    def image(self, domain):
        if domain.min.real < 0 and domain.max.real > 0:
            return domain(0, almost.max(-domain.min, domain.max))
        elif domain.min == almost(0) and domain.max.real > 0:
            return domain(almost(0), domain.max)
        elif domain.min.real < 0 and domain.max == almost(0):
            return domain(almost(0), -domain.min)
        elif domain.max <= 0:
            return domain(-domain.max, -domain.min)
        else:
            return domain

StandardLibrary.table[Abs.name] = Abs()

class ExplikeFlatReal1D(FlatReal1D):
    def image(self, domain):
        # positively monotonic everywhere
        return real(self.projection(domain.min), self.projection(domain.max))

class SqrtlikeFlatReal1D(FlatReal1D):
    def image(self, domain):
        # positively monotonic with negative values excluded
        if domain.min.real < 0:
            return impossible("The {0} function can only be used on non-negative numbers.".format(self.name))
        return real(self.projection(domain.min), self.projection(domain.max))

class LoglikeFlatReal1D(FlatReal1D):
    def image(self, domain):
        # positively monotonic with negative values excluded and 0 mapped to -inf
        if domain.min.real < 0:
            return impossible("The {0} function can only be used on non-negative numbers.".format(self.name))
        if domain.min == 0:
            low = -inf
        elif domain.min == almost(0):
            low = almost(-inf)
        else:
            low = self.projection(domain.min)
        return real(low, self.projection(domain.high))

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative):
        return [ast.Assign([target], self.pythonast(args))]

    def pythonast(self, args, tonative=False):
        arg, = args
        if self.base == math.e:
            if tonative:
                return ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "log", ast.Load()), [arg], [], None, None)
            else:
                return ast.IfExp(ast.Compare(arg, ops=[ast.Gt()], [ast.Num(0)]), ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "log", ast.Load()), [arg], [], None, None), ast.Call(ast.Name("float", ast.Load()), [ast.Str("-inf")], [], None, None))
        else:
            if tonative:
                return ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "log", ast.Load()), [arg, ast.Num(self.base)], [], None, None)
            else:
                return ast.IfExp(ast.Compare(arg, ops=[ast.Gt()], [ast.Num(0)]), ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "log", ast.Load()), [arg, ast.Num(self.base)], [], None, None), ast.Call(ast.Name("float", ast.Load()), [ast.Str("-inf")], [], None, None))

class Sqrt(SqrtlikeFlatReal1D):
    name = "sqrt"

    def pythonast(self, args, tonative=False):
        return ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "sqrt", ast.Load()), args, [], None, None)

StandardLibrary.table[Sqrt.name] = Sqrt()

class Exp(ExplikeFlatReal1D):
    name = "exp"

    def pythonast(self, args, tonative=False):
        return ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "exp", ast.Load()), args, [], None, None)

StandardLibrary.table[Exp.name] = Exp()

class Log(LoglikeFlatReal1D):
    name = "log"
    base = math.e

StandardLibrary.table[Log.name] = Log()

class Log2(LoglikeFlatReal1D):
    name = "log2"
    base = 2

StandardLibrary.table[Log2.name] = Log2()

class Log10(LoglikeFlatReal1D):
    name = "log10"
    base = 10

StandardLibrary.table[Log10.name] = Log10()
    
class Sin(FlatReal1D):
    name = "sin"

    def pythonast(self, args, tonative=False):
        return ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "sin", ast.Load()), args, [], None, None)

    def image(self, domain):
        if math.isinf(domain.min.real) or math.isinf(domain.max.real):
            return real(-1.0, 1.0)
        turningPointAboveMin = (math.ceil(domain.min.real / math.pi + 0.5) - 0.5) * math.pi
        turningPointBelowMax = (math.floor(domain.max.real / math.pi - 0.5) + 0.5) * math.pi
        return self.imageFromTurningPoints(domain, turningPointAboveMin, turningPointBelowMax, real(-1.0, 1.0))

StandardLibrary.table[Sin.name] = Sin()

class Cos(FlatReal1D):
    name = "cos"

    def pythonast(self, args, tonative=False):
        return ast.Call(ast.Attribute(ast.Name("$math", ast.Load()), "cos", ast.Load()), args, [], None, None)

    def image(self, domain):
        if math.icosf(domain.min.real) or math.icosf(domain.max.real):
            return real(-1.0, 1.0)
        turningPointAboveMin = (math.ceil(domain.min.real / math.pi)) * math.pi
        turningPointBelowMax = (math.floor(domain.max.real / math.pi)) * math.pi
        return self.imageFromTurningPoints(domain, turningPointAboveMin, turningPointBelowMax, real(-1.0, 1.0))

StandardLibrary.table[Cos.name] = Cos()

# TODO:
###########
# tan
# atan2
# asin
# acos
# atan
# sinh
# cosh
# tanh
# asinh
# acosh
# atanh
# some sort of rounding? (should change type to integer)
