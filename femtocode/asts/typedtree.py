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

class SimpleRef(lispytree.Ref):
    order = 0

    def __init__(self, schema, name, original=None):
        self.schema = schema
        super(SimpleRef, self).__init__(name, original)

    def __repr__(self):
        return "SimpleRef({0}, {1})".format(self.schema, self.name)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if isinstance(other, SimpleRef):
                if self.schema == other.schema:
                    return self.name < other.name
                else:
                    return self.schema < other.schema
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, SimpleRef):
            return self.schema == other.schema and self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash((SimpleRef, self.name, self.schema))

class EmbeddedRef(lispytree.Ref):
    order = 1

    def __init__(self, schema, name, caller, callargs, original=None):
        self.schema = schema
        self.caller = caller
        self.callargs = tuple(callargs)
        super(EmbeddedRef, self).__init__(name, original)

    def __repr__(self):
        return "EmbeddedRef({0}, {1}, {2}, {3})".format(self.schema, self.caller, self.callargs, self.name)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if isinstance(other, EmbeddedRef):
                if self.schema == other.schema:
                    if self.name == other.name:
                        if self.caller == other.caller:
                            return self.callargs < other.callargs
                        else:
                            return self.caller < other.caller
                    else:
                        return self.name < other.name
                else:
                    return self.schema < other.schema
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, EmbeddedRef):
            return self.schema == other.schema and self.name == other.name and self.caller == other.caller and self.callargs == other.callargs
        else:
            return False

    def __hash__(self):
        return hash((EmbeddedRef, self.schema, self.name, self.caller, self.callargs))

class Literal(lispytree.Literal):
    order = 2

    def __init__(self, schema, value, original=None):
        self.schema = schema
        super(Literal, self).__init__(value, original)

    def __repr__(self):
        return "Literal({0}, {1})".format(self.schema, self.value)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if isinstance(other, Literal):
                if self.schema == other.schema:
                    return self.value < other.value
                else:
                    return self.schema < other.schema
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, Literal):
            return self.schema == other.schema and self.value == other.value
        else:
            return False

    def __hash__(self):
        return hash((Literal, self.schema, self.value))
    
class Call(lispytree.Call):
    order = 3

    def __init__(self, schema, fcn, args, original=None):
        self.schema = schema
        super(Call, self).__init__(fcn, args, original)

    def __repr__(self):
        return "Call({0}, {1}, {2})".format(self.schema, self.fcn, self.args)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if isinstance(other, Call):
                if self.schema == other.schema:
                    if self.fcn == other.fcn:
                        return self.args < other.args
                    else:
                        return self.fcn < other.fcn
                else:
                    return self.schema < other.schema
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, Call):
            return self.schema == other.schema and self.fcn == other.fcn and self.args == other.args
        else:
            return False

    def __hash__(self):
        return hash((Call, self.schema, self.fcn, self.sortedargs()))

class UserFunction(lispytree.UserFunction):
    order = 4

    def __init__(self, schema, refs, body, original=None):
        self.schema = schema
        self.refs = refs
        self.body = body
        self.original = original

    def __repr__(self):
        return "UserFunction({0}, {1}, {2})".format(self.schema, self.refs, self.body)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if isinstance(other, UserFunction):
                if self.schema == other.schema:
                    if self.refs == other.refs:
                        return self.body < other.body
                    else:
                        return self.refs < other.refs
                else:
                    return self.schema < other.schema
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, UserFunction):
            return self.schema == other.schema and self.refs == other.refs and self.body == other.body
        else:
            return False

    def __hash__(self):
        return hash((UserFcn, self.schema, self.refs, self.body))

def buildUserFunction(fcn, schemas, caller, callargs, frame):
    if len(fcn.names) != len(schemas):
        raise ProgrammingError("UserFunction takes a different number of parameters ({0}) than the arguments passed ({1})".format(len(fcn.names), len(schemas)))

    refs = [EmbeddedRef(s, n, caller, callargs) for n, s in zip(fcn.names, schemas)]
    body = build(fcn.body, frame.fork(dict((lispytree.Ref(n), s) for n, s in zip(fcn.names, schemas))))[0]
    return UserFunction(body.schema, refs, body, fcn.original)

def build(tree, frame):
    if isinstance(tree, lispytree.Ref):
        if frame.defined(tree):
            return SimpleRef(frame[tree], tree.name, tree.original), frame
        else:
            raise ProgrammingError("{0} was defined when building lispytree but is not defined when building typedtree".format(self))
        
    elif isinstance(tree, lispytree.Literal):
        return Literal(tree.schema, tree.value, tree.original), frame

    elif isinstance(tree, lispytree.Call):
        if isinstance(tree.fcn, UserFunction):
            raise ProgrammingError("UserFunctions should not directly appear in lispytree.Call: {0}".format(tree))

        schema, typedargs, subframe = tree.fcn.buildTyped(tree.args, frame)

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

        return Call(schema, tree.fcn, tree.args, tree.original), subframe

    else:
        raise ProgrammingError("unexpected in lispytree: {0}".format(tree))
