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
        self.inputSizes = [None]
        self.targets = []
        self.statements = []
        self.run = None

    def __repr__(self):
        return "<Loop over {0} at 0x{1:012x}>".format(str(self.plateauSize), id(self))

    def __str__(self):
        return "\n".join(["Loop over {0} params ({1}) inputSizes ({2})".format(self.plateauSize, ", ".join(map(str, self.params())), ", ".join(map(str, self.inputSizes)))] + ["    " + str(x) for x in self.statements])

    def toJson(self):
        return {"plateauSize": None if self.plateauSize is None else str(self.plateauSize),
                "inputSizes": [str(x) for x in self.inputSizes],
                "targets": [str(x) for x in self.targets],
                "statements": [x.toJson() for x in self.statements],
                "run": None if self.run is None else self.run.toJson()}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["plateauSize", "inputSizes", "targets", "statements", "run"])
        assert obj["plateauSize"] is None or isinstance(obj["plateauSize"], string_types)
        assert isinstance(obj["inputSizes"], list)
        assert isinstance(obj["targets"], list)
        assert all(isinstance(x, string_types) for x in obj["targets"])
        assert isinstance(obj["statements"], list)

        out = Loop(None if obj["plateauSize"] is None else ColumnName.parse(obj["plateauSize"]))
        out.inputSizes = [ColumnName.parse(x) for x in obj["inputSizes"]]
        out.targets = [ColumnName.parse(x) for x in obj["targets"]]
        out.statements = [statementlist.Statement.fromJson(x) for x in obj["statements"]]
        assert all(isinstance(x, statementlist.Call) for x in out.statements)
        out.run = None if obj["run"] is None else LoopFunction.fromJson(obj["run"])
        return out

    def newTarget(self, column):
        if column not in self.targets:
            self.targets.append(column)

    def newStatement(self, statement, allstatements):
        if statement not in self.statements:
            if isinstance(statement, statementlist.Call):
                inputSizes = statement.inputSizes(allstatements)
                for ins in inputSizes:
                    if ins not in self.inputSizes:
                        self.inputSizes.append(ins)

            self.statements.append(statement)

    def params(self):
        defines = set(x.column for x in self.statements)
        out = []
        for statement in self.statements:
            for arg in statement.args:
                if isinstance(arg, ColumnName) and arg not in defines and arg not in out:
                    out.append(arg)
        return out

    def __contains__(self, column):
        return any(x.column == column for x in self.statements)

def testy(statements):
    if isinstance(statements[0], statementlist.ExplodeSize):
        preloop = Loop([statements[0].tosize])
        preloop.newTarget(statements[0].column)
        preloop.newStatement(statements[0], statements)

        loop = Loop(statements[-1].tosize)
        loop.newTarget(statements[-1].column)
        for s in statements[1:]:
            loop.newStatement(s, statements)

    else:
        preloop = None
        loop = Loop(statements[-1].tosize)
        loop.newTarget(statements[-1].column)
        for s in statements:
            loop.newStatement(s, statements)

    print preloop
    print loop

    for ins in loop.inputSizes:
        print "init index on", ins
    print "while loop over", loop.plateauSize





class LoopFunction(Serializable):
    pass  # FIXME

class Compiler(object):
    pass  # FIXME

class Executor(Serializable):
    pass  # FIXME


