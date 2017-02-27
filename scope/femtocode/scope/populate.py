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

from femtocode.rootio.dataset import ROOTDataset

def populateMongo(dataset, mongourl, database, collection):
    client = MongoClient(mongourl)
    client[database][collection].insert_one(dataset.toJson())

########################################### TODO: temporary!
metadataFileName = "tests/metadataFromRoot.yaml"
populateMongo(ROOTDataset.fromYamlString(open(metadataFileName)), "mongodb://localhost:27017", "metadb", "datasets")
###########################################
