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

from femtocode.asts import lispytree
from femtocode.defs import *
from femtocode.py23 import *
from femtocode.typesystem import *

class TypedTree(object):
    pass

class Ref(lispytree.Ref):
    def __init__(self, schema, name, original=None):
        self.schema = schema
        super(Ref, self).__init__(name, original)

    def __repr__(self):
        return "Ref({0}, {1})".format(self.schema, self.name)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.schema == other.schema:
                return super(Ref, self).__lt__(other)
            else:
                return self.schema < other.schema
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, TypedTree):
            return self.schema == other.schema and super(Ref, self).__eq__(other)
        else:
            return False

    def __hash__(self):
        return hash((self.order, self.name, self.schema))

class Literal(lispytree.Literal):
    def __init__(self, schema, value, original=None):
        self.schema = schema
        super(Literal, self).__init__(value, original)

    def __repr__(self):
        return "Literal({0}, {1})".format(self.schema, self.value)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.schema == other.schema:
                return super(Literal, self).__lt__(other)
            else:
                return self.schema < other.schema
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, TypedTree):
            return self.schema == other.schema and super(Literal, self).__eq__(other)
        else:
            return False

    def __hash__(self):
        return hash((self.order, self.value, self.schema))
    
class Call(lispytree.Call):
    def __init__(self, schema, fcn, args, original=None):
        self.schema = schema
        super(Call, self).__init__(fcn, args, original)

    def __repr__(self):
        return "Call({0}, {1}, {2})".format(self.schema, self.fcn, self.args)

    def __lt__(self, other):
        if isinstance(other, TypedTree):
            if self.schema == other.schema:
                return super(Call, self).__lt__(other)
            else:
                return self.schema < other.schema
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, TypedTree):
            return self.schema == other.schema and super(Call, self).__eq__(other)
        else:
            return False

    def __hash__(self):
        return hash((self.order, self.fcn, self.sortedargs(), self.schema))



