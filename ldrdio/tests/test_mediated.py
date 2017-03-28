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

import time
import unittest

import numpy

from femtocode.ldrdio.dataset import *

class TestMediated(unittest.TestCase):
    def runTest(self):
        pass

    def test_printout(self):
        metadb = MetadataFromLDRD("http://dbdata0vm.fnal.gov:9091/striped/app")
        ds = metadb.dataset("ZZ_13TeV_pythia8", groups=(96, 97, 98), columns=["Muon[]-pt", "Muon[]-eta", "Muon[]-phi"], schema=False)

        self.assertEqual(ds.toJson(), {'name': 'ZZ_13TeV_pythia8', 'numGroups': 99, 'numEntries': 985600, 'groups': [{'segments': {'Muon[]-eta': {'sizeLength': 10000, 'numEntries': 10000, 'dataLength': 42472}, 'Muon[]-phi': {'sizeLength': 10000, 'numEntries': 10000, 'dataLength': 42472}, 'Muon[]-pt': {'sizeLength': 10000, 'numEntries': 10000, 'dataLength': 42472}}, 'numEntries': 10000, 'id': 96}, {'segments': {'Muon[]-eta': {'sizeLength': 10000, 'numEntries': 10000, 'dataLength': 40616}, 'Muon[]-phi': {'sizeLength': 10000, 'numEntries': 10000, 'dataLength': 40616}, 'Muon[]-pt': {'sizeLength': 10000, 'numEntries': 10000, 'dataLength': 40616}}, 'numEntries': 10000, 'id': 97}, {'segments': {'Muon[]-eta': {'sizeLength': 5600, 'numEntries': 5600, 'dataLength': 23080}, 'Muon[]-phi': {'sizeLength': 5600, 'numEntries': 5600, 'dataLength': 23080}, 'Muon[]-pt': {'sizeLength': 5600, 'numEntries': 5600, 'dataLength': 23080}}, 'numEntries': 5600, 'id': 98}], 'class': 'femtocode.ldrdio.dataset.LDRDDataset', 'columns': {'Muon[]-eta': {'dataType': 'float64', 'apisize': u'Muon.@size', 'apidata': u'Muon.eta', 'data': 'Muon[]-eta', 'size': 'Muon[]-eta@size'}, 'Muon[]-phi': {'dataType': 'float64', 'apisize': u'Muon.@size', 'apidata': u'Muon.phi', 'data': 'Muon[]-phi', 'size': 'Muon[]-phi@size'}, 'Muon[]-pt': {'dataType': 'float64', 'apisize': u'Muon.@size', 'apidata': u'Muon.pt', 'data': 'Muon[]-pt', 'size': 'Muon[]-pt@size'}}, 'schema': None, 'urlhead': 'http://dbdata0vm.fnal.gov:9091/striped/app'})
