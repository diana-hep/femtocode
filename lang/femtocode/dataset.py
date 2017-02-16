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

from femtocode.typesystem import Schema

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

    @classmethod
    def fromJson(cls, segment):
        return Segment(
            segment["numEntries"],
            segment["dataLength"])

    def __eq__(self, other):
        return other.__class__ == Segment and self.numEntries == other.numEntries and self.dataLength == other.dataLength

    def __hash__(self):
        return hash((Segment, self.numEntries, self.dataLength))

class Group(Metadata):
    def __init__(self, id, segments, numEntries):
        self.id = id
        self.segments = segments
        self.numEntries = numEntries

    def __repr__(self):
        return "<{0} id={1} numEntries={2} at 0x{3:012x}>".format(self.__class__.__name__, self.id, self.numEntries, id(self))

    def toJson(self):
        return {"id": self.id, "segments": dict((k, v.toJson()) for k, v in self.segments.items()), "numEntries": self.numEntries}

    @classmethod
    def fromJson(cls, group):
        return Group(
            group["id"],
            dict((k, Segment.fromJson(v)) for k, v in group["segments"].items()),
            group["numEntries"])

    def __eq__(self, other):
        return other.__class__ == Group and self.id == other.id and self.segments == other.segments and self.numEntries == other.numEntries

    def __hash__(self):
        return hash((Group, self.id, tuple(self.segments.items()), self.numEntries))

class Column(Metadata):
    def __init__(self, data, size, dataType):
        self.data = data
        self.size = size
        self.dataType = dataType

    def __repr__(self):
        return "<{0} data={1} size={2} at 0x{3:012x}>".format(self.__class__.__name__, self.data, self.size, id(self))

    def toJson(self):
        return {"data": self.data, "size": self.size, "dataType": str(self.dataType)}

    @classmethod
    def fromJson(cls, column):
        return Column(
            column["data"],
            column["size"],
            column["dataType"])

    def __eq__(self, other):
        return other.__class__ == Column and self.data == other.data and self.size == other.size and self.dataType == other.dataType

    def __hash__(self):
        return hash((Column, self.data, self.size, self.dataType))

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

    @classmethod
    def fromJsonString(cls, dataset):
        return cls.fromJson(json.loads(dataset))

    @classmethod
    def fromJson(cls, dataset):
        return Dataset(
            dataset["name"],
            dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
            dict((k, Column.fromJson(v)) for k, v in dataset["columns"].items()),
            [Group.fromJson(x) for x in dataset["groups"]],
            dataset["numEntries"])

    def __eq__(self, other):
        return other.__class__ == Dataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries

    def __hash__(self):
        return hash((Dataset, self.name, self.schema, tuple(self.columns.items()), tuple(self.groups), self.numEntries))
