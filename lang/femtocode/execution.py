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

    class _NumEntries(object): pass
    class _Countdown(object): pass
    class _Array(object):
        def __init__(self, name):
            self.name = name
    class _Index(object):
        def __init__(self, over):
            self.over = over

    def codetext(self, fcnname, nametrans, lengthScan):
        parameters = [self._NumEntries(), self._Countdown()]
        params = ["numEntries", "countdown"]

        uniqueToSizeArray = []
        uniqueToSizeIndex = []
        for i, size in enumerate(self.uniques):
            parameters.append(self._Array(size))
            parameters.append(self._Index(size))
            params.append("array_" + nametrans(str(size)))
            params.append("index_" + nametrans(str(size)))
            uniqueToSizeArray.append("array_" + nametrans(str(size)))
            uniqueToSizeIndex.append("index_" + nametrans(str(size)))

        uniqueToDataIndex = {}
        for explodedata in self.explodedatas:
            parameters.append(self._Array(explodedata.data))
            parameters.append(self._Index(explodedata.data))
            params.append("array_" + nametrans(str(explodedata.data)))
            params.append("index_" + nametrans(str(explodedata.data)))
            for i, size in enumerate(self.uniques):
                if explodedata.fromsize == size:
                    uniqueToDataIndex[i] = "index_" + nametrans(str(explodedata.data))
                    break
                assert i in uniqueToDataIndex

        for explode in self.explodes:
            parameters.append(self._Array(explode.data))
            params.append(nametrans(str(explode.data)))

        definedHere = set(x.column for x in self.explodedatas + self.explodes + self.statements)
        for statement in self.statements:
            for arg in statement.args:
                if isinstance(arg, ColumnName) and not arg.issize() and arg not in definedHere:
                    parameters.append(self._Array(arg))
                    params.append(nametrans(str(arg)))

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
            countdown[deepi] = {array}[{index}[{ud}]]
            print "size", {array}[{index}[{ud}]]
            numEntries[2] += 1
            {index}[{ud}] += 1""".format(deepi = deepi,
                                         array = uniqueToSizeArray[uniquei],
                                         index = uniqueToSizeIndex[uniquei],
                                         ud = uniqueDepth[uniquei],
                                         udm1 = uniqueDepth[uniquei] - 1)

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
        for explodedata in self.explodedatas:
            d = nametrans(str(explodedata.data))
            dataassigns.append("{d} = array_{d}[index_{d}[{depth}]]".format(
                d = d, depth = deepestData[explodedata.column]))

        dataincrements = dict((i, []) for i in range(len(self.sizes) + 1))
        for i, unique in enumerate(self.uniques):
            rindex_plus1 = len(self.sizes) - list(reversed(self.sizes)).index(unique)
            for explodedata in self.explodedatas:
                if explodedata.fromsize == unique:
                    dataincrements[rindex_plus1].append("index_{0}[{1}] += 1".format(nametrans(str(explodedata.data)), unique.depth()))

        blocks.append("""if deepi == {deepi}:
            deepi -= 1
            {assigns}
            print {datarefs}
            {increments}
            numEntries[1] += 1""".format(
            deepi = len(self.sizes),
            assigns = "\n            ".join(dataassigns),
            datarefs = ", ".join(nametrans(str(x.data)) for x in self.explodedatas),
            increments = "\n            ".join(dataincrements[len(self.sizes)])))

        resets = []
        for deepi, size in enumerate(self.sizes):
            revs = []
            for unique in self.uniques:
                if len(reversals[unique]) > 0:
                    if deepi == 0 or self.sizes[deepi - 1] == unique:
                        revs.append(reversals[unique].pop())

            revs.extend(dataincrements[deepi])

            resets.append("if deepi == {deepi}:{revs}".format(
                deepi = deepi,
                revs = "".join("\n                " + x for x in revs) if len(revs) > 0 else "\n                pass"))

        return parameters, """
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










            
class LoopFunction(Serializable):
    pass  # FIXME

class Compiler(object):
    pass  # FIXME

class Executor(Serializable):
    pass  # FIXME


