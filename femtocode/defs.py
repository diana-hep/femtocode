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

def complain(message, p):
    femtocode.parser.complain(message, p.source, p.pos, p.lineno, p.col_offset, p.sourceName, 1)

class ProgrammingError(Exception): pass   # my mistake, not the user's; user should NEVER see this  :)
class FemtocodeError(Exception): pass     # error in the user's Femtocode

class Function(object):
    def argname(self, index):
        raise ProgrammingError("missing implementation")

    def arity(self, index):
        raise ProgrammingError("missing implementation")

    def retschema(self, symbolFrame, args):
        raise ProgrammingError("missing implementation")

    def sortargs(self, positional, named):
        if len(named) > 0:
            raise ProgrammingError(self.name + " function shouldn't get named arguments")
        return positional

    @staticmethod
    def sortargsWithNames(positional, named, names):
        positional = list(reversed(positional))
        named = dict(named.items())
        out = []
        for name in names:
            if name in named:
                out.append(named.pop(name))
            elif len(positional) > 0:
                out.append(positional.pop())
            else:
                raise TypeError("too few arguments: missing \"{0}\"".format(name))
        if len(named) > 0:
            raise TypeError("unrecognized named arguments: " + ", ".join("\"" + x + "\"" for x in named))
        if len(positional) > 0:
            raise TypeError("too many positional arguments")
        return out

class BuiltinFunction(Function):
    def __repr__(self):
        return "BuiltinFunction[\"" + self.name + "\"]"

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __hash__(self):
        return hash(self.__class__)

class UserFunction(Function):
    def __init__(self, names, defaults, body):
        self.names = tuple(names)
        self.defaults = tuple(defaults)
        self.body = body

    def __repr__(self):
        return "UserFunction({0}, {1}, {2})".format(self.names, self.defaults, self.body)

    def __eq__(self, other):
        if not isinstance(other, UserFunction):
            return False
        else:
            return self.names == other.names and self.defaults == other.defaults and self.body == other.body

    def __hash__(self):
        return hash((UserFunction, self.names, self.defaults, self.body))

    def argname(self, index):
        return self.names[index]

    def arity(self, index):
        return None

    def retschema(self, symbolFrame, args):
        subframe = symbolFrame.fork()
        for name, arg in zip(self.names, args):
            subframe[name] = arg.schema(symbolFrame)
        return self.body.schema(subframe)

    def sortargs(self, positional, named):
        return Function.sortargsWithNames(positional, named, self.names)

class SymbolTable(object):
    def __init__(self, values={}, types={}, parent=None):
        if isinstance(parent, dict):
            raise Exception

        self.parent = parent
        self.values = dict(values.items())
        self.types = dict(types.items())

    def fork(self, values={}, types={}):
        return SymbolTable(values, types, self)

    def definedHere(self, x):
        if isinstance(x, basestring):
            return x in self.values
        else:
            return x in self.types

    def defined(self, x):
        if self.definedHere(x):
            return True
        elif self.parent is not None:
            return self.parent.defined(x)
        else:
            return False

    def getHere(self, x, default=None):
        if isinstance(x, basestring):
            trial = self.values.get(x)
        else:
            trial = self.types.get(x)
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
        if isinstance(x, basestring):
            self.values[x] = y
        else:
            self.types[x] = y

    def __getitem__(self, x):
        out = self.get(x)
        if out is None:
            raise ProgrammingError("symbol \"{0}\" is required but is not in the SymbolTable".format(x))
        return out
