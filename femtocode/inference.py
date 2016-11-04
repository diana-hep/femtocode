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

from femtocode.defs import *
from femtocode.asts.functiontree import *

from femtocode.thirdparty.boolean.boolean import BooleanAlgebra
from femtocode.thirdparty.boolean.boolean import Symbol
from femtocode.thirdparty.boolean.boolean import AND
from femtocode.thirdparty.boolean.boolean import OR
from femtocode.thirdparty.boolean.boolean import NOT

def conjunctiveNormalForm(tree):
    alg = BooleanAlgebra()

    andFcn, orFcn, notFcn = None, None, None

    def wrap(x):
        if isinstance(x, Call):
            if x.fcn.name == "and":
                andFcn, orFcn, notFcn = x.andFcn, x.orFcn, x.notFcn
                out = alg.AND(*[wrap(y) for y in x.args])
            elif x.fcn.name == "or":
                andFcn, orFcn, notFcn = x.andFcn, x.orFcn, x.notFcn
                out = alg.OR(*[wrap(y) for y in x.args])
            elif x.fcn.name == "not" and len(x.args) == 1:
                andFcn, orFcn, notFcn = x.andFcn, x.orFcn, x.notFcn
                out = alg.NOT(wrap(x.args[0]))
            else:
                out = Symbol(x)
            out.original = x.original
            return out

        elif isinstance(x, Literal):
            if x.value is True:
                return alg.TRUE
            elif x.value is False:
                return alg.FALSE
            else:
                out = Symbol(x)
                out.original = x.original
                return out
        else:
            out = Symbol(x)
            out.original = x.original
            return out

    def unwrap(x):
        if x == alg.TRUE:
            return Literal(True, tree)
        elif x == alg.FALSE:
            return Literal(False, tree)
        elif isinstance(x, AND):
            return Call(andFcn, [unwrap(y) for y in x.args], tree)
        elif isinstance(x, OR):
            return Call(orFcn, [unwrap(y) for y in x.args], tree)
        elif isinstance(x, NOT):
            return Call(notFcn, [unwrap(y) for y in x.args], tree)
        elif isinstance(x, Symbol):
            return x.obj
        else:
            raise ProgrammingError("unrecognized element from boolean package: " + repr(x))

    return unwrap(alg.cnf(wrap(tree)))
