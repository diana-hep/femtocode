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

def level(name):
    try:
        index = name.rindex("[")
        return name[:index]
    except ValueError:
        return None

class Segment(object):
    def __init__(self, data, size, numEntries, dataLength, dataType):
        self.data = data
        self.size = size
        self.numEntries = numEntries
        self.dataLength = dataLength
        self.dataType = dataType

    def __repr__(self):
        return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, self.data, id(self))

class Group(object):
    def __init__(self, id, segments, numEntries):
        self.id = id
        self.segments = segments
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, self.id, id(self))

class Dataset(object):
    def __init__(self, name, schema, groups, numEntries):
        self.name = name
        self.schema = schema
        self.groups = groups
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} {1} at 0x{2:012x}>".format(self.__class__.__name__, self.name, id(self))
