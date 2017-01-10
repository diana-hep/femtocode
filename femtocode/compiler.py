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

from collections import namedtuple
import re
import sys
import json

from femtocode.defs import *
from femtocode.py23 import *
import femtocode.parser as parser
import femtocode.asts.lispytree as lispytree
import femtocode.asts.typedtree as typedtree
import femtocode.asts.statementlist as statementlist
import femtocode.lib.standard as standard
from femtocode.version import version
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

        targets, actions, result = (), (), None
        for step in lin[1:]:
            targets, actions, result, symbolTable = step._propagate(targets, actions, result, symbolTable)

        expr = parser.parse(expression)
        lt, _ = lispytree.build(expr, symbolTable)
        if isinstance(lt, lispytree.UserFunction):
            raise FemtocodeError("Cannot express the type of a user-defined function.")

        tt, _ = typedtree.build(lt, typeTable)
        return tt.schema

    def typeString(self, expression, libs=None, highlight=lambda t: "", indent="  ", prefix=""):
        return pretty(self.type(expression, libs), highlight, indent, prefix)

    def typeCompare(self, expr1, expr2, libs=None, header=None, between=lambda t1, t2: " " if t1 == t2 or t1 is None or t2 is None else ">", indent="  ", prefix="", width=None):
        return compare(self.type(expr1, libs), self.type(expr2, libs), header, between, indent, prefix, width)

    def _propagate(self, targets, actions, result, symbolTable):
        return targets, actions, result, symbolTable

    def compile(self, libs=None):
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

        source = None
        for x in lin:
            if isinstance(x, DataSource):
                source = x
                break
        if source is None:
            raise FemtocodeError("Workflows must contain a data source.")

        for n, t in lin[0].schemas.items():
            symbolTable[n] = lispytree.Ref(n)
            typeTable[lispytree.Ref(n)] = t

        targets, actions, result = (), (), None
        for step in lin[1:]:
            targets, actions, result, symbolTable = step._propagate(targets, actions, result, symbolTable)

        if not isinstance(lin[-1], (DataSink, Aggregation)):
            raise FemtocodeError("Workflows must end with a data sink or aggregation, not {0}.".format(lin[-1]))

        typedtrees = []
        for target in targets:
            tt, typeTable = typedtree.build(target, typeTable)
            typedtrees.append(tt)

        replacements = {}
        refnumber = 0
        statements = statementlist.Statements()
        actionsToRefs = {}
        actionsToTypes = {}
        for tt, action in zip(typedtrees, actions):
            ref, ss, refnumber = statementlist.build(tt, lin[0].columns, replacements, refnumber)
            statements.extend(ss)
            actionsToRefs[id(action)] = ref

        memo = set()
        return {"version": version,
                "source": source.sourceToJson(lin[0].schemas, lin[0].columns),
                "schemas": dict((n, t._json_memo(memo)) for n, t in lin[0].schemas.items()),
                "inputs": dict((n.toJson(), c.schema.toJson()) for n, c in lin[0].columns.items()),
                "temporaries": dict((s.column.name.toJson(), s.column.schema.toJson()) for s in statements),
                "statements": statements.toJson(),
                "result": result.toJson(actionsToRefs)}

    def compileString(self, libs=None):
        return json.dumps(self.compile(libs))

    def run(self, libs=None):
        compiled = self.compile(libs)

        # we know this is a Dataset because the above succeeded
        if self.engine is None:
            raise FemtocodeError("No engine has been associated with this Dataset.")

        return self.engine.run(compiled)
        
    def submit(self, libs=None):
        raise NotImplementedError("submit is like run, but it returns a Future that reports progress and partial results are inspectable")

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

    def fromPython(self, **data):
        return self._add_step(fromPython(**data))

    def toPython(self, expression):
        return self._add_step(toPython(expression))

    def define(self, **quantities):
        return self._add_step(define(**quantities))

class Action(object):
    def toJson(self, actionsToRefs):
        raise NotImplementedError

class DataSource(Workflow):
    def sourceToJson(self, schemas, columns):
        raise NotImplementedError

class Transformation(Workflow): pass
class Aggregation(Action, Workflow): pass
class DataSink(Action, Workflow): pass

class fromPython(DataSource):
    def __init__(self, **data):
        if len(data) == 0:
            raise FemtocodeError("No data supplied in fromPython.")

        for n, d in data.items():
            try:
                for datum in d:
                    break
            except TypeError:
                raise FemtocodeError("Data supplied as {0} in fromPython is not iterable.".format(json.dumps(n)))

        self.data = data
        super(fromPython, self).__init__()

    def _format_args(self):
        return repr(self.data)

    def _copy(self):
        out = super(fromPython, self)._copy()
        out.data = self.data
        return out

    def sourceToJson(self, schemas, columns):
        stripes = dict((statementlist.ColumnName(n) if isinstance(n, string_types) else n, []) for n in columns)
        numEntries = None
        for name in self.data:
            if name not in schemas:
                raise FemtocodeError("Name {0} found in fromPython but not in dataset schemas.".format(json.dumps(name)))

            schema = schemas[name]
            columnName = statementlist.ColumnName(name)
            total = 0
            for datum in self.data[name]:
                fromPython.shred(datum, schema, columns, stripes, columnName)
                total += 1

            if numEntries is None:
                numEntries = total
            elif numEntries != total:
                raise FemtocodeError("Data supplied as {0} in fromPython has a different number of entries than the others ({1} vs {2}).".format(name, total, numEntries))

        return {"type": "literal", "numEntries": numEntries, "stripes": dict((n.toJson(), s) for n, s in stripes.items())}

    @staticmethod
    def shred(datum, schema, columns, stripes, name):   # NB: columns is ONLY used by Union
        if datum not in schema:
            raise FemtocodeError("Datum {0} is not an instance of schema:\n\n{1}".format(datum, pretty(schema, prefix="    ")))

        if isinstance(schema, Null):
            pass

        elif isinstance(schema, (Boolean, Number)):
            stripes[name].append(datum)

        elif isinstance(schema, String):
            stripes[name].extend(list(datum))
            if schema.charset != "bytes" or schema.fewest != schema.most:
                sizeName = name.size()
                stripes[sizeName].append(len(datum))

        elif isinstance(schema, Collection):
            if schema.fewest != schema.most:
                size = len(datum)
                for n, s in stripes.items():
                    if n.startswith(name) and n.endswith(ColumnName.sizeSuffix):
                        s.append(size)
            items = schema.items
            for x in datum:
                fromPython.shred(x, items, columns, stripes, name)

        elif isinstance(schema, Record):
            for n, t in schema.fields.items():
                fromPython.shred(getattr(datum, n), t, columns, stripes, name.rec(n))

        elif isinstance(schema, Union):
            ctag = columns[name.tag()]
            for i, p in enumerate(ctag.possibilities):
                if datum in p:
                    stripes[name.tag()].append(i)
                    fromPython.shred(datum, p, columns, stripes, name.pos(i))
                    break

        else:
            assert False, "unexpected type: {0} {1}".format(type(schema), schema)

class toPython(DataSink):
    def __init__(self, expression):
        self.expression = expression
        super(toPython, self).__init__()

    def _format_args(self):
        return self._format_code(self.expression)

    def _copy(self):
        out = super(toPython, self)._copy()
        out.expression = self.expression
        return out

    def _propagate(self, targets, actions, result, symbolTable):
        expr = parser.parse(self.expression)
        lt, symbolTable = lispytree.build(expr, symbolTable.fork())
        return targets + (lt,), actions + (self,), self, symbolTable

    def toJson(self, actionsToRefs):
        return {"type": "toPython", "ref": actionsToRefs[id(self)].toJson()}

    @staticmethod
    def assemble(schema, columns, stripes, indexes, name):   # NB: columns is ONLY used by Union
        if isinstance(schema, Null):
            return None

        elif isinstance(schema, (Boolean, Number)):
            stripe = stripes[name]
            out = stripe[indexes[name]]
            indexes[name] += 1

            if isinstance(schema, Boolean):
                return bool(out)
            elif schema.whole:
                return int(out)
            else:
                return float(out)

        elif isinstance(schema, String):
            stripe = stripes[name]
            index = indexes[name]
            if schema.charset == "bytes" and schema.fewest == schema.most:
                size = schema.fewest
            else:
                sizeName = name.size()
                sizeStripe = stripes[sizeName]
                size = sizeStripe.data[indexes[sizeName]]
                indexes[sizeName] += 1

            start = index
            end = index + size

            if schema.charset == "bytes":
                if sys.version_info[0] >= 3:
                    out = bytes(stripe[start:end])
                else:
                    out = b"".join(stripe[start:end])
            else:
                out = u"".join(stripe[start:end])

            indexes[name] += 1
            return out

        elif isinstance(schema, Collection):
            if schema.fewest == schema.most:
                size = schema.fewest
            else:
                size = None
                for n, s in stripes.items():
                    if n.startswith(name) and n.endswith(ColumnName.sizeSuffix):
                        size = s[indexes[n]]
                        indexes[n] += 1
                assert size is not None, "Misaligned collection index"

            items = schema.items
            return [assemble(items, columns, stripes, indexes, name) for i in xrange(size)]

        elif isinstance(schema, Record):
            ns = list(schema.fields.keys())
            return namedtuple("tmp", ns)(*[assemble(schema.fields[n], columns, stripes, indexes, name.rec(n)) for n in ns])

        elif isinstance(schema, Union):
            tagName = name.tag()
            stag = stripes[tagName]
            pos = stag[indexes[tagName]]
            indexes[tagName] += 1
            return assemble(columns[tagName].possibilities[pos], columns, stripes, name.pos(pos))

        else:
            assert False, "unexpected type: {0} {1}".format(type(schema), schema)

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

    def _propagate(self, targets, actions, result, symbolTable):
        newSymbols = {}

        for name, expression in self.quantities.items():
            expr = parser.parse(expression)
            lt, _ = lispytree.build(expr, symbolTable.fork())
            newSymbols[name] = lt

        return targets, actions, result, symbolTable.fork(newSymbols)

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
        self.engine = None

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
        out.engine = self.engine
        return out
