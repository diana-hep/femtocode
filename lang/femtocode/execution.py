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
from femtocode.dataset import *
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
                exec("raise self.exception.__class__, self.exception, self.traceback")
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
    def __init__(self, target, query, lookup, required):
        self.target = target
        self.query = query
        self.lookup = lookup
        self.required = required

        calls = [x for x in self.query.statements if isinstance(x, statementlist.Call) and x.column == target]
        assert len(calls) == 1, "each new column must be defined exactly once: calls = {0} for target = {1}".format(calls, target)
        self.statement = calls[0]
        self.plateauSize = self.statement.plateauSize(self.query.statements)

        self.dependencies = []
        for c in self.statement.args:
            if isinstance(c, ColumnName):
                if c.issize() and any(x.size == c for x in query.dataset.columns.values()):
                    self.required.add(c)

                elif c in self.query.dataset.columns:
                    self.required.add(c)

                elif c in self.lookup:
                    self.dependencies.append(self.lookup[c])

                else:
                    self.dependencies.append(DependencyGraph(c, self.query, self.lookup, self.required))

    def __repr__(self):
        return "<DependencyGraph of [{0}] at 0x{1:012x}>".format(", ".join(map(str, sorted(self.flattened()))), id(self))

    def pretty(self, indent=""):
        return "\n".join([indent + str(self.statement)] + [x.pretty(indent + "    ") for x in self.dependencies])

    def flattened(self):
        out = set([self.target])
        for x in self.dependencies:
            out.update(x.flattened())
        return out

    def overlap(self, other):
        return len(self.flattened().intersection(other.flattened())) > 0

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.target == other.target

    @staticmethod
    def wholedag(query):
        lookup = {}
        required = set()
        targetsToEndpoints = {}
        for action in query.actions:
            for target in action.columns():
                if target.issize() and any(x.size == target for x in query.dataset.columns.values()):
                    required.add(target)
                elif target in query.dataset.columns:
                    required.add(target)
                else:
                    targetsToEndpoints[target] = DependencyGraph(target, query, lookup, required)

        return targetsToEndpoints, lookup, required

    @staticmethod
    def connectedSubgraphs(graphs):
        connectedSubgraphs = []
        for graph in graphs:
            found = False
            for previous in connectedSubgraphs:
                if any(graph.overlap(g) for g in previous):
                    previous.append(graph)
                    found = True
                    break

            if not found:
                connectedSubgraphs.append([graph])

        return connectedSubgraphs

    def _bucketfill(self, loop, endpoints):
        for dependency in self.dependencies:
            if dependency.plateauSize == loop.plateauSize:   #  and not isinstance(dependency.statement, statementlist.ExplodeSize):
                if dependency.target not in loop:
                    dependency._bucketfill(loop, endpoints)
            else:
                endpoints.append(dependency)

        loop.newStatement(self.statement)

    @staticmethod
    def loops(graphs):
        loops = {}
        # sizeToExplosion = {}
        for startpoints in DependencyGraph.connectedSubgraphs(graphs):
            while len(startpoints) > 0:
                newloops = {}
                endpoints = []
                for startpoint in startpoints:
                    # if isinstance(startpoint.statement, statementlist.ExplodeSize):
                    #     sizeToExplosion[startpoint.statement.column] = startpoint.statement.explosions

                    issingleton = False   # isinstance(startpoint.statement, statementlist.ExplodeSize)

                    if (startpoint.plateauSize, issingleton) in newloops:
                        loop = newloops[(startpoint.plateauSize, issingleton)]

                    # elif isinstance(startpoint.statement, statementlist.ExplodeSize):
                    #     loop = ExplodeSizeLoop(startpoint.statement)

                    else:
                        loop = Loop(startpoint.plateauSize)   # NoExplodeSizeLoop(startpoint.plateauSize)

                    if not issingleton:
                        loop.newTarget(startpoint.target)
                        startpoint._bucketfill(loop, endpoints)

                    newloops[(loop.plateauSize, issingleton)] = loop

                for (plateauSize, issingleton), loop in newloops.items():
                    if plateauSize not in loops:
                        loops[(plateauSize, issingleton)] = []
                    loops[(plateauSize, issingleton)].append(loop)

                startpoints = []
                for x in endpoints:
                    if x not in startpoints:
                        startpoints.append(x)

        # for loopsAtPlateau in loops.values():
        #     for loop in loopsAtPlateau:
        #         if startpoint.plateauSize in sizeToExplosion:
        #             loop.setExplosions(sizeToExplosion[startpoint.plateauSize])

        return loops

    @staticmethod
    def order(loops, actions, required):
        toadd = sum(loops.values(), [])
        provided = set(required)

        order = []
        while len(toadd) > 0:
            canadd = [loop for loop in toadd if loop.needs().issubset(provided)]
            assert len(canadd) > 0

            # FIXME: put logic here to allow "Filter" actions to run as early as possible
            choice = canadd[0]
            provided.update(choice.defines())
            order.append(choice)
            toadd.remove(choice)

        # Aggregations go last
        order.extend([x for x in actions if isinstance(x, statementlist.Aggregation)])
        return order

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
            if isinstance(v, list):
                return getattr(self.__module__, n)(ColumnName.parse(*v))
            else:
                return getattr(self.__module__, n)(ColumnName.parse(v))
        else:
            assert False

    def __repr__(self):
        return self.toJsonString()

    def __eq__(self, other):
        return self.__class__ == other.__class__

class NamedParamNode(ParamNode):
    def __init__(self, name):
        self.name = name

    def toJson(self):
        return {self.__class__.__name__: str(self.name)}

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

class NumEntries(ParamNode): pass
class Countdown(ParamNode): pass
class Skip(ParamNode): pass
class Index(NamedParamNode): pass
class SizeArray(NamedParamNode): pass
class DataArray(NamedParamNode): pass
class OutSizeArray(NamedParamNode): pass
class OutDataArray(NamedParamNode):
    def __init__(self, name, dtype):
        super(OutDataArray, self).__init__(name)
        self.dtype = dtype

    def toJson(self):
        return {self.__class__.__name__: [str(self.name), self.dtype]}

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name and self.dtype == other.dtype

class Loop(Serializable):
    def __init__(self, plateauSize):
        self.plateauSize = plateauSize

        if self.plateauSize is None:
            self.explosions = ()
            self.deepiToUnique = []
            self.uniques = []
        else:
            self.setExplosions(self.plateauSize.explosions())

        self.explodesize = None
        self.explodes = []
        self.explodedatas = []
        self.statements = []
        self.targets = []

        self.prerun = None
        self.run = None

    def __contains__(self, column):
        return any(x.column == column for x in self.statements)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.plateauSize == other.plateauSize and self.explodesize == other.explodesize and self.explodes == other.explodes and self.explodedatas == other.explodedatas and self.statements == other.statements and self.targets == other.targets

    def defines(self):
        definedHere = set()
        if self.explodesize is not None:
            definedHere.add(self.explodesize.column)

        for statement in self.explodes + self.explodedatas + self.statements:
            definedHere.add(statement.column)

        return definedHere

    def needs(self):
        definedHere = set()
        requires = set()
        if self.explodesize is not None:
            definedHere.add(self.explodesize.column)
            requires.update(explosionsToSizes(self.explodesize.explosions))

        for statement in self.explodes + self.explodedatas + self.statements:
            definedHere.add(statement.column)
            for arg in statement.args:
                if isinstance(arg, ColumnName):
                    requires.add(arg)

        return requires.difference(definedHere)

    def allstatements(self):
        out = statementlist.Statements()
        if self.explodesize is not None:
            out.append(self.explodesize)
        out.extend(self.explodes)
        out.extend(self.explodedatas)
        out.extend(self.statements)
        return out

    def setExplosions(self, explosions):
        self.explosions = explosions
        self.deepiToUnique = []
        self.uniques = []
        for deepi, explosion in reversed(list(enumerate(self.explosions))):
            found = False
            for uniquei, unique in enumerate(self.uniques):
                if unique.startswith(explosion) and unique != explosion.size():
                    self.deepiToUnique.append(uniquei)
                    found = True

            if not found:
                self.deepiToUnique.append(len(self.uniques))
                self.uniques.append(explosion.size())

        self.uniques = list(reversed(self.uniques))
        self.deepiToUnique = [len(self.uniques) - i - 1 for i in reversed(self.deepiToUnique)]

    def newTarget(self, column):
        if column not in self.targets:
            self.targets.append(column)

    def newStatement(self, statement):
        if statement not in self.statements:
            if isinstance(statement, statementlist.ExplodeSize):
                if statement != self.explodesize:
                    assert self.explodesize is None, "should not assign two explodesizes in the same loop"
                    assert statement.column == self.plateauSize
                    self.setExplosions(statement.explosions)
                    self.explodesize = statement

            elif isinstance(statement, statementlist.ExplodeData):
                assert self.explodesize is not None
                assert self.explodesize.column == statement.explodesize
                if statement not in self.explodedatas:
                    self.explodedatas.append(statement)
                
            elif isinstance(statement, statementlist.Explode):
                assert statement.tosize == self.plateauSize
                if statement not in self.explodes:
                    self.explodes.append(statement)

            else:
                assert statement.tosize == self.plateauSize
                if statement not in self.statements:
                    self.statements.append(statement)

    def parameters(self, nametrans, lengthScan):
        parameters = [NumEntries(), Countdown(), Skip()]
        params = ["numEntries", "countdown", "skip"]

        uniqueToSizeArray = []
        uniqueToSizeIndex = []
        for i, size in enumerate(self.uniques):
            arrayname = "sarray_{0}_{1}".format(nametrans(str(size)), i)
            indexname = "sindex_{0}_{1}".format(nametrans(str(size)), i)

            parameters.append(SizeArray(size))
            params.append(arrayname)
            uniqueToSizeArray.append(arrayname)

            parameters.append(Index(size))
            params.append(indexname)
            uniqueToSizeIndex.append(indexname)

        uniqueToExplodeDataNames = {}
        if not lengthScan:
            for explodedata in self.explodedatas:
                for i, size in enumerate(self.uniques):
                    if explodedata.fromsize == size:
                        arrayname = "xdarray_{0}_{1}".format(nametrans(str(explodedata.data)), i)
                        indexname = "xdindex_{0}_{1}".format(nametrans(str(explodedata.data)), i)
                        varname = nametrans(explodedata.column)

                        if (i, explodedata.data) not in uniqueToExplodeDataNames:
                            uniqueToExplodeDataNames[(i, explodedata.data)] = (explodedata, arrayname, indexname, varname)

                            parameters.append(DataArray(explodedata.data))
                            params.append(arrayname)

                            parameters.append(Index(explodedata.data))
                            params.append(indexname)

                            break

        uniqueToExplodeDataNames = sorted(uniqueToExplodeDataNames.items())

        if not lengthScan:
            for explode in self.explodes:
                if DataArray(explode.data) not in parameters:
                    parameters.append(DataArray(explode.data))
                    params.append("xarray_" + nametrans(str(explode.data)))

        definedHere = set(x.column for x in self.explodedatas + self.explodes + self.statements)
        if not lengthScan:
            for statement in self.statements:
                for arg in statement.args:
                    if isinstance(arg, ColumnName) and not arg.issize() and arg not in definedHere and DataArray(arg) not in parameters:
                        parameters.append(DataArray(arg))
                        params.append("darray_" + nametrans(str(arg)))

        return parameters, params, uniqueToSizeArray, uniqueToSizeIndex, uniqueToExplodeDataNames, definedHere

    def targetcode(self, nametrans, lengthScan, parameters, params):
        targetcode = []
        if not lengthScan:
            mightneedsize = False
            for target in self.targets:
                if isinstance(target, ColumnName):
                    for statement in self.explodes + self.explodedatas + self.statements:
                        if statement.column == target:
                            for c in schemaToColumns(ColumnName(target.path[0]), statement.schema).values():
                                if OutDataArray(c.data, c.dataType) not in parameters:
                                    parameters.append(OutDataArray(c.data, c.dataType))
                                    params.append("tarray_" + nametrans(str(c.data)))
                                    mightneedsize = True
                                    ## FIXME: surely this doesn't handle multicolumns right...
                                    targetcode.append("tarray_{t}[numEntries[1]] = {t}".format(t = nametrans(str(c.data))))

        targetsizecode = ""
        if not lengthScan:
            if mightneedsize and self.explodesize is not None and OutSizeArray(self.explodesize.column) not in parameters:
                parameters.append(OutSizeArray(self.explodesize.column))
                params.append("tsarray_" + nametrans(str(self.explodesize.column)))
                targetsizecode = "tsarray_{ts}[numEntries[2]] = countdown[deepi]".format(ts = nametrans(str(self.explodesize.column)))

        return targetcode, targetsizecode

    def codetext(self, fcnname, nametrans, lengthScan):
        parameters, params, uniqueToSizeArray, uniqueToSizeIndex, uniqueToExplodeDataNames, definedHere = self.parameters(nametrans, lengthScan)
        targetcode, targetsizecode = self.targetcode(nametrans, lengthScan, parameters, params)

        blocks = []
        reversals = dict((size, []) for size in self.uniques)
        uniqueDepth = [0] * len(self.uniques)

        deepestData = {}
        for deepi, explosion in enumerate(self.explosions):
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
                for (i, explodedata), (explodedata, arrayname, indexname, varname) in uniqueToExplodeDataNames:
                    if i == uniquei:
                        block += """
            {index}[{ud}] = {index}[{udm1}]""".format(index = indexname,
                                                      ud = uniqueDepth[uniquei],
                                                      udm1 = uniqueDepth[uniquei] - 1)


                        if deepestData.get(explodedata.column, 0) < uniqueDepth[uniquei]:
                            deepestData[explodedata.column] = uniqueDepth[uniquei]

            blocks.append(block + "\n")

            reversal = "{index}[{udm1}] = {index}[{ud}]".format(
                index = uniqueToSizeIndex[uniquei],
                ud = uniqueDepth[uniquei],
                udm1 = uniqueDepth[uniquei] - 1)

            for (i, explodeddata), (explodedata, arrayname, indexname, varname) in uniqueToExplodeDataNames:
                if i == uniquei:
                    reversal += "\n                {index}[{udm1}] = {index}[{ud}]".format(
                        index = indexname,
                        ud = uniqueDepth[uniquei],
                        udm1 = uniqueDepth[uniquei] - 1)

            reversals[self.uniques[uniquei]].insert(0, reversal)

        dataassigns = []
        if not lengthScan:
            for (uniquei, explodedata), (explodedata, arrayname, indexname, varname) in uniqueToExplodeDataNames:
                dataassigns.append("{n} = {array}[{index}[{depth}]]".format(
                    n = varname, array = arrayname, index = indexname, depth = deepestData[explodedata.column]))

            for explode in self.explodes:
                dataassigns.append("{n} = xarray_{d}[entry]".format(
                    n = nametrans(explode.column), d = nametrans(str(explode.data))))

            for statement in self.statements:
                for arg in statement.args:
                    if isinstance(arg, ColumnName) and arg not in definedHere:
                        dataassigns.append("{d} = darray_{d}[numEntries[1]]".format(d = nametrans(str(arg))))

        dataincrements = dict((i, []) for i in range(len(self.explosions) + 1))
        if not lengthScan:
            for (uniquei, explodedata), (explodedata, arrayname, indexname, varname) in uniqueToExplodeDataNames:
                rindex_plus1 = len(self.deepiToUnique) - list(reversed(self.deepiToUnique)).index(uniquei)
                dataincrements[rindex_plus1].append("{index}[{depth}] += 1".format(index = indexname, depth = self.uniques[uniquei].depth()))

        blocks.append("""if deepi == {deepi}:
            deepi -= 1
            {assigns}

            REPLACEME     # <--- see replacement below{targetcode}

            {increments}
            numEntries[1] += 1""".format(
            deepi = len(self.explosions),
            assigns = "\n            ".join(dataassigns),
            targetcode = ("\n\n            " if len(targetcode) > 0 else "") + "\n            ".join(targetcode),
            increments = "\n            ".join(dataincrements[len(self.explosions)])))

        resets = []
        for deepi, explosion in enumerate(self.explosions):
            revs = []
            for uniquei, unique in enumerate(self.uniques):
                if len(reversals[unique]) > 0:
                    if deepi == 0 or self.deepiToUnique[deepi - 1] == uniquei:
                        revs.append(reversals[unique].pop())

            if not lengthScan:
                revs.extend(dataincrements[deepi])

            resets.append("if deepi == {deepi}:{revs}".format(
                deepi = deepi,
                revs = "".join("\n                " + x for x in revs) if len(revs) > 0 else "\n                pass"))

        return parameters, params, """
def {fcnname}({params}):
    entry = 0
    deepi = 0

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
           blocks = "\n        el".join(blocks),
           resets = "\n            el".join(resets))

    def compileToPython(self, fcnname, inputs, fcntable, tonative, debug):
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

        needPrerun = False
        if self.explodesize is not None:
            for target in self.targets:
                if isinstance(target, ColumnName):
                    needPrerun = True
                    break

        if needPrerun:
            prevalidNames = {}
            def prevalid(n):
                if n not in prevalidNames:
                    prevalidNames[n] = "v" + repr(len(prevalidNames))
                return prevalidNames[n]

            # get a function that looks just like our real one, but with no contents: for measuring the size of arrays before allocating
            preparameters, preparams, precodetext = self.codetext(fcnname + "_prerun", prevalid, True)
            premodule = ast.parse(precodetext)
            replace(premodule, [])
            fakeLineNumbers(premodule)
            self.prerun = LoopFunction(self._reallyCompile(fcnname + "_prerun", premodule, {}), preparameters)

        else:
            self.prerun = None

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

            if isinstance(statement, statementlist.IsType):
                assignment = fcntable[statement.fcnname].buildexec(asttarget, statement.schema, astargs, schemas, newname, references, tonative, statement.fromtype, statement.totype, statement.negate)
            else:
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
            if self.prerun is not None:
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

# class NoExplodeSizeLoop(Loop):
#     def setExplosions(self, explosions):
#         self.explosions = explosions
#         self.deepiToUnique = []
#         self.uniques = []
#         for deepi, explosion in reversed(list(enumerate(self.explosions))):
#             found = False
#             for uniquei, unique in enumerate(self.uniques):
#                 if unique.startswith(explosion) and unique != explosion.size():
#                     self.deepiToUnique.append(uniquei)
#                     found = True

#             if not found:
#                 self.deepiToUnique.append(len(self.uniques))
#                 self.uniques.append(explosion.size())

#         self.uniques = list(reversed(self.uniques))
#         self.deepiToUnique = [len(self.uniques) - i - 1 for i in reversed(self.deepiToUnique)]

#     def newStatement(self, statement):
#         if statement not in self.statements:
#             assert not isinstance(statement, statementlist.ExplodeSize)

#             if isinstance(statement, statementlist.ExplodeData):
#                 if statement not in self.explodedatas:
#                     self.explodedatas.append(statement)
                
#             elif isinstance(statement, statementlist.Explode):
#                 assert statement.tosize == self.plateauSize
#                 if statement not in self.explodes:
#                     self.explodes.append(statement)

#             else:
#                 assert statement.tosize == self.plateauSize
#                 if statement not in self.statements:
#                     self.statements.append(statement)

# class ExplodeSizeLoop(Loop):
#     def __init__(self, explodesize):
#         super(ExplodeSizeLoop, self).__init__(explodesize.column)
#         self.newStatement(explodesize)
#         self.newTarget(explodesize.column)

#     def targetcode(self, nametrans, lengthScan, parameters, params):
#         targetcode = []
#         targetsizecode = ""
#         if not lengthScan:
#             parameters.append(OutSizeArray(self.explodesize.column))
#             params.append("tsarray_" + nametrans(str(self.explodesize.column)))
#             targetsizecode = "tsarray_{ts}[numEntries[2]] = countdown[deepi]".format(ts = nametrans(str(self.explodesize.column)))

#         return targetcode, targetsizecode

class LoopFunction(Serializable):
    def __init__(self, fcn, parameters):
        self.fcn = fcn
        self.parameters = parameters

class Executor(Serializable):
    def __init__(self, query, debug):
        self.query = query
        targetsToEndpoints, lookup, self.required = DependencyGraph.wholedag(self.query)

        loops = DependencyGraph.loops(targetsToEndpoints.values())
        self.order = DependencyGraph.order(loops, self.query.actions, self.required)
        self.compileLoops(debug)

        # transient
        self._setColumnToSegmentKey()

    def _setColumnToSegmentKey(self):
        self.columnToSegmentKey = {}
        for column in self.required:
            if column.issize():
                for c in self.query.dataset.columns.values():
                    if c.size == column:
                        self.columnToSegmentKey[column] = c.data
                assert column in self.columnToSegmentKey
            else:
                self.columnToSegmentKey[column] = column
        
    def compileLoops(self, debug):
        fcntable = SymbolTable(StandardLibrary.table.asdict())
        for lib in self.query.libs:
            fcntable = fcntable.fork(lib.table.asdict())

        for i, loop in enumerate(self.order):
            if isinstance(loop, Loop):
                fcnname = "f{0}_{1}".format(self.query.id, i)
                loop.compileToPython(fcnname, self.query.inputs, fcntable, False, debug)

    def makeArray(self, length, dtype, init):
        if init:
            return [0] * length
        else:
            return [None] * length   # more useful error messages

    def run(self, inarrays, group, columns):
        columnLengths = {None: (group.numEntries, None)}
        lengths = {}
        for name, segment in group.segments.items():
            lengths[columns[name].data] = segment.dataLength
            if columns[name].size is not None:
                columnLengths[columns[name].size] = (segment.dataLength, segment.sizeLength)
                lengths[columns[name].size] = segment.sizeLength

        out = None
        for loopOrAction in self.order:
            if isinstance(loopOrAction, Loop):
                loop = loopOrAction

                if loop.prerun is not None:
                    i = 0
                    for param in loop.prerun.parameters:
                        if isinstance(param, NumEntries):
                            i += 3
                        elif isinstance(param, Countdown):
                            i += len(loop.explosions)
                        elif isinstance(param, Skip):
                            i += max(0, len(loop.explosions) - 1)
                        elif isinstance(param, Index):
                            i += param.name.depth() + 1

                    # cut up a single, contiguous array so that the indexes will probably all be on the same memory page (only when this is Numpy, of course)
                    indexarrays = self.makeArray(i, sizeType, True)
                    i = 0

                    arguments = []
                    for param in loop.prerun.parameters:
                        if isinstance(param, NumEntries):
                            numEntries = indexarrays[i : i + 3]
                            numEntries[0] = group.numEntries
                            arguments.append(numEntries)
                            i += 3

                        elif isinstance(param, Countdown):
                            arguments.append(indexarrays[i : i + len(loop.explosions)])
                            i += len(loop.explosions)

                        elif isinstance(param, Skip):
                            arguments.append(indexarrays[i : i + max(0, len(loop.explosions) - 1)])
                            i += max(0, len(loop.explosions) - 1)

                        elif isinstance(param, Index):
                            arguments.append(indexarrays[i : i + param.name.depth() + 1])
                            i += param.name.depth() + 1

                        elif isinstance(param, SizeArray):
                            arguments.append(inarrays[param.name])

                        else:
                            assert False, "unexpected Parameter in Loop.prerun: {0}".format(param)

                    loop.prerun.fcn(*arguments)
                    dataLength = int(numEntries[1])
                    sizeLength = int(numEntries[2])
                    columnLengths[loop.plateauSize] = dataLength, sizeLength

                else:
                    dataLength, sizeLength = columnLengths[loop.plateauSize]

                i = 0
                for param in loop.run.parameters:
                    if isinstance(param, NumEntries):
                        i += 3
                    elif isinstance(param, Countdown):
                        i += len(loop.explosions)
                    elif isinstance(param, Skip):
                        i += max(0, len(loop.explosions) - 1)
                    elif isinstance(param, Index):
                        i += param.name.depth() + 1

                # cut up a single, contiguous array so that the indexes will probably all be on the same memory page (only when this is Numpy, of course)
                indexarrays = self.makeArray(i, sizeType, True)
                i = 0

                arguments = []
                for param in loop.run.parameters:
                    if isinstance(param, NumEntries):
                        numEntries = indexarrays[i : i + 3]
                        numEntries[0] = group.numEntries
                        arguments.append(numEntries)
                        i += 3

                    elif isinstance(param, Countdown):
                        arguments.append(indexarrays[i : i + len(loop.explosions)])
                        i += len(loop.explosions)

                    elif isinstance(param, Skip):
                        arguments.append(indexarrays[i : i + max(0, len(loop.explosions) - 1)])
                        i += max(0, len(loop.explosions) - 1)

                    elif isinstance(param, Index):
                        arguments.append(indexarrays[i : i + param.name.depth() + 1])
                        i += param.name.depth() + 1

                    elif isinstance(param, (SizeArray, DataArray)):
                        arguments.append(inarrays[param.name])

                    elif isinstance(param, OutSizeArray):
                        inarrays[param.name] = self.makeArray(sizeLength, sizeType, False)
                        arguments.append(inarrays[param.name])
                        columnLengths[param.name] = columnLengths[loop.plateauSize]

                    elif isinstance(param, OutDataArray):
                        inarrays[param.name] = self.makeArray(dataLength, param.dtype, False)
                        arguments.append(inarrays[param.name])

                    else:
                        assert False, "unexpected Parameter in Loop.run: {0}".format(param)

                loop.run.fcn(*arguments)
                
                if loop.explodesize is not None:
                    lengths[loop.explodesize.column] = columnLengths[loop.plateauSize][1]
                for target in loop.targets:
                    if isinstance(target, ColumnName):
                        lengths[target] = columnLengths[loop.plateauSize][0]

                        if loop.plateauSize is not None and not target.issize():
                            columnLengths[target.size()] = columnLengths[loop.plateauSize]

            else:
                action = loopOrAction
                out = action.act(group, columns, columnLengths, lengths, inarrays)

        return out
