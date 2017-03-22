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

from datetime import datetime
from pymongo import MongoClient

from femtocode.dataset import Dataset
from femtocode.dataset import MetadataFromJson
from femtocode.workflow import Query
from femtocode.server.communication import *
from femtocode.util import *
import femtocode.asts.statementlist as statementlist

class GroupTally(Serializable):
    def __init__(self, groupid, tally):
        self.groupid = groupid
        self.tally = tally

    def toJson(self):
        return {"groupid": self.groupid, "tally": self.tally.toJson()}

    @staticmethod
    def fromJson(obj, action):
        assert isinstance(obj, dict)
        assert "groupid" in obj and "tally" in obj
        return GroupTally(obj["groupid"], action.tallyFromJson(obj["tally"]))

class WholeTally(Serializable):
    def __init__(self, query, groups, lastAccess, mongoid):
        self.query = query
        self.groups = groups
        self.lastAccess = lastAccess
        self.mongoid = mongoid

    def toJson(self):
        return {"queryid": self.query.id,
                "query": self.query.stripToName().toJson(),
                "groups": [x.toJson() for x in self.groups],
                "lastAccess": lastAccess}

    @staticmethod
    def fromJson(obj):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["queryid", "query", "groups", "lastAccess"])
        query = Query.fromJson(obj["query"])
        assert query.id == obj["queryid"]

        action = query.actions[-1]
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"

        groups = {}
        for group in obj["groups"]:
            groupTally = GroupTally.fromJson(group, action)
            groups[group["groupid"]] = groupTally

        return WholeTally(query, list(groups.values()), obj["lastAccess"], obj.get("_id"))

class ResultStore(object):
    def __init__(self, mongourl, database, collection, timeout):
        self.client = MongoClient(mongourl, serverSelectionTimeoutMS=roundup(timeout * 1000))
        self.client.server_info()
        self.collection = self.client[database][collection]
        self.timeout = timeout

    def get(self, query):
        for obj in self.collection.find({"queryid": query.id}, modifiers={"$maxTimeMS": roundup(self.timeout * 1000)}):
            wholeTally = WholeTally.fromJson(obj)
            if wholeTally.query == query:
                self.collection.update({"_id": obj["_id"]}, {"$set": {"lastAccess": datetime.utcnow()}}, modifiers={"$maxTimeMS": roundup(self.timeout * 1000)})
                return wholeTally
        return None

    def put(self, query):
        self.collection.insert(WholeTally(query, [], datetime.utcnow()).toJson(), modifiers={"$maxTimeMS": roundup(self.timeout * 1000)})

    def add(self, mongoid, groupid, tally):
        self.collection.update({"_id": mongoid, {"$push": {"groups": GroupTally(groupid, tally)}}}, modifiers={"$maxTimeMS": roundup(self.timeout * 1000)})

class MetadataFromMongoDB(object):
    def __init__(self, mongourl, database, collection, timeout):
        self.client = MongoClient(mongourl, serverSelectionTimeoutMS=roundup(timeout * 1000))
        self.client.server_info()
        self.collection = self.client[database][collection]
        self.timeout = timeout
        self._cache = {}

    def dataset(self, name, groups=(), columns=None, schema=True):
        key = (name, tuple(sorted(groups)), None if columns is None else tuple(sorted(columns)), schema)
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

            if columns is None:
                project["columns"] = True
                project["groups.segments"] = True
            else:
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

                self._cache[key] = Dataset.fromJson(results[0])

        return self._cache[key]

def populateMongoDBMetadata(dataset, mongourl, database, collection):
    client = MongoClient(mongourl)
    client[database][collection].insert_one(dataset.toJson())

# m = MetadataAPIServer(MetadataFromJson("/home/pivarski/diana/femtocode/tests"))
# m.start()

# from femtocode.rootio.dataset import ROOTDataset
# db = MetadataFromMongoDB("mongodb://localhost:27017", "metadb", "datasets", ROOTDataset, 1.0)

# metadataFileName = "tests/metadataFromRoot.yaml"
# populateMongo(ROOTDataset.fromYamlString(open(metadataFileName)), "mongodb://localhost:27017", "metadb", "datasets")
