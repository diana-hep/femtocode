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

import threading
import multiprocessing
try:
    import Queue as queue
except ImportError:
    import queue

from femtocode.scope.messages import *
from femtocode.scope.communication import *
from femtocode.scope.util import *
from femtocode.scope.assignment import *



import sys
import time
foremanName = sys.argv[1]
minionNames = sys.argv[2:]

class QueryInfo(Message):
    __slots__ = ("broadcastTime", "query")
    def __init__(self, broadcastTime, query):
        self.broadcastTime = broadcastTime
        self.query = query

class MinionInfo(Message):
    __slots__ = ("lastMessage", "queriesKnown")
    def __init__(self, lastMessage, queriesKnown):
        self.lastMessage = lastMessage
        self.queriesKnown = queriesKnown

class Foreman(threading.Thread):
    drumbeat = 1.0          # seconds
    responseThreshold = 3   # beats of the drum
    deadThreshold = 10      # beats of the drum

    def __init__(self):
        super(Foreman, self).__init__(queryPort, gaboPort)

        # treat as thread-local
        self.queryBroadcast = Broadcast(queryPort)
        self.gabos = context.socket(zmq.REP)
        self.gabos.bind("tcp://*:".format(gaboPort))
        self.gabos.RCVTIMEO = int(self.drumbeat * 1000)

        self.todoQueries = queue.Queue()   # [CompiledQuery]
        self.doneQueries = queue.Queue()   # [CompiledQuery]
        self.unassigned = {}               # {queryid: QueryInfo}
        self.minionInfos = {}              # {minion: MinionInfo}
        self.assignments = {}              # {queryid: {minion: [groupid]}}
        self.deltaAssignments = {}         # {minion: {queryid: [groupid]}} (items that haven't yet been reported to the minion)

        self.daemon = True

    def ping(self, minion, queryid):
        # when have we last heard from this minion and which queries has it responded to?
        now = time.time()
        if minion not in self.minionInfos:
            self.minionInfos[minion] = MinionInfo(now, set([queryid]) if queryid is not None else set())
        else:
            self.minionInfos[minion].lastMessage = now
            if queryid is not None:
                self.minionInfos[minion].queriesKnown.add(queryid)

    def updateMinions(self):
        now = time.time()
        for minion, minionInfo in list(self.minionInfos.items()):
            if now > minionInfo.lastMessage + (self.drumbeat * self.deadThreshold):
                # this minion is now dead
                del self.minionInfos[minion]

        print("minionInfos {}".format(self.minionInfos))

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
            survivors = set(self.minionInfos).intersection(oldAssignments.keys())

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
                    self.deltaAssignments[minion][queryid] = list(self.deltaAssignments.get(minion, {}).get(queryid, set()).union(delta))

                self.assignments[queryid] = newAssignments

        print("updateWork assignments ".format(self.assignments))

    def callForWork(self):
        now = time.time()

        # brand new queries get broadcast and temporarily held in self.unassigned
        for newQuery in drainQueue(self.todoQueries):
            # every queryid should be new (for a given foreman)
            assert newQuery.queryid not in self.unassigned
            assert newQuery.queryid not in self.assignments

            # every new query is a new chance for a minion to start working
            self.queryBroadcast.send(newQuery)
            self.unassigned[newQuery.queryid] = QueryInfo(now, newQuery)

        print("unassigned ".format(self.unassigned))

        # queries that have been in self.unassigned for the requisite number of drumbeats
        for queryid, queryInfo in list(self.unassigned.items()):
            if now > queryInfo.broadcastTime + (self.drumbeat * self.responseThreshold):
                # which minions have responded to the broadcast for this particular query?
                heardTheCall = [minion for minion, minionInfo in self.minionInfos.items() if queryid in minionInfo.queriesKnown]

                # only minions who have responded to the call for this particular query are assigned to it
                newAssignments = assign(queryid, queryInfo.query.numGroups, minionNames, heardTheCall)

                # everything is new; just add them to self.deltaAssignments and self.assignments
                for minion in minionNames:
                    self.deltaAssignments[minion][queryid] = newAssignments[minion]
                self.assignments[newQuery.queryid] = newAssignments

        print("callForWork assignments ".format(self.assignments))

    def run(self):
        while True:
            try:
                message = self.gabos.recv_pyobj()
            except zmq.Again:
                self.updateMinions()
                self.updateWork()
                self.callForWork()

            else:
                if isinstance(message, Heartbeat):
                    minion = message.identity
                    queryid = None

                elif isinstance(message, ResponseToQuery):
                    minion = message.minion
                    queryid = message.queryid
                    assert message.foreman == foremanName
                    
                else:
                    assert False, "unrecognized message from minion on gabo channel {0}".format(message)

                self.ping(minion, queryid)
                self.updateMinions()
                self.updateWork()
                self.callForWork()

                assignment = self.deltaAssignments.get(minion, {})
                for queryid in assignment:
                    assert queryid in self.minionInfos.get(minion)

                if len(assignment) > 0:
                    self.gabos.send_pyobj(WorkAssignment(foremanName, assignment))
                else:
                    self.gabos.send_pyobj(Heartbeat(foremanName))

foreman = Foreman(5557, 5556)
foreman.start()

print("foreman {} starting".format(foremanName))

time.sleep(1)
foreman.todoQueries.put(CompiledQuery(foremanName, 1, 100))

time.sleep(8)
foreman.todoQueries.put(CompiledQuery(foremanName, 2, 100))

time.sleep(100)
