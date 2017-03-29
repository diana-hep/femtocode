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

class ComputationStatus(Serializable):
    @staticmethod
    def empty(query, groupid):
        now = datetime.utcnow()
        return ComputationStatus(query, groupid, False, None, now, now)

    def __init__(self, query, groupid, loaded, result, lastAccess, lastUpdate):
        self.query = query
        self.groupid = groupid
        self.loaded = loaded
        self.result = result
        self.lastAccess = lastAccess
        self.lastUpdate = lastUpdate

    def toJson(self):
        return {"queryid": self.query.id,
                "query": self.query.stripToName().toJson(),
                "groupid": self.groupid,
                "loaded": self.loaded,
                "result": None if self.result is None else self.result.toJson(),
                "lastAccess": self.lastAccess,
                "lastUpdate": self.lastUpdate}

    @staticmethod
    def fromJson(obj, action):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["queryid", "query", "groupid", "loaded", "result", "lastAccess", "lastUpdate"])

        query = Query.fromJson(obj["query"])
        assert query.id == obj["queryid"]

        action = query.actions[-1]
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"

        if obj["result"] is None:
            result = None
        elif ExecutionFailure.failureJson(obj["result"]):
            result = ExecutionFailure.fromJson(obj["result"])
        else:
            result = action.tallyFromJson(obj["result"])

        return ComputationStatus(query, obj["groupid"], obj["loaded"], result, obj["lastAccess"], obj["lastUpdate"])

class ComputationStatuses(object):
    def __init__(self, statuses):
        self.statuses = statuses

    def groupidToUniqueid(self):
        return dict((status.groupid, uniqueid) for uniqueid, status in self.statuses.items())

    def uniqueidToGroupid(self):
        return dict((uniqueid, status.groupid) for uniqueid, status in self.statuses.items())

    def loaded(self):
        return dict((x.groupid, x.loaded) for x in self.statuses.values())

    def result(self):
        return dict((x.groupid, x.result) for x in self.statuses.values())

    def failure(self):
        for status in self.statuses.values():
            if isinstance(status.result, ExecutionFailure):
                return status.result
        return None

    def lastAccess(self):
        return max(x.lastAccess for x in self.statuses.values())

    def lastUpdate(self):
        return max(x.lastUpdate for x in self.statuses.values())

class ResultStore(object):
    def __init__(self, mongourl, database, collection, timeout):
        self.client = MongoClient(mongourl, socketTImeoutMS=roundup(timeout * 1000))
        self.client.server_info()
        self.collection = self.client[database][collection]

    def get(self, query, numGroups):
        now = datetime.utcnow()

        out = {}
        for obj in self.collection.find({"queryid": query.id}):
            if obj["query"] == query:
                out[obj["_id"]] = ComputationStatus.fromJson(obj)
                self.collection.update({"_id": obj["_id"], {"$set": {"lastAccess": now}}})

        groupids = set(x.groupid for x in out.values())

        # make sure there's a ComputationStatus for every groupid
        for groupid in range(numGroups):
            if groupid not in groupids:
                empty = ComputationStatus.empty(query, groupid)
                uniqueid = self.collection.insert({empty.toJson()})
                out[uniqueid] = empty

        return ComputationStatuses(out)






# class ComputeResult(Serializable):
#     def __init__(self, groupid, computeTime, subtally):
#         self.groupid = groupid
#         self.computeTime = computeTime
#         self.subtally = subtally

#     def toJson(self):
#         return {"groupid": self.groupid,
#                 "computeTime": self.computeTime,
#                 "subtally": self.subtally.toJson()}

#     @staticmethod
#     def fromJson(obj, action):
#         assert isinstance(obj, dict)
#         assert set(obj.keys()).difference(set(["_id"])) == set(["groupid", "computeTime", "subtally"])
#         return ComputeResult(obj["groupid"],
#                              obj["computeTime"],
#                              action.tallyFromJson(obj["subtally"]))

# class WholeData(Serializable):
#     @staticmethod
#     def empty(query):
#         return WholeData(query, [], [], None, datetime.utcnow(), datetime.utcnow())

#     def __init__(self, query, loaded, computeResults, failure, lastAccess, lastUpdate):
#         self.query = query
#         self.loaded = loaded
#         self.computeResults = computeResults
#         self.failure = None
#         self.lastAccess = lastAccess
#         self.lastUpdate = lastUpdate

#     def toJson(self):
#         return {"queryid": self.query.id,
#                 "query": self.query.stripToName().toJson(),
#                 "loaded": self.loaded,
#                 "computeResults": [x.toJson() for x in self.computeResults],
#                 "failure": None if self.failure is None else self.failure.toJson(),
#                 "lastAccess": self.lastAccess,
#                 "lastUpdate": self.lastUpdate}

#     @staticmethod
#     def fromJson(obj):
#         assert isinstance(obj, dict)
#         assert set(obj.keys()).difference(set(["_id"])) == set(["queryid", "query", "loaded", "computeResults", "failure", "lastAccess", "lastUpdate"])
#         query = Query.fromJson(obj["query"])
#         assert query.id == obj["queryid"]

#         action = query.actions[-1]
#         assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"

#         computeResults = [ComputeResult.fromJson(x, action) for x in obj["computeResults"]]
#         failure = None if obj["failure"] is None else ExecutionFailure.fromJson(obj["failure"])

#         return WholeData(query, obj["loaded"], computeResults, failure, obj["lastAccess"], obj["lastUpdate"])

class ResultStore(object):
    def __init__(self, mongourl, database, collection, timeout):
        self.client = MongoClient(mongourl, socketTimeoutMS=roundup(timeout * 1000))
        self.client.server_info()
        self.collection = self.client[database][collection]

    def get(self, query):
        # returns a WholeData and a uniqueid (or None, None)
        for obj in self.collection.find({"queryid": query.id}):
            wholeData = WholeData.fromJson(obj)
            if wholeData.query == query:
                self.collection.update({"_id": obj["_id"]}, {"$set": {"lastAccess": datetime.utcnow()}})
                return wholeData, obj["_id"]
        return None, None

    def create(self, wholeData):
        # returns the uniqueid
        return self.collection.insert(wholeData.toJson())

    def clearload(self, uniqueid):
        now = datetime.utcnow()
        self.collection.update({"_id": uniqueid}, {"$set": {"loaded": [], "lastAccess": now, "lastUpdate": now}})

    def clearfailure(self, uniqueid):
        now = datetime.utcnow()
        self.collection.update({"_id": uniqueid}, {"$set": {"failure": None, "lastAccess": now, "lastUpdate": now}})
        
    def pushload(self, uniqueid, groupid):
        now = datetime.utcnow()
        self.collection.update({"_id": uniqueid}, {"$push": {"loaded": groupid}, "$set": {"lastAccess": now, "lastUpdate": now}})

    def pushcompute(self, uniqueid, computeResult):
        now = datetime.utcnow()
        self.collection.update({"_id": uniqueid}, {"$push": {"computeResults": computeResult.toJson()}, "$set": {"lastAccess": now, "lastUpdate": now}})

    def setfailure(self, uniqueid, failure):
        now = datetime.utcnow()
        self.collection.update({"_id": uniqueid, "failure": None}, {"$set": {"failure": failure.toJson(), "lastAccess": now, "lastUpdate": now}})

    def removeold(self, cutoffdate):
        self.collection.remove({"lastAccess": {"$lt": cutoffdate}})

class MetadataFromMongoDB(object):
    def __init__(self, mongourl, database, collection, timeout):
        self.client = MongoClient(mongourl, socketTimeoutMS=roundup(timeout * 1000))
        self.client.server_info()
        self.collection = self.client[database][collection]
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

            results = list(self.collection.find(select, project))

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
