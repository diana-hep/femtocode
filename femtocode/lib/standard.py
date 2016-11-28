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
from femtocode.asts import typingtree
from femtocode.defs import *
from femtocode.typesystem import *

table = SymbolTable()

class Add(typingtree.BuiltinFunction):
    name = "+"

    def commutative(self):
        return True

    def literaleval(self, args):
        return sum(args)
        
    def retschema(self, frame, args):
        return inference.add(args[0].retschema(frame)[0], args[1].retschema(frame)[0]), frame

    def generate(self, args):
        return "({0} + {1})".format(args[0].generate(), args[1].generate())

table[Add.name] = Add()

class Eq(typingtree.BuiltinFunction):
    name = "=="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] == args[1]

    def retschema(self, frame, args):
        out = intersection(args[0].retschema(frame)[0], args[1].retschema(frame)[0])
        if isinstance(out, Impossible):
            return impossible("The argument types have no overlap (values can never be equal)."), frame
        else:
            return boolean, frame.fork({args[0]: out, args[1]: out})

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[Eq.name] = Eq()

class NotEq(typingtree.BuiltinFunction):
    name = "!="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] != args[1]

    def retschema(self, frame, args):
        const = None
        expr = None
        if isinstance(args[0], typingtree.Literal):
            const = args[0].value
            expr = args[1]
        elif isinstance(args[1], typingtree.Literal):
            const = args[1].value
            expr = args[0]

        if expr is not None:
            subframe = frame.fork({expr: inference.literal(expr.retschema(frame)[0], "!=", const)})
            if isinstance(subframe[expr], Impossible):
                return impossible("Expression {0} has only one value at {1} (can never be unequal).".format(expr.generate(), const))
        else:
            subframe = frame.fork()

        return boolean, subframe

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[NotEq.name] = NotEq()

class And(typingtree.BuiltinFunction):
    name = "and"

    def commutative(self):
        return True

    def literaleval(self, args):
        return all(args)
        
    def retschema(self, frame, args):
        subframe = frame.fork()
        subsubframes = []
        keys = set()

        for arg in args:
            t, subsubframe = arg.retschema(subframe)
            keys = keys.union(subsubframe.keys(subframe))
            subsubframes.append(subsubframe)

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
                        # error message) below in arg.retschema(tmpframe).
                        tmpframe[k] = constraint

            # Check the type again, this time with all others as preconditions (regarless of order).
            if not isinstance(arg.retschema(tmpframe)[0], Boolean):
                return impossible("All arguments must be boolean."), frame
            
        # 'and' constraints become intersections.
        for k in keys:
            constraints = [f[k] for f in subsubframes if f.defined(k)]
            if len(constraints) > 0:
                subframe[k] = intersection(*constraints)

        return boolean, subframe

    def generate(self, args):
        return "(" + " and ".join(x.generate() for x in args) + ")"

table[And.name] = And()

class Or(typingtree.BuiltinFunction):
    name = "or"

    def commutative(self):
        return True

    def literaleval(self, args):
        return any(args)

    def retschema(self, frame, args):
        subframe = frame.fork()
        subsubframes = []
        keys = None

        for arg in args:
            t, subsubframe = arg.retschema(subframe)
            if not isinstance(t, Boolean):
                return impossible("All arguments must be boolean."), frame
            subsubframes.append(subsubframe)
            if keys is None:
                keys = subsubframe.keys(subframe)
            else:
                # Only apply a constraint if it is mentioned in all arguments of the 'or'.
                keys = keys.intersection(subsubframe.keys(subframe))

        # 'or' constraints become unions.
        for k in keys:
            subframe[k] = union(*[f[k] for f in subsubframes])
                    
        return boolean, subframe

    def generate(self, args):
        return "(" + " or ".join(x.generate() for x in args) + ")"

table[Or.name] = Or()

class Not(typingtree.BuiltinFunction):
    name = "not"

    def literaleval(self, args):
        return not args

    def retschema(self, frame, args):
        if not isinstance(args[0].retschema(frame)[0], Boolean):
            return impossible("Argument must be boolean."), frame
        else:
            return boolean, frame

table[Not.name] = Not()

class If(typingtree.BuiltinFunction):
    name = "if"

    def retschema(self, frame, args):
        predicates = args[0::3]
        antipredicates = args[1::3]
        consequents = args[2::3]
        alternate = args[-1]

        topframe = frame.fork()
        subframe = topframe
        outtypes = []
        for predicate, antipredicate, consequent in zip(predicates, antipredicates, consequents):
            try:
                pschema, pframe = predicate.retschema(subframe)
            except FemtocodeError as err:
                raise FemtocodeError("Error in \"if\" predicate. " + str(err))
            if not isinstance(pschema, Boolean):
                complain("\"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(pschema.retschema(frame)[0], prefix="    "))), predicate.original)

            try:
                aschema, aframe = antipredicate.retschema(subframe)
            except FemtocodeError as err:
                raise FemtocodeError("Error while negating \"if\" predicate. " + str(err))
            if not isinstance(pschema, Boolean):
                complain("Negation of \"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(aschema.retschema(frame)[0], prefix="    "))), predicate.original)

            schema, subsubframe = consequent.retschema(pframe)
            outtypes.append(schema)

            subframe = aframe

        schema, subsubframe = alternate.retschema(subframe)
        outtypes.append(schema)

        return union(*outtypes), topframe

    def generate(self, args):
        predicates = args[0::3]
        consequents = args[2::3]
        alternate = args[-1]
        return " else ".join("if ({0}) {{{1}}}".format(p.generate(), c.generate()) for p, c in zip(predicates, consequents)) + " else {" + alternate.generate() + "}"
            
table[If.name] = If()

class Map(typingtree.BuiltinFunction):
    name = ".map"
            
    def arity(self, index):
        if index == 1:
            return 1
        else:
            return None

    def retschema(self, frame, args):
        if len(args) != 2:
            return impossible("Exactly two arguments required."), frame

        targ0 = args[0].retschema(frame)[0]
        if not isinstance(targ0, Collection):
            return impossible("First argument must be a collection."), frame

        if not isinstance(args[1], Function):
            return impossible("Second argument must be a function."), frame

        return collection(args[1].retschema(frame, [typingtree.Placeholder(targ0.items)])[0]), frame

    def generate(self, args):
        return args[0].generate() + "(" + args[1].generate() + ")"

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, ["fcn"], [None])

table[Map.name] = Map()
