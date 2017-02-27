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
import re
import sys
import unittest

import femtocode.asts.lispytree as lispytree
import femtocode.asts.typedtree as typedtree
import femtocode.asts.statementlist as statementlist
from femtocode.defs import SymbolTable
from femtocode.lib.standard import table
from femtocode.parser import parse
from femtocode.dataset import *
from femtocode.typesystem import *

import numpy

import sys

# dataset = MetadataFromJson(Dataset, "/home/pivarski/diana/femtocode/tests").dataset("MuOnia")

if sys.version_info.major >= 3:
    long = int
    basestring = str

class TestStatementlist(unittest.TestCase):
    def runTest(self):
        pass

    def mockDataset(self, **symbolTypes):
        columns = {}
        def build(x, columnName, hasSize):
            if isinstance(x, Number):
                columns[columnName] = Column(
                    columnName,
                    columnName.size() if hasSize else None,
                    numpy.dtype(numpy.int64) if x.whole else numpy.dtype(numpy.float64))

            elif isinstance(x, Collection):
                build(x.items, columnName.array(), True)

            elif isinstance(x, Record):
                for fn, ft in x.fields.items():
                    build(ft, columnName.rec(fn), hasSize)

            else:
                raise NotImplementedError

        for n, t in symbolTypes.items():
            build(t, ColumnName(n), False)

        return Dataset("Dummy", symbolTypes, columns, [], 0)

    def compile(self, code, dataset):
        lt, frame = lispytree.build(parse(code), table.fork(dict((n, lispytree.Ref(n)) for n in dataset.schema)))
        tt, frame = typedtree.build(lt, SymbolTable(dict((lispytree.Ref(n), t) for n, t in dataset.schema.items())))
        result, statements, refnumber = statementlist.build(tt, dataset)
        return result, statements

    def test_add(self):
        dataset = self.mockDataset(x=real, y=real)

        result, statements = self.compile("x + y", dataset)
        print(result)
        print(statements)
