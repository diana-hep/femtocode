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

from femtocode.scope.messages import *

class DataAddress(Message):
    __slots__ = ("dataset", "column", "group")
    def __init__(self, dataset, column, group):
        self.dataset = dataset
        self.column = column
        self.group = group

class DummyFetch(threading.Thread):
    def __init__(self, occupants):
        super(DummyFetch, self).__init__()
        self.occupants = occupants

    def run(self):
        import time
        import random
        for occupant in self.occupants:
            time.sleep(random.expovariate(10.0))
            occupant.fill("." * occupant.totalBytes)
            with occupant.lock:
                occupant.filled = True
