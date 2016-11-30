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
    if p is None:
        raise FemtocodeError(message)
    else:
        femtocode.parser.complain(message, p.source, p.pos, p.lineno, p.col_offset, p.sourceName, 1)

ProgrammingError = femtocode.parser.ProgrammingError
FemtocodeError = femtocode.parser.FemtocodeError

class Function(object):
    def commutative(self):
        return False

    def arity(self, index):
        return None

    def constrain(self, frame, args):
        return {}

    def retschema(self, frame, args):
        raise ProgrammingError("missing implementation")

    def sortargs(self, positional, named):
        if len(named) > 0:
            raise ProgrammingError("{0} function shouldn't get named arguments".format(self.name))
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
                raise TypeError("Too few arguments: missing \"{0}\".".format(name))
        if len(named) > 0:
            raise TypeError("Unrecognized named arguments: {0}.".format(", ".join("\"" + x + "\"" for x in named)))
        if len(positional) > 0:
            raise TypeError("Too many positional arguments.")
        return out

class SymbolTable(object):
    def __init__(self, values={}, parent=None):
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

    def keys(self, exclude=None):
        out = set(self.values.keys())
        if self.parent is not None and self.parent is not exclude:
            return out.union(self.parent.keys(exclude))
        else:
            return out

    def defined(self, x, exclude=None):
        if self.definedHere(x):
            return True
        elif self.parent is not None and self.parent is not exclude:
            return self.parent.defined(x, exclude)
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
