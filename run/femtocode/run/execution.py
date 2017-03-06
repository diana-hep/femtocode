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

from femtocode.asts import statementlist
from femtocode.dataset import ColumnName
from femtocode.execution import Loop
from femtocode.execution import DependencyGraph
from femtocode.execution import Compiler
from femtocode.execution import Executor

class NativeCompiler(Compiler):
    pass

class NativeExecutor(Executor):
    def __init__(self, query):
        super(NativeExecutor, self).__init__(query)

    def compileLoops(self):
        raise Exception

    def runloop(self, loop, args):
        loop.nativefcn(*args)
    
class AsynchronousNativeExecutor(NativeExecutor):
    def inarrays(self, group):
        raise Exception

    def sizearrays(self, group, inarrays):
        raise Exception

    def workarrays(self, group, lengths):
        raise Exception

    def compiledQuery(self):
        raise Exception

    @staticmethod
    def fromCompiledQuery(compiledQuery):
        raise Exception
