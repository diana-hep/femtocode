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

import ast
import base64
import importlib
import marshal
import math
import sys
import traceback
import types

from femtocode.asts import statementlist
from femtocode.dataset import ColumnName
from femtocode.dataset import sizeType
from femtocode.defs import *
from femtocode.lib.standard import StandardLibrary
from femtocode.py23 import *
from femtocode.typesystem import *
from femtocode.util import *
from femtocode.workflow import Query

class ExecutionFailure(Serializable):
    def __init__(self, exception, traceback):
        self.exception = exception
        self.traceback = traceback

    def __repr__(self):
        return "<ExecutionFailure: {0}>".format(str(self.exception))

    def __str__(self):
        if self.traceback is None:
            return repr(self)
        elif isinstance(self.traceback, string_types):
            return self.traceback
        else:
            return "".join(traceback.format_exception(self.exception.__class__, self.exception, self.traceback))

    def reraise(self):
        if isinstance(self.exception, string_types):
            out = "Server raised: {0}\n\n----%<-------------------------------------------------------------\n\nServer {1}".format(self.exception, self.traceback)
            raise RuntimeError(out)

        elif isinstance(self.traceback, string_types):
            out = "Server raised: {0}\n\n----%<-------------------------------------------------------------\n\nServer {1}".format(str(self.exception), self.traceback)
            raise RuntimeError(out)

        else:
            if sys.version_info[0] <= 2:
                raise self.exception.__class__, self.exception, self.traceback
            else:
                raise self.exception.with_traceback(self.traceback)

    def toJson(self):
        if self.traceback is None:
            traceback = None
        elif isinstance(self.traceback, string_types):
            traceback = self.traceback
        else:
            traceback = str(self.traceback)

        return {"class": self.exception.__class__.__name__,
                "message": str(self.exception),
                "traceback": traceback}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert "class" in obj
        assert "message" in obj
        assert "traceback" in obj
        return ExecutionFailure("{0}: {1}".format(obj["class"], obj["message"]), obj["traceback"])

    @staticmethod
    def failureJson(obj):
        return isinstance(obj, dict) and set(obj.keys()).difference(set(["_id"])) == set(["class", "message", "traceback"])

class DependencyGraph(object):
    pass  # FIXME

class ParamNode(Serializable):
    def toJson(self):
        return self.__class__.__name__

    @staticmethod
    def fromJson(obj):
        if isinstance(obj, string_types):
            return getattr(self.__module__, obj)()
        elif isinstance(obj, dict):
            n, = obj.keys()
            v, = obj.values()
            return getattr(self.__module__, n)(ColumnName.parse(v))
        else:
            assert False

    def __repr__(self):
        return self.toJsonString()

class NamedParamNode(ParamNode):
    def __init__(self, name):
        self.name = name

    def toJson(self):
        return {self.__class__.__name__: str(self.name)}

class NumEntries(ParamNode): pass
class Countdown(ParamNode): pass
class SizeArray(NamedParamNode): pass
class DataArray(NamedParamNode): pass
class OutDataArray(NamedParamNode): pass
class OutSizeArray(NamedParamNode): pass
class Index(NamedParamNode): pass

class Loop(Serializable):
    def __init__(self, plateauSize):
        self.plateauSize = plateauSize

        self.sizes = ()
        self.uniques = []
        self.deepiToUnique = []

        self.explodesize = None
        self.explodes = []
        self.explodedatas = []
        self.statements = []
        self.targets = []

        self.prerun = None
        self.run = None

    def setSizes(self, sizes):
        self.sizes = sizes
        self.deepiToUnique = []
        self.uniques = []
        for size in self.sizes:
            if size not in self.uniques:
                self.deepiToUnique.append(len(self.uniques))
                self.uniques.append(size)
            else:
                self.deepiToUnique.append(self.uniques.index(size))

        assert sum(x.depth() for x in self.uniques) == len(self.sizes)

    def newTarget(self, column):
        if column not in self.targets:
            self.targets.append(column)

    def newStatement(self, statement):
        if statement not in self.statements:
            if isinstance(statement, statementlist.ExplodeSize):
                assert self.explodesize is None, "should not assign two explodesizes in the same loop"
                assert statement.column == self.plateauSize
                self.setSizes(statement.tosize)
                self.explodesize = statement

            elif isinstance(statement, statementlist.ExplodeData):
                assert self.explodesize is not None
                assert self.explodesize.column == statement.explodesize
                self.explodedatas.append(statement)

            elif isinstance(statement, statementlist.Explode):
                assert statement.tosize == self.plateauSize
                self.explodes.append(statement)

            else:
                assert statement.tosize == self.plateauSize
                self.statements.append(statement)

    def codetext(self, fcnname, nametrans, lengthScan):
        parameters = [NumEntries(), Countdown()]
        params = ["numEntries", "countdown"]

        uniqueToSizeArray = []
        uniqueToSizeIndex = []
        for i, size in enumerate(self.uniques):
            parameters.append(SizeArray(size))
            params.append("sarray_" + nametrans(str(size)))
            uniqueToSizeArray.append("sarray_" + nametrans(str(size)))
            parameters.append(Index(size))
            params.append("sindex_" + nametrans(str(size)))
            uniqueToSizeIndex.append("sindex_" + nametrans(str(size)))

        uniqueToDataIndex = {}
        if not lengthScan:
            for explodedata in self.explodedatas:
                parameters.append(DataArray(explodedata.data))
                params.append("xdarray_" + nametrans(str(explodedata.data)))
                parameters.append(Index(explodedata.data))
                params.append("xdindex_" + nametrans(str(explodedata.data)))
                for i, size in enumerate(self.uniques):
                    if explodedata.fromsize == size:
                        uniqueToDataIndex[i] = "xdindex_" + nametrans(str(explodedata.data))
                        break
                    assert i in uniqueToDataIndex

        if not lengthScan:
            for explode in self.explodes:
                parameters.append(DataArray(explode.data))
                params.append("xarray_" + nametrans(str(explode.data)))

        definedHere = set(x.column for x in self.explodedatas + self.explodes + self.statements)
        if not lengthScan:
            for statement in self.statements:
                for arg in statement.args:
                    if isinstance(arg, ColumnName) and not arg.issize() and arg not in definedHere:
                        parameters.append(DataArray(arg))
                        params.append("darray_" + nametrans(str(arg)))

        targetcode = []
        if not lengthScan:
            mightneedsize = False
            for target in self.targets:
                if isinstance(target, ColumnName):
                    parameters.append(OutDataArray(target))
                    params.append("tarray_" + nametrans(str(target)))
                    mightneedsize = True
                    targetcode.append("tarray_{t}[numEntries[1]] = {t}".format(t = nametrans(str(target))))

        targetsizecode = ""
        if not lengthScan:
            if mightneedsize and self.explodesize is not None:
                parameters.append(OutSizeArray(self.explodesize.column))
                params.append("tsarray_" + nametrans(str(self.explodesize.column)))
                targetsizecode = "tsarray_{ts}[numEntries[2]] = countdown[deepi]".format(ts = nametrans(str(self.explodesize.column)))

        init = ["entry = 0", "deepi = 0"]

        blocks = []
        reversals = dict((size, []) for size in self.uniques)
        uniqueDepth = [0] * len(self.uniques)

        deepestData = {}
        for deepi, size in enumerate(self.sizes):
            uniquei = self.deepiToUnique[deepi]
            uniqueDepth[uniquei] += 1

            block = """if deepi == {deepi}:
            {index}[{ud}] = {index}[{udm1}]
            countdown[deepi] = {array}[{index}[{ud}]]{targetsizecode}
            numEntries[2] += 1
            {index}[{ud}] += 1""".format(deepi = deepi,
                                         array = uniqueToSizeArray[uniquei],
                                         index = uniqueToSizeIndex[uniquei],
                                         targetsizecode = "\n            " + targetsizecode,
                                         ud = uniqueDepth[uniquei],
                                         udm1 = uniqueDepth[uniquei] - 1)

            if not lengthScan:
                for explodedata in self.explodedatas:
                    if explodedata.fromsize == size:
                        block += """
            {index}[{ud}] = {index}[{udm1}]""".format(index = uniqueToDataIndex[uniquei],
                                                      ud = uniqueDepth[uniquei],
                                                      udm1 = uniqueDepth[uniquei] - 1)

                        if deepestData.get(explodedata.column, 0) < uniqueDepth[uniquei]:
                            deepestData[explodedata.column] = uniqueDepth[uniquei]

            blocks.append(block + "\n")

            reversal = "{index}[{udm1}] = {index}[{ud}]".format(
                index = uniqueToSizeIndex[uniquei],
                ud = uniqueDepth[uniquei],
                udm1 = uniqueDepth[uniquei] - 1)

            if uniquei in uniqueToDataIndex:
                reversal += "\n                {index}[{udm1}] = {index}[{ud}]".format(
                    index = uniqueToDataIndex[uniquei],
                    ud = uniqueDepth[uniquei],
                    udm1 = uniqueDepth[uniquei] - 1)

            reversals[self.uniques[uniquei]].insert(0, reversal)

        dataassigns = []
        if not lengthScan:
            for explodedata in self.explodedatas:
                d = nametrans(str(explodedata.data))
                dataassigns.append("{n} = xdarray_{d}[xdindex_{d}[{depth}]]".format(
                    n = nametrans(explodedata.column), d = d, depth = deepestData[explodedata.column]))

            for explode in self.explodes:
                dataassigns.append("{n} = xarray_{d}[numEntries[0]]".format(
                    n = nametrans(explode.column), d = nametrans(str(explode.data))))

            for statement in self.statements:
                for arg in statement.args:
                    if isinstance(arg, ColumnName) and arg not in definedHere:
                        dataassigns.append("{d} = darray_{d}[numEntries[1]]".format(d = nametrans(str(arg))))

        dataincrements = dict((i, []) for i in range(len(self.sizes) + 1))
        if not lengthScan:
            for i, unique in enumerate(self.uniques):
                rindex_plus1 = len(self.sizes) - list(reversed(self.sizes)).index(unique)
                for explodedata in self.explodedatas:
                    if explodedata.fromsize == unique:
                        dataincrements[rindex_plus1].append("xdindex_{0}[{1}] += 1".format(nametrans(str(explodedata.data)), unique.depth()))

        blocks.append("""if deepi == {deepi}:
            deepi -= 1
            {assigns}

            REPLACEME     # <--- see replacement below{targetcode}
            {increments}
            numEntries[1] += 1""".format(
            deepi = len(self.sizes),
            assigns = "\n            ".join(dataassigns),
            targetcode = ("\n\n            " if len(targetcode) > 0 else "") + "\n            ".join(targetcode),
            increments = "\n            ".join(dataincrements[len(self.sizes)])))

        resets = []
        for deepi, size in enumerate(self.sizes):
            revs = []
            for unique in self.uniques:
                if len(reversals[unique]) > 0:
                    if deepi == 0 or self.sizes[deepi - 1] == unique:
                        revs.append(reversals[unique].pop())

            if not lengthScan:
                revs.extend(dataincrements[deepi])

            resets.append("if deepi == {deepi}:{revs}".format(
                deepi = deepi,
                revs = "".join("\n                " + x for x in revs) if len(revs) > 0 else "\n                pass"))

        return parameters, params, """
def {fcnname}({params}):
    {init}

    while entry < numEntries[0]:
        if deepi != 0:
            countdown[deepi - 1] -= 1

        {blocks}

        deepi += 1

        while deepi != 0 and countdown[deepi - 1] == 0:
            deepi -= 1

            {resets}

        if deepi == 0:
            entry += 1
""".format(fcnname = fcnname,
           params = ", ".join(params),
           init = "\n    ".join(init),
           blocks = "\n        el".join(blocks),
           resets = "\n            el".join(resets))

    def compileToPython(self, fcnname, inputs, fcntable, tonative, debug):
        prevalidNames = {}
        def prevalid(n):
            if n not in prevalidNames:
                prevalidNames[n] = "v" + repr(len(prevalidNames))
            return prevalidNames[n]

        def replace(node, withwhat):
            if isinstance(node, ast.AST):
                for field in node._fields:
                    replace(getattr(node, field), withwhat)

            elif isinstance(node, list):
                index = None
                for i, x in enumerate(node):
                    if isinstance(x, ast.Expr) and isinstance(x.value, ast.Name) and x.value.id == "REPLACEME":
                        index = i
                        break

                if index is not None:
                    node[index : index + 1] = withwhat
                else:
                    for x in node:
                        replace(x, withwhat)

        # get a function that looks just like our real one, but with no contents: for measuring the size of arrays before allocating
        preparameters, preparams, precodetext = self.codetext(fcnname + "_prerun", prevalid, True)
        premodule = ast.parse(precodetext)
        replace(premodule, [])
        fakeLineNumbers(premodule)
        self.prerun = LoopFunction(self._reallyCompile(fcnname + "_prerun", premodule, {}), preparameters)

        # reset the validNames
        validNames = {}
        def valid(n):
            if n not in validNames:
                validNames[n] = "v" + repr(len(validNames))
            return validNames[n]

        def newname():
            n = len(validNames)  # an integer can't collide with any incoming names
            validNames[n] = "_" + repr(n)
            return validNames[n]

        # now get our real function
        parameters, params, codetext = self.codetext(fcnname, valid, False)
        module = ast.parse(codetext)

        references = {}
        aststatements = []
        schemalookup = dict(inputs)
        for statement in self.explodedatas + self.explodes:
            schemalookup[statement.column] = statement.schema

        for statement in self.statements:
            asttarget = ast.Name(valid(statement.column), ast.Store())

            assert not isinstance(statement, (statementlist.Explode, statementlist.ExplodeSize, statementlist.ExplodeData))

            # f(x[i0], y[i0], 3.14, ...)
            astargs = []
            schemas = []
            for arg in statement.args:
                if isinstance(arg, ColumnName):
                    astargs.append(ast.Name(valid(arg), ast.Load()))
                    schemas.append(schemalookup[arg])
                else:
                    astargs.append(arg.buildexec())
                    schemas.append(arg.schema)

            assignment = fcntable[statement.fcnname].buildexec(asttarget, statement.schema, astargs, schemas, newname, references, tonative)
            schemalookup[statement.column] = statement.schema

            # FIXME: numeric types with restricted min/max should have additional statements "clamping" the result to that range (to avoid bugs due to round-off)
            # So append a few more statements onto that assignment to make sure they stay within range (if applicable)!

            aststatements.extend(assignment)

        replace(module, aststatements)
        fakeLineNumbers(module)

        if debug:
            print("")
            print("Statements:")
            if self.explodesize is not None:
                print("    " + str(self.explodesize))
            for statement in self.explodedatas + self.explodes + self.statements:
                print("    " + str(statement))
            print("")
            print("Prerun parameters:")
            for parameter, param in zip(preparameters, preparams):
                print("    {0}: {1}".format(param, parameter))
            print("")
            print("Parameters:")
            for parameter, param in zip(parameters, params):
                print("    {0}: {1}".format(param, parameter))
            print(codetext)
            print("REPLACEME:")
            print("    " + astToSource(ast.Module(aststatements)).replace("\n", "\n    "))
            print("")
            if len(references) > 0:
                print("References:")
                for n in sorted(references):
                    print("    {0}: {1}".format(n, references[n]))
                print("")

        self.run = LoopFunction(self._reallyCompile(fcnname, module, references), parameters)

    def _reallyCompile(self, fcnname, module, references):
        compiled = compile(module, "Femtocode", "exec")
        out = dict(references)
        out["$math"] = math
        exec(compiled, out)    # exec can't be called in the same function with nested functions
        return out[fcnname]

class LoopFunction(Serializable):
    def __init__(self, fcn, parameters):
        self.fcn = fcn
        self.parameters = parameters





class Executor(Serializable):
    pass  # FIXME


