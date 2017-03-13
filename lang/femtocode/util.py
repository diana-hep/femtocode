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
import math

try:
    import Queue as queue
except ImportError:
    import queue

def roundup(x):
    return int(math.ceil(x))

def drainQueue(q):
    out = []
    while True:
        try:
            out.append(q.get_nowait())
        except queue.Empty:
            break
    return out

def dropIfPresent(d, key):
    try:
        del d[key]
    except KeyError:
        pass

class Serializable(object):
    def toJsonString(self):
        return json.dumps(self.toJson())

    def toJsonFile(self, file):
        json.dump(file, self.toJson())

    @classmethod
    def fromJsonString(cls, string):
        return cls.fromJson(json.loads(string))

    @classmethod
    def fromJsonFile(cls, file):
        return cls.fromJson(json.load(file))
