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

from femtocode.dataset import ColumnName
from femtocode.dataset import Segment
from femtocode.dataset import Group
from femtocode.dataset import Column
from femtocode.dataset import Dataset
from femtocode.typesystem import *
from femtocode.ldrdio.fetch import LDRDFetcher

from client.StripedClient import StripedClient







class LDRDDataset(Dataset):
    fetcher = LDRDFetcher

    def __init__(self, name, schema, columns, groups, numEntries, numGroups):
        super(LDRDDataset, self).__init__(name, schema, columns, groups, numEntries, numGroups)

    @staticmethod
    def fromJson(dataset):
        return LDRDDataset(
            dataset["name"],
            dict((k, Schema.fromJson(v)) for k, v in dataset["schema"].items()),
            dict((ColumnName.parse(k), LDRDColumn.fromJson(v)) for k, v in dataset["columns"].items()),
            [LDRDGroup.fromJson(x) for x in dataset["groups"]],
            dataset["numEntries"],
            dataset["numGroups"])

    def __eq__(self, other):
        return other.__class__ == LDRDDataset and self.name == other.name and self.schema == other.schema and self.columns == other.columns, self.groups == other.groups and self.numEntries == other.numEntries and self.numGroups == other.numGroups

    def __hash__(self):
        return hash(("LDRDDataset", self.name, tuple(sorted(self.schema.items())), tuple(sorted(self.columns.items())), tuple(self.groups), self.numEntries, self.numGroups))

class MetadataFromLDRD(object):
    def __init__(self, urlhead):
        self.urlhead = urlhead
        self.client = StripedClient(urlhead)

    def dataset(self, name, groups=(), columns=None, schema=True):
        schemaFromDB = dict((k, Schema.fromJson(v)) for k, v in self.client.dataset(name).schema["fields"].items())

        columnNames, apiNames = [], []
        def getnames(name, apiname, tpe):
            if isinstance(tpe, Collection):
                getnames(name.coll(), apiname, tpe.items)

            elif isinstance(tpe, Record):
                for fn, ft in tpe.fields.items():
                    getnames(name.rec(fn), apiname + "." + fn, ft)

            elif isinstance(tpe, Union):
                raise NotImplementedError

            else:
                columnNames.append(name)
                apiNames.append(apiname)

        for n, t in schemaFromDB.items():
            getnames(ColumnName(n), n, t)

        for c, a in zip(columnNames, apiNames):
            print c, a



        return LDRDDataset(name,
                           schemaFromDB if schema else None,
                           {},
                           [],
                           0,
                           0)

# def toStripedColumnName(cname):
#     return str(cname).replace(cname.colltag,"").replace(cname.sizetag, ".@size")

# def fromStripedColumnName(cname, parent):
#     assert parent is None or cname == parent or cname.startswith(parent + ".")
#     path = cname.split(".")
#     if parent:
#         parent_path = parent.split(".")
#         l = len(parent_path)
#         path = path[:l] + [self.colltag] + path[l:]
#     if path[-1] == "@size":
#         path[-1] = self.sizetag
#     return Column(path)

# def getMetadata(client, dataset, canonic_column_names, rgids):
#     #
#     # client - StripedClient object
#     # dataset - dataset name, string
#     # canonic_column_names - list of ColumnName objects - assumes only data columns are here
#     # rgids - list of integer rgid's
#     #
#     # returns Dataset object
#     #
#     assert not any((c.issize() for c in canonic_column_names)), "Only data columns accepted"
#     column_name_map = dict((toStripedColumnName(x), x) for x in canonic_column_names)
#     column_names = column_name_map.keys()
#     ds = StripedDataset(client, dataset)
#     striped_columns = [ds.column(cn) for cn in column_names]
#     stripe_sizes = ds.stripeSizes(striped_columns, rgids)
#     columns = {}
#     for c in striped_columns:
#         desc = c.descriptor
#         ccn = column_name_map[cn]
#         columns[ccn] = Column(ccn, ccn+ColumnName.sizetag, np.dtype(desc.ConvertToNPType)) 
#     gropus = []
#     rginfo_lst = ds.rginfo(rgids)
#     total_events = 0
#     for rginfo in rginfo_lst:
#         segments = {}
#         rgid = rginfo["RGID"]
#         for cn in column_names:
#             ccn = column_name_map[cn]
#             segments[ccn] = Segment(rginfo["NEvents"], stripe_sizes[cn][rgid], rginfo["NEvents"]) # or None for sizeLength for depth=0
#         groups.append(Group(rgid, segments, rginfo["NEvents"]))
#         total_events += rginfo["NEvents"]
#     return Dataset(dataset, client.datasetSchema(dataset), columns, groups, total_events, len(rgids))

