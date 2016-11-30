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
from femtocode.asts import columnartree
from femtocode.defs import *
from femtocode.typesystem import *

table = SymbolTable()

class Is(lispytree.BuiltinFunction):
    name = "is"

    def literaleval(self, args):
        return True

    def getschema(self, args, frame):
        fromtype = args[0].getschema(frame)[0]
        totype = args[1].value   # literal type expression
        negate = args[2].value   # literal boolean

        if negate:
            out = difference(fromtype, totype)
        else:
            out = intersection(fromtype, totype)
        if isinstance(out, Impossible):
            return impossible("Cannot constrain type:\n\n{0}".format(compare(fromtype, totype, header=("from", "excluding" if negate else "to"), between=lambda t1, t2: "|", prefix="    ")), out.reason), frame

        return boolean, frame.fork({args[0]: out})
        
    def generate(self, args):
        return "({0} is {1})".format(args[0].generate(), repr(args[1].value))

table[Is.name] = Is()

class Add(lispytree.BuiltinFunction):
    name = "+"

    def commutative(self):
        return True

    def literaleval(self, args):
        return sum(args)
        
    def getschema(self, args, frame):
        return inference.add(args[0].getschema(frame)[0], args[1].getschema(frame)[0]), frame
        
    def generate(self, args):
        return "({0} + {1})".format(args[0].generate(), args[1].generate())

table[Add.name] = Add()

class Eq(lispytree.BuiltinFunction):
    name = "=="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] == args[1]

    def getschema(self, args, frame):
        out = intersection(args[0].getschema(frame)[0], args[1].getschema(frame)[0])
        if isinstance(out, Impossible):
            return impossible("The argument types have no overlap (values can never be equal)."), frame
        else:
            return boolean, frame.fork({args[0]: out, args[1]: out})

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[Eq.name] = Eq()

class NotEq(lispytree.BuiltinFunction):
    name = "!="

    def commutative(self):
        return True

    def literaleval(self, args):
        return args[0] != args[1]

    def getschema(self, args, frame):
        const = None
        expr = None
        if isinstance(args[0], lispytree.Literal):
            const = args[0].value
            expr = args[1]
        elif isinstance(args[1], lispytree.Literal):
            const = args[1].value
            expr = args[0]

        if expr is not None:
            subframe = frame.fork({expr: inference.literal(expr.getschema(frame)[0], "!=", const)})
            if isinstance(subframe[expr], Impossible):
                return impossible("Expression {0} has only one value at {1} (can never be unequal).".format(expr.generate(), const))
        else:
            subframe = frame.fork()

        return boolean, subframe

    def generate(self, args):
        return "({0} == {1})".format(args[0].generate(), args[1].generate())

table[NotEq.name] = NotEq()

class And(lispytree.BuiltinFunction):
    name = "and"

    def commutative(self):
        return True

    def literaleval(self, args):
        return all(args)
        
    def getschema(self, args, frame):
        subframe = frame.fork()
        subsubframes = []
        keys = set()

        for arg in args:
            t, subsubframe = arg.getschema(subframe)
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
                        # error message) below in arg.getschema(tmpframe).
                        tmpframe[k] = constraint

            # Check the type again, this time with all others as preconditions (regarless of order).
            if not isinstance(arg.getschema(tmpframe)[0], Boolean):
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

class Or(lispytree.BuiltinFunction):
    name = "or"

    def commutative(self):
        return True

    def literaleval(self, args):
        return any(args)

    def getschema(self, args, frame):
        subframe = frame.fork()
        subsubframes = []
        keys = None

        for arg in args:
            t, subsubframe = arg.getschema(subframe)
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

class Not(lispytree.BuiltinFunction):
    name = "not"

    def literaleval(self, args):
        return not args

    def getschema(self, args, frame):
        if not isinstance(args[0].getschema(frame)[0], Boolean):
            return impossible("Argument must be boolean."), frame
        else:
            return boolean, frame

table[Not.name] = Not()

class If(lispytree.BuiltinFunction):
    name = "if"

    def getschema(self, args, frame):
        predicates = args[:-1][0::3]
        antipredicates = args[:-1][1::3]
        consequents = args[:-1][2::3]
        alternate = args[-1]

        topframe = frame.fork()
        subframe = topframe
        outtypes = []
        for index, (predicate, antipredicate, consequent) in enumerate(zip(predicates, antipredicates, consequents)):
            try:
                pschema, pframe = predicate.getschema(subframe)
            except FemtocodeError as err:
                raise FemtocodeError("Error in \"if\" predicate. " + str(err))
            if not isinstance(pschema, Boolean):
                complain("\"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(pschema.getschema(frame)[0], prefix="    "))), predicate.original)

            try:
                aschema, aframe = antipredicate.getschema(subframe)
            except FemtocodeError as err:
                if index == len(predicates) - 1:
                    which = "\"else\""
                else:
                    which = "\"elif\""
                raise FemtocodeError("Error while negating predicate for {0} clause. {1}".format(which, str(err)))
            if not isinstance(pschema, Boolean):
                complain("Negation of \"if\" predicate must be boolean, not\n\n{0}\n".format(",\n".join(pretty(aschema.getschema(frame)[0], prefix="    "))), predicate.original)

            schema, subsubframe = consequent.getschema(pframe)
            outtypes.append(schema)

            subframe = aframe

        schema, subsubframe = alternate.getschema(subframe)
        outtypes.append(schema)

        return union(*outtypes), topframe

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

    def getschema(self, args, frame):
        if len(args) != 2:
            return impossible("Exactly two arguments required."), frame

        targ0 = args[0].getschema(frame)[0]
        if not isinstance(targ0, Collection):
            return impossible("First argument must be a collection."), frame

        if not isinstance(args[1], Function):
            return impossible("Second argument must be a function."), frame

        return collection(args[1].getschema([lispytree.Placeholder(targ0.items)], frame)[0]), frame

    def generate(self, args):
        return args[0].generate() + "(" + args[1].generate() + ")"

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, ["fcn"], [None])

table[Map.name] = Map()
