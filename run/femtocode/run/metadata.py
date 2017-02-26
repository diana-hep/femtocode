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

import os.path

class MetadataFromJson(object):
    def __init__(self, datasetClass, directory="."):
        self.datasetClass = datasetClass
        self.directory = directory
        self._cache = {}

    def dataset(self, name, groups=(), columns=(), schema=False):
        if name not in self._cache:
            fileName = os.path.join(self.directory, name) + ".json"
            self._cache[name] = self.datasetClass.fromJsonString(open(fileName).read())

        return self._cache[name]
