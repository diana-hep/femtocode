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
from femtocode.asts import columnartree
from femtocode.defs import *
from femtocode.typesystem import *

table = SymbolTable()

class Is(lispytree.BuiltinFunction):
    name = "is"

    def literaleval(self, args):
        return True

    def buildTyped(self, args, typeframe):
        typedargs = [typedtree.build(arg, typeframe)[0] for arg in args]

        fromtype = typedargs[0].schema
        totype = typedargs[1].value   # literal type expression
        negate = typedargs[2].value   # literal boolean

        if negate:
            out = difference(fromtype, totype)
        else:
            out = intersection(fromtype, totype)

        if isinstance(out, Impossible):
            return impossible("Cannot constrain type:\n\n{0}".format(compare(fromtype, totype, header=("from", "excluding" if negate else "to"), between=lambda t1, t2: "|", prefix="    ")), out.reason), typedargs, typeframe

        return boolean, typedargs, typeframe.fork({args[0]: out})

    def generate(self, args):
        return "({0} is {1})".format(args[0].generate(), repr(args[1].value))

table[Is.name] = Is()

class Add(lispytree.BuiltinFunction):
    name = "+"

    def commutative(self):
        return True

    def literaleval(self, args):
        return sum(args)
        
    def buildTyped(self, args, typeframe):
        typedargs = [typedtree.build(arg, typeframe)[0] for arg in args]
        return inference.add(typedargs[0].schema, typedargs[1].schema), typedargs, typeframe
        
    def generate(self, args):
        return "({0} + {1})".format(args[0].generate(), args[1].generate())

table[Add.name] = Add()

class Eq(lispytree.BuiltinFunction):
    name = "=="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] == args[1]

    def buildTyped(self, args, typeframe):
        typedargs = [typedtree.build(arg, typeframe)[0] for arg in args]
        out = intersection(typedargs[0].schema, typedargs[1].schema)
        if isinstance(out, Impossible):
            return impossible("The argument types have no overlap (values can never be equal)."), typedargs, typeframe
        else:
            return boolean, typedargs, typeframe.fork({args[0]: out, args[1]: out})

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[Eq.name] = Eq()

class NotEq(lispytree.BuiltinFunction):
    name = "!="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] != args[1]

    def buildTyped(self, args, typeframe):
        typedargs = [typedtree.build(arg, typeframe)[0] for arg in args]

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
            subtypeframe = typeframe.fork({expr: restriction})
            if isinstance(subtypeframe[expr], Impossible):
                return impossible("Expression {0} has only one value at {1} (can never be unequal).".format(expr.generate(), const)), typedargs, typeframe
        else:
            subtypeframe = typeframe.fork()

        return boolean, typedargs, subtypeframe

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[NotEq.name] = NotEq()

class And(lispytree.BuiltinFunction):
    name = "and"

    def commutative(self):
        return True

    def literaleval(self, args):
        return all(args)
        
    def buildTyped(self, args, typeframe):
        subtypeframe = typeframe.fork()
        subsubtypeframes = []
        keys = set()

        for arg in args:
            # First pass gets all constraints in isolation.
            typedarg, subsubtypeframe = typedtree.build(arg, subtypeframe)
            keys = keys.union(subsubtypeframe.keys(subtypeframe))
            subsubtypeframes.append(subsubtypeframe)

        typedargs = []
        for i in xrange(len(args)):
            arg = args[i]
            tmptypeframe = subtypeframe.fork()
            for k in keys:
                # Combine all constraints except the ones in 'arg' so that they can be used as preconditions,
                # regardless of the order in which the constraints are written.
                constraints = [f[k] for f in [subsubtypeframes[j] for j in xrange(len(args)) if i != j] if f.defined(k)]
                if len(constraints) > 0:
                    constraint = intersection(*constraints)
                    if not isinstance(constraint, Impossible):
                        # Ignore the impossible ones for now; they'll come up again (with a more appropriate
                        # error message) below in arg.getschema(tmptypeframe).
                        tmptypeframe[k] = constraint

            # Check the type again, this time with all others as preconditions (regarless of order).
            typedargs.append(typedtree.build(arg, tmptypeframe)[0])

        for typedarg in typedargs:
            if not isinstance(typedarg.schema, Boolean):
                return impossible("All arguments must be boolean."), typedargs, typeframe
            
        # 'and' constraints become intersections.
        for k in keys:
            constraints = [f[k] for f in subsubtypeframes if f.defined(k)]
            if len(constraints) > 0:
                subtypeframe[k] = intersection(*constraints)

        return boolean, typedargs, subtypeframe

    def generate(self, args):
        return "(" + " and ".join(x.generate() for x in args) + ")"

table[And.name] = And()

class Or(lispytree.BuiltinFunction):
    name = "or"

    def commutative(self):
        return True

    def literaleval(self, args):
        return any(args)

    def buildTyped(self, args, typeframe):
        subtypeframe = typeframe.fork()
        subsubtypeframes = []
        keys = None

        typedargs = []
        for arg in args:
            typedarg, subsubtypeframe = typedtree.build(arg, subtypeframe)
            typedargs.append(typedarg)

            subsubtypeframes.append(subsubtypeframe)
            if keys is None:
                keys = subsubtypeframe.keys(subtypeframe)
            else:
                # Only apply a constraint if it is mentioned in all arguments of the 'or'.
                keys = keys.intersection(subsubtypeframe.keys(subtypeframe))

        # 'or' constraints become unions.
        for k in keys:
            subtypeframe[k] = union(*[f[k] for f in subsubtypeframes])

        for typedarg in typedargs:
            if not isinstance(typedarg.schema, Boolean):
                return impossible("All arguments must be boolean."), typedargs, typeframe
                    
        return boolean, typedargs, subtypeframe

    def generate(self, args):
        return "(" + " or ".join(x.generate() for x in args) + ")"

table[Or.name] = Or()

class Not(lispytree.BuiltinFunction):
    name = "not"

    def literaleval(self, args):
        return not args

    def buildTyped(self, args, typeframe):
        typedargs = [typedtree.build(arg, typeframe)[0] for arg in args]
        if not isinstance(typedargs[0].schema, Boolean):
            return impossible("Argument must be boolean."), typedargs, typeframe
        else:
            return boolean, typedargs, typeframe

table[Not.name] = Not()

class If(lispytree.BuiltinFunction):
    name = "if"

    def buildTyped(self, args, typeframe):
        predicates = args[:-1][0::3]
        antipredicates = args[:-1][1::3]
        consequents = args[:-1][2::3]
        alternate = args[-1]

        toptypeframe = typeframe.fork()
        subtypeframe = toptypeframe
        typedargs = []
        outschemas = []
        for index, (predicate, antipredicate, consequent) in enumerate(zip(predicates, antipredicates, consequents)):
            try:
                typedpred, predtypeframe = typedtree.build(predicate, subtypeframe)
            except FemtocodeError as err:
                raise FemtocodeError("Error in \"if\" predicate. " + str(err))
            if not isinstance(typedpred.schema, Boolean):
                complain("\"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(typedpred.schema, prefix="    "))), predicate.original)

            try:
                typedanti, antitypeframe = typedtree.build(antipredicate, subtypeframe)
            except FemtocodeError as err:
                if index == len(predicates) - 1:
                    which = "\"else\""
                else:
                    which = "\"elif\""
                raise FemtocodeError("Error while negating predicate for {0} clause. {1}".format(which, str(err)))

            if not isinstance(typedanti.schema, Boolean):
                complain("Negation of \"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(typedanti.schema, prefix="    "))), predicate.original)

            typedcons = typedtree.build(consequent, predtypeframe)[0]

            typedargs.append(typedpred)
            typedargs.append(typedanti)
            typedargs.append(typedcons)
            outschemas.append(typedcons.schema)
            subtypeframe = antitypeframe

        typedalt = typedtree.build(alternate, subtypeframe)[0]
        typedargs.append(typedalt)
        outschemas.append(typedalt.schema)

        return union(*outschemas), typedargs, toptypeframe

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

    def buildTyped(self, args, typeframe):
        if len(args) != 2:
            return impossible("Exactly two arguments required."), [], typeframe

        typedarg0 = typedtree.build(args[0], typeframe)[0]
        if not isinstance(typedarg0.schema, Collection):
            return impossible("First argument must be a collection."), [], typeframe

        if isinstance(args[1], lispytree.BuiltinFunction):
            fcn = lispytree.UserFunction([1], [None], lispytree.Call(args[1], [lispytree.Ref(1)], args[1].original))
        elif isinstance(args[1], lispytree.UserFunction):
            fcn = args[1]
        else:
            return impossible("Second argument must be a function."), [], typeframe

        typedarg1 = typedtree.buildUserFunction(fcn, [typedarg0.schema.items], typeframe)

        return collection(typedarg1.schema), [typedarg0, typedarg1], typeframe

    def generate(self, args):
        return args[0].generate() + "(" + args[1].generate() + ")"

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, ["fcn"], [None])

table[Map.name] = Map()
