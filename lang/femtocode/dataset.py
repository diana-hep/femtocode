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

class Column(object):
    def __init__(self, name, size=None):
        self.name = name
        self.size = size

class Group(object):
    def __init__(self, id, numEntries, lengths):
        self.id = id
        self.numEntries = numEntries
        self.lengths = lengths

class Dataset(object):
    def __init__(self, name, schema, numEntries, columns):
        self.name = name
        self.schema = schema
        self.numEntries = numEntries
        self.columns = columns
