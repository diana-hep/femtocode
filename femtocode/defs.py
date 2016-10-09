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

class BuiltinFunction(object):
    def name(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.name() + "()"

    def sortArgs(self, positional, named):
        raise NotImplementedError

class SymbolTable(object):
    def __init__(self, **symbols):
        self.symbols = symbols

    def __repr__(self):
        return "SymbolTable(" + ", ".join(n + " = " + repr(v) for n, v in sorted(self.symbols.items())) + ")"

    def copy(self):
        return SymbolTable(**self.symbols.copy())

    def append(self, name, value):
        self.symbols[name] = value

    def __add__(self, other):
        if isinstance(other, SymbolTable):
            return SymbolTable(**dict(self.symbols.items() + other.symbols.items()))
        else:
            raise TypeError("cannot add SymbolTable and " + repr(type(other)))
