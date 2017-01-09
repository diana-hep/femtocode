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

import re
import json

from femtocode.defs import *
from femtocode.py23 import *
import femtocode.parser as parser
import femtocode.asts.lispytree as lispytree
import femtocode.asts.typedtree as typedtree
import femtocode.asts.statementlist as statementlist
from femtocode.lib.standard import table
from femtocode.typesystem import *

class Dataset(object):
    def __init__(self, **schemas):
        names = sorted(schemas.keys())
        for name in names:
            if re.match("^" + parser.t_NAME.__doc__ + "$", name) is None:
                raise FemtocodeError("Not a valid field name: {0}".format(json.dumps(name)))

        types = resolve([schemas[n] for n in names])

        columns = {}
        for n, t in zip(names, types):
            columns.update(schemaToColumns(n, t))

        self.schemas = schemas
        self.columns = columns

class EngineStep(object):
    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return "{0}({1})".format(self.name, ", ".join(map(repr, self.args)))

class Code(object):
    def __str__(self):
        return "{0}(\'\'\'\n{1}\n\'\'\')".format(self.name, self.args[0])

class DataSource(EngineStep): pass
class Transformation(EngineStep): pass
class Action(EngineStep): pass
class DataSink(EngineStep): pass

class Engine(object):
    def __init__(self, *steps):
        self.steps = steps
        
    def compile(self):
        pass

    def run(self):
        raise NotImplementedError("This is a generic engine. Instantiate a specific engine, such as NumpyEngine.")

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, ", ".join(map(repr, self.steps)))

    def __str__(self):
        steps = map(str, self.steps)
        slash = min(max(map(len, steps)) + 5, 80)
        out = ["{0}()".format(self.__class__.__name__)]
        trailing = False
        for step in steps:
            if trailing:
                out[-1] += "." + step
            else:
                out[-1] += " " * (slash - len(out[-1])) + " \\"
                out.append("    ." + step)
            trailing = step.endswith("\'\'\')")
        return "\n".join(out)

    def fromPython(self, data):
        return self.__class__(*(self.steps + (FromPython(data),)))

    def toPython(self):
        return self.__class__(*(self.steps + (ToPython(),)))

    def map(self, femtocode):
        return self.__class__(*(self.steps + (Map(femtocode),)))
        
class FromPython(DataSource):
    name = "fromPython"
    def __init__(self, data):
        self.args = (data,)

class ToPython(DataSink):
    name = "toPython"
    args = ()

class Map(Code, Transformation):
    name = "map"
    def __init__(self, femtocode):
        self.args = (femtocode,)
