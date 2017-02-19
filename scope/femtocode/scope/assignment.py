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

def assign(offset, numGroups, index, outof):
    fairShare = numGroups // outof
    oindex = (index + offset) % outof

    start = oindex * fairShare
    if oindex == outof - 1:
        stop = numGroups
    else:
        stop = (oindex+1) * fairShare

    return slice(start, stop)

def regress(offset, numGroups, outof, depth):
    fairShare = numGroups // outof
    if depth == 0:
        # exactly agree with assign
        return lambda i: (min(i // fairShare, outof - 1) - offset) % outof
    elif depth < outof:
        # different edge-case handling, but exactly subdivide an assignment among all workers
        return lambda i: ((i * outof**depth // fairShare) % outof - offset) % outof
    else:
        # just round-robin; continue until each group has been assigned to some surviving worker
        return lambda i: (i + depth - offset) % outof

def assignAsSlices(offset, numGroups, workers):
    assignments = {}
    for i, x in enumerate(workers):
        assignments[x] = assign(offset, numGroups, i, len(workers))
    return assignments

def reassign(offset, numGroups, workers, survivors):
    pass










# def assignExtra(offset, numGroups, unassigned, survivors):
#     assignments = {}

#     j = offset
#     for slce in unassigned:
#         for group in range(numGroups)[slce]:
#             j = j % len(survivors)
#             minion = survivors[j]
#             j += 1

#             if minion not in assignments:
#                 assignments[minion] = []
#             assignments[minion].append(group)

#     return assignments
