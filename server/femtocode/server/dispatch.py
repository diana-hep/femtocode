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

from femtocode.py23 import *
from femtocode.workflow import Query
from femtocode.server.messages import *
from femtocode.server.communication import *
from femtocode.server.execution import NativeAccumulateExecutor

class DispatchAPIServer(HTTPServer):
    def __init__(self, accumulates, metadb, bindaddr, bindport, timeout):
        self.accumulateClients = [HTTPInternalClient(x, timeout) for x in accumulates]
        self.metadb = metadb
        self.bindaddr = bindaddr
        self.bindport = bindport
        self.timeout = timeout

        assert len(self.accumulateClients) > 0

    def __call__(self, environ, start_response):
        path = self.getpath(environ)

        try:
            if path == "metadata":
                try:
                    obj = self.getjson(environ)
                    name = obj["name"]
                    assert isinstance(name, string_types)
                except:
                    return self.senderror("400 Bad Request", start_response)
                else:
                    dataset = self.metadb.dataset(name, (), None, True)
                    return self.sendjson(dataset.toJson(), start_response)

            elif path == "submit":
                try:
                    query = Query.fromJson(self.getjson(environ))
                except:
                    return self.senderror("400 Bad Request", start_response)
                else:
                    # rotate who gets to be the "first" accumulate so that load gets distributed
                    cut = abs(hash(query)) % len(self.accumulateClients)
                    accumulates = self.accumulateClients[cut:] + self.accumulateClients[:cut]

                    # ask everybody for their status at the same time
                    waiting = [x.async(GetQueryById(query.id)) for x in accumulates]
                    responses = [x.await() for x in waiting]

                    # those who respond positively to the queryid don't necessarily have the query
                    # (due to extremely unlikely queryid collision); follow-up and make sure they do
                    for i, response in enumerate(responses):
                        if isinstance(response, HaveIdPleaseSendQuery):
                            responses[i] = accumulates[i].sync(GetQuery(query))
                            responses[i].accumulate = accumulates[i]         # (attach for possible case 3)
                            
                    results = [x for x in responses if isinstance(x, Result)]

                    if len(results) == 0:
                        # case 1: nobody's heard of this query; assign it to the first accumulate
                        executor = NativeAccumulateExecutor(query)

                        firstgood = None
                        for accumulate in accumulates:
                            if isinstance(accumulate, DontHaveQuery):
                                firstgood = accumulate
                                break

                        if firstgood is None:
                            return senderror("500 Internal Server Error", start_response, "all accumulate nodes are unresponsive")
                        else:
                            result = firstgood.sync(AssignExecutor(executor))
                            return self.sendjson(result.resultMessage.toJson())

                    elif len(results) == 1:
                        # case 2: only one accumulate is working on it; return its (partial) result
                        return self.sendjson(results[0].resultMessage.toJson())

                    else:
                        # case 3: something went wrong (server was unreachable and then returned);
                        #         cancel queries on all but the first accumulate and return that
                        for extraresult in results[1:]:
                            extraresult.accumulate.sync(CancelQuery(query))  # (extraresult.accumulate attached above)

                        return self.sendjson(results[0].resultMessage.toJson())

            else:
                return self.senderror("400 Bad Request", start_response)

        except Exception as err:
            return self.senderror("500 Internal Server Error", start_response)
