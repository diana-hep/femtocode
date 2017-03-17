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
try:
    from urllib2 import urlparse, urlopen, HTTPError
except ImportError:
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.error import HTTPError

from femtocode.py23 import *
from femtocode.server.metadata import MetadataAPIServer
from femtocode.server.communication import *
from femtocode.workflow import Query

class DispatchAPIServer(HTTPServer):
    def __init__(self, metadb, accumulates, bindaddr="", bindport=8080):
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

                # NOTE: The following seek through accumulates is synchronous and blocking; each dead accumulate adds self.timeout (0.5 sec) to the
                #       total response time. If the number of accumulates ever becomes large (e.g. several), this will need to become asynchronous.
                cut = query.id % len(self.accumulates)
                statusUpdates = []
                finalResult = None
                for accumulate in self.accumulates[cut:] + self.accumulates[:cut]:
                    result = accumulate.result(query)

                    if result is None:   # timeout from upstream server
                        continue         # ignore it; use the other servers
                    elif isinstance(result, StatusUpdate):
                        result.accumulate = accumulate
                        statusUpdates.append(result)
                    else:
                        if finalResult is None:
                            finalResult = result

                        # make sure nobody else thinks they're running this query
                        query.cancelled = True

                if finalResult is not None:
                    return self.sendjson(result.toJson(), start_response)

                assert len(statusUpdates) != 0, "all accumulate servers are unresponsive"
                bestChoice = min(statusUpdates, key=lambda x: x.load)

                result = bestChoice.accumulate.assign(NativeAccumulateExecutor(query))
                return self.sendjson(result.toJson(), start_response)

            else:
                return self.senderror("404 Not Found", start_response, "URL path not recognized by dispatcher: {0}".format(path))

        except Exception:
            return self.senderror("500 Internal Server Error", start_response)
