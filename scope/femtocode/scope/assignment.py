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

def assign(offset, numGroups, minions, survivors):
    fairShare = numGroups // len(minions)

    assignments = {}

    unassigned = []
    for i, minion in enumerate(minions):
        j = (i + offset) % len(minions)

        if j == len(minions) - 1:
            assignment = slice(j * fairShare, None)
        else:
            assignment = slice(j * fairShare, (j+1) * fairShare)

        if minion in survivors:
            assignments[minion] = assignment
        else:
            unassigned.append(assignment)

    return assignments, unassigned

def assignExtra(offset, numGroups, unassigned, survivors):
    assignments = {}

    j = offset
    for slce in unassigned:
        for group in range(numGroups)[slce]:
            j = j % len(survivors)
            minion = survivors[j]
            j += 1

            if minion not in assignments:
                assignments[minion] = []
            assignments[minion].append(group)

    return assignments
