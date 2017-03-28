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

from femtocode.py23 import *
from femtocode.dataset import ColumnName
from femtocode.dataset import sizeType
from femtocode.run.compute import DataAddress
from femtocode.run.cache import CacheOccupant

class LDRDFetcher(threading.Thread):
    def __init__(self, occupants, workItem):
        self.occupants = occupants
        self.workItem = workItem
        self.daemon = True

    def run(self):
        workItem.executor.query.dataset



        workItem.group.apiDataset.column().stripe()

