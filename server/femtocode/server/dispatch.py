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
from wsgiref.simple_server import make_server

from femtocode.py23 import *
from femtocode.server.metadata import MetadataAPIServer
from femtocode.server.communication import *
from femtocode.workflow import Query

class DispatchAPIServer(HTTPServer):
    def __init__(self, metadb, accumulates, bindaddr="", bindport=8080, timeout=0.5):
        self.metadb = metadb
        self.accumulates = accumulates
        self.bindaddr = bindaddr
        self.bindport = bindport
        self.timeout = timeout

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "").lstrip("/")

        try:
            if path == "metadata":
                if isinstance(self.metadb, string_types):
                    # self.metadb the url of an upstream server
                    return self.gateway(self.metadb, environ, start_response)

                elif isinstance(self.metadb, MetadataAPIServer):
                    # self.metadb is a class embedded in this process
                    return self.metadb(environ, start_response)

                else:
                    assert isinstance(self.metadb, string_types) or isinstance(self.metadb, MetadataAPIServer), "self.metadb improperly configured")

            elif path == "submit":
                query = Query.fromJson(self.getjson(environ))

                cut = query.id % len(self.accumulates)
                statusUpdates = []
                for accumulate in self.accumulates[cut:] + self.accumulates[:cut]:
                    if isinstance(accumulate, string_types):
                        # accumulate the url of an upstream server
                        result = Result.fromJson(json.loads(self.gateway(accumulate, environ, start_response)))

                    elif isinstance(accumulate, AccumulateAPIServer):
                        # accumulate is a class embedded in this process
                        result = accumulate(environ, start_response)

                    else:
                        assert isinstance(accumulate, string_types) or isinstance(accumulate, AccumulateAPIServer), "self.accumulates improperly configured")

                    if isinstance(result, StatusUpdate):
                        statusUpdates.append(result)
                    else:
                        return self.sendjson(result.toJson(), start_response)

                assert len(statusUpdates) != 0, "all accumulate servers are unresponsive"
                bestChoice = min(statusUpdates, key=lambda x: x.load)
                bestChoice.assign(query)

                return self.sendjson({"assigned": bestChoice.name}, start_response)

            elif path == "store":
                return self.senderror("501 Not Implemented", start_response, "large object storage has not yet been implemented")

            else:
                return self.senderror("404 Not Found", start_response, "URL path not recognized by dispatcher: {0}".format(path))

        except Exception:
            return self.senderror("500 Internal Server Error", start_response)

# from femtocode.dataset import MetadataFromJson
# m = DispatchAPIServer(MetadataAPIServer(MetadataFromJson("/home/pivarski/diana/femtocode/tests")))
# m.start()

# m = DispatchAPIServer("http://localhost:8081", timeout=1.0)
# m.start()
