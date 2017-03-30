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
    def empty(uniqueQuery, groupid):
        now = datetime.utcnow()
        return ComputationStatus(uniqueQuery, groupid, False, 0.0, None, now, now)

    def __init__(self, uniqueQuery, groupid, loaded, computeTime, result, lastAccess, lastUpdate):
        self.uniqueQuery = uniqueQuery
        self.groupid = groupid
        self.loaded = loaded
        self.computeTime = computeTime
        self.result = result
        self.lastAccess = lastAccess
        self.lastUpdate = lastUpdate

    def toJson(self):
        return {"uniqueQuery": self.uniqueQuery,
                "groupid": self.groupid,
                "loaded": self.loaded,
                "computeTime": self.computeTime,
                "result": None if self.result is None else self.result.toJson(),
                "lastAccess": self.lastAccess,
                "lastUpdate": self.lastUpdate}

    @staticmethod
    def fromJson(obj, action):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["uniqueQuery", "groupid", "loaded", "computeTime", "result", "lastAccess", "lastUpdate"])

        if obj["result"] is None:
            result = None
        elif ExecutionFailure.failureJson(obj["result"]):
            result = ExecutionFailure.fromJson(obj["result"])
        else:
            result = action.tallyFromJson(obj["result"])

        return ComputationStatus(obj["uniqueQuery"], obj["groupid"], obj["loaded"], obj["computeTime"], result, obj["lastAccess"], obj["lastUpdate"])

class ComputationStatuses(object):
    def __init__(self, uniqueidToStatus):
        self.uniqueidToStatus = uniqueidToStatus

    def groupidToUniqueid(self):
        return dict((status.groupid, uniqueid) for uniqueid, status in self.uniqueidToStatus.items())

    def missingGroupids(self):
        return sorted(x.groupid for x in self.uniqueidToStatus.values() if x.result is None)

    def loaded(self):
        return sum(1 for x in self.uniqueidToStatus.values() if x.loaded)

    def computed(self):
        return sum(1 for x in self.uniqueidToStatus.values() if x.result is not None and not isinstance(x.result, ExecutionFailure))

    def computeTime(self):
        return sum(x.computeTime for x in self.uniqueidToStatus.values())

    def results(self):
        return [x.result for x in self.uniqueidToStatus.values() if x.result is not None and not isinstance(x.result, ExecutionFailure)]

    def failure(self):
        for status in self.uniqueidToStatus.values():
            if isinstance(status.result, ExecutionFailure):
                return status.result
        return None

    def lastAccess(self):
        return max(x.lastAccess for x in self.uniqueidToStatus.values())

    def lastUpdate(self):
        return max(x.lastUpdate for x in self.uniqueidToStatus.values())

class ResultStore(object):
    def __init__(self, mongourl, database, queries, groups, timeout):
        self.client = MongoClient(mongourl, socketTImeoutMS=roundup(timeout * 1000))
        self.client.server_info()
        self.queries = self.client[database][queries]
        self.groups = self.client[database][groups]

    def get(self, query):
        # see if this query exists in the queries collection
        stripped = query.stripToName()
        uniqueQuery = None
        for obj in self.queries.find({"queryid": query.id}):
            if Query.fromJson(obj["query"]) == stripped:
                uniqueQuery = obj["_id"]

        # if it doesn't, add it; if it does, update its lastAccess
        now = datetime.utcnow()
        if uniqueQuery is None:
            uniqueQuery = self.queries.insert({"queryid": query.id, "query": stripped.toJson(), "created": now, "lastAccess": now})
        else:
            self.queries.update({"_id": uniqueQuery}, {"$set": {"lastAccess": now}})

        # we'll need the action to interpret the ComputationStatus JSON
        action = query.actions[-1]
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"

        # read in all the ComputationStatuses that already exist
        uniqueidToStatus = {}
        for obj in self.groups.find({"uniqueQuery": uniqueQuery}):
            uniqueidToStatus[obj["_id"]] = ComputationStatus.fromJson(obj, action)

        # update their lastAccess en masse
        self.groups.update({"uniqueQuery": uniqueQuery}, {"$set": {"lastAccess": datetime.utcnow()}})

        # identify which groups have ComputationStatuses
        found = set(x.groupid for x in uniqueidToStatus.values())

        # for the ones that don't (usually everything or nothing), create them
        for groupid in range(query.dataset.numGroups):
            if groupid not in found:
                empty = ComputationStatus.empty(uniqueQuery, groupid)
                uniqueid = self.groups.insert(empty.toJson())
                uniqueidToStatus[uniqueid] = empty

        return ComputationStatuses(uniqueidToStatus)

    def setload(self, uniqueid):
        # set loaded to True and update lastAccess/lastUpdate
        now = datetime.utcnow()
        self.groups.update({"_id": uniqueid}, {"$set": {"loaded": True, "lastAccess": now, "lastUpdate": now}})

    def setresult(self, uniqueid, computeTime, result):
        # set the computeTime and result and update lastAccess/lastUpdate
        now = datetime.utcnow()
        self.groups.update({"_id": uniqueid}, {"$set": {"computeTime": computeTime, "result": result.toJson(), "lastAccess": now, "lastUpdate": now}})

    def removeOldQueries(self, threshold):
        # clear documents from the queries collection if they are strictly older than threshold
        self.queries.remove({"lastAccess": {"$lt": threshold}})

    def removeOldGroups(self, threshold):
        # clear documents from the groups (ComputationStatuses) collection if they are strictly older than threshold
        self.groups.remove({"lastAccess": {"$lt": threshold}})

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
