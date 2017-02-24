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

from femtocode.scope.util import *

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

# def assign(offset, numGroups, workers, survivors):
#     # must have somebody to give work to
#     assert len(survivors) > 0
#     # survivors must be members of the set of workers
#     assert set(survivors).difference(workers) == set()

#     # assign with a deterministic algorithm that will always give the same work to survivors
#     # and redistribute dead workers' work the same way to the survivors
#     assignments = dict((worker, []) for worker in workers)
#     for groupid in range(numGroups):
#         depth = 0
#         while True:  # will halt before depth == 2*len(workers), given the way assignIndex works
#             worker = workers[assignIndex(offset, groupid, numGroups, len(workers), depth)]
#             if worker in survivors:
#                 assignments[worker].append(groupid)
#                 break
#             depth += 1

#     # every group has to be assigned to somebody
#     assert set(sum(assignments.values(), [])) == set(range(numGroups))
#     # dead workers (non-survivors) must not be assigned any work
#     assert all(assignments[dead] == [] for dead in set(workers).difference(survivors))
#     # okay, good!
#     return assignments
