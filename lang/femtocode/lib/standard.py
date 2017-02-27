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

from femtocode import inference
from femtocode.asts import lispytree
from femtocode.asts import typedtree
from femtocode.asts import statementlist
from femtocode.defs import *
from femtocode.typesystem import *

table = SymbolTable()
    
class Is(lispytree.BuiltinFunction):
    name = "is"

    def literaleval(self, args):
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

    def generate(self, args):
        return "({0} is {1})".format(args[0].generate(), repr(args[1].value))

table[Is.name] = Is()

class Add(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "+"

    def commutative(self):
        return True

    def associative(self):
        return True

    def literaleval(self, args):
        return sum(args)
        
    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.add(*[x.schema for x in typedargs]), typedargs, frame

    def generate(self, args):
        return "({0})".format(" + ".join(arg.generate() for arg in args))

table[Add.name] = Add()

class Subtract(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "-"

    def literaleval(self, args):
        return args[0] - args[1]
        
    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.subtract(*[x.schema for x in typedargs]), typedargs, frame

    def generate(self, args):
        return "({0} - {1})".format(args[0].generate(), args[1].generate())

table[Subtract.name] = Subtract()

class Divide(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "/"

    def literaleval(self, args):
        return float(args[0]) / float(args[1])
        
    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        return inference.divide(typedargs[0].schema, typedargs[1].schema), typedargs, frame

    def generate(self, args):
        return "({0} / {1})".format(args[0].generate(), args[1].generate())

table[Divide.name] = Divide()

class Eq(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "=="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] == args[1]

    def buildtyped(self, args, frame):
        typedargs = [typedtree.build(arg, frame)[0] for arg in args]
        out = intersection(typedargs[0].schema, typedargs[1].schema)
        if isinstance(out, Impossible):
            return impossible("The argument types have no overlap (values can never be equal)."), typedargs, frame
        else:
            return boolean, typedargs, frame.fork({args[0]: out, args[1]: out})

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[Eq.name] = Eq()

class NotEq(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "!="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] != args[1]

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
                return impossible("Expression {0} has only one value at {1} (can never be unequal).".format(expr.generate(), const)), typedargs, frame
        else:
            subframe = frame.fork()

        return boolean, typedargs, subframe

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[NotEq.name] = NotEq()

class And(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "and"

    def commutative(self):
        return True

    def associative(self):
        return True

    def literaleval(self, args):
        return all(args)
        
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

    def generate(self, args):
        return "(" + " and ".join(x.generate() for x in args) + ")"

table[And.name] = And()

class Or(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "or"

    def commutative(self):
        return True

    def associative(self):
        return True

    def literaleval(self, args):
        return any(args)

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

    def generate(self, args):
        return "(" + " or ".join(x.generate() for x in args) + ")"

table[Or.name] = Or()

class Not(statementlist.FlatStatements, lispytree.BuiltinFunction):
    name = "not"

    def literaleval(self, args):
        return not args

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

    def generate(self, args):
        predicates = args[0::3]
        consequents = args[2::3]
        alternate = args[-1]
        return " el".join("if ({0}) {{{1}}}".format(p.generate(), c.generate()) for p, c in zip(predicates, consequents)) + " else {" + alternate.generate() + "}"
            
table[If.name] = If()

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

        # FIXME: generalize this out (knowing the number of arguments, [1])
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
        argref, statements, refnumber = statementlist.build(call.args[0], dataset, replacements, refnumber, explosions)

        # the argument of the UserFunction is the values of the collection
        reref = statementlist.Ref(argref.name.array(), argref.schema, dataset.dataColumn(argref.name.array()), dataset.sizeColumn(argref.name.array()))
        replacements[(typedtree.TypedTree, call.args[1].refs[0])] = reref
            
        if reref.size is not None:
            explosions = explosions + (reref.size,)
        result, ss, refnumber = statementlist.build(call.args[1].body, dataset, replacements, refnumber, explosions)
        statements.extend(ss)

        replacements[(typedtree.TypedTree, call)] = replacements[(typedtree.TypedTree, call.args[1].body)]
        return statementlist.Ref(result.name, call.schema, result.data, result.size), statements, refnumber

    def generate(self, args):
        return args[0].generate() + "(" + args[1].generate() + ")"

    def sortargs(self, positional, named, original):
        return Function.sortargsWithNames(positional, named, ["fcn"], [None], original)

table[Map.name] = Map()
