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
import socket
try:
    from urllib2 import urlopen, HTTPError
except ImportError:
    from urllib.request import urlopen
    from urllib.error import HTTPError

from femtocode.dataset import Dataset

class MetadataFromRemote(object):
    def __init__(self, url, timeout=None):
        self.url = url
        self.timeout = timeout
        self.cache = {}

    def dataset(self, name, groups=(), columns=(), schema=True):
        request = json.dumps({"name": name, "groups": groups, "columns": map(str, columns), "schema": schema})
        if request not in self.cache:
            try:
                if self.timeout is None:
                    handle = urlopen(self.url, request)
                else:
                    handle = urlopen(self.url, request, self.timeout)

                self.cache[request] = Dataset.fromJson(json.loads(handle.read()))

            except socket.timeout:
                raise IOError("Attempt to access {0} failed after {1} seconds.".format(self.url, self.timeout))

            except HTTPError as err:
                message = "Request for {0}\n         from {1} failed as {2}:\n\n{3}".format(request, self.url, str(err), err.read())
                raise IOError(message)

        return self.cache[request]

# class RemoteSession(object):
#     def __init__(self, )


# set(columnNames())


#     def source(self, name, asdict=None, **askwds):
#         return Source(self, TestDataset.fromSchema(name, asdict, **askwds))

#     def submit(self, query, callback=None):
#         executor = Executor(query)
#         action = query.actions[-1]
#         assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"

#         tally = action.initialize()

#         for group in query.dataset.groups:
#             subtally = executor.run(executor.inarraysFromTest(group), group)
#             action.update(tally, subtally)

#         result = action.finalize(tally)
#         if callback is not None:
#             callback(result)
#         return result

