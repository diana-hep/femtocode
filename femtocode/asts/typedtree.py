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

from femtocode.asts import lispytree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

class TypedTree(object):
    pass

class Ref(lispytree.Ref):
    order = 0

    def __init__(self, identifier, schema, dependencies=None, original=None):
        self.identifier = identifier
        self.schema = schema
        self.dependencies = dependencies
        self.original = original

    def __repr__(self):
        return "Ref({0}, {1}, {2})".format(self.identifier, self.schema, self.dependencies)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.order == other.order:
                if self.identifier == other.identifier:
                    return self.schema < other.schema
                else:
                    return self.identifier < other.identifier
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        return other.__class__ == Ref and self.identifier == other.identifier and self.schema == other.schema

    def __hash__(self):
        return hash((Ref, self.identifier, self.schema))

class Literal(lispytree.Literal):
    order = 1

    def __init__(self, value, schema, dependencies=None, original=None):
        self.value = value
        self.schema = schema
        self.dependencies = dependencies
        self.original = original

    def __repr__(self):
        return "Literal({0}, {1}, {2})".format(self.value, self.schema, self.dependencies)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.order == other.order:
                if self.schema == other.schema:
                    return self.value < other.value
                else:
                    return self.schema < other.schema
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        return other.__class__ == Literal and self.value == other.value and self.schema == other.schema

    def __hash__(self):
        return hash((Literal, self.value, self.schema))
    
class Call(lispytree.Call):
    order = 2

    def __init__(self, fcn, args, schema, dependencies=None, original=None):
        self.fcn = fcn
        self.args = args
        self.schema = schema
        self.dependencies = dependencies
        self.original = original

    def __repr__(self):
        return "Call({0}, {1}, {2}, {3})".format(self.fcn, self.args, self.schema, self.dependencies)

    def commuteargs(self):
        if self.fcn.commutative():
            return tuple(sorted(self.args))
        else:
            return self.args

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.order == other.order:
                if self.fcn == other.fcn:
                    if self.args == other.args:
                        return self.schema < other.schema
                    else:
                        return self.commuteargs() < other.commuteargs()
                else:
                    return self.fcn < other.fcn
            else:
                return self.order == other.order
        else:
            return True

    def __eq__(self, other):
        return other.__class__ == Call and self.fcn == other.fcn and self.commuteargs() == other.commuteargs() and self.schema == other.schema

    def __hash__(self):
        return hash((Call, self.fcn, self.commuteargs(), self.schema))

class UserFunction(lispytree.UserFunction):
    order = 3

    def __init__(self, refs, body, schema, dependencies=None, original=None):
        self.refs = refs
        self.body = body
        self.schema = schema
        self.dependencies = dependencies
        self.original = original

    def __repr__(self):
        return "UserFunction({0}, {1}, {2}, {3})".format(self.refs, self.body, self.schema, self.dependencies)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.order == other.order:
                if self.refs == other.refs:
                    if self.body == other.body:
                        return self.schema < other.schema
                    else:
                        return self.body < other.body
                else:
                    return self.refs < other.refs
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        return other.__class__ == UserFunction and self.refs == other.refs and self.body == other.body and self.schema == other.schema

    def __hash__(self):
        return hash((UserFunction, self.refs, self.body, self.schema))

def buildUserFunction(fcn, schemas, frame, depth):
    if len(fcn.names) != len(schemas):
        raise ProgrammingError("UserFunction takes a different number of parameters ({0}) than the arguments passed ({1})".format(len(fcn.names), len(schemas)))

    refs = [Ref((n, depth), s, None) for n, s in zip(fcn.names, schemas)]
    body = build(fcn.body, frame.fork(dict((lispytree.Ref(n), s) for n, s in zip(fcn.names, schemas))), depth + 1)[0]
    return UserFunction(refs, body, body.schema, None, fcn.original)

def build(tree, frame, depth=0):
    if isinstance(tree, lispytree.Ref):
        if frame.defined(tree):
            return Ref((tree.name, depth), frame[tree], None, tree.original), frame
        else:
            raise ProgrammingError("{0} was defined when building lispytree but is not defined when building typedtree".format(self))
        
    elif isinstance(tree, lispytree.Literal):
        return Literal(tree.value, tree.schema, None, tree.original), frame

    elif isinstance(tree, lispytree.Call):
        if not isinstance(tree.fcn, lispytree.BuiltinFunction):
            raise ProgrammingError("only BuiltinFunctions should directly appear in lispytree.Call: {0}".format(tree))

        schema, typedargs, subframe = tree.fcn.buildTyped(tree.args, frame, depth)

        if isinstance(schema, Impossible):
            if tree.fcn.name == "is":
                complain(schema.reason, tree.original)
            else:
                if schema.reason is not None:
                    reason = "\n\n    " + schema.reason
                else:
                    reason = ""
                complain("Function \"{0}\" does not accept arguments with the given types:\n\n    {0}({1}){2}".format(tree.fcn.name, ",\n    {0} ".format(" " * len(tree.fcn.name)).join(pretty(x.schema, prefix="     " + " " * len(tree.fcn.name)).lstrip() for x in typedargs), reason), tree.original)

        for expr, t in subframe.itemsHere():
            if isinstance(t, Impossible):
                if t.reason is not None:
                    reason = "\n\n    " + t.reason
                else:
                    reason = ""
                complain("Function \"{0}\" puts impossible constraints on {1}:\n\n    {0}({2}){3}".format(tree.fcn.name, expr.generate(), ",\n    {0} ".format(" " * len(tree.fcn.name)).join(pretty(x.schema, prefix="     " + " " * len(tree.fcn.name)).lstrip() for x in typedargs), reason), tree.original)

        if frame.defined(tree):
            schema = intersection(frame[tree], schema)
            if isinstance(schema, Impossible):
                if schema.reason is not None:
                    reason = "\n\n    " + schema.reason
                else:
                    reason = ""
                complain("Expression {0} previously constrained to be\n\n{1}\n    but new constraints on its arguments are incompatible with that.\n\n    {2}({3}){4}".format(tree.generate(), pretty(frame[tree], prefix="        "), tree.fcn.name, ",\n    {0} ".format(" " * len(tree.fcn.name)).join(pretty(x.schema, prefix="     " + " " * len(tree.fcn.name)).lstrip() for x in typedargs), reason), tree.original)

            subframe[tree] = schema

        return Call(tree.fcn, tree.args, schema, None, tree.original), subframe

    else:
        raise ProgrammingError("unexpected in lispytree: {0}".format(tree))
