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
                
    def __eq__(self, other):
        return self.__class__ == other.__class__ and all(getattr(self, n) == getattr(other, n) for n in self.__slots__)

    def __hash__(self):
        return hash((self.__class__,) + tuple(getattr(self, n) for n in self.__slots__))

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
    __slots__ = ("foreman", "queryid", "dataset", "inputs", "numGroups")
    def __init__(self, foreman, queryid, dataset, inputs, numGroups):
        self.foreman = foreman
        self.queryid = queryid
        self.dataset = dataset
        self.inputs = inputs
        self.numGroups = numGroups

class Heartbeat(Message):
    __slots__ = ("identity",)
    def __init__(self, identity):
        self.identity = identity

class ResponseToQuery(Message):
    __slots__ = ("minion", "foreman", "queryid")     # foreman and queryid are always paired because
    def __init__(self, minion, foreman, queryid):    # queryid is only unique for a given foreman
        self.minion = minion
        self.foreman = foreman
        self.queryid = queryid

class WorkAssignment(Message):
    __slots__ = ("foreman", "assignment")
    def __init__(self, foreman, assignment):
        self.foreman = foreman
        self.assignment = assignment                  # {queryid: [groupid]}
