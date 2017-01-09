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

from femtocode.py23 import *

class FemtocodeError(Exception):
    """Error in the user's Femtocode, not the system itself.

    Usually raised within the 'complain' function, which is verbose and informative. May also be directly raised from a schema constructor (no line number to 'complain' about).

    Errors in the system itself raise AssertionErrors.
    """

def complain(message, *args):
    if len(args) == 0 or (len(args) == 1 and args[0] == None):
        raise FemtocodeError(message)
    elif len(args) == 1:
        p, = args
        return complain(message, p.source, p.pos, p.lineno, p.col_offset, p.sourceName, 1)
    else:
        source, pos, lineno, col_offset, sourceName, length = args
        start = source.rfind("\n", 0, pos)
        if start == -1: start = 0
        start = source.rfind("\n", 0, start)
        if start == -1: start = 0
        end = source.find("\n", pos)
        if end == -1:
            snippet = source[start:]
        else:
            snippet = source[start:end]
        snippet = "    " + snippet.replace("\n", "\n    ")
        indicator = "-" * col_offset + "^" * length
        if sourceName == "<string>":
            where = ""
        else:
            where = "in \"" + sourceName + "\""
        raise FemtocodeError("%s\n\nCheck line:col %d:%d (pos %d)%s:\n\n%s\n----%s\n" % (message, lineno, col_offset, pos, where, snippet, indicator))

class Function(object):
    def commutative(self):
        return False

    def arity(self, index):
        return None

    def constrain(self, frame, args):
        return {}

    def sortargs(self, positional, named, original):
        assert len(named) == 0, "{0} function shouldn't get named arguments".format(self.name)
        return positional

    @staticmethod
    def sortargsWithNames(positional, named, names, defaults, original):
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
                complain("Too few arguments: missing \"{0}\".".format(name), original)
        if len(named) > 0:
            complain("Unrecognized named arguments: {0}.".format(", ".join("\"" + x + "\"" for x in named)), original)
        if len(positional) > 0:
            complain("Too many positional arguments.", original)
        return out

class SymbolTable(object):
    def __init__(self, values={}, parent=None):
        self.parent = parent
        self.values = dict(values.items())
        self._framenumber = 0

    def __repr__(self):
        if self.parent is None:
            return "SymbolTable({0})".format(self.values)
        else:
            return "SymbolTable({0}, {1})".format(self.values, repr(self.parent))

    def framenumber(self):
        if hasattr(self, "_framenumber"):
            return self._framenumber
        else:
            return self.parent.framenumber()

    def _framenumber_inc(self):
        if hasattr(self, "_framenumber"):
            self._framenumber += 1
        else:
            self.parent._framenumber_inc()

    def fork(self, values={}):
        self._framenumber_inc()
        out = SymbolTable(values, self)
        del out._framenumber
        return out

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
        assert out is not None, "symbol \"{0}\" is required but is not in the SymbolTable".format(x)
        return out
