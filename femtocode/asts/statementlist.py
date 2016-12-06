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

import femtocode.asts.lispytree as lispytree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

class Column(object):
    repSuffix = "@rep"

    def __init__(self, name, schema, rep):
        self.name = name
        self.schema = schema
        self.rep = rep
        
    def __repr__(self):
        return "Column({0}, {1}, {2})".format(self.name, self.schema, self.rep)

def schemaToColumns(name, schema, rep=None):
    if isinstance(schema, Null):
        return {}

    elif isinstance(schema, (Boolean, Number)) or (isinstance(schema, Union) and all(isinstance(p, Number) for p in schema.possibilities)):
        return {name: Column(name, schema, rep)}
        
    elif isinstance(schema, String):
        if schema.charset == "bytes" and schema.fewest == schema.most:
            return {name: Column(name, schema, rep)}
        else:
            repName = name + "." + Column.repSuffix
            maxRep = schema.most * (1 if rep is None else rep.schema.max)
            rep = Column(repName, Number(0, maxRep, True), None)
            return {repName: rep, name: Column(name, schema, rep)}

    elif isinstance(schema, Collection):
        if schema.fewest == schema.most:
            return {name: Column(name, schema, rep)}
        else:
            repName = name + "." + Column.repSuffix
            maxRep = schema.most * (1 if rep is None else rep.schema.max)
            rep = Column(repName, Number(0, maxRep, True), None)
            return schemaToColumns(name, schema.items, rep)


