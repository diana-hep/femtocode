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

from femtocode.asts import parsingtree
from femtocode.defs import BuiltinFunction
from femtocode.py23 import *
from femtocode.typesystem import *

class Ref(object):
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema
    def __repr__(self):
        return "Ref({0}, {1})".format(self.name, self.schema)

class Literal(object):
    def __init__(self, value, schema):
        self.value = value
        self.schema = schema
    def __repr__(self):
        return "Literal({0}, {1})".format(self.value, self.schema)

class Call(object):
    def __init__(self, fcn, args):
        self.fcn = fcn
        self.args = args
    def __repr__(self):
        return "Call({0}, {1})".format(self.fcn, self.args)

class Def(object):
    def __init__(self, params, body):
        self.params = params
        self.body = body
    def __repr__(self):
        return "Def({0}, {1})".format(self.params, self.body)

def convert(parsing, symbols, **options):
    if isinstance(parsing, parsingtree.Add):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.And):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Attribute):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.BinOp):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.BoolOp):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Compare):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Div):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Eq):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.ExtSlice):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.FloorDiv):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Gt):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.GtE):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.In):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Index):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.List):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Load):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Lt):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.LtE):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Mod):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Mult):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Name):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Not):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.NotEq):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.NotIn):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Num):
        if isinstance(parsing.n, float):
            t = Real(min=parsing.n, max=parsing.n)
        elif isinstance(parsing.n, (int, long)):
            t = Integer(min=parsing.n, max=parsing.n)
        else:
            raise TypeError("Num.n is {0}".format(parsing.n))
        return Literal(parsing.n, t)

    elif isinstance(parsing, parsingtree.Or):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Param):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Pow):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Slice):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Store):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Str):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Sub):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Subscript):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Tuple):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.UAdd):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.USub):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.UnaryOp):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Suite):
        if len(parsing.assignments) > 0:
            raise NotImplementedError
        return convert(parsing.expression, symbols, **options)

    elif isinstance(parsing, parsingtree.AtArg):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.Assignment):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.FcnCall):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.FcnDef):
        raise NotImplementedError

    elif isinstance(parsing, parsingtree.IfChain):
        raise NotImplementedError

    else:
        raise TypeError("unrecognized element in parsingtree: " + repr(parsing))
    
from femtocode.parser import parse

print convert(parse("3"), {})

