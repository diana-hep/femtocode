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

class GetQueryById(Message):
    def __init__(self, id):
        self.id = id

class DontHaveQueryId(Message):
    def __init__(self, load):
        self.load = load

class HaveIdPleaseSendQuery(Message): pass

class GetQuery(Message):
    def __init__(self, query):
        self.query = query

class Result(Message):
    def __init__(self, resultMessage):
        self.resultMessage = resultMessage

class Assign(Message):
    def __init__(self, query):
        self.query = query
