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

import numpy

from femtocode.run.cache import CacheOccupant

class LDRDFetcher(threading.Thread):
    def __init__(self, occupants, workItem):
        super(LDRDFetcher, self).__init__()

        self.occupants = occupants
        self.workItem = workItem
        self.daemon = True

    def run(self):
        dataset = self.workItem.executor.query.dataset
        apiDataset = dataset.apiDataset

        for occupant in self.occupants:
            apiname = None

            if occupant.address.column.issize():
                for c in dataset.columns.values():
                    if c.size == occupant.address.column:
                        apiname = c.apisize
                        break
                assert apiname is not None

            else:
                apiname = dataset.columns[occupant.address.column].apidata

            array = apiDataset.column(apiname).stripe(occupant.address.group)

            occupant.rawarray[:] = array.view(CacheOccupant.untyped)[:]
            occupant.setfilled(occupant.totalBytes)
