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
from femtocode.asts import functiontree
from femtocode.defs import *
from femtocode.typesystem import *

table = SymbolTable()

class Add(BuiltinFunction):
    name = "+"

    def commutative(self):
        return True

    def literaleval(self, args):
        return sum(args)
        
    def retschema(self, frame, args):
        return inference.add(*(x.retschema(frame)[0] for x in args)), frame

    def generate(self, args):
        return "(" + " + ".join(x.generate() for x in args) + ")"

table[Add.name] = Add()

class Eq(BuiltinFunction):
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

class And(BuiltinFunction):
    name = "and"

    def commutative(self):
        return True

    def literaleval(self, args):
        return all(args)
        
    def retschema(self, frame, args):
        # subframe = frame.fork()
        # for arg in args:
        #     t, subframe = arg.retschema(subframe)
        #     if not isinstance(t, Boolean):
        #         return impossible("All arguments must be boolean."), frame
        # return boolean, subframe

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
                constraints = [f[k] for f in [subsubframes[j] for j in xrange(len(args)) if i != j] if f.defined(k)]
                if len(constraints) > 0:
                    constraint = intersection(*constraints)
                    if not isinstance(constraint, Impossible):
                        tmpframe[k] = constraint

            if not isinstance(arg.retschema(tmpframe)[0], Boolean):
                return impossible("All arguments must be boolean."), frame
            
        for k in keys:
            constraints = [f[k] for f in subsubframes if f.defined(k)]
            if len(constraints) > 0:
                subframe[k] = intersection(*constraints)

        return boolean, subframe

    def generate(self, args):
        return "(" + " and ".join(x.generate() for x in args) + ")"

table[And.name] = And()

class Or(BuiltinFunction):
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
                keys = keys.intersection(subsubframe.keys(subframe))

        for k in keys:
            subframe[k] = union(*[f[k] for f in subsubframes])
                    
        return boolean, subframe

    def generate(self, args):
        return "(" + " or ".join(x.generate() for x in args) + ")"

table[Or.name] = Or()

class If(BuiltinFunction):
    name = "if"

table[If.name] = If()

class Map(BuiltinFunction):
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

        return collection(args[1].retschema(frame, [functiontree.Placeholder(targ0.items)])[0]), frame

    def generate(self, args):
        return args[0].generate() + "(" + args[1].generate() + ")"

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, ["fcn"], [None])

table[Map.name] = Map()
