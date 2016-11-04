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

import femtocode.parser
from femtocode.py23 import *

def complain(message, p):
    femtocode.parser.complain(message, p.source, p.pos, p.lineno, p.col_offset, p.sourceName, 1)

class ProgrammingError(Exception): pass   # my mistake, not the user's; user should NEVER see this  :)
class FemtocodeError(Exception): pass     # error in the user's Femtocode

class Function(object):
    def commutative(self):
        return False

    def arity(self, index):
        return None

    def typeConstraints(self, frame, args, negation=False):
        return {}

    def retschema(self, types, args):
        raise ProgrammingError("missing implementation")

    def sortargs(self, positional, named):
        if len(named) > 0:
            raise ProgrammingError(self.name + " function shouldn't get named arguments")
        return positional

    @staticmethod
    def sortargsWithNames(positional, named, names, defaults):
        positional = list(reversed(positional))
        named = dict(named.items())
        out = []

        for name, default in zip(names, defaults):
            if name in named:
                out.append(named.pop(name))
            elif len(positional) > 0:
                out.append(positional.pop())
            elif default is not None:
                out.append(default)
            else:
                raise TypeError("too few arguments: missing \"{0}\"".format(name))
        if len(named) > 0:
            raise TypeError("unrecognized named arguments: " + ", ".join("\"" + x + "\"" for x in named))
        if len(positional) > 0:
            raise TypeError("too many positional arguments")
        return out

class BuiltinFunction(Function):
    order = 0

    def __repr__(self):
        return "BuiltinFunction[\"" + self.name + "\"]"

    def __lt__(self, other):
        if isinstance(other, BuiltinFunction):
            return self.name < other.name
        else:
            return self.order < other.order

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)

class UserFunction(Function):
    order = 1

    def __init__(self, names, defaults, body):
        self.names = tuple(names)
        self.defaults = tuple(defaults)
        self.body = body

    def __repr__(self):
        return "UserFunction({0}, {1}, {2})".format(self.names, self.defaults, self.body)

    def __lt__(self, other):
        if isinstance(other, UserFunction):
            if self.names == other.names:
                if self.defaults == defaults:
                    return self.body < other.body
                else:
                    return self.defaults < other.defaults
            else:
                return self.names < other.names
        else:
            return self.order < other.order

    def __eq__(self, other):
        if not isinstance(other, UserFunction):
            return False
        else:
            return self.names == other.names and self.defaults == other.defaults and self.body == other.body

    def __hash__(self):
        return hash((UserFunction, self.names, self.defaults, self.body))

    def arity(self, index):
        return None

    def retschema(self, types, args):
        subframe = types.fork()
        for name, arg in zip(self.names, args):
            subframe[name] = arg.schema(types)
        return self.body.schema(subframe)

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, self.names, self.defaults)
        
class SymbolTable(object):
    def __init__(self, values={}, parent=None):
        if isinstance(parent, dict):
            raise Exception

        self.parent = parent
        self.values = dict(values.items())

    def __repr__(self):
        if self.parent is None:
            return "SymbolTable({0})".format(self.values)
        else:
            return "SymbolTable({0}, {1})".format(self.values, repr(self.parent))

    def fork(self, values={}):
        return SymbolTable(values, self)

    def definedHere(self, x):
        return x in self.values

    def lenHere(self):
        return len(self.values)

    def itemsHere(self):
        return self.values.items()

    def defined(self, x):
        if self.definedHere(x):
            return True
        elif self.parent is not None:
            return self.parent.defined(x)
        else:
            return False

    def getHere(self, x, default=None):
        trial = self.values.get(x)
        if trial is not None:
            return trial
        else:
            return default

    def get(self, x, default=None):
        trial = self.getHere(x)
        if trial is not None:
            return trial
        elif self.parent is not None:
            return self.parent.get(x, default)
        else:
            return default

    def __setitem__(self, x, y):
        self.values[x] = y

    def __getitem__(self, x):
        out = self.get(x)
        if out is None:
            raise ProgrammingError("symbol \"{0}\" is required but is not in the SymbolTable".format(x))
        return out
