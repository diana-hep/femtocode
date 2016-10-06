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

from ast import AST
from ast import expr

# Use the Python AST directly
from ast import Add
from ast import And
from ast import Attribute
from ast import BinOp
from ast import BoolOp
from ast import Div
from ast import Eq
from ast import ExtSlice
from ast import FloorDiv
from ast import Gt
from ast import GtE
from ast import In
from ast import Index
from ast import Load
from ast import Lt
from ast import LtE
from ast import Mod
from ast import Mult
from ast import Name
from ast import Not
from ast import NotEq
from ast import NotIn
from ast import Num
from ast import Or
from ast import Pow
from ast import Slice
from ast import Str
from ast import Sub
from ast import Subscript
from ast import Tuple
from ast import UAdd
from ast import USub
from ast import UnaryOp

class Femtocode(AST): pass

class Suite(expr):
    _fields = ("assignments", "expression")
    def __init__(self, assignments, expression, **kwds):
        self.assignments = assignments
        self.expression = expression
        self.__dict__.update(kwds)

