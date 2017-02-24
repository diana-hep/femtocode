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

from femtocode.util import *

def assignIndex(offset, groupid, numGroups, outof, depth):
    fairShare = roundup(float(numGroups) / float(outof))
    if depth < outof:
        return (groupid * outof**depth // fairShare + offset) % outof
    else:
        return (groupid + depth + offset) % outof

def assign(offset, groupids, numGroups, thisworker, workers, survivors):
    out = []
    for groupid in groupids:
        depth = 0
        while True:  # will halt before depth == 2*len(workers), given the way assignIndex works
            worker = workers[assignIndex(offset, groupid, numGroups, len(workers), depth)]
            if worker in survivors:
                assignment = worker
                break
            depth += 1

        if worker == thisworker:
            out.append(groupid)

    return out
