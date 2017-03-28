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

import numpy

from femtocode.dataset import ColumnName
from femtocode.dataset import Segment
from femtocode.dataset import Group
from femtocode.dataset import Column
from femtocode.dataset import Dataset
from femtocode.typesystem import *
from femtocode.ldrdio.fetch import LDRDFetcher

from client.StripedClient import StripedClient

class LDRDSegment(Segment):
    def __init__(self, numEntries, dataLength, sizeLength):
        super(LDRDSegment, self).__init__(numEntries, dataLength, sizeLength)

    @staticmethod
    def fromJson(segment):
        return LDRDSegment(
            segment["numEntries"],
            segment["dataLength"],
            segment["sizeLength"])

    def __eq__(self, other):
        return other.__class__ == LDRDSegment and self.numEntries == other.numEntries and self.dataLength == other.dataLength and self.sizeLength == other.sizeLength

    def __hash__(self):
        return hash(("LDRDSegment", self.numEntries, self.dataLength, self.sizeLength))

class LDRDGroup(Group):
    @staticmethod
    def fromJson(group):
        return LDRDGroup(
            group["id"],
            dict((ColumnName.parse(k), LDRDSegment.fromJson(v)) for k, v in group["segments"].items()),
            group["numEntries"])

    def __eq__(self, other):
        return other.__class__ == LDRDGroup and self.id == other.id and self.segments == other.segments and self.numEntries == other.numEntries

    def __hash__(self):
        return hash(("LDRDGroup", self.id, tuple(sorted(self.segments.items())), self.numEntries))
        
class LDRDColumn(Column):
    def __init__(self, data, size, dataType, apidata, apisize):
        super(LDRDColumn, self).__init__(data, size, dataType)
        self.apidata = apidata
        self.apisize = apisize

    def toJson(self):
        out = super(LDRDColumn, self).toJson()
        out["apidata"] = self.apidata
        out["apisize"] = self.apisize
        return out

    @staticmethod
    def fromJson(column):
        data = ColumnName.parse(column["data"])
        size = None if column["size"] is None else ColumnName.parse(column["size"])
        dataType = column["dataType"]
        apidata = column["apidata"]
        apisize = column["apisize"]
        return LDRDColumn(data, size, dataType, apidata, apisize)

    def __eq__(self, other):
        return other.__class__ == LDRDColumn and self.data == other.data and self.size == other.size and self.dataType == other.dataType and self.apidata == other.apidata and self.apisize == other.apisize

    def __hash__(self):
        return hash(("LDRDColumn", self.data, self.size, self.dataType, self.apidata, self.apisize))

class LDRDDataset(Dataset):
    fetcher = LDRDFetcher

    def __init__(self, name, schema, columns, groups, numEntries, numGroups, apiDataset):
        super(LDRDDataset, self).__init__(name, schema, columns, groups, numEntries, numGroups)
        self.apiDataset = apiDataset

    def toJson(self):
        out = super(LDRDDataset, self).toJson()
        out["urlhead"] = self.apiDataset.Client.URLHead
        return out

    @staticmethod
    def fromJson(dataset):
        return LDRDDataset(
            dataset["name"],
            dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
            dict((ColumnName.parse(k), LDRDColumn.fromJson(v)) for k, v in dataset["columns"].items()),
            [LDRDGroup.fromJson(x) for x in dataset["groups"]],
            dataset["numEntries"],
            dataset["numGroups"],
            StripedClient(dataset["urlhead"]).dataset(dataset["name"]))

    def __eq__(self, other):
        return other.__class__ == LDRDDataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries and self.numGroups == other.numGroups and self.apiDataset.Client.URLHead == other.apiDataset.Client.URLHead

    def __hash__(self):
        return hash(("LDRDDataset", self.name, tuple(sorted(self.schema.items())), tuple(sorted(self.columns.items())), tuple(self.groups), self.numEntries, self.numGroups, self.apiDataset.Client.URLHead))

class MetadataFromLDRD(object):
    def __init__(self, urlhead):
        self.urlhead = urlhead

    def dataset(self, name, groups=(), columns=None, schema=True):
        client = StripedClient(self.urlhead)
        apiDataset = client.dataset(name)

        schemaFromDB = dict((k, Schema.fromJson(v)) for k, v in apiDataset.schema["fields"].items())

        ldrdcolumns = {}
        def get(name, apiname, tpe, hasSize):
            if isinstance(tpe, Collection):
                get(name.coll(), apiname, tpe.items, True)

            elif isinstance(tpe, Record):
                for fn, ft in tpe.fields.items():
                    get(name.rec(fn), apiname + "." + fn, ft, hasSize)

            elif isinstance(tpe, Union):
                raise NotImplementedError

            else:
                if columns is not None and name in columns:
                    ldrdcolumns[name] = LDRDColumn(name,
                                                   name.size() if hasSize else None,
                                                   None,                 # fill in later
                                                   apiname,
                                                   None)                 # fill in later

        if columns is not None:
            for n, t in schemaFromDB.items():
                get(ColumnName(n), n, t, False)

            striped_columns = []
            for c in ldrdcolumns.values():
                striped_columns.append(apiDataset.column(c.apidata))
                desc = striped_columns[-1].descriptor
                c.dataType = str(numpy.dtype(desc.ConvertToNPType))
                c.apisize = desc.SizeColumn

            rgids = apiDataset.rgids
            assert set(rgids) == set(range(len(rgids)))
            
            rginfos = apiDataset.rginfo(rgids)
            relevant = dict((x["RGID"], x) for x in rginfos if x["RGID"] in groups)

            if len(striped_columns) > 0:
                stripe_sizes = apiDataset.stripeSizes(striped_columns, rgids)
            else:
                stripe_sizes = []

            ldrdgroups = []
            for groupid in groups:
                rginfo = relevant[groupid]
                segments = {}
                for c in ldrdcolumns.values():
                    segments[c.data] = LDRDSegment(rginfo["NEvents"], stripe_sizes[c.apidata][groupid], rginfo["NEvents"])
                    
                ldrdgroups.append(LDRDGroup(groupid, segments, rginfo["NEvents"]))

        return LDRDDataset(name,
                           schemaFromDB if schema else None,
                           ldrdcolumns,
                           ldrdgroups,
                           sum(x["NEvents"] for x in rginfos),
                           len(rgids),
                           apiDataset)
