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

import json

def level(name):
    try:
        index = name.rindex("[")
        return name[:index]
    except ValueError:
        return None

class Metadata(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

class Segment(Metadata):
    def __init__(self, numEntries, dataLength):
        self.numEntries = numEntries
        self.dataLength = dataLength

    def __repr__(self):
        return "<{0} numEntries={1} dataLength={2} at 0x{3:012x}>".format(self.__class__.__name__, self.numEntries, self.dataLength, id(self))

    def toJson(self):
        return {"numEntries": self.numEntries, "dataLength": self.dataLength}

class Group(Metadata):
    def __init__(self, id, segments, numEntries):
        self.id = id
        self.segments = segments
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} id={1} numEntries={2} at 0x{3:012x}>".format(self.__class__.__name__, self.id, self.numEntries, id(self))

    def toJson(self):
        return {"id": self.id, "segments": dict((k, v.toJson()) for k, v in self.segments.items()), "numEntries": self.numEntries}

class Column(Metadata):
    def __init__(self, data, size, dataType):
        self.data = data
        self.size = size
        self.dataType = dataType

    def __repr__(self):
        return "<{0} data={1} size={2} at 0x{3:012x}>".format(self.__class__.__name__, self.data, self.size, id(self))

    def toJson(self):
        return {"data": self.data, "size": self.size, "dataType": str(self.dataType)}

class Dataset(Metadata):
    def __init__(self, name, schema, columns, groups, numEntries):
        self.name = name
        self.schema = schema
        self.columns = columns
        self.groups = groups
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} name={1} len(groups)={2}, numEntries={3} at 0x{4:012x}>".format(self.__class__.__name__, self.name, len(self.groups), self.numEntries, id(self))

    def toJson(self):
        return {"name": self.name, "schema": dict((k, v.toJson()) for k, v in self.schema.items()), "columns": dict((k, v.toJson()) for k, v in self.columns.items()), "groups": [x.toJson() for x in self.groups], "numEntries": self.numEntries}
