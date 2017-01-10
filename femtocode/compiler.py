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
import femtocode.lib.standard as standard
from femtocode.typesystem import *

class Workflow(object):
    def __init__(self, *steps):
        self.steps = list(steps)

    def __repr__(self):
        lin = self.linearize()
        out = self._short_chain(["{0}({1})".format(lin[0].__class__.__name__, lin[0]._format_args())] + lin[1:])
        if "\n" in out or len(out) > 80:
            out = self._long_chain(["{0}({1})".format(lin[0].__class__.__name__, lin[0]._format_args())] + lin[1:])
        return out

    def _copy(self):
        out = Workflow.__new__(self.__class__)
        out.steps = list(self.steps)
        return out

    def linearize(self):
        out = [self._copy()]
        for x in out[0].steps:
            out.extend(x.linearize())
        out[0].steps = []
        if out[0].__class__ == Workflow:
            del out[0]
        return out

    def type(self, expression, libs=None):
        symbolTable = SymbolTable(standard.table.asdict())
        if libs is not None:
            for lib in libs:
                symbolTable = symbolTable.fork(libs.asdict())
        symbolTable = symbolTable.fork()
        typeTable = SymbolTable()

        lin = self.linearize()
        if len(lin) == 0:
            raise FemtocodeError("Workflow is empty.")

        if not isinstance(lin[0], Dataset):
            raise FemtocodeError("Workflows must begin with a Dataset, not {0}.".format(lin[0]))

        for n, t in lin[0].schemas.items():
            symbolTable[n] = lispytree.Ref(n)
            typeTable[lispytree.Ref(n)] = t

        for step in lin[1:]:
            symbolTable = step.propagateSymbols(symbolTable)

        expr = parser.parse(expression)
        lt, _ = lispytree.build(expr, symbolTable)
        if isinstance(lt, lispytree.UserFunction):
            raise FemtocodeError("Cannot express the type of a user-defined function.")

        tt, _ = typedtree.build(lt, typeTable)
        return tt.schema

    def prettyType(self, expression, libs=None, highlight=lambda t: "", indent="  ", prefix=""):
        return pretty(self.type(expression, libs), highlight, indent, prefix)

    def propagateSymbols(self, symbolTable):
        return symbolTable

    def _short_chain(self, steps):
        return ".".join(str(x) for x in steps)

    def _long_chain(self, steps):
        steps = map(str, steps)
        slash = min(max(max(map(len, x.split("\n"))) for x in steps) + 5, 80)
        out = [steps[0]]
        trailing = False
        for step in steps[1:]:
            if trailing:
                out[-1] += "." + step
            else:
                out[-1] += " " * (slash - len(out[-1].split("\n")[-1])) + " \\"
                out.append("    ." + step)
            trailing = step.endswith("\'\'\')") or step.endswith("   )")
        return "\n".join(out)
        
    def _format_args(self):
        return ""

    def _format_code(self, code):
        if "\n" in code:
            return "\'\'\'\n{0}\n\'\'\'".format(code)
        else:
            return json.dumps(code)

    def _add_step(self, step):
        out = self._copy()
        out.steps.append(step)
        lin = out.linearize()
        if len(lin) >= 2:
            last, next = lin[-2:]

            if isinstance(last, DataSource) and isinstance(next, DataSource):
                raise FemtocodeError("Cannot have more than one data source: {0} followed by {1}".format(last.__class__.__name__, next.__class__.__name__))

            if isinstance(last, Transformation) and isinstance(next, DataSource):
                raise FemtocodeError("Cannot add data source after transformation: {0} followed by {1}".format(last.__class__.__name__, next.__class__.__name__))

            if isinstance(last, Aggregation):
                raise FemtocodeError("Cannot add anything after aggregation: {0} followed by {1}".format(last.__class__.__name__, next.__class__.__name__))

            if isinstance(last, DataSink):
                raise FemtocodeError("Cannot add anything after data sink: {0} followed by {1}".format(last.__class__.__name__, next.__class__.__name__))

        return out

    def fromPython(self, data):
        return self._add_step(fromPython(data))

    def toPython(self):
        return self._add_step(toPython())

    def define(self, **quantities):
        return self._add_step(define(**quantities))

class DataSource(Workflow): pass
class Transformation(Workflow): pass
class Aggregation(Workflow): pass
class DataSink(Workflow): pass

class fromPython(DataSource):
    def __init__(self, data):
        self.data = data
        super(fromPython, self).__init__()

    def _format_args(self):
        return repr(self.data)

    def _copy(self):
        out = super(fromPython, self)._copy()
        out.data = self.data
        return out

    @staticmethod
    def shred(obj, schema, columns, stripes, name):
        if isinstance(name, string_types):
            name = ColumnName(name)

        # HERE




class toPython(DataSink):
    def _format_args(self):
        return ""

class define(Transformation):
    def __init__(self, **quantities):
        self.quantities = quantities
        super(define, self).__init__()

    def _format_args(self):
        names = sorted(self.quantities.keys())
        out = ", ".join(n + "=" + self._format_code(self.quantities[n]) for n in names)
        if "\n" in out or len(out) + len(self.__class__.__name__) + 2 > 80:
            out = "\n       " + ",\n       ".join(n + "=" + self._format_code(self.quantities[n]) for n in names) + "\n   "
        if out.endswith("'''\n   "):
            out = out[:-7] + "'''"
        return out

    def _copy(self):
        out = super(define, self)._copy()
        out.quantities = self.quantities
        return out

    def propagateSymbols(self, symbolTable):
        newSymbols = {}

        for name, expression in self.quantities.items():
            expr = parser.parse(expression)
            lt, _ = lispytree.build(expr, symbolTable.fork())
            newSymbols[name] = lt

        return symbolTable.fork(newSymbols)

class Dataset(Workflow):
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

        super(Dataset, self).__init__()

    def _format_args(self):
        memo = set()
        names = sorted(self.schemas.keys())
        out = ", ".join(n + "=" + self.schemas[n]._repr_memo(memo) for n in names)
        if "\n" in out or len(out) + len(self.__class__.__name__) + 2 > 80:
            memo.clear()
            return "\n  " + ",\n  ".join(n + "=" + pretty(self.schemas[n], prefix=" " * (len(n) + 3), memo=memo).lstrip(" ") for n in names) + "\n   "
        else:
            return out

    def _copy(self):
        out = super(Dataset, self)._copy()
        out.schemas = self.schemas
        out.columns = self.columns
        return out
