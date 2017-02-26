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

from pymongo import MongoClient

from femtocode.util import *

class MetadataFromMongoDB(object):
    def __init__(self, datasetClass, mongourl, database, collection, timeout):
        self.datasetClass = datasetClass
        self.client = MongoClient(mongourl, serverSelectionTimeoutMS=roundup(timeout * 1000))
        self.client.server_info()
        self.collection = self.client[database][collection]
        self.timeout = timeout
        self._cache = {}

    def dataset(self, name, groups=(), columns=(), schema=False):
        key = (name, tuple(groups) if isinstance(groups, list) else groups, tuple(columns) if isinstance(columns, list) else columns, schema)
        if key not in self._cache:
            project = {"name": True, "numEntries": True}
            if schema:
                project["schema"] = True

            if len(groups) == 0:
                select = {"name": name}
            else:
                select = {"$or": [{"name": name, "groups.id": {"$eq": i}} for i in groups]}
                project["groups.id"] = True
                project["groups.numEntries"] = True
                project["groups.files"] = True

            for column in columns:
                project["columns." + column] = True
                project["groups.segments." + column] = True
                project["groups.segments." + column + ".files"] = True

            results = list(self.collection.find(select, project, modifiers={"$maxTimeMS": roundup(self.timeout * 1000)}))

            if len(results) == 0:
                raise IOError("dataset/groups not found: {0}".format(key))
            elif len(results) > 1:
                raise IOError("more than one dataset/groups match for {0}: {1}".format(key, results))
            else:
                if "schema" not in results[0]:
                    results[0]["schema"] = {}

                if "groups" not in results[0]:
                    results[0]["groups"] = []

                for group in results[0]["groups"]:
                    if "files" not in group:
                        group["files"] = None
                    if "segments" not in group:
                        group["segments"] = {}
                    for segment in group["segments"].values():
                        if "files" not in segment:
                            segment["files"] = None
                
                if "columns" not in results[0]:
                    results[0]["columns"] = {}

                self._cache[key] = self.datasetClass.fromJson(results[0])

        return self._cache[key]

# from femtocode.fromroot.dataset import ROOTDataset
# db = MetadataFromMongoDB("mongodb://localhost:27017", "metadb", "datasets", ROOTDataset, 1.0)
