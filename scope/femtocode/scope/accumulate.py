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
import threading
import time
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.scope.assignment import *
from femtocode.scope.communication import *
from femtocode.scope.messages import *
from femtocode.scope.util import *

########################################### TODO: temporary!
import sys
foremanName = sys.argv[1]
minionNames = sys.argv[2:]
###########################################

class QueryInfo(object):
    def __init__(self, broadcastTime, query):
        self.broadcastTime = broadcastTime
        self.query = query

    def __repr__(self):
        return "QueryInfo({0}, {1})".format(self.broadcastTime, self.query)

class MinionInfo(object):
    def __init__(self, lastMessage, queriesKnown):
        self.lastMessage = lastMessage
        self.queriesKnown = queriesKnown

    def __repr__(self):
        return "MinionInfo({0}, {1})".format(self.lastMessage, self.queriesKnown)

class Foreman(threading.Thread):
    responseThreshold = 0.030   # 30 ms      collect responses to a call: minimum possible latency for queries
    deadThreshold = 0.5         # 500 ms     previously active minions disappar
    listenThreshold = 1.0       # 1000 ms    no response from any minion; reset Server recv/send state

    def __init__(self, queryAddress, gaboAddress):
        super(Foreman, self).__init__()

        # accessed by external threads
        self.queryBroadcast = Broadcast(queryAddress)
        # thread-safe
        self.doneQueries = queue.Queue()

        # shared: self.unassigned can be changed by external threads, so it must be locked
        self.unassigned = {}               # {queryid: QueryInfo}
        self.lock = threading.Lock()

        # treat as thread-local
        self.gabos = Server(gaboAddress, self.listenThreshold)
        self.minionInfos = {}              # {minion: MinionInfo}
        self.assignments = {}              # {queryid: {minion: [groupid]}}
        self.deltaAssignments = {}         # {minion: {queryid: [groupid]}} (items that haven't yet been reported to the minion)

        self.daemon = True

    def ping(self, minion, queryid):
        # when have we last heard from this minion and which queries has it responded to?
        if minion not in self.minionInfos:
            self.minionInfos[minion] = MinionInfo(time.time(), set([queryid]) if queryid is not None else set())
        else:
            self.minionInfos[minion].lastMessage = time.time()
            if queryid is not None:
                self.minionInfos[minion].queriesKnown.add(queryid)

    def updateMinions(self):
        for minion, minionInfo in list(self.minionInfos.items()):
            if time.time() > minionInfo.lastMessage + self.deadThreshold:
                # this minion is now dead
                del self.minionInfos[minion]

    def updateWork(self):
        # get rid of all references to queries that are done or canceled
        for queryid in drainQueue(self.doneQueries):
            dropIfPresent(self.assignments, queryid)
            for assignments in self.deltaAssignments.values():
                dropIfPresent(assignments, queryid)
            for minionInfo in self.minionInfos.values():
                dropIfPresent(minionInfo.queriesKnown, queryid)

        # if any minions have died, reassign their old work
        for queryid, oldAssignments in list(self.assignments.items()):
            # minions available to a queryid always decreases (to avoid back-and-forth assignment)
            survivors = set(self.minionInfos).intersection(n for n, a in oldAssignments.items() if len(a) > 0)

            # FIXME: if this happens, cancel the query and return it to the user
            assert len(survivors) > 0

            # if set of surviving minions has actually changed since last assignment...
            if survivors != set(oldAssignments.keys()):
                numGroups = len(sum(oldAssignments.values(), []))
                newAssignments = assign(queryid, numGroups, minionNames, survivors)

                for minion in minionNames:
                    # what new groupids have been assigned to this minion since oldAssignments?
                    delta = set(newAssignments[minion]).difference(oldAssignments.get(minion, []))

                    # new work may accumulate if we don't hear from a minion for a few cycles
                    if minion not in self.deltaAssignments:
                        self.deltaAssignments[minion] = {}
                    self.deltaAssignments[minion][queryid] = self.deltaAssignments[minion].get(queryid, set()).union(delta)

                    # don't include any empty sets in the deltaAssignments
                    if len(self.deltaAssignments[minion][queryid]) == 0:
                        del self.deltaAssignments[minion]

                    # don't include any empty sets in the newAssignments
                    if len(newAssignments[minion]) == 0:
                        del newAssignments[minion]

                self.assignments[queryid] = newAssignments

    def newWork(self):
        # need a lock to access self.unassigned, since this is touched by both threads
        with self.lock:
            # queries that have been in self.unassigned for the requisite number of heartbeats
            for queryid, queryInfo in list(self.unassigned.items()):
                if time.time() > queryInfo.broadcastTime + self.responseThreshold:
                    # which minions have responded to the broadcast for this particular query?
                    heardTheCall = [minion for minion, minionInfo in self.minionInfos.items() if queryid in minionInfo.queriesKnown]

                    # only minions who have responded to the call for this particular query are assigned to it
                    newAssignments = assign(queryid, queryInfo.query.numGroups, minionNames, heardTheCall)

                    # everything is new; just add them to self.deltaAssignments and self.assignments
                    for minion in minionNames:
                        if len(newAssignments[minion]) > 0:
                            if minion not in self.deltaAssignments:
                                self.deltaAssignments[minion] = {}
                            self.deltaAssignments[minion][queryid] = set(newAssignments[minion])
                        else:
                            dropIfPresent(self.deltaAssignments, minion)

                    self.assignments[queryid] = newAssignments
                    del self.unassigned[queryid]

    def run(self):
        while True:
            # interaction is initiated by receiving a message from a minion
            message = self.gabos.recv()

            if message is None:
                pass
            elif isinstance(message, Heartbeat):
                minion = message.identity
                queryid = None
            elif isinstance(message, ResponseToQuery):
                minion = message.minion
                queryid = message.queryid
                assert message.foreman == foremanName
            else:
                assert False, "unrecognized message from minion on gabo channel {0}".format(message)

            # update state with the new information from minion
            if message is not None:
                self.ping(minion, queryid)
            self.updateMinions()
            self.updateWork()

            # respond to the minion, possibly giving it more work
            if message is not None:
                assignment = self.deltaAssignments.get(minion, {})

                for queryid in assignment:
                    assert queryid in self.minionInfos.get(minion).queriesKnown
                dropIfPresent(self.deltaAssignments, minion)

                if len(assignment) > 0:
                    self.gabos.send(WorkAssignment(foremanName, assignment))
                else:
                    self.gabos.send(Heartbeat(foremanName))

            # since the following locks, do it outside the server recv/send
            # its new information wouldn't be useful to the minion until the responseThreshold pause, anyway
            self.newWork()

    # startQuery can be called by external threads
    def startQuery(self, newQuery):
        # need a lock to access self.unassigned, since this is touched by both threads
        with self.lock:
            # brand new queries get broadcast and temporarily held in self.unassigned
            # every queryid should be new (for a given foreman)
            assert newQuery.queryid not in self.unassigned

            # every new query is a new chance for a minion to start working
            self.unassigned[newQuery.queryid] = QueryInfo(time.time(), newQuery)
            self.queryBroadcast.send(newQuery)

    # endQuery can be called by external threads
    def endQuery(self, queryid):
        self.doneQueries.push(queryid)

foreman = Foreman("tcp://*:5557", "tcp://*:5556")
foreman.start()

print("foreman {} starting".format(foremanName))

time.sleep(1)
print("submit 0!")
foreman.startQuery(CompiledQuery(foremanName, 0, "MuOnia", ["muons[]-pt", "jets[]-pt"], 1))

time.sleep(5)
print("submit 1!")
foreman.startQuery(CompiledQuery(foremanName, 1, "MuOnia", ["muons[]-pt", "jets[]-pt"], 1))

# time.sleep(1)
# print("submit 1!")
# foreman.startQuery(CompiledQuery(foremanName, 2, "MuOnia", ["muons[]-pt", "jets[]-pt"], 1))

# time.sleep(1)
# print("submit 1!")
# foreman.startQuery(CompiledQuery(foremanName, 3, "MuOnia", ["muons[]-pt", "jets[]-pt"], 1))

while True:
    time.sleep(1)
