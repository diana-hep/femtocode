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
import sys
import traceback
from wsgiref.simple_server import make_server

from pymongo import MongoClient

from femtocode.util import *
from femtocode.dataset import Dataset
from femtocode.dataset import MetadataFromJson

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

class MetadataAPIServer(object):
    def __init__(self, metadb, bindaddr="", bindport=8080):
        self.metadb = metadb
        self.bindaddr = bindaddr
        self.bindport = bindport

        self.server = make_server(self.bindaddr, self.bindport, self)
        self.server.serve_forever()

    def __call__(self, environ, start_response):
        try:
            length = int(environ.get("CONTENT_LENGTH", "0"))
            data = environ["wsgi.input"].read(length)
            obj = json.loads(data)
            name = obj["name"]

            dataset = self.metadb.dataset(name, (), None, True)
            serialized = json.dumps(dataset.toJson())

        except Exception as err:
            start_response("400 Bad Request", [("Content-type", "text/plain")])
            return [traceback.format_exc()]

        else:
            start_response("200 OK", [("Content-type", "application/json")])
            return [serialized]

m = MetadataAPIServer(MetadataFromJson("/home/pivarski/diana/femtocode/tests"))

# from femtocode.rootio.dataset import ROOTDataset
# db = MetadataFromMongoDB("mongodb://localhost:27017", "metadb", "datasets", ROOTDataset, 1.0)
