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

import multiprocessing

from femtocode.scope.messages import *
from femtocode.scope.communication import *

class QueryStore(multiprocessing.Process):
    def __init__(self, from_accumulate):
        super(QueryStore, self).__init__()
        self.from_accumulate = from_accumulate
        # self.daemon = True

    def run(self):
        compiledQueries = {}

        def install(compiledQuery):
            compiledQueries[compiledQuery.id] = compiledQuery
            print(compiledQueries)

        installer = Listen(self.from_accumulate, "install", install)

        def remove(queryid):
            try:
                del compiledQueries[queryid]
            except KeyError:
                pass
            print(compiledQueries)

        remover = Listen(self.from_accumulate, "remove", remove)

        def clear(dummy):
            compiledQueries.clear()
            print(compiledQueries)

        clearer = Listen(self.from_accumulate, "clear", clear)

        loop()

queryStore = QueryStore("tcp://127.0.0.1:5557")

queryStore.start()
