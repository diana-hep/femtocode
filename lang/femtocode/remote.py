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
import time
try:
    from urllib2 import urlparse, urlopen, HTTPError
except ImportError:
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from urllib.error import HTTPError

from femtocode.asts import statementlist
from femtocode.dataset import Dataset
from femtocode.execution import ExecutionFailure
from femtocode.util import *
from femtocode.workflow import Source

class Result(Serializable):
    def __init__(self, loadsDone, computesDone, done, computeTime, lastUpdate, data):
        self.loadsDone = loadsDone
        self.computesDone = computesDone
        self.done = done
        self.computeTime = computeTime
        self.lastUpdate = lastUpdate
        self.data = data

    def __repr__(self):
        return "Result({0}, {1}, {2}, {3}, {4}, {5})".format(self.loadsDone, self.computesDone, self.done, self.computeTime, self.lastUpdate, self.data)

    def toJson(self):
        return {"loadsDone": self.loadsDone,
                "computesDone": self.computesDone,
                "done": self.done,
                "computeTime": self.computeTime,
                "lastUpdate": self.lastUpdate,
                "data": self.data.toJson()}

    @staticmethod
    def fromJson(obj, action):
        assert isinstance(obj, dict)
        assert set(obj.keys()).difference(set(["_id"])) == set(["loadsDone", "computesDone", "done", "computeTime", "lastUpdate", "data"])

        if ExecutionFailure.failureJson(obj["data"]):
            data = ExecutionFailure.fromJson(obj["data"])
        else:
            data = action.tallyFromJson(obj["data"])

        return Result(obj["loadsDone"],
                      obj["computesDone"],
                      obj["done"],
                      obj["computeTime"],
                      obj["lastUpdate"],
                      data)

class FutureQueryResult(object):
    number = 0

    class PollForUpdates(threading.Thread):
        def __init__(self, future, ondone, onupdate, url, minpolldelay, maxpolldelay):
            super(FutureQueryResult.PollForUpdates, self).__init__()
            self.future = future
            self.ondone = ondone
            self.onupdate = onupdate
            self.url = url
            self.minpolldelay = minpolldelay
            self.maxpolldelay = maxpolldelay

            self.action = future.query.actions[-1]
            assert isinstance(self.action, statementlist.Aggregation), "last action must always be an aggregation"

            FutureQueryResult.number += 1
            self.name = "<Dataset \"{0}\" Query {1}>".format(self.future.query.dataset.name, FutureQueryResult.number)
            self.daemon = False   # why this is a thread: don't let Python exit until the callback is done!

        def update(self):
            try:
                obj = urlopen(self.url, self.future.query.toJsonString()).read()

            except HTTPError as err:
                out = "Remote server raised {0}\n\n--%<-----------------------------------------------------------------\n\nREMOTE {1}".format(str(err), err.read())
                raise RuntimeError(out)

            else:
                result = Result.fromJson(json.loads(obj), self.action)

                if not result.done:
                    self.lastTime = time.time()

                with self.future._lock:
                    self.future.loaded = result.loadsDone
                    self.future.computed = result.computesDone
                    self.future.done = result.done
                    self.future.wallTime = self.lastTime - self.startTime
                    self.future.computeTime = result.computeTime
                    self.future.lastUpdate = result.lastUpdate
                    self.future.data = result.data

                return result.done

        def run(self):
            self.startTime = time.time()
            self.lastTime = self.startTime

            polldelay = self.minpolldelay
            try:
                while True:
                    if self.update(): break
                    time.sleep(polldelay)
                    polldelay = min(polldelay * 2, self.maxpolldelay)

            finally:
                self.future._doneevent.set()

    def __init__(self, query, ondone, onupdate, url, minpolldelay, maxpolldelay):
        self.query = query
        self.query.dataset = self.query.dataset.strip()

        self.loaded = 0.0
        self.computed = 0.0
        self.done = False
        self.wallTime = 0.0
        self.computeTime = 0.0
        self.lastUpdate = None
        self.data = None
        self._lock = threading.Lock()
        self._doneevent = threading.Event()

        poll = FutureQueryResult.PollForUpdates(self, ondone, onupdate, url, minpolldelay, maxpolldelay)
        poll.start()

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

    def submit(self, query, ondone=None, onupdate=None, debug=False, minpolldelay=0.5, maxpolldelay=60.0):
        if debug:
            raise NotImplementedError
        return FutureQueryResult(query, ondone, onupdate, self.submit_url, minpolldelay, maxpolldelay)

###############################################################

if __name__ == "__main__":
    session = RemoteSession("http://localhost:8080")
    result = session.source("xy").define(z = "x + y").toPython(a = "z - 3", b = "z - 0.5").submit()
    for x in result.await():
        print x
