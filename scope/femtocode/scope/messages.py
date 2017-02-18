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

class Message(object):
    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, ", ".join(repr(getattr(self, n)) for n in self.__slots__))
                
class Query(Message):
    __slots__ = ("dataset", "workflow")
    def __init__(self, dataset, workflow):
        self.dataset = dataset   # just the name; look it up
        self.workflow = workflow

# class CompiledQuery(Message):
#     def __init__(self, accumulator, id, dataset, inputs, temporaries, result, objectcode, sequence, assignments):
#         self.accumulator = accumulator
#         self.id = id   # id is per-accumulator
#         # self.dataset = dataset
#         self.inputs = inputs
#         # self.temporaries = temporaries
#         # self.result = result
#         # self.objectcode = objectcode
#         # self.sequence = sequence
#         self.assignments = assignments

class CompiledQuery(Message):
    __slots__ = ("tallyman", "queryid")
    def __init__(self, tallyman, queryid, numGroups):
        self.tallyman = tallyman
        self.queryid = queryid
        self.numGroups = numGroups

class Heartbeat(Message):
    __slots__ = ("identity",)
    def __init__(self, identity):
        self.identity = identity

class GiveMeWork(Message):
    __slots__ = ("minion", "tallyman", "queryid")
    def __init__(self, minion, tallyman, queryid):
        self.minion = minion
        self.tallyman = tallyman
        self.queryid = queryid

class HeresSomeWork(Message):
    __slots__ = ("tallyman", "queryid", "groups")
    def __init__(self, tallyman, queryid, groups):
        self.tallyman = tallyman
        self.queryid = queryid
        self.groups = groups
