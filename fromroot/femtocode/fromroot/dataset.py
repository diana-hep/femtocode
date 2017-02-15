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

import femtocode.dataset

class ROOTSegment(femtocode.dataset.Segment):
    def __init__(self, dataName, dataLength, dataType, sizeName, numEntries, files, treeName):
        super(ROOTSegment, self).__init__(dataName, dataLength, dataType, sizeName, numEntries)
        self.files = files
        self.treeName = treeName

class ROOTGroup(femtocode.dataset.Group):
    def __init__(self, id, segments, numEntries):
        super(ROOTGroup, self).__init__(id, segments, numEntries)

class ROOTDataset(femtocode.dataset.Dataset):
    def __init__(self, name, schema, groups, numEntries):
        super(ROOTDataset, self).__init__(name, schema, groups, numEntries)
