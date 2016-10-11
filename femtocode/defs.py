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
    femtocode.parser.complain(message, p.source, p.pos, p.lineno, p.col_offset, p.fileName, 1)

class ProgrammingError(Exception): pass

class BuiltinFunction(object):
    def name(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.name() + "()"

    def argschema(self, index, args):
        raise ProgrammingError("missing implementation")

    def retschema(self, args):
        raise ProgrammingError("missing implementation")

    def sortargs(self, positional, named):
        raise ProgrammingError("missing implementation")

class SymbolTable(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def fork(self, **init):
        out = SymbolTable(self)
        for name, value in init.items():
            out[name] = value
        return out

    def getHere(self, name, default=None):
        trial = self.symbols.get(name)
        if trial is not None:
            return trial
        else:
            return default

    def get(self, name, default=None):
        trial = self.getHere(name)
        if trial is not None:
            return trial
        elif self.parent is not None:
            return self.parent.get(name, default)
        else:
            return default

    def __setitem__(self, name, value):
        self.symbols[name] = value

    def __getitem__(self, name):
        out = self.get(name)
        if out is None:
            raise ProgrammingError("symbol \"{0}\" is absolutely required but is not in the SymbolTable".format(name))
        return out


# class BuiltinFunction(object):
#     def name(self):
#         return self.__class__.__name__

#     def __repr__(self):
#         return self.name() + "()"

#     def sortArgs(self, positional, named):
#         raise ProgrammingError("missing implementation")

#     def typify(self, tree, typifyTree, **options):
#         raise ProgrammingError("missing implementation")

# class ParameterSymbol(object):
#     def __init__(self, name):
#         self.name = name

#     def __repr__(self):
#         return "ParameterSymbol({0})".format(self.name)

# class SymbolTable(object):
#     def __init__(self, parent=None):
#         self.parent = parent
#         self.symbols = {}

#     def definedHere(self, name):
#         return name in self.symbols

#     def defined(self, name):
#         return self.definedHere(name) or (self.parent is not None and self.parent.defined(name))

#     def getHere(self, name):
#         return self.symbols.get(name)

#     def get(self, name):
#         trial = self.getHere(name)
#         if trial is not None:
#             return trial
#         elif self.parent is not None:
#             return self.parent.get(name)
#         else:
#             return None

#     def append(self, name, value):
#         self.symbols[name] = value

#     def child(self):
#         return SymbolTable(self)
