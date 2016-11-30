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
    def __init__(self, schema, name, original=None):
        self.schema = schema
        super(Ref, self).__init__(name, original)

    def __repr__(self):
        return "Ref({0}, {1})".format(self.schema, self.name)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.schema == other.schema:
                return super(Ref, self).__lt__(other)
            else:
                return self.schema < other.schema
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, TypedTree):
            return self.schema == other.schema and super(Ref, self).__eq__(other)
        else:
            return False

    def __hash__(self):
        return hash((self.order, self.name, self.schema))

class Literal(lispytree.Literal):
    def __init__(self, schema, value, original=None):
        self.schema = schema
        super(Literal, self).__init__(value, original)

    def __repr__(self):
        return "Literal({0}, {1})".format(self.schema, self.value)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.schema == other.schema:
                return super(Literal, self).__lt__(other)
            else:
                return self.schema < other.schema
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, TypedTree):
            return self.schema == other.schema and super(Literal, self).__eq__(other)
        else:
            return False

    def __hash__(self):
        return hash((self.order, self.value, self.schema))
    
class Call(lispytree.Call):
    def __init__(self, schema, fcn, args, original=None):
        self.schema = schema
        super(Call, self).__init__(fcn, args, original)

    def __repr__(self):
        return "Call({0}, {1}, {2})".format(self.schema, self.fcn, self.args)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.schema == other.schema:
                return super(Call, self).__lt__(other)
            else:
                return self.schema < other.schema
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, TypedTree):
            return self.schema == other.schema and super(Call, self).__eq__(other)
        else:
            return False

    def __hash__(self):
        return hash((self.order, self.fcn, self.sortedargs(), self.schema))

class UserFunction(lispytree.UserFunction):
    def __init__(self, schema, refs, body, original=None):
        self.schema = schema
        self.refs = refs
        self.body = body
        self.original = original

    def __repr__(self):
        return "UserFunction({0}, {1}, {2})".format(self.schema, self.refs, self.body)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.schema == other.schema:
                if isinstance(other, UserFunction):
                    if self.refs == other.refs:
                        return self.body < other.body
                    else:
                        return self.refs < other.refs
                else:
                    return self.order < other.order
            else:
                return self.schema < other.schema
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, UserFunction):
            return self.schema == other.schema and self.refs == other.refs and self.body == other.body
        else:
            return False

    def __hash__(self):
        return hash((self.order, self.refs, self.body, self.schema))

def buildUserFunction(fcn, schemas, frame):
    if len(fcn.names) != len(schemas):
        raise ProgrammingError("UserFunction takes a different number of parameters ({0}) than the arguments passed ({1})".format(len(fcn.names), len(schemas)))

    refs = [Ref(s, n) for n, s in zip(fcn.names, schemas)]
    body = build(fcn.body, frame.fork(dict((lispytree.Ref(n), s) for n, s in zip(fcn.names, schemas))))[0]
    return UserFunction(body.schema, refs, body, fcn.original)

def build(tree, frame):
    if isinstance(tree, lispytree.Ref):
        if frame.defined(tree):
            return Ref(frame[tree], tree.name, tree.original), frame
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
