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
import threading
try:
    from urllib2 import urlparse, urlopen, HTTPError
except ImportError:
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.error import HTTPError

from femtocode.dataset import Dataset
from femtocode.workflow import Source
from femtocode.execution import ExecutionFailure
from femtocode.util import *

class FutureQueryResult(object):
    class PollForUpdates(threading.Thread):
        def __init__(self, future, ondone, onupdate, url, minpolldelay, maxpolldelay):
            super(FutureQueryResult.PollForUpdates, self).__init__()
            self.future = future
            self.ondone = ondone
            self.onupdate = onupdate
            self.url = url
            self.minpolldelay = minpolldelay
            self.maxpolldelay = maxpolldelay
            self.daemon = False   # why this is a thread: don't let Python exit until the callback is done!

        def run(self):
            polldelay = self.minpolldelay
            while True:

                if getattr(self.future.query, "cancelled", False):
                    pass

                # HERE
                with self.future._lock:
                    self.future.loaded = 1.0
                    self.future.computed = 1.0
                    self.future.done = True
                    self.future.wallTime = 999.0
                    self.future.computeTime = 3.14
                    self.future.data = None

                if done:
                    self.future._doneevent.set()

                time.sleep(polldelay)
                polldelay = min(polldelay * 2, self.maxpolldelay)
            
    def __init__(self, query, ondone, onupdate, url, minpolldelay, maxpolldelay):
        self.query = query
        self.query.dataset = self.query.dataset.strip(set(columnNames()))

        self.loaded = 0.0
        self.computed = 0.0
        self.done = False
        self.wallTime = 0.0
        self.computeTime = 0.0
        self.data = None
        self._lock = threading.Lock()
        self._doneevent = threading.Event()

    def __repr__(self):
        return "<FutureQueryResult {0}% loaded {1}% computed{2}>".format(roundup(self.loaded * 100), roundup(self.computed * 100), " (wall: {0:.2g} sec, cpu: {1:.2g} core-sec)".format(self.wallTime, self.computeTime) if self.done else "")

    def await(self, timeout=None):
        self._doneevent.wait(timeout)
        if isinstance(self.data, ExecutionFailure):
            self.data.reraise()
        else:
            return self.data

    def cancel(self):
        self.query.cancelled = True

class MetadataFromRemote(object):
    def __init__(self, url, timeout=None):
        self.url = url
        self.timeout = timeout
        self.cache = {}

    def dataset(self, name):
        request = json.dumps({"name": name})
        if request not in self.cache:
            try:
                if self.timeout is None:
                    handle = urlopen(self.url, request)
                else:
                    handle = urlopen(self.url, request, self.timeout)

                self.cache[request] = Dataset.fromJson(json.loads(handle.read()), ignoreclass=True)

            except socket.timeout:
                raise IOError("Attempt to access {0} failed after {1} seconds.".format(self.url, self.timeout))

            except HTTPError as err:
                message = "Request for {0}\n         from {1} failed as {2}:\n\n{3}".format(request, self.url, str(err), err.read())
                raise IOError(message)

        return self.cache[request]

class RemoteSession(object):
    def __init__(self, url, timeout=None):
        self.url = url
        self.timeout = timeout
        self.metadata = MetadataFromRemote(self.metadata_url, self.timeout)

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

        p = urlparse.urlparse(self.url)
        def sub(x):
            return urlparse.urlunparse(urlparse.ParseResult(p.scheme, p.hostname + ":" + repr(p.port), p.path + "/" + x, "", "", ""))

        self.submit_url = sub("submit")
        self.metadata_url = sub("metadata")
        self.store_url = sub("store")

        if hasattr(self, "metadata"):
            self.metadata.url = self.metadata_url

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

        if hasattr(self, "metadata"):
            self.metadata.timeout = self.timeout

    def source(self, name):
        return Source(self, self.metadata.dataset(name))

    def submit(self, query, ondone=None, onupdate=None, minpolldelay=0.5, maxpolldelay=60.0):
        
        future = FutureQueryResult(query, ondone, onupdate, self.submit_url, minpolldelay, maxpolldelay)


        return future

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

