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

    def __init__(self, name, framenumber, schema, original=None):
        self.name = name
        self.framenumber = framenumber
        self.schema = schema
        self.original = original

    def __repr__(self):
        return "Ref({0}, {1}, {2})".format(self.name, self.framenumber, self.schema)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.order == other.order:
                if self.name == other.name:
                    if self.framenumber == other.framenumber:
                        return self.schema < other.schema
                    else:
                        return self.framenumber < other.framenumber
                elif isinstance(self.name, int) and isinstance(other.name, int):
                    return self.name < other.name
                elif isinstance(self.name, string_types) and isinstance(other.name, string_types):
                    return self.name < other.name
                else:
                    return True
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        return other.__class__ == Ref and self.name == other.name and self.framenumber == other.framenumber and self.schema == other.schema

    def __hash__(self):
        return hash((Ref, self.name, self.framenumber, self.schema))

class Literal(lispytree.Literal):
    order = 1

    def __init__(self, value, schema, original=None):
        self.value = value
        self.schema = schema
        self.original = original

    def __repr__(self):
        return "Literal({0}, {1})".format(self.value, self.schema)

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

    def __init__(self, fcn, args, schema, original=None):
        self.fcn = fcn
        self.args = tuple(args)
        self.schema = schema
        self.original = original

    def __repr__(self):
        return "Call({0}, {1}, {2})".format(self.fcn, self.args, self.schema)

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

    def __init__(self, refs, framenumber, body, schema, original=None):
        self.refs = tuple(refs)
        self.framenumber = framenumber
        self.body = body
        self.schema = schema
        self.original = original

    def __repr__(self):
        return "UserFunction({0}, {1}, {2}, {3})".format(self.refs, self.framenumber, self.body, self.schema)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.order == other.order:
                if self.refs == other.refs:
                    if self.framenumber == other.framenumber:
                        if self.body == other.body:
                            return self.schema < other.schema
                        else:
                            return self.body < other.body
                    else:
                        return self.framenumber < other.framenumber
                else:
                    return self.refs < other.refs
            else:
                return self.order < other.order
        else:
            return True

    def __eq__(self, other):
        return other.__class__ == UserFunction and self.refs == other.refs and self.framenumber == other.framenumber and self.body == other.body and self.schema == other.schema

    def __hash__(self):
        return hash((UserFunction, self.refs, self.framenumber, self.body, self.schema))

def buildUserFunction(fcn, schemas, frame):
    if len(fcn.names) != len(schemas):
        raise ProgrammingError("UserFunction takes a different number of parameters ({0}) than the arguments passed ({1})".format(len(fcn.names), len(schemas)))

    refs = [Ref(n, fcn.framenumber, s) for n, s in zip(fcn.names, schemas)]
    body = build(fcn.body, frame.fork(dict((lispytree.Ref(n, fcn.framenumber), s) for n, s in zip(fcn.names, schemas))))[0]
    return UserFunction(refs, fcn.framenumber, body, body.schema, fcn.original)

def build(tree, frame):
    if isinstance(tree, lispytree.Ref):
        if frame.defined(tree):
            return Ref(tree.name, tree.framenumber, frame[tree], tree.original), frame
        else:
            raise ProgrammingError("{0} was defined when building lispytree but is not defined when building typedtree".format(tree))
        
    elif isinstance(tree, lispytree.Literal):
        return Literal(tree.value, tree.schema, tree.original), frame

    elif isinstance(tree, lispytree.Call):
        if not isinstance(tree.fcn, lispytree.BuiltinFunction):
            raise ProgrammingError("only BuiltinFunctions should directly appear in lispytree.Call: {0}".format(tree))

        schema, typedargs, subframe = tree.fcn.buildtyped(tree.args, frame)

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

        return Call(tree.fcn, typedargs, schema, tree.original), subframe

    else:
        raise ProgrammingError("unexpected in lispytree: {0}".format(tree))

########################################

def toStatements(tree, statements, replacements, number):
    if isinstance(tree, Ref):
        if tree.framenumber is None:
            replacements[tree] = tree

    elif isinstance(tree, Literal):
        replacements[tree] = tree

    elif isinstance(tree, Call):
        number = tree.fcn.toStatements(tree, statements, replacements, number)

    else:
        raise ProgrammingError("unexpected in typedtree: {0}".format(tree))        

    return number







########################################

def fillUniquesSet(tree, uniques):
    uniques[tree] = tree
    if isinstance(tree, Call):
        for arg in tree.args:
            fillUniquesSet(arg, uniques)
    elif isinstance(tree, UserFunction):
        fillUniquesSet(tree.body, uniques)

def treeOfUniques(tree, uniques):
    if isinstance(tree, (Ref, Literal)):
        return uniques[tree]

    elif isinstance(tree, Call):
        out = uniques[tree]
        out.args = [treeOfUniques(arg, uniques) for arg in out.args]
        return out

    elif isinstance(tree, UserFunction):
        out = uniques[tree]
        out.body = treeOfUniques(out.body, uniques)
        return out

    else:
        raise ProgrammingError("unexpected in typedtree: {0}".format(tree))

def assignDependencies(tree, framenumberToDeps=None):
    if framenumberToDeps is None:
        framenumberToDeps = {}

    if not hasattr(tree, "dependencies"):
        if isinstance(tree, Ref):
            if tree.framenumber in framenumberToDeps:
                tree.dependencies = set(framenumberToDeps[tree.framenumber])
            else:
                tree.dependencies = set([tree])

        elif isinstance(tree, Literal):
            tree.dependencies = set([tree])

        elif isinstance(tree, Call):
            dependencies = set()

            for arg in tree.args:
                if not isinstance(arg, UserFunction):
                    assignDependencies(arg, framenumberToDeps)
                    dependencies.update(arg.dependencies)

            for arg in tree.args:
                if isinstance(arg, UserFunction):
                    framenumberToDeps[arg.framenumber] = dependencies
                    assignDependencies(arg.body, framenumberToDeps)
                    dependencies.update(arg.body.dependencies)

            tree.dependencies = dependencies

        else:
            raise ProgrammingError("unexpected in typedtree: {0}".format(tree))        

def assignLevels(tree, base=()):
    if not hasattr(tree, "level"):
        if isinstance(tree, Ref) and tree.framenumber is None:
            tree.level = ()

        elif isinstance(tree, Ref):
            tree.level = base

        elif isinstance(tree, Literal):
            tree.level = ()

        elif isinstance(tree, Call):
            tree.level = tree.fcn.level(tree.args, base)

        else:
            raise ProgrammingError("unexpected in typedtree: {0}".format(tree))        

    return tree.level
