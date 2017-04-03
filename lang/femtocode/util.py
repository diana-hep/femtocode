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
import json
import math
try:
    import Queue as queue
except ImportError:
    import queue

import femtocode.thirdparty.meta as meta

def bytecodeToSource(bytecode):
    return meta.dump_python_source(meta.decompile(bytecode)).strip()

def astToSource(pythonast):
    return meta.dump_python_source(pythonast).strip()

def statementsToAst(source, *orderedReplacements, **namedReplacements):
    result = ast.parse(source).body

    def replace(x, index):
        if isinstance(x, ast.AST):
            for fieldName in x._fields:
                old = getattr(x, fieldName)

                if isinstance(old, ast.Name) and old.id in namedReplacements:
                    replacement = namedReplacements[old.id]

                elif isinstance(old, ast.Name) and index < len(orderedReplacements):
                    replacement = orderedReplacements[index]
                    index += 1

                else:
                    replacement, index = replace(old, index)

                setattr(x, fieldName, replacement)
            
        elif isinstance(x, list):
            for i, xi in enumerate(x):
                x[i], index = replace(xi, index)

        return x, index

    return replace(result, 0)[0]

def expressionToAst(source, *orderedReplacements, **namedReplacements):
    out = statementsToAst(source, *orderedReplacements, **namedReplacements)
    return out[0].value

def fakeLineNumbers(node):
    if isinstance(node, ast.AST):
        node.lineno = 1
        node.col_offset = 0
        for field in node._fields:
            fakeLineNumbers(getattr(node, field))

    elif isinstance(node, (list, tuple)):
        for x in node:
            fakeLineNumbers(x)

def roundup(x):
    return int(math.ceil(x))

def drainQueue(q):
    out = []
    while True:
        try:
            out.append(q.get_nowait())
        except queue.Empty:
            break
    return out

def dropIfPresent(d, key):
    try:
        del d[key]
    except KeyError:
        pass

class Serializable(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

    def toJsonFile(self, file):
        json.dump(file, self.toJson())

    @classmethod
    def fromJsonString(cls, string):
        return cls.fromJson(json.loads(string))

    @classmethod
    def fromJsonFile(cls, file):
        return cls.fromJson(json.load(file))
