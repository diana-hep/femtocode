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

class EngineStep(object):
    def __str__(self):
        return "{0}({1})".format(self.name, ", ".join(map(repr, self.args)))

class Code(object):
    def __str__(self):
        if "\n" in self.args[0]:
            return "{0}(\'\'\'\n{1}\n\'\'\')".format(self.name, self.args[0])
        else:
            return "{0}({1})".format(self.name, json.dumps(self.args[0]))

class DataSource(EngineStep): pass
class Transformation(EngineStep): pass
class Aggregation(EngineStep): pass
class DataSink(EngineStep): pass

class Dataset(object):
    def __init__(self, **schemas):
        if len(schemas) == 0:
            raise FemtocodeError("At least one column is required.")

        names = sorted(schemas.keys())
        for name in names:
            if re.match("^" + parser.t_NAME.__doc__ + "$", name) is None:
                raise FemtocodeError("Not a valid field name: {0}".format(json.dumps(name)))

        types = resolve([schemas[n] for n in names])

        columns = {}
        for n, t in zip(names, types):
            columns.update(statementlist.schemaToColumns(n, t))

        self.schemas = schemas
        self.columns = columns
        self.steps = []

    def __repr__(self):
        memo = set()
        names = sorted(self.schemas.keys())
        out = "{0}({1})".format(self.__class__.__name__, ", ".join(n + "=" + self.schemas[n]._repr_memo(memo) for n in names)) + self._short_chain()
        if "\n" in out or len(out) > 80:
            memo.clear()
            return "{0}(\n  {1}\n   )".format(self.__class__.__name__, ",\n  ".join(n + "=" + pretty(self.schemas[n], prefix=" " * (len(n) + 3), memo=memo).lstrip(" ") for n in names)) + self._long_chain()
        else:
            return out

    def _short_chain(self):
        return "".join("." + str(x) for x in self.steps)

    def _long_chain(self):
        if len(self.steps) == 0:
            return ""
        else:
            steps = map(str, self.steps)
            slash = min(max(map(len, steps)) + 5, 80)
            out = [""]
            trailing = True
            for step in steps:
                if trailing:
                    out[-1] += "." + step
                else:
                    out[-1] += " " * (slash - len(out[-1].split("\n")[-1])) + " \\"
                    out.append("    ." + step)
                trailing = step.endswith("\'\'\')")
            return "\n".join(out)

    @property
    def issource(self):
        return False

    def _add_step(self, step):
        if len(self.steps) == 0:
            if self.issource and isinstance(step, DataSource):
                raise FemtocodeError("Attempting to add a {0} to a {1}, but both are data sources.".format(step.__class__.__name__, self.__class__.__name__))
            elif not self.issource and not isinstance(step, DataSource):
                raise FemtocodeError("First step on a {0} must be a data source, not {1}.".format(self.__class__.__name__, step.__class__.__name__))

        else:
            last = self.steps[-1]
            if isinstance(step, DataSource):
                raise FemtocodeError("Attempting to add {0}, which is a data source, after {1}".format(step.__class__.__name__, last.__class__.__name__))
            if isinstance(last, DataSink):
                raise FemtocodeError("Attempting to add {0} after {1}, which is a data sink.".format(step.__class__.__name__, last.__class__.__name__))
            if isinstance(last, Aggregation):
                raise FemtocodeError("Attempting to add {0} after {1}, which is an aggregation.".format(step.__class__.__name__, last.__class__.__name__))

        out = Dataset.__new__(Dataset)
        out.schemas = self.schemas
        out.columns = self.columns
        out.steps = self.steps + [step]
        return out

    def fromPython(self, data):
        return self._add_step(FromPython(data))

    def toPython(self):
        return self._add_step(ToPython())

    def map(self, femtocode):
        return self._add_step(Map(femtocode))
        
class FromPython(DataSource):
    name = "fromPython"
    def __init__(self, data):
        self.args = (data,)

    @staticmethod
    def shred(obj, schema, columns, stripes, name):
        if isinstance(name, string_types):
            name = ColumnName(name)

        # HERE




class ToPython(DataSink):
    name = "toPython"
    args = ()

class Map(Code, Transformation):
    name = "map"
    def __init__(self, femtocode):
        self.args = (femtocode,)
