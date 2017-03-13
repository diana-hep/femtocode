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

from wsgiref.simple_server import make_server

from femtocode.py23 import *
from femtocode.server.metadata import MetadataAPIServer
from femtocode.server.util import *

class DispatchAPIServer(HTTPServer):
    def __init__(self, metadb, accumulates, bindaddr="", bindport=8080, timeout=None):
        self.metadb = metadb
        self.accumulates = accumulates
        self.bindaddr = bindaddr
        self.bindport = bindport
        self.timeout = timeout

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "").lstrip("/")

        if path == "metadata":
            if isinstance(self.metadb, string_types):
                # self.metadb the url of an upstream server
                return self.gateway(environ, start_response)

            elif isinstance(self.metadb, MetadataAPIServer):
                # self.metadb is a class embedded in this process
                return self.metadb(environ, start_response)

            else:
                return self.senderror("500 Internal Server Error", start_response)

        elif path == "submit":
            return self.senderror("501 Not Implemented", start_response)
                
        elif path == "store":
            return self.senderror("501 Not Implemented", start_response)

        else:
            return self.senderror("404 Not Found", start_response, "URL path not recognized by dispatcher: {0}".format(path))

# from femtocode.dataset import MetadataFromJson
# m = DispatchAPIServer(MetadataAPIServer(MetadataFromJson("/home/pivarski/diana/femtocode/tests")))
# m.start()

# m = DispatchAPIServer("http://localhost:8081", timeout=1.0)
# m.start()
