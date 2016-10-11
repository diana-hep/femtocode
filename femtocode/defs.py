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
    def __repr__(self):
        return "BuiltinFunction[\"" + self.name + "\"]"

class SymbolTable(object):
    def __init__(self, parent=None, init={}):
        self.parent = parent
        self.symbols = dict(init.items())

    def fork(self, init={}):
        return SymbolTable(self, init)

    def frame(self, name):
        if name in self.symbols:
            return self
        elif self.parent is not None:
            return self.parent.frame(name)
        else:
            return None

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
            raise ProgrammingError("symbol \"{0}\" is required but is not in the SymbolTable".format(name))
        return out
