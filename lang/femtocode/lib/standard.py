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
import sys

from femtocode.asts import lispytree
from femtocode.asts import statementlist
from femtocode.asts import typedtree
from femtocode.defs import *
from femtocode import inference
from femtocode.typesystem import *
from femtocode.util import *

table = SymbolTable()

class Is(lispytree.BuiltinFunction):
    ## FIXME: this will be a tricky one; maybe shouldn't be a library function

    name = "is"

    def pythoneval(self, args):
        return True

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]

        fromtype = typedargs[0].schema
        totype = typedargs[1].value   # literal type expression
        negate = typedargs[2].value   # literal boolean

        if negate:
            out = difference(fromtype, totype)
        else:
            out = intersection(fromtype, totype)

        if isinstance(out, Impossible):
            return impossible("Cannot constrain type:\n\n{0}".format(compare(fromtype, totype, header=("from", "excluding" if negate else "to"), between=lambda t1, t2: "|", prefix="    ")), out.reason), typedargs, frame

        return boolean, typedargs, frame.fork({args[0]: out})

    def tosrc(self, args):
        return "(" + astToSource(args[0]) + " is " + astToSource(args[1]) + ")"

table[Is.name] = Is()

class Add(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "+"

    def commutative(self):
        return True

    def associative(self):
        return True

    def pythonast(self, args):
        return reduce(lambda x, y: ast.BinOp(x, ast.Add(), y), args)
        
    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.add(*[x.schema for x in typedargs]), typedargs, frame

table[Add.name] = Add()

class Subtract(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "-"

    def pythonast(self, args):
        return ast.BinOp(args[0], ast.Sub(), args[1])
        
    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.subtract(*[x.schema for x in typedargs]), typedargs, frame

table[Subtract.name] = Subtract()

class UnaryMinus(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "u-"

    def pythonast(self, args):
        return ast.UnaryOp(ast.USub(), args[0])

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        if len(typedargs) != 1 or not isinstance(typedargs[0].schema, Number):
            return impossible("Unary minus (-) can only be used with a number."), typedargs, frame
        else:
            return Number(-typedargs[0].schema.max, -typedargs[0].schema.min, typedargs[0].schema.whole), typedargs, frame

table[UnaryMinus.name] = UnaryMinus()

class Mult(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "*"

    def commutative(self):
        return True

    def associative(self):
        return True

    def pythonast(self, args):
        return reduce(lambda x, y: ast.BinOp(x, ast.Mult(), y), args)
        
    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.multiply(*[x.schema for x in typedargs]), typedargs, frame

table[Mult.name] = Mult()

class Div(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "/"

    def pythonast(self, args):
        return ast.BinOp(args[0], ast.Div(), ast.Call(ast.Name("float", ast.Load()), [args[1]], [], None, None))

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.divide(typedargs[0].schema, typedargs[1].schema), typedargs, frame

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative):
        if tonative:
            return super(Div, self).buildexec(target, schema, args, argschemas, newname, references, tonative)
        else:
            return statementsToAst("""
                try:
                    OUT = ARG0 / ARG1
                except ZeroDivisionError:
                    OUT = float("inf") * (1 if ARG0 > 0 else -1)
                """, OUT = target, ARG0 = args[0], ARG1 = args[1])

table[Div.name] = Div()

class FloorDiv(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "//"

    def pythonast(self, args):
        return ast.BinOp(args[0], ast.FloorDiv(), args[1])

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.floordivide(typedargs[0].schema, typedargs[1].schema), typedargs, frame

table[FloorDiv.name] = FloorDiv()

class Power(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "**"

    def pythonast(self, args):
        return ast.BinOp(args[0], ast.Pow(), args[1])

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.power(typedargs[0].schema, typedargs[1].schema), typedargs, frame

    def buildexec(self, target, schema, args, argschemas, newname, references, tonative):
        if isinstance(args[1], ast.Num) and args[1].n == 0:
            if schema.whole:
                return statementsToAst("""OUT = 1""", OUT = target)
            else:
                return statementsToAst("""OUT = 1.0""", OUT = target)
                
        elif isinstance(args[1], ast.Num) and args[1].n == 0.5:
            return statementsToAst("""OUT = math.sqrt(ARG0)""", OUT = target, ARG0 = args[0])

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
            return super(Power, self).buildexec(target, schema, args, argschemas, newname, references, tonative)

        else:
            # make Python behave like low-level exponentiation
            x, y = newname(), newname()
            return statementsToAst("""
                X, Y = ARG0, ARG1
              
                if math.isnan(x) and y == 0:
                    OUT = 1.0
                elif math.isnan(x) or math.isnan(y):
                    OUT = float("nan")
                elif x == 0 and y < 0:
                    OUT = float("inf")
                elif math.isinf(y):
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
                elif math.isinf(x):
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
                        OUT = math.pow(x, y)
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
                """, OUT = target, ARG0 = args[0], ARG1 = args[1],
                                   x = ast.Name(x, ast.Load()), y = ast.Name(y, ast.Load()),
                                   X = ast.Name(x, ast.Store()), Y = ast.Name(y, ast.Store()))

table[Power.name] = Power()

class Eq(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "=="

    def commutative(self):
        return True

    def pythonast(self, args):
        return ast.Compare(args[0], [ast.Eq()], [args[1]])

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        out = intersection(typedargs[0].schema, typedargs[1].schema)
        if isinstance(out, Impossible):
            return impossible("The argument types have no intersection (their values can never be equal)."), typedargs, frame
        else:
            return boolean, typedargs, frame.fork({args[0]: out, args[1]: out})

table[Eq.name] = Eq()

class NotEq(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "!="

    def commutative(self):
        return True

    def pythonast(self, args):
        return ast.Compare(args[0], [ast.NotEq()], [args[1]])

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]

        const = None
        expr = None
        if isinstance(args[0], lispytree.Literal):
            const = args[0].value
            expr = args[1]
            restriction = inference.literal(typedargs[1].schema, "!=", const)
        elif isinstance(args[1], lispytree.Literal):
            const = args[1].value
            expr = args[0]
            restriction = inference.literal(typedargs[0].schema, "!=", const)

        if expr is not None:
            subframe = frame.fork({expr: restriction})
            if isinstance(subframe[expr], Impossible):
                return subframe[expr], typedargs, frame
        else:
            subframe = frame.fork()

        return boolean, typedargs, subframe

table[NotEq.name] = NotEq()

class And(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "and"

    def commutative(self):
        return True

    def associative(self):
        return True

    def pythonast(self, args):
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
                return impossible("All arguments must be boolean."), typedargs, frame
            
        # 'and' constraints become intersections.
        for k in keys:
            constraints = [f[k] for f in subsubframes if f.defined(k)]
            if len(constraints) > 0:
                subframe[k] = intersection(*constraints)

        return boolean, typedargs, subframe

table[And.name] = And()

class Or(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "or"

    def commutative(self):
        return True

    def associative(self):
        return True

    def pythonast(self, args):
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
                return impossible("All arguments must be boolean."), typedargs, frame
                    
        return boolean, typedargs, subframe

table[Or.name] = Or()

class Not(statementlist.FlatFunction, lispytree.BuiltinFunction):
    name = "not"

    def pythonast(self, args):
        return ast.UnaryOp(ast.Not(), args[0])

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        if not isinstance(typedargs[0].schema, Boolean):
            return impossible("Argument must be boolean."), typedargs, frame
        else:
            return boolean, typedargs, frame

table[Not.name] = Not()

class If(lispytree.BuiltinFunction):
    name = "if"

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
                complain("\"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(typedpred.schema, prefix="    "))), predicate.original)

            try:
                typedanti, antiframe = typedtree.build(antipredicate, subframe)
            except FemtocodeError as err:
                if index == len(predicates) - 1:
                    which = "\"else\""
                else:
                    which = "\"elif\""
                raise FemtocodeError("Error while negating predicate for {0} clause. {1}".format(which, str(err)))

            if not isinstance(typedanti.schema, Boolean):
                complain("Negation of \"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(typedanti.schema, prefix="    "))), predicate.original)

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

    # def buildexec(self, target, schema, args, argschemas, newname, references):
    ## FIXME: need to think about this one

    def tosrc(self, args):
        predicates = args[0::3]
        consequents = args[2::3]
        alternate = args[-1]
        return " el".join("if ({0}) {{{1}}}".format(astToSource(p), astToSource(c)) for p, c in zip(predicates, consequents)) + " else {" + astToSource(alternate) + "}"
            
table[If.name] = If()

class Dot(lispytree.BuiltinFunction):
    name = "."

    def pythonast(self, args):
        return ast.Attribute(args[0], args[1])

    def buildtyped(self, args, frame):
        assert len(args) == 2 and isinstance(args[1].value, string_types), "dot (.) dereference operator got the wrong kinds of objects: {0}".format(", ".join(repr, args[0]))

        typedarg = typedtree.build(args[0], frame)[0]
        if isinstance(typedarg.schema, Record):
            if args[1].value in typedarg.schema.fields:
                schema = typedarg.schema.fields[args[1].value]
            else:
                schema = impossible("Record has no field named {0}.".format(json.dumps(args[1].value)))
        else:
            schema = impossible("Dot (.) used on a non-record type (first argument).")

        return schema, [typedarg, args[1]], frame

    def buildstatements(self, call, dataset, replacements, refnumber, explosions):
        argref, statements, inputs, refnumber = statementlist.build(call.args[0], dataset, replacements, refnumber, explosions)
        field = call.args[1].value

        rename = argref.name.rec(field)
        reref = statementlist.Ref(rename, argref.schema.fields[field], dataset.dataColumn(rename), dataset.sizeColumn(rename))

        replacements[(typedtree.TypedTree, call)] = reref

        return reref, statements, inputs, refnumber

table[Dot.name] = Dot()

class Map(lispytree.BuiltinFunction):
    name = ".map"
            
    def arity(self, index):
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

        # FIXME: many other functions will need this; put it somewhere upstream (hint: use the number of arguments, [1])
        if isinstance(args[1], lispytree.BuiltinFunction):
            subframe = frame.fork()
            framenumber = subframe.framenumber()
            fcn = lispytree.UserFunction([1], framenumber, [None], lispytree.Call(args[1], [lispytree.Ref(1, framenumber)], args[1].original))
        elif isinstance(args[1], lispytree.UserFunction):
            fcn = args[1]
        else:
            return impossible("Second argument must be a function."), [], frame

        typedarg1 = typedtree.buildUserFunction(fcn, [typedarg0.schema.items], frame)

        c = typedarg0.schema
        return collection(typedarg1.schema, c.fewest, c.most, c.ordered), [typedarg0, typedarg1], frame

    def buildstatements(self, call, dataset, replacements, refnumber, explosions):
        argref, statements, inputs, refnumber = statementlist.build(call.args[0], dataset, replacements, refnumber, explosions)

        # the argument of the UserFunction is the values of the collection
        rename = argref.name.coll()
        reref = statementlist.Ref(rename, argref.schema.items, dataset.dataColumn(rename), dataset.sizeColumn(rename))
        replacements[(typedtree.TypedTree, call.args[1].refs[0])] = reref

        result, ss, ins, refnumber = statementlist.build(call.args[1].body, dataset, replacements, refnumber, explosions + (reref,))
        statements.extend(ss)
        inputs.update(ins)

        replacements[(typedtree.TypedTree, call)] = replacements[(typedtree.TypedTree, call.args[1].body)]
        return statementlist.Ref(result.name, call.schema, result.data, result.size), statements, inputs, refnumber

    def tosrc(self, args):
        return astToSource(args[0]) + ".map(" + astToSource(args[1]) + ")"

    def sortargs(self, positional, named, original):
        return Function.sortargsWithNames(positional, named, ["fcn"], [None], original)

table[Map.name] = Map()
