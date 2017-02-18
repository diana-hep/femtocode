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







import sys
import time
tallyman = sys.argv[1]
minions = set(sys.argv[2:])

gabos = context.socket(zmq.REP)
gabos.bind("tcp://*:5556")

queryBroadcast = Broadcast("5557")

startTime = time.time()
def now():
    return time.time() - startTime

class MinionWatcher(threading.Thread):
    delay = 1.0
    deadThreshold = 10

    def __init__(self):
        super(MinionWatcher, self).__init__()
        self.lastMessage = {}
        self.lastMessageLock = threading.Lock()
        self.daemon = True

    def update(self, minion):
        with self.lastMessageLock:
            self.lastMessage[minion] = now()

    def living(self):
        with self.lastMessageLock:
            return set(self.lastMessage.keys())

    def dead(self):
        return self.living().difference(minions)

    def run(self):
        while True:
            with self.lastMessageLock:
                for minion, lastMessage in list(self.lastMessage.items()):
                    if now() > lastMessage + (self.delay * self.deadThreshold):
                        print("{} is dead".format(minion))
                        del self.lastMessage[minion]

            time.sleep(self.delay)
            print(self.living())

minionWatcher = MinionWatcher()
minionWatcher.start()

print("tallyman {} starting".format(tallyman))

time.sleep(1)
queryBroadcast.send(CompiledQuery(tallyman, 1))

while True:
    message = gabos.recv_pyobj()
    print(message)
    if isinstance(message, GiveMeWork):
        if message.minion in minions:
            assert message.tallyman == tallyman
            minionWatcher.update(message.minion)
            gabos.send_pyobj(HeresSomeWork(tallyman, message.queryid, [1, 2, 3]))
        else:
            gabos.send(b"")

    elif isinstance(message, Heartbeat):
        if message.identity in minions:
            minionWatcher.update(message.identity)
            gabos.send_pyobj(Heartbeat(tallyman))
        else:
            gabos.send(b"")
