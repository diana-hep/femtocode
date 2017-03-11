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

class DispatchAPIServer(object):
    def __init__(self, bindaddr="", bindport=8080):
        self.bindaddr = bindaddr
        self.bindport = bindport

        self.server = make_server(self.bindaddr, self.bindport, self)
        self.server.serve_forever()

    def __call__(self, environ, start_response):
        pass

        # try:
        #     length = int(environ.get("CONTENT_LENGTH", "0"))
        #     data = environ["wsgi.input"].read(length)
        #     obj = json.loads(data)
        #     name = obj["name"]

        #     dataset = self.metadb.dataset(name, (), None, True)
        #     serialized = json.dumps(dataset.toJson())

        # except Exception as err:
        #     start_response("400 Bad Request", [("Content-type", "text/plain")])
        #     return [traceback.format_exc()]

        # else:
        #     start_response("200 OK", [("Content-type", "application/json")])
        #     return [serialized]

