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

class Message(object): pass
                
class Query(Message):
    def __init__(self, dataset, workflow):
        self.dataset = dataset   # just the name; look it up
        self.workflow = workflow

class CompiledQuery(Message):
    def __init__(self, id, dataset, inputs, temporaries, result, objectcode, sequence):
        self.id = id
        self.dataset = dataset
        self.inputs = inputs
        self.temporaries = temporaries
        self.result = result
        self.objectcode = objectcode
        self.sequence = sequence

class TaskOnGroups(Message):
    def __init__(self, queryid, groups):
        self.queryid = queryid   # just the id; look it up
        self.groups = groups



