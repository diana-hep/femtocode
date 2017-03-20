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

# from dispatch to accumulate

class GetQueryById(Message):
    def __init__(self, queryid):
        self.queryid = queryid

class GetQuery(Message):
    def __init__(self, query):
        self.query = query

class AssignExecutor(Message):
    def __init__(self, executor):
        self.executor = executor

class CancelQuery(Message):
    def __init__(self, query):
        self.query = query

# from accumulate back to dispatch

class DontHaveQuery(Message): pass

class HaveIdPleaseSendQuery(Message): pass

class Result(Message):
    def __init__(self, resultMessage):
        self.resultMessage = resultMessage

# from accumulate to compute

class AssignExecutorGroupids(Message):
    def __init__(self, executor, groupids):
        self.executor = executor
        self.groupids = groupids

class GetResults(Message):
    def __init__(self, queryids):
        self.queryids = queryids

class CancelQueryById(Message):
    def __init__(self, queryid):
        self.queryid = queryid

# from compute back to accumulate

class OneLoadDone(Message):
    def __init__(self, groupid):
        self.groupid = groupid

class OneComputeDone(Message):
    def __init__(self, groupid, computeTime, subtally):
        self.groupid = groupid
        self.computeTime = computeTime
        self.subtally = subtally

class OneFailure(Message):
    def __init__(self, failure):
        self.failure = failure

class Results(Message):
    def __init__(self, queryidToAssignment, queryidToMessages):
        self.queryidToAssignment = queryidToAssignment
        self.queryidToMessages = queryidToMessages
