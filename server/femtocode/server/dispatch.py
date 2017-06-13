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

import sys
import time
import threading

import femtocode.asts.statementlist as statementlist
from femtocode.py23 import *
from femtocode.execution import ExecutionFailure
from femtocode.remote import Result
from femtocode.run.execution import NativeExecutor
from femtocode.server.assignment import assign
from femtocode.server.communication import *
from femtocode.server.mongodb import *

class Watchman(threading.Thread):
    def __init__(self, minions, checkperiod, deadthreshold):
        super(Watchman, self).__init__()
        self.minions = minions
        self.checkperiod = checkperiod
        self.deadthreshold = deadthreshold

        self.lock = threading.Lock()
        self.survivors = set(minions)
        self.lastErrorByMinion = {}
        self.lastError = None
        self.daemon = True

    def seterror(self, err, minion):
        if isinstance(err, HTTPError):
            self.lastError = ExecutionFailure(err, err.read())
        else:
            self.lastError = ExecutionFailure(err, "".join(traceback.format_exception(err.__class__, err, sys.exc_info()[2])))

        self.lastErrorByMinion[minion] = self.lastError

    def declaredead(self, minion):
        self.survivors.discard(minion)

    def declarelive(self, minion):
        if minion in self.minions:
            self.survivors.add(minion)

    def run(self):
        while True:
            # send heartbeats to the minions, keeping track of which ones respond successfully and which timeout or throw HTTP error
            for minion in self.minions:
                try:
                    sendpickle(minion, None, self.deadthreshold)
                except Exception as err:
                    self.seterror(err, minion)
                    self.declaredead(minion)
                else:
                    self.declarelive(minion)

            time.sleep(self.checkperiod)

    def assign(self, executor, groupidToUniqueid, groupids):
        # different datasets should be rotated differently in how they're assigned to computes
        offset = abs(hash(executor.query.dataset.name))

        numGroups = executor.query.dataset.numGroups
        unassigned = []

        with self.lock:
            dead = []
            if len(self.survivors) == 0:
                # no survivors? send the last error seen as a diagnostic (they *all* have errors, possibly
                # different errors, but the last one seen is usually pretty helpful in debugging)
                return self.lastError

            for minion in self.survivors:
                # call our magical assignment algorithm to eliminate cache dilution
                subset = assign(offset, groupids, numGroups, minion, self.minions, self.survivors)

                # only send the groupidToUniqueid that are relevant for this subset
                subg2u = dict((groupid, uniqueid) for groupid, uniqueid in groupidToUniqueid.items() if groupid in subset)

                try:
                    sendpickle(minion, AssignExecutor(executor, subg2u, subset), self.deadthreshold)

                except Exception as err:
                    self.seterror(err, minion)
                    dead.append(minion)
                    unassigned.extend(subset)
                
            # can't modify the set of survivors while iterating over it (in Python 3)
            for x in dead:
                self.declaredead(x)

        # recursively try to clean up work that couldn't be assigned in this round
        if len(unassigned) > 0:
            return self.assign(executor, unassigned, numGroups)

        # no errors encountered
        return None

    def cancel(self, query):
        with self.lock:
            for minion in self.minions:
                try:
                    sendpickle(minion, CancelQuery(query), self.deadthreshold)
                except Exception as err:
                    self.seterror(err, minion)
                    self.declaredead(minion)
                else:
                    self.declarelive(minion)

class Tallyman(object):
    @staticmethod
    def tallyme(query, status, failure):
        # use the status information collected from the ResultsStore to produce a single Result record that the client understands

        action = query.actions[-1]
        assert isinstance(action, statementlist.Aggregation), "last action must always be an aggregation"

        # these are the same for both failure and success
        loaded = float(status.loaded()) / query.dataset.numGroups
        computed = float(status.computed()) / query.dataset.numGroups
        done = status.computed() == query.dataset.numGroups
        computeTime = status.computeTime()
        lastUpdate = status.lastUpdate().isoformat(" ") + " UTC"

        # failure is passed in because it might have come from Watchman.assign
        if failure is not None:
            done = True
            return Result(loaded, computed, done, computeTime, lastUpdate, failure)

        else:
            tally = action.initialize()
            for result in status.results():
                tally = action.update(tally, result)

            return Result(loaded, computed, done, computeTime, lastUpdate, tally)

class Dispatch(HTTPServer):
    def __init__(self, metadb, store, watchman):
        self.metadb = metadb
        self.store = store
        self.watchman = watchman

    def __call__(self, environ, start_response):
        path = self.getpath(environ)

        try:
            if path == "metadata":
                # user is asking for metadata, forward it to whatever we're using to serve up metadata
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
                # user is submitting a query
                try:
                    query = Query.fromJson(self.getjson(environ))
                except:
                    return self.senderror("400 Bad Request", start_response)
                else:
                    # we might already have the completed result
                    status = self.store.get(query)
                    failure = status.failure()

                    if failure is not None:
                        # if any one of them has a failure, cancel the rest; no point in continuing
                        self.watchman.cancel(query)

                    else:
                        # whichever results aren't complete should be assigned to minions
                        # (if the minions are already working on them, they'll ignore the duplicate request)
                        missing = status.missingGroupids()
                        if len(missing) > 0:
                            # compile the query into machine code (ONLY IF submitting)
                            executor = NativeExecutor(query, False)
                            # submit; failure is only non-None if there are no survivors, so no need to cancel anything
                            failure = self.watchman.assign(executor, status.groupidToUniqueid(), missing)

                    # add up all results collected so far
                    result = Tallyman.tallyme(query, status, failure)

                    # and return the sum
                    return self.sendjson(result.toJson(), start_response)

            else:
                return self.senderror("400 Bad Request", start_response)

        except Exception as err:
            return self.senderror("500 Internal Server Error", start_response)

if __name__ == "__main__":
    from femtocode.dataset import MetadataFromJson

    metadb = MetadataFromJson("../tests/")
    # metadb = MetadataFromMongoDB("mongodb://localhost:27017", "metadb", "datasets", ROOTDataset, 1.0)
    store = ResultStore("mongodb://localhost:27017", "store", "queries", "groups", 1.0)
    watchman = Watchman(["http://localhost:8081"], 1.0, 0.1)
    watchman.start()

    server = Dispatch(metadb, store, watchman)
    server.start("", 8080)
